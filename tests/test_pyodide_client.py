import shutil
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path

import pytest
import tomllib


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_pipeline_via_pyodide(tmp_path: Path) -> None:
    """Execute the pipeline through the browser client using a Pyodide stub."""

    version = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
    wheel_name = f"kaiserlift-{version}-py3-none-any.whl"
    wheel_path = tmp_path / wheel_name
    with zipfile.ZipFile(wheel_path, "w"):
        pass

    script = tmp_path / "run.mjs"
    script.write_text(
        textwrap.dedent(
            f"""
            import {{ init }} from 'file://{Path("client/main.js").resolve().as_posix()}';
            import {{ spawnSync }} from 'child_process';
            import fs from 'fs/promises';

            const wheelBytes = await fs.readFile('{wheel_path.as_posix()}');
            globalThis.fetch = async (url) => {{
              if (url === 'client/kaiserlift.whl') {{
                return new Response(wheelBytes);
              }}
              throw new Error('unexpected fetch ' + url);
            }};

            const csv = `Date,Exercise,Category,Weight,Weight Unit,Reps,Distance,Distance Unit,Time,Comment\\n2025-05-21,Bicep Curl,Biceps,50,lbs,10,,,0:00:00,\\n2025-05-22,Bicep Curl,Biceps,55,lbs,8,,,0:00:00,`;
            const elements = {{
              csvFile: {{ files: [{{ text: async () => csv }}] }},
              uploadButton: {{
                addEventListener: (event, cb) => {{ elements.uploadButton._cb = cb; }},
                click: async () => {{ await elements.uploadButton._cb(); }}
              }},
              result: {{ textContent: '', innerHTML: '' }}
            }};
            const doc = {{ getElementById: id => elements[id] }};

            const pyodide = {{
              fsPath: '',
              FS: {{ writeFile: (name, data) => {{ pyodide.fsPath = name; }} }},
              globals: new Map(),
              loadPackage: async () => {{}},
              runPythonAsync: async code => {{
                if (code.includes("micropip.install")) {{
                  const match = code.match(/micropip.install\\(['"]([^'"]+)['"]\\)/);
                  if (!match) throw new Error('missing wheel');
                  const wheel = match[1];
                  if (wheel !== 'kaiserlift.whl') {{
                    throw new Error('unexpected wheel ' + wheel);
                  }}
                  const py = `\\nfrom packaging.utils import parse_wheel_filename\\nparse_wheel_filename(__import__('sys').argv[1])\\n`;
                  const r = spawnSync('{sys.executable}', ['-c', py, '{wheel_name}'], {{ encoding: 'utf-8' }});
                  if (r.status !== 0) throw new Error(r.stderr);
                  return;
                }}
                if (code.includes("pipeline([")) {{
                  const csv = pyodide.globals.get('csv_text');
                  const py = `\\nimport io, sys, json\\nfrom kaiserlift.pipeline import pipeline\\nbuffer = io.StringIO(json.loads(sys.argv[1]))\\nsys.stdout.write(pipeline([buffer]))\\n`;
                  const r = spawnSync('{sys.executable}', ['-c', py, JSON.stringify(csv)], {{ encoding: 'utf-8' }});
                  if (r.status !== 0) throw new Error(r.stderr);
                  return r.stdout;
                }}
              }}
            }};

            await init(() => pyodide, doc);
            console.log(pyodide.fsPath === 'kaiserlift.whl');
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
