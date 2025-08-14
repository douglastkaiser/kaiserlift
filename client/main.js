export function initializeUI(root = document) {
  const $root = typeof window !== "undefined" && window.$ ? window.$(root) : null;
  if (!$root) {
    return;
  }

  const tableEl = $root.find("#exerciseTable");
  if (!tableEl.length) {
    return;
  }
  const table = tableEl.DataTable({ responsive: true });

  const dropdown = $root.find("#exerciseDropdown");
  if (dropdown.length) {
    dropdown.select2({ placeholder: "Filter by Exercise", allowClear: true });
    dropdown.on("change", function () {
      const val = window.$.fn.dataTable.util.escapeRegex(window.$(this).val());
      table.column(0).search(val ? "^" + val + "$" : "", true, false).draw();

      window.$(".exercise-figure").hide();
      const figId = window.$(this).find("option:selected").data("fig");
      if (figId) {
        window.$("#fig-" + figId).show();
      }
    });
  }
}

export async function init(loadPyodide, doc = document) {
  const result = doc.getElementById("result");

  try {
    const loader =
      loadPyodide ??
      (await import(
        "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.mjs"
      )).loadPyodide;
    const pyodide = await loader();
    await pyodide.loadPackage(["pandas", "numpy", "matplotlib", "micropip"]);
    const wheelUrl = "client/kaiserlift-0.1.25-py3-none-any.whl";
    const response = await fetch(wheelUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch wheel: ${response.status}`);
    }
    const data = new Uint8Array(await response.arrayBuffer());
    const wheelName = wheelUrl.split("/").pop();
    pyodide.FS.writeFile(wheelName, data);
    await pyodide.runPythonAsync(`
import micropip
await micropip.install('${wheelName}')
`);

    const fileInput = doc.getElementById("csvFile");
    const uploadButton = doc.getElementById("uploadButton");

    uploadButton.addEventListener("click", async () => {
      const file = fileInput.files?.[0];
      if (!file) {
        result.textContent = "Please select a CSV file.";
        return;
      }

      try {
        result.innerHTML = "";
        const text = await file.text();
        pyodide.globals.set("csv_text", text);
        const html = await pyodide.runPythonAsync(`
import io
from kaiserlift.pipeline import pipeline
buffer = io.StringIO(csv_text)
pipeline([buffer])
`);
        result.innerHTML = html;
        initializeUI(result);
      } catch (err) {
        console.error(err);
        result.textContent = "Failed to process CSV: " + err;
      } finally {
        pyodide.globals.delete("csv_text");
      }
    });
    initializeUI(doc);
  } catch (err) {
    console.error(err);
    result.textContent = "Failed to initialize Pyodide: " + err;
  }
}

if (typeof window !== "undefined") {
  init().catch((err) => console.error(err));
}
