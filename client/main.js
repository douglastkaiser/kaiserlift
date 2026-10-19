import { VERSION } from "./version.js";

export function initializeUI(root = document) {
  if (typeof window !== "undefined" && window.initializeDashboard &&
      root.querySelector("[data-exercise-panel], [data-plot]")) {
    window.initializeDashboard(root);
    return;
  }
  if (typeof $ === "undefined") {
    return;
  }
  const tableEl = root.querySelector("#exerciseTable");
  const dropdownEl = root.querySelector("#exerciseDropdown");
  if (!tableEl || !dropdownEl) {
    return;
  }

  // Check if DataTable is already initialized to prevent reinitialization error
  const table = ($.fn.DataTable && $.fn.DataTable.isDataTable(tableEl))
    ? $(tableEl).DataTable()
    : $(tableEl).DataTable({ responsive: true });
  $(dropdownEl)
    .select2({ placeholder: "Filter by Exercise", allowClear: true })
    .on("change", function () {
      const val = $.fn.dataTable.util.escapeRegex($(this).val());
      table.column(0).search(val ? "^" + val + "$" : "", true, false).draw();
      $(".exercise-figure").hide();
      const figId = $(this).find("option:selected").data("fig");
      if (figId) {
        $("#fig-" + figId + "-wrapper").show();
      }
    });
}

async function fetchWheel(doc) {
  const bases = [];
  try {
    bases.push(new URL(import.meta.url));
  } catch (_) {}
  if (doc?.baseURI) {
    bases.push(new URL(doc.baseURI));
  }

  const names = [
    "kaiserlift.whl",
    `kaiserlift-${VERSION}-py3-none-any.whl`,
    "dist/kaiserlift.whl",
    `dist/kaiserlift-${VERSION}-py3-none-any.whl`,
  ];

  const candidates = [];
  for (const base of bases) {
    for (const name of names) {
      candidates.push(new URL(name, base));
    }
  }

  for (const url of candidates) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return { response, url: url.href };
      }
      console.error(`Wheel fetch returned ${response.status} at ${url.href}`);
    } catch (err) {
      console.error("Failed to fetch Pyodide wheel", url.href, err);
    }
  }
  console.error(
    "Failed to fetch wheel from known locations: " +
      candidates.map((u) => u.href).join(", "),
  );
  return null;
}

