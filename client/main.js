import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.mjs";

async function main() {
  const result = document.getElementById("result");

  try {
    const pyodide = await loadPyodide();
    await pyodide.loadPackage(["pandas", "numpy", "matplotlib", "micropip"]);
    await pyodide.runPythonAsync(`
import micropip
await micropip.install('client/kaiserlift.whl')
`);

    const fileInput = document.getElementById("csvFile");
    const uploadButton = document.getElementById("uploadButton");

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
pipeline([buffer])
`);
        result.innerHTML = html;
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

main().catch((err) => console.error(err));
