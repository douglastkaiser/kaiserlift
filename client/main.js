import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.mjs";

async function main() {
  const pyodide = await loadPyodide();

  const fileInput = document.getElementById("csvFile");
  const result = document.getElementById("result");
  const uploadButton = document.getElementById("uploadButton");

  uploadButton.addEventListener("click", async () => {
    const file = fileInput.files?.[0];
    if (!file) {
      result.textContent = "Please select a CSV file.";
      return;
    }

    try {
      const text = await file.text();
      pyodide.FS.writeFile("uploaded.csv", text);
      const html = await pyodide.runPythonAsync(`
import pandas as pd
pd.read_csv('uploaded.csv').head().to_html()
`);
      result.innerHTML = html;
    } catch (err) {
      console.error(err);
      result.textContent = "Failed to process CSV.";
    }
  });
}

main();