export async function init(loadPyodide, doc = document) {
  const result = doc.getElementById("result");
  const sampleHtml = result.innerHTML;
  const running = doc.body?.dataset?.trainingMode === "running";
  const cachePrefix = running ? "kaiserliftRunning" : "kaiserlift";
  const runtimeStatus = doc.getElementById("runtimeStatus");
  const importButton = doc.getElementById("uploadButton");
  if (importButton) importButton.disabled = true;
  const setStatus = message => { if (runtimeStatus) runtimeStatus.textContent = message; };

  // Ensure the initial UI is usable even if Pyodide fails to load.
  initializeUI(doc);

  const cachedHtml = localStorage.getItem(cachePrefix + "Html");
  if (cachedHtml && cachedHtml.includes('data-lab-view')) {
    result.innerHTML = cachedHtml;
    initializeUI(result);
  }

  try {
    const loader =
      loadPyodide ??
      (await import(
        "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.mjs"
      )).loadPyodide;
    const pyodide = await loader();
    await pyodide.loadPackage(["pandas", "numpy", "matplotlib", "micropip"]);

    const wheel = await fetchWheel(doc);
    try {
      if (wheel) {
        const data = new Uint8Array(await wheel.response.arrayBuffer());
        const wheelName = wheel.url.split("/").pop();
        pyodide.FS.writeFile(wheelName, data);
        await pyodide.runPythonAsync(`
import micropip
await micropip.install('${wheelName}')
`);
      } else {
        console.warn("Falling back to installing kaiserlift from PyPI");
        await pyodide.runPythonAsync(`
import micropip
await micropip.install('kaiserlift')
`);
      }
    } catch (err) {
      console.error("Failed to install kaiserlift", err);
      throw err;
    }

    const fileInput = doc.getElementById("csvFile");
    const uploadButton = doc.getElementById("uploadButton");
    const progressBar = doc.getElementById("uploadProgress");
    const clearButton = doc.getElementById("clearButton");
    uploadButton.disabled = false;
    setStatus("Importer ready / Choose a CSV file to begin.");

    async function processText(text) {
      pyodide.globals.set("csv_text", text);
      try {
        const pipelineImport = running
          ? "from kaiserlift.running_pipeline import running_pipeline as pipeline"
          : "from kaiserlift.pipeline import pipeline";
        return await pyodide.runPythonAsync(`
import io
${pipelineImport}
buffer = io.StringIO(csv_text)
pipeline([buffer], embed_assets=False)
`);
      } finally {
        pyodide.globals.delete("csv_text");
      }
    }

    // Rebuild older cached layouts from their original CSV in the new design.
    const savedCsv = localStorage.getItem(cachePrefix + "Csv");
    if (cachedHtml && !cachedHtml.includes('data-lab-view') && savedCsv) {
      result.innerHTML = await processText(savedCsv);
      initializeUI(result);
      localStorage.setItem(cachePrefix + "Html", result.innerHTML);
    }

    if (clearButton) {
      clearButton.addEventListener("click", () => {
        localStorage.removeItem(cachePrefix + "Csv");
        localStorage.removeItem(cachePrefix + "Html");
        result.innerHTML = sampleHtml;
        initializeUI(result);
        setStatus("Saved data cleared / Showing the example performance map.");
      });
    }

    uploadButton.addEventListener("click", async () => {
      const importError = doc.getElementById("importError");
      if (importError) importError.hidden = true;
      const file = fileInput.files?.[0];
      if (!file) {
        showError("No file selected", "Please select a CSV file to upload.");
        return;
      }

      // Validate file type
      if (!file.name.toLowerCase().endsWith('.csv')) {
        showError("Invalid file type", "Please upload a CSV file. Selected file: " + file.name);
        return;
      }

      uploadButton.disabled = true;
      setStatus("Reading your training history…");
      const advance = value => {
        if (progressBar) {
          progressBar.style.display = "block";
          progressBar.value = value;
        }
      };
      advance(10);

      try {
        const text = await file.text();
        advance(25);

        // Validate CSV format
        if (!text.includes('Date') || !text.includes('Exercise')) {
          throw new Error('Invalid CSV format. Please ensure your CSV contains "Date" and "Exercise" columns. Use FitNotes export format.');
        }

        advance(50);
        const html = await processText(text);
        result.innerHTML = "";
        result.innerHTML = html;
        localStorage.setItem(cachePrefix + "Csv", text);
        localStorage.setItem(cachePrefix + "Html", html);
        initializeUI(result);
        advance(100);
        setStatus("Data loaded / Your performance map is ready.");

      } catch (err) {
        console.error(err);
        showError("Processing Failed", getErrorMessage(err));
      } finally {
        uploadButton.disabled = false;
        if (progressBar) progressBar.style.display = "none";
      }
    });

    function getErrorMessage(err) {
      const errorStr = err.toString();
      if (running) {
        return "Use a running CSV with Date, Exercise, Distance and Duration columns. " + errorStr;
      }

      if (errorStr.includes('KeyError') || errorStr.includes('columns')) {
        return `Missing required columns in CSV. Please ensure your CSV has these columns: Date, Exercise, Category, Weight, Reps.

Expected format:
Date,Exercise,Category,Weight,Reps
2022-09-14,Bench Press,Chest,135.0,10

Error details: ${errorStr}`;
      }

      if (errorStr.includes('Invalid CSV format')) {
        return err.message + `

Expected CSV format:
Date,Exercise,Category,Weight,Reps
2022-09-14,Flat Barbell Bench Press,Chest,45.0,10
2022-09-14,Dumbbell Curl,Biceps,35.0,10`;
      }

      return `Failed to process CSV: ${errorStr}

Common issues:
• CSV is missing required columns (Date, Exercise, Category, Weight, Reps)
• Data format is incorrect
• File is corrupted or empty

Please check your CSV file and try again.`;
    }

    function showError(title, message) {
      const escape = value => String(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '\"': "&quot;", "'": "&#39;"
      })[char]);
      setStatus(title + " / " + message);
      // A separate alert preserves the graph while explaining import errors.
      const alert = doc.getElementById("importError");
      if (alert) {
        alert.hidden = false;
        alert.innerHTML = `<h3>${escape(title)}</h3><pre>${escape(message)}</pre>`;
      }
    }

  } catch (err) {
    console.error(err);
    setStatus("CSV importer unavailable. Reload to try again. Your charts are still available.");
  }
}

if (typeof window !== "undefined") {
  init().catch((err) => console.error(err));
}
