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

            const csv1 = `Date,Exercise,Category,Weight,Weight Unit,Reps,Distance,Distance Unit,Time,Comment\\n2025-05-21,Bicep Curl,Biceps,50,lbs,10,,,0:00:00,\\n2025-05-22,Bicep Curl,Biceps,55,lbs,8,,,0:00:00,`;
            const csv2 = `Date,Exercise,Category,Weight,Weight Unit,Reps,Distance,Distance Unit,Time,Comment\\n2025-05-23,Tricep Pushdown,Triceps,40,lbs,12,,,0:00:00,\\n2025-05-24,Tricep Pushdown,Triceps,45,lbs,10,,,0:00:00,`;

            const elements = {{
              csvFile: {{ files: [{{ text: async () => csv1 }}] }},
              uploadButton: {{
                addEventListener: (event, cb) => {{ elements.uploadButton._cb = cb; }},
                click: async () => {{ await elements.uploadButton._cb(); }}
              }},
              result: {{ textContent: '', innerHTML: '<tr><td>Old Exercise</td></tr>' }}
            }};
            const doc = {{
              getElementById: id => elements[id],
              baseURI: 'https://example.test/',
            }};

            const pyodide = {{
              installed: null,
              FS: {{ writeFile: () => {{}} }},
              globals: new Map(),
              loadPackage: async () => {{}},
              runPythonAsync: async code => {{
                if (code.includes("micropip.install")) {{
                  const match = code.match(/micropip.install\\(['"]([^'"]+)['"]\\)/);
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
            console.log((elements.result.innerHTML.match(/id=\"csvFile\"/g) || []).length === 1);
            console.log((elements.result.innerHTML.match(/id=\"uploadButton\"/g) || []).length === 1);
            console.log(elements.result.innerHTML.includes('Bicep Curl'));
            console.log(elements.result.innerHTML.includes('exercise-figure'));

            elements.csvFile.files = [{{ text: async () => csv2 }}];
            await elements.uploadButton.click();
            console.log((elements.result.innerHTML.match(/id=\"csvFile\"/g) || []).length === 1);
            console.log((elements.result.innerHTML.match(/id=\"uploadButton\"/g) || []).length === 1);
            console.log(elements.result.innerHTML.includes('Tricep Pushdown'));
            console.log(!elements.result.innerHTML.includes('Bicep Curl'));
            console.log(elements.result.innerHTML.includes('exercise-figure'));
            """
        )
    )

    result = subprocess.run(
        ["node", script.as_posix()], capture_output=True, text=True, check=True
    )
    lines = [line for line in result.stdout.splitlines() if line]
    assert lines[-10:] == ["true"] * 10
