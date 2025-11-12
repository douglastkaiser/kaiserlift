import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_pipeline_via_pyodide(tmp_path: Path) -> None:
    """Execute the pipeline through the browser client using a Pyodide stub."""

    script = tmp_path / "run.mjs"
    (Path("client/version.js")).write_text("export const VERSION = '0.0.0';\n")
    script.write_text(
        textwrap.dedent(
            f"""
            import {{ init }} from 'file://{Path("client/main.js").resolve().as_posix()}';
            import {{ spawnSync }} from 'child_process';
            globalThis.fetch = async (url) => {{
              console.log(url.href.endsWith('/client/kaiserlift.whl'));
              return new Response(new Uint8Array(), {{ status: 200 }});
            }};

            const localStorage = {{
              _map: new Map(),
              getItem(key) {{ return this._map.has(key) ? this._map.get(key) : null; }},
              setItem(key, val) {{ this._map.set(key, val); }},
              removeItem(key) {{ this._map.delete(key); }}
            }};
            globalThis.localStorage = localStorage;

            const initCalls = [];
            globalThis.$ = (el) => ({{
              DataTable: () => {{
                initCalls.push(el);
                return {{
                  column: () => ({{
                    search: () => ({{ draw: () => {{}} }})
                  }})
                }};
              }},
              select2: () => ({{ on: () => {{}} }})
            }});
            $.fn = {{ dataTable: {{ util: {{ escapeRegex: (val) => val }} }} }};

            const csv1 = `Date,Exercise,Category,Weight,Weight Unit,Reps,Distance,Distance Unit,Time,Comment\\n2025-05-21,Bicep Curl,Biceps,50,lbs,10,,,0:00:00,\\n2025-05-22,Bicep Curl,Biceps,55,lbs,8,,,0:00:00,`;
            const csv2 = `Date,Exercise,Category,Weight,Weight Unit,Reps,Distance,Distance Unit,Time,Comment\\n2025-05-23,Tricep Pushdown,Triceps,40,lbs,12,,,0:00:00,\\n2025-05-24,Tricep Pushdown,Triceps,45,lbs,10,,,0:00:00,`;

            const elements = {{
              csvFile: {{ files: [{{ name: 'test.csv', text: async () => csv1 }}] }},
              uploadButton: {{
                addEventListener: (event, cb) => {{ elements.uploadButton._cb = cb; }},
                click: async () => {{ await elements.uploadButton._cb(); }}
              }},
              uploadProgress: {{ style: {{ display: 'none' }}, value: 0 }},
              clearButton: {{
                addEventListener: (event, cb) => {{ elements.clearButton._cb = cb; }},
                click: () => {{ elements.clearButton._cb(); }}
              }},
              result: {{ textContent: '', innerHTML: '<tr><td>Old Exercise</td></tr>' }}
            }};
            elements.result.querySelector = (sel) => {{
              if (sel === '#exerciseTable' && elements.result.innerHTML.includes('id="exerciseTable"')) return {{}};
              if (sel === '#exerciseDropdown' && elements.result.innerHTML.includes('id="exerciseDropdown"')) return {{}};
              return null;
            }};
            const doc = {{
              getElementById: id => elements[id],
              baseURI: 'https://example.test/',
              querySelector: (sel) => elements.result.querySelector(sel)
            }};

            const pyodide = {{
              installed: null,
              FS: {{ writeFile: () => {{}} }},
              globals: new Map(),
              loadPackage: async () => {{}},
              runPythonAsync: async code => {{
                if (code.includes("micropip.install")) {{
                  const match = code.match(/micropip.install\\(['"]([^'\"]+)['"]\\)/);
                  if (!match) throw new Error('missing package');
                  pyodide.installed = match[1];
                  return;
                }}
                if (code.includes("pipeline([")) {{
                  const csv = pyodide.globals.get('csv_text');
                  const py = `\\nimport io, sys, json\\nfrom kaiserlift.pipeline import pipeline\\nbuffer = io.StringIO(json.loads(sys.argv[1]))\\nsys.stdout.write(pipeline([buffer], embed_assets=True))\\n`;
                  const r = spawnSync('{sys.executable}', ['-c', py, JSON.stringify(csv)], {{ encoding: 'utf-8' }});
                  if (r.status !== 0) throw new Error(r.stderr);
                  return r.stdout;
                }}
              }}
            }};

            await init(() => pyodide, doc);
            console.log(pyodide.installed.endsWith('kaiserlift.whl'));

            await elements.uploadButton.click();
            console.log(initCalls.length === 1);
            console.log((elements.result.innerHTML.match(/id=\\"csvFile\\"/g) || []).length === 1);
            console.log((elements.result.innerHTML.match(/id=\\"uploadButton\\"/g) || []).length === 1);
            console.log(elements.result.innerHTML.includes('Bicep Curl'));
            console.log(elements.result.innerHTML.includes('exercise-figure'));
            console.log(localStorage.getItem('kaiserliftCsv') === csv1);
            console.log(localStorage.getItem('kaiserliftHtml').includes('Bicep Curl'));
            console.log(elements.uploadProgress.value === 100);
            console.log(elements.uploadProgress.style.display === 'none');

            elements.result.innerHTML = '<tr><td>Old Exercise</td></tr>';
            await init(() => pyodide, doc);
            console.log(elements.result.innerHTML.includes('Bicep Curl'));
            console.log(initCalls.length === 2);

            elements.csvFile.files = [{{ name: 'test.csv', text: async () => csv2 }}];
            await elements.uploadButton.click();
            console.log(initCalls.length === 3);
            console.log((elements.result.innerHTML.match(/id=\\"csvFile\\"/g) || []).length === 1);
            console.log((elements.result.innerHTML.match(/id=\\"uploadButton\\"/g) || []).length === 1);
            console.log(elements.result.innerHTML.includes('Tricep Pushdown'));
            console.log(!elements.result.innerHTML.includes('Bicep Curl'));
            console.log(elements.result.innerHTML.includes('exercise-figure'));
            console.log(localStorage.getItem('kaiserliftCsv') === csv2);
            console.log(localStorage.getItem('kaiserliftHtml').includes('Tricep Pushdown'));
            console.log(elements.uploadProgress.value === 100);
            console.log(elements.uploadProgress.style.display === 'none');

            elements.clearButton.click();
            console.log(localStorage.getItem('kaiserliftCsv') === null);
            console.log(localStorage.getItem('kaiserliftHtml') === null);
            """
        )
    )

    result = subprocess.run(
        ["node", script.as_posix()], capture_output=True, text=True, check=False
    )

    # Provide detailed error message if the script failed
    if result.returncode != 0:
        error_msg = f"Node script failed with exit code {result.returncode}\n"
        error_msg += f"\n=== STDOUT ===\n{result.stdout}\n"
        error_msg += f"\n=== STDERR ===\n{result.stderr}"
        raise AssertionError(error_msg)

    lines = [line for line in result.stdout.splitlines() if line]
    if lines[-24:] != ["true"] * 24:
        error_msg = f"Expected 24 'true' lines, got:\n{lines[-24:]}\n"
        error_msg += f"\n=== FULL STDOUT ===\n{result.stdout}"
        raise AssertionError(error_msg)
