import { VERSION } from "./version.js";

export function initializeUI(root = document) {
  if (typeof $ === "undefined") {
    return;
  }
  const tableEl = root.querySelector("#exerciseTable");
  const dropdownEl = root.querySelector("#exerciseDropdown");
  if (!tableEl || !dropdownEl) {
    return;
  }

  const table = $(tableEl).DataTable({ responsive: true });
  $(dropdownEl)
    .select2({ placeholder: "Filter by Exercise", allowClear: true })
    .on("change", function () {
      const val = $.fn.dataTable.util.escapeRegex($(this).val());
      table.column(0).search(val ? "^" + val + "$" : "", true, false).draw();
      $(".exercise-figure").hide();
      const figId = $(this).find("option:selected").data("fig");
      if (figId) {
        $("#fig-" + figId).show();
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

  // Ensure the initial UI is usable even if Pyodide fails to load.
  initializeUI(doc);

  const cachedHtml = localStorage.getItem("kaiserliftHtml");
  if (cachedHtml) {
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

    if (clearButton) {
      clearButton.addEventListener("click", () => {
        localStorage.removeItem("kaiserliftCsv");
        localStorage.removeItem("kaiserliftHtml");
        result.innerHTML = "";
      });
    }

    uploadButton.addEventListener("click", async () => {
      const file = fileInput.files?.[0];
      if (!file) {
        result.textContent = "Please select a CSV file.";
        return;
      }

      let progressInterval;
      let advance = () => {};
      if (progressBar) {
        progressBar.style.display = "block";
        progressBar.value = 0;
        let targetProgress = 0;
        advance = (val) => {
          if (val > targetProgress) targetProgress = val;
        };
        progressInterval = setInterval(() => {
          if (progressBar.value < Math.min(targetProgress, 90)) {
            progressBar.value += 1;
          }
        }, 100);
        advance(10);
      }

      try {
        const text = await file.text();
        advance(25);
        pyodide.globals.set("csv_text", text);
        advance(50);
        advance(75);
        const html = await pyodide.runPythonAsync(`
          import io
          from kaiserlift.pipeline import pipeline
          buffer = io.StringIO(csv_text)
          pipeline([buffer], embed_assets=False)
        `);
        result.innerHTML = "";
        result.innerHTML = html;
        localStorage.setItem("kaiserliftCsv", text);
        localStorage.setItem("kaiserliftHtml", html);
        initializeUI(result);
        if (progressBar) {
          advance(90);
          await new Promise((resolve) => {
            const wait = setInterval(() => {
              if (progressBar.value >= 90) {
                clearInterval(wait);
                resolve();
              }
            }, 50);
          });
          if (progressInterval) clearInterval(progressInterval);
          progressBar.value = 100;
        }
      } catch (err) {
        console.error(err);
        result.textContent = "Failed to process CSV: " + err;
      } finally {
        if (progressInterval) clearInterval(progressInterval);
        pyodide.globals.delete("csv_text");
        if (progressBar) progressBar.style.display = "none";
      }
    });
  } catch (err) {
    console.error(err);
    result.textContent = "Failed to initialize Pyodide: " + err;
  }
}

if (typeof window !== "undefined") {
  init().catch((err) => console.error(err));
}
