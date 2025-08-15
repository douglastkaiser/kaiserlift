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
    script.write_text(
        textwrap.dedent(
            f"""
            import {{ init }} from 'file://{Path("client/main.js").resolve().as_posix()}';
            import {{ spawnSync }} from 'child_process';
            globalThis.fetch = async (url) => new Response(null, {{ status: 404 }});

            const csv = `Date,Exercise,Category,Weight,Weight Unit,Reps,Distance,Distance Unit,Time,Comment\\n2025-05-21,Bicep Curl,Biceps,50,lbs,10,,,0:00:00,\\n2025-05-22,Bicep Curl,Biceps,55,lbs,8,,,0:00:00,`;
            const elements = {{
              csvFile: {{ files: [{{ text: async () => csv }}] }},
              uploadButton: {{
                addEventListener: (event, cb) => {{ elements.uploadButton._cb = cb; }},
                click: async () => {{ await elements.uploadButton._cb(); }}
              }},
              result: {{ textContent: '', innerHTML: '' }}
            }};
            const doc = {{
              getElementById: id => elements[id],
              baseURI: 'https://example.test/',
            }};

            const pyodide = {{
              installed: null,
              FS: {{ writeFile: () => {{ throw new Error('unexpected writeFile'); }} }},
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
                  const py = `\\nimport io, sys, json\\nfrom kaiserlift.pipeline import pipeline\\nbuffer = io.StringIO(json.loads(sys.argv[1]))\\nsys.stdout.write(pipeline([buffer], embed_assets=False))\\n`;
                  const r = spawnSync('{sys.executable}', ['-c', py, JSON.stringify(csv)], {{ encoding: 'utf-8' }});
                  if (r.status !== 0) throw new Error(r.stderr);
                  return r.stdout;
                }}
              }}
            }};

            await init(() => pyodide, doc);
            console.log(pyodide.installed === 'kaiserlift');
            await elements.uploadButton.click();
            console.log(elements.result.innerHTML.includes('exercise-figure'));
            """
        )
    )

    result = subprocess.run(
        ["node", script.as_posix()], capture_output=True, text=True, check=True
    )
    lines = [line for line in result.stdout.splitlines() if line]
    assert lines[-2:] == ["true", "true"]
