export function workerThread() {
  console.log('client worker: starting');

  const pyodideReady = (async () => {
    console.log('client worker: loading pyodide');
    const { loadPyodide } = await import(
      'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.mjs'
    );
    const pyodide = await loadPyodide();
    console.log('client worker: pyodide loaded');
    await pyodide.loadPackage(['pandas', 'numpy', 'matplotlib', 'micropip']);

    try {
      console.log('client worker: installing kaiserlift from PyPI');
      await pyodide.runPythonAsync(`
import micropip
await micropip.install('kaiserlift')
`);
    } catch (err) {
      console.error('Failed to install kaiserlift', err);
      throw err;
    }

    return pyodide;
  })();

  self.addEventListener('message', async (event) => {
    const csv = event.data?.csv;
    if (typeof csv !== 'string') {
      return;
    }
    console.log('client worker: received CSV');
    try {
      const pyodide = await pyodideReady;
      pyodide.globals.set('csv_text', csv);
      const html = await pyodide.runPythonAsync(`
import io
from kaiserlift.pipeline import pipeline
buffer = io.StringIO(csv_text)
pipeline([buffer], embed_assets=False)
`);
      pyodide.globals.delete('csv_text');
      console.log('client worker: pipeline completed');
      self.postMessage({ type: 'result', html });
    } catch (err) {
      console.error(err);
      self.postMessage({ type: 'error', error: err.toString() });
    }
  });
}
