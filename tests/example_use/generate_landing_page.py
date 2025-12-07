"""Create a landing page linking to both lifting and running examples."""

from pathlib import Path


def main() -> None:
    """Generate index page with links to both demos."""
    here = Path(__file__).parent
    out_dir = here / "build"
    out_dir.mkdir(exist_ok=True)

    landing_html = """<!DOCTYPE html>
<html>
<head>
    <title>KaiserLift - Data-Driven Workout Optimization</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;700&family=Lato:ital,wght@0,300;0,400;0,700;1,300;1,400&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-green: #4a7c59;
            --primary-green-hover: #3d6a4a;
            --bg: #f9f9f9;
            --fg: #444444;
            --fg-light: #666666;
            --bg-alt: #ffffff;
            --border: #e0e0e0;
            --shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Lato', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg);
            color: var(--fg);
            max-width: 900px;
            margin: 0 auto;
            padding: 50px 30px;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            margin-bottom: 50px;
            padding-bottom: 30px;
            border-bottom: 1px solid var(--border);
        }
        h1 {
            font-family: 'Oswald', sans-serif;
            font-size: 3.5em;
            font-weight: 400;
            letter-spacing: 2px;
            margin-bottom: 15px;
            text-transform: uppercase;
        }
        h1 .brand-name {
            color: var(--fg);
        }
        h1 .brand-accent {
            color: var(--primary-green);
        }
        .tagline {
            font-size: 1.1em;
            font-style: italic;
            font-weight: 300;
            color: var(--fg-light);
        }
        h2 {
            font-family: 'Oswald', sans-serif;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 1.5em;
            margin-bottom: 15px;
            color: var(--fg);
        }
        h3 {
            font-family: 'Oswald', sans-serif;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 1.2em;
            margin-bottom: 15px;
            margin-top: 40px;
            color: var(--fg);
        }
        .demo-section {
            background-color: var(--bg-alt);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 30px;
            margin: 25px 0;
            box-shadow: var(--shadow);
        }
        .demo-section h2 {
            margin-top: 0;
        }
        a {
            color: var(--primary-green);
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .demo-link {
            display: inline-block;
            background-color: var(--primary-green);
            color: white;
            padding: 12px 28px;
            border-radius: 4px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.9em;
            margin-top: 15px;
            transition: all 0.2s ease;
            text-decoration: none;
        }
        .demo-link:hover {
            background-color: var(--primary-green-hover);
            text-decoration: none;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }
        .badge {
            display: inline-block;
            background-color: var(--primary-green);
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.7em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-left: 10px;
            vertical-align: middle;
        }
        ul {
            margin: 15px 0;
            padding-left: 0;
            list-style: none;
        }
        li {
            margin: 10px 0;
            padding-left: 25px;
            position: relative;
        }
        li::before {
            content: "";
            position: absolute;
            left: 0;
            top: 8px;
            width: 8px;
            height: 8px;
            background-color: var(--primary-green);
            border-radius: 50%;
        }
        .section-divider {
            border: none;
            border-top: 1px solid var(--border);
            margin: 50px 0;
        }
        pre {
            background-color: var(--bg-alt);
            padding: 15px 20px;
            border-radius: 4px;
            overflow-x: auto;
            border: 1px solid var(--border);
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 0.9em;
        }
        .links-section ul {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .links-section li {
            padding-left: 0;
        }
        .links-section li::before {
            display: none;
        }
        .links-section a {
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }
        .social-links {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }
        .social-link {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background-color: #555;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            text-decoration: none;
            transition: background-color 0.2s ease;
        }
        .social-link:hover {
            background-color: var(--primary-green);
        }
        footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
            font-size: 0.85em;
            color: var(--fg-light);
            text-align: center;
        }
        @media (max-width: 600px) {
            body {
                padding: 30px 20px;
            }
            h1 {
                font-size: 2.5em;
            }
            .demo-section {
                padding: 20px;
            }
            .links-section ul {
                flex-direction: column;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1><span class="brand-name">KAISER</span><span class="brand-accent">LIFT</span></h1>
        <p class="tagline">Data-driven workout optimization. Never guess your next workout again.</p>
    </div>

    <div class="demo-section">
        <h2>Lifting Data <span class="badge">Original</span></h2>
        <p>
            Track weight training with Pareto front optimization.
            Uses 1RM (Epley formula) to compare across rep ranges.
        </p>
        <ul>
            <li>Weight vs Reps analysis</li>
            <li>1RM calculations</li>
            <li>Pareto optimal PR tracking</li>
            <li>Next workout targets</li>
        </ul>
        <a href="lifting/" class="demo-link">View Lifting Demo</a>
    </div>

    <div class="demo-section">
        <h2>Running Data <span class="badge">New</span></h2>
        <p>
            Track cardio/running with distance and pace metrics.
            Uses aerobic degradation model to predict race paces.
        </p>
        <ul>
            <li>Distance vs Pace analysis</li>
            <li>Pace prediction at any distance</li>
            <li>Race pace calculator (5K, 10K, etc.)</li>
            <li>Training target recommendations</li>
        </ul>
        <a href="running/" class="demo-link">View Running Demo</a>
    </div>

    <hr class="section-divider">

    <h3>Installation</h3>
    <pre>uv pip install kaiserlift</pre>

    <div class="links-section">
        <h3>Links</h3>
        <ul>
            <li><a href="https://github.com/douglastkaiser/kaiserlift">GitHub Repository</a></li>
            <li><a href="https://pypi.org/project/kaiserlift/">PyPI Package</a></li>
            <li><a href="https://www.douglastkaiser.com/projects/#workoutPlanner">Project Overview</a></li>
        </ul>
    </div>

    <div class="social-links">
        <a href="https://github.com/douglastkaiser/kaiserlift" class="social-link" target="_blank" title="GitHub">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
            </svg>
        </a>
    </div>

    <footer>
        <span id="version-info">Loading version...</span>
        <span style="margin: 0 10px;">|</span>
        <a href="https://douglastkaiser.github.io" target="_blank">douglastkaiser.github.io</a>
    </footer>

    <script type="module">
        import { VERSION, GIT_HASH, GIT_HASH_FULL } from './version.js';
        const versionEl = document.getElementById('version-info');
        const commitUrl = `https://github.com/douglastkaiser/kaiserlift/commit/${GIT_HASH_FULL}`;
        versionEl.innerHTML = `v${VERSION} (<a href="${commitUrl}" target="_blank" style="color: var(--primary-green);">${GIT_HASH}</a>)`;
    </script>
</body>
</html>"""

    (out_dir / "index.html").write_text(landing_html, encoding="utf-8")


if __name__ == "__main__":
    main()
