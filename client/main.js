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
    const wheelUrl = "client/kaiserlift-0.1.24-py3-none-any.whl";
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

if (typeof window !== "undefined") {
  init().catch((err) => console.error(err));
}
