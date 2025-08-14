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
  const candidates = [];
  try {
    candidates.push(new URL("kaiserlift.whl", import.meta.url));
  } catch (_) {}
  if (doc?.baseURI) {
    candidates.push(new URL("kaiserlift.whl", doc.baseURI));
    candidates.push(new URL("client/kaiserlift.whl", doc.baseURI));
  }
  for (const url of candidates) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return { response, url: url.href };
      }
      console.error(
        `Wheel fetch returned ${response.status} at ${url.href}`,
      );
    } catch (err) {
      console.error("Failed to fetch Pyodide wheel", url.href, err);
    }
  }
  throw new Error(
    "Failed to fetch wheel from known locations: " +
      candidates.map((u) => u.href).join(", "),
  );
}

export async function init(loadPyodide, doc = document) {
  const result = doc.getElementById("result");

  // Ensure the initial UI is usable even if Pyodide fails to load.
  initializeUI(doc);

  try {
    const loader =
      loadPyodide ??
      (await import(
        "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.mjs"
      )).loadPyodide;
    const pyodide = await loader();
    await pyodide.loadPackage(["pandas", "numpy", "matplotlib", "micropip"]);

    const { response, url: wheelUrl } = await fetchWheel(doc);
    const data = new Uint8Array(await response.arrayBuffer());
    const wheelName = wheelUrl.split("/").pop();
    pyodide.FS.writeFile(wheelName, data);
    try {
      await pyodide.runPythonAsync(`
import micropip
await micropip.install('${wheelName}')
`);
    } catch (err) {
      console.error("Failed to install wheel", wheelName, err);
      throw err;
    }

    const fileInput = doc.getElementById("csvFile");
    const uploadButton = doc.getElementById("uploadButton");

    uploadButton.addEventListener("click", async () => {
      const file = fileInput.files?.[0];
      if (!file) {
        result.textContent = "Please select a CSV file.";
        return;
      }

      try {
        const text = await file.text();
        pyodide.globals.set("csv_text", text);
        const html = await pyodide.runPythonAsync(`
import io
from kaiserlift.pipeline import pipeline
buffer = io.StringIO(csv_text)
pipeline([buffer], embed_assets=False)
`);
        result.innerHTML = "";
        result.innerHTML = html;
        initializeUI(result);
      } catch (err) {
        console.error(err);
        result.textContent = "Failed to process CSV: " + err;
      } finally {
        pyodide.globals.delete("csv_text");
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
