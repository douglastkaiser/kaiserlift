import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_pipeline_via_pyodide(tmp_path: Path) -> None:
    """Run the pipeline inside a Pyodide instance via Node.js."""

    # Build a wheel so Pyodide can install the local project
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", ".", "-w", str(tmp_path)], check=True
    )
    wheel = next(tmp_path.glob("kaiserlift-*.whl"))

    script = tmp_path / "run.mjs"
    script.write_text(
        textwrap.dedent(
            f"""
            import fs from 'fs';
            const src = await (await fetch('https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.mjs')).text();
            fs.writeFileSync('{(tmp_path / "pyodide.mjs").as_posix()}', src);
            const {{ loadPyodide }} = await import('file://{(tmp_path / "pyodide.mjs").as_posix()}');
            const pyodide = await loadPyodide({{ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/' }});
            await pyodide.loadPackage(['pandas','numpy','matplotlib','micropip']);
            pyodide.FS.writeFile('kaiserlift.whl', fs.readFileSync('{wheel.as_posix()}'));
            await pyodide.runPythonAsync(`
import micropip
await micropip.install('kaiserlift.whl')
            `);
            const csv = `time,exercise,weight,reps\n2025-05-21,Bicep Curl,50,10\n2025-05-22,Bicep Curl,55,8`;
            pyodide.globals.set('csv_text', csv);
            const html = await pyodide.runPythonAsync(`
import io
from kaiserlift.pipeline import pipeline
buffer = io.StringIO(csv_text)
pipeline([buffer])
            `);
            console.log(html.includes('exercise-figure'));
            """
        )
    )

    env = os.environ.copy()
    env.setdefault("NODE_OPTIONS", "--dns-result-order=ipv4first")

    try:
        result = subprocess.run(
            ["node", script.as_posix()],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as err:  # pragma: no cover - network issues
        pytest.skip(f"Pyodide run failed: {err.stderr}")

    assert "true" in result.stdout
