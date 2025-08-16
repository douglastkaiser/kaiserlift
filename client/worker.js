import { VERSION } from './version.js';

console.log('client worker: starting');

async function fetchWheel() {
  const bases = [];
  try {
    bases.push(new URL(import.meta.url));
  } catch (_) {}
  if (self.location?.href) {
    bases.push(new URL(self.location.href));
  }

  const names = [
    'kaiserlift.whl',
    `kaiserlift-${VERSION}-py3-none-any.whl`,
    'dist/kaiserlift.whl',
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
      console.error('Failed to fetch Pyodide wheel', url.href, err);
    }
  }
  console.error(
    'Failed to fetch wheel from known locations: ' +
      candidates.map((u) => u.href).join(', '),
  );
  return null;
}

const pyodideReady = (async () => {
  console.log('client worker: loading pyodide');
  const { loadPyodide } = await import(
    'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.mjs'
  );
  const pyodide = await loadPyodide();
  console.log('client worker: pyodide loaded');
  await pyodide.loadPackage(['pandas', 'numpy', 'matplotlib', 'micropip']);

  const wheel = await fetchWheel();
  try {
    if (wheel) {
      console.log('client worker: installing wheel from', wheel.url);
      const data = new Uint8Array(await wheel.response.arrayBuffer());
      const wheelName = wheel.url.split('/').pop();
      pyodide.FS.writeFile(wheelName, data);
      await pyodide.runPythonAsync(`
import micropip
await micropip.install('${wheelName}')
`);
    } else {
      console.warn('Falling back to installing kaiserlift from PyPI');
      await pyodide.runPythonAsync(`
import micropip
await micropip.install('kaiserlift')
`);
    }
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
