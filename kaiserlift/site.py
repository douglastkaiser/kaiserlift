"""Shared neo-retro site shell for static exports and the web application."""

from html import escape

SITE_STYLE = """
<style>
:root { --paper:#f3f1e9; --white:#fffef8; --ink:#171915; --muted:#62655a;
    --line:#b7b9ab; --acid:#d8f568; --blue:#2744da; --orange:#ed653c;
    --mono:'Courier New',monospace; --sans:Arial,Helvetica,sans-serif; }
* { box-sizing:border-box; }
html { scroll-behavior:smooth; scroll-padding-top:24px; }
body { margin:0; background:var(--paper); color:var(--ink); font:15px/1.5 var(--sans); }
a { color:inherit; text-underline-offset:4px; }
button,input,select { font:inherit; color:inherit; border-radius:0; }
button,.button { display:inline-flex; align-items:center; justify-content:center; gap:16px;
    min-height:44px; padding:10px 18px; border:1px solid var(--ink); background:var(--ink);
    color:var(--white); text-decoration:none; cursor:pointer; font:700 12px/1.3 var(--mono);
    text-transform:uppercase; box-shadow:3px 3px 0 var(--line); }
button:hover,.button:hover { background:var(--blue); color:white; }
button:active,.button:active { box-shadow:none; transform:translate(2px,2px); }
button:disabled { opacity:.55; cursor:wait; }
.button.secondary,button.secondary { background:transparent; color:var(--ink); }
.button.secondary:hover,button.secondary:hover { background:var(--acid); }
:focus-visible { outline:3px solid var(--blue); outline-offset:4px; }
[hidden] { display:none !important; }
h1,h2,h3,p { margin:0; }
h1,h2,h3 { line-height:1; letter-spacing:-.055em; }
.skip-link { position:absolute; left:16px; top:-100px; background:var(--acid); padding:10px; z-index:20; }
.skip-link:focus { top:12px; }
.site-topline { background:var(--ink); color:var(--paper); padding:7px 28px;
    display:flex; justify-content:space-between; font:10px/1.4 var(--mono); letter-spacing:.08em; }
.site-masthead { display:flex; align-items:center; justify-content:space-between; gap:24px;
    padding:22px 28px; border-bottom:1px solid var(--ink); }
.wordmark { font-size:27px; font-weight:900; letter-spacing:-1.8px; text-decoration:none; line-height:1; }
.wordmark span { background:var(--acid); padding:0 4px; }
.masthead-caption { font:10px/1.4 var(--mono); text-transform:uppercase; letter-spacing:.07em; }
.site-nav { display:flex; gap:4px; flex-wrap:wrap; }
.site-nav a { padding:10px 16px; font:700 11px/1.4 var(--mono); text-decoration:none;
    text-transform:uppercase; border:1px solid transparent; }
.site-nav a:hover { border-color:var(--ink); }
.site-nav a[aria-current] { background:var(--ink); color:var(--acid); }
.site-frame { display:grid; grid-template-columns:172px minmax(0,1fr); max-width:1680px; margin:auto; }
.site-index { padding:30px 20px 30px 28px; border-right:1px solid var(--ink); }
.index-label,.eyebrow,.section-code { font:700 10px/1.5 var(--mono); letter-spacing:.09em; text-transform:uppercase; }
.index-label { color:var(--muted); margin-bottom:22px; }
.index-link { display:block; border-bottom:1px solid var(--line); padding:12px 0;
    font:11px/1.5 var(--mono); text-decoration:none; }
.index-link:hover { color:var(--blue); }
.index-note { margin-top:60px; font:10px/1.7 var(--mono); color:var(--muted); }
.index-square { display:block; width:28px; height:28px; background:var(--acid); border:1px solid var(--ink); margin-bottom:12px; }
.site-main { min-width:0; padding:32px 36px 48px; }
.page-intro { display:flex; justify-content:space-between; align-items:end; gap:24px;
    padding-bottom:28px; border-bottom:1px solid var(--ink); margin-bottom:24px; }
.page-intro h1 { font-size:clamp(48px,6.8vw,105px); font-weight:900; letter-spacing:-.075em; text-transform:uppercase; }
.page-intro .eyebrow { margin-bottom:12px; }
.page-intro p:last-child { max-width:270px; font-size:13px; color:var(--muted); }
.content-card { margin:0 0 24px; min-width:0; }
.dashboard-toolbar { display:flex; justify-content:space-between; align-items:center;
    border:1px solid var(--ink); border-bottom:0; padding:15px 20px; gap:20px; background:var(--white); }
.dashboard-toolbar h2 { font:700 13px/1.5 var(--mono); letter-spacing:0; text-transform:uppercase; }
.dashboard-toolbar .eyebrow { color:var(--muted); margin-bottom:4px; }
.control-stack { display:flex; align-items:center; gap:12px; min-width:0; }
.control-stack label { font:10px/1.4 var(--mono); text-transform:uppercase; }
select { min-height:44px; max-width:100%; border:1px solid var(--ink); background:var(--paper); padding:10px 32px 10px 10px; }
#exerciseDropdown { width:260px; }
.figures-grid { min-width:0; }
.dashboard-grid { display:grid; grid-template-columns:minmax(0,1fr) 244px; border:1px solid var(--ink); background:var(--white); }
.chart-card { min-width:0; padding:20px 16px 0; }
.chart-heading { display:flex; align-items:center; justify-content:space-between; gap:16px; margin:0 4px 12px; }
.chart-heading h3 { font-size:22px; font-weight:800; letter-spacing:-.04em; }
.chart-controls { display:flex; gap:6px; }
.chart-controls button { min-height:36px; padding:7px 10px; font-size:10px; box-shadow:none; background:var(--paper); color:var(--ink); }
.chart-controls button:hover { background:var(--acid); }
.exercise-figure,.running-figure { min-width:0; width:100%; }
.running-plot-card { border:1px solid var(--ink); background:var(--white); padding:20px 12px 8px; }
.running-plot-card + .running-plot-card { border-top:0; }
.running-plot-card .chart-heading { margin-left:10px; }
.target-card { background:var(--ink); color:var(--paper); padding:24px 20px; border-left:1px solid var(--ink); display:flex; flex-direction:column; }
.target-card::before { content:'+1'; display:block; font:700 52px/1 var(--mono); letter-spacing:-5px; color:var(--acid); margin-bottom:28px; }
.target-card .eyebrow { color:var(--acid); }
.target-value { display:block; font:700 30px/1.18 var(--mono); letter-spacing:-1.6px; margin:18px 0 24px; }
.target-card p { font:11px/1.7 var(--mono); color:#c4c7b7; margin-bottom:20px; }
.target-card p:last-child { padding-top:18px; border-top:1px solid #5b5e50; margin-top:auto; }
.chart-help { margin:12px 4px 0; border-top:1px solid var(--line); padding:12px 0; font:11px/1.7 var(--mono); }
.chart-help summary { cursor:pointer; text-transform:uppercase; font-weight:bold; min-height:30px; }
.chart-help p { padding:8px 0; max-width:70ch; }
.target-table { border:1px solid var(--ink); background:var(--white); }
.section-heading { display:flex; justify-content:space-between; align-items:center; gap:16px; padding:16px 20px; background:var(--acid); border-bottom:1px solid var(--ink); }
.section-heading h2 { font:700 13px/1.5 var(--mono); letter-spacing:0; text-transform:uppercase; }
.section-heading span { font:10px/1.5 var(--mono); }
.table-wrapper { overflow-x:auto; padding:18px 20px; min-width:0; }
table.dataTable { width:100% !important; border-collapse:collapse !important; font:11px/1.5 var(--mono); border:0 !important; margin:16px 0 !important; }
table.dataTable thead th { padding:12px 10px !important; background:var(--ink); color:var(--paper); border:1px solid var(--ink) !important; text-align:left; white-space:nowrap; }
table.dataTable tbody td { padding:12px 10px !important; border:1px solid var(--line) !important; background:transparent; white-space:nowrap; }
table.dataTable tbody tr:nth-child(even) { background:#eceee3; }
table.dataTable tbody tr:hover { background:#e0e5f8; }
.target-table tr.is-selected td { background:var(--acid) !important; }
#exerciseTable tbody tr { cursor:pointer; }
.dataTables_wrapper { font:10px/1.6 var(--mono); }
.dataTables_length,.dataTables_filter { margin-bottom:10px; }
.dataTables_filter input,.dataTables_length select { border:1px solid var(--ink) !important; border-radius:0 !important; padding:8px !important; min-height:36px; background:var(--paper) !important; }
.dataTables_wrapper .dataTables_paginate .paginate_button { border-radius:0 !important; box-shadow:none !important; }
.dataTables_wrapper .dataTables_paginate .paginate_button.current { background:var(--acid) !important; border:1px solid var(--ink) !important; color:var(--ink) !important; }
.import-panel { border:1px solid var(--ink); margin:0 0 24px; background:var(--paper); }
.import-panel summary { padding:14px 18px; font:700 11px/1.5 var(--mono); cursor:pointer; text-transform:uppercase; }
.import-panel[open] summary { border-bottom:1px solid var(--ink); background:var(--acid); }
.import-content { padding:20px; }
.import-content p { font:11px/1.7 var(--mono); color:var(--muted); margin-bottom:16px; max-width:70ch; }
.upload-controls { display:flex; flex-wrap:wrap; align-items:center; gap:12px; }
input[type=file] { max-width:100%; min-width:0; font:11px/1.5 var(--mono); }
input::file-selector-button { min-height:44px; padding:10px; background:var(--white); border:1px solid var(--ink); border-radius:0; margin-right:10px; font:700 11px var(--mono); cursor:pointer; }
progress { accent-color:var(--blue); width:100%; height:10px; }
.site-footer { display:flex; justify-content:space-between; gap:16px; padding:18px 28px; border-top:1px solid var(--ink); font:10px/1.5 var(--mono); text-transform:uppercase; }
.home-hero { display:grid; grid-template-columns:minmax(0,1fr) 265px; border-bottom:1px solid var(--ink); margin-bottom:28px; }
.home-hero h1 { font-size:clamp(65px,8.5vw,138px); font-weight:900; text-transform:uppercase; letter-spacing:-.085em; margin:22px 0; line-height:.85; }
.home-hero h1 em { font-style:normal; color:var(--blue); }
.home-hero .hero-copy { max-width:460px; padding:10px 30px 32px 0; font-size:16px; }
.home-field { border-left:1px solid var(--ink); padding:22px; background:var(--acid); }
.home-field .field-number { font:700 90px/1 var(--mono); letter-spacing:-12px; margin:26px 0; }
.home-field p { font:11px/1.8 var(--mono); }
.mode-grid { display:grid; grid-template-columns:1fr 1fr; border:1px solid var(--ink); margin-bottom:28px; }
.mode-card { padding:26px; min-width:0; background:var(--white); display:flex; flex-direction:column; }
.mode-card + .mode-card { border-left:1px solid var(--ink); }
.mode-card h2 { font-size:46px; margin:30px 0 16px; text-transform:uppercase; font-weight:900; }
.mode-card p { max-width:37ch; color:var(--muted); font-size:13px; margin-bottom:24px; }
.mode-card .button { align-self:start; margin-top:auto; }
.mode-card .mode-icon { font:700 44px/1 var(--mono); float:right; color:var(--blue); }
.method-strip { display:grid; grid-template-columns:repeat(3,1fr); gap:24px; border-top:1px solid var(--ink); border-bottom:1px solid var(--ink); padding:24px 0; margin-bottom:28px; }
.method-strip h3 { font:700 12px var(--mono); letter-spacing:0; margin-bottom:12px; text-transform:uppercase; }
.method-strip p { font-size:12px; color:var(--muted); }
.home-imports { display:grid; grid-template-columns:1fr 1fr; gap:24px; }
.home-imports form { padding:20px; border:1px solid var(--ink); background:var(--white); }
.home-imports label { display:block; font:700 12px var(--mono); margin-bottom:18px; }
.home-imports .upload-controls { align-items:start; flex-direction:column; }
.error-panel { border:2px solid var(--ink); padding:24px; background:#ffe2d8; }
.error-panel h3 { font:700 16px var(--mono); margin-bottom:12px; }
.error-panel pre { white-space:pre-wrap; overflow-wrap:anywhere; font:12px/1.6 var(--mono); }
@media(min-width:1700px) { .site-frame { border-left:1px solid var(--ink); border-right:1px solid var(--ink); } }
@media(max-width:1100px) {
    .site-frame { grid-template-columns:130px minmax(0,1fr); }
    .site-index { padding-left:18px; } .site-main { padding:24px; }
    .dashboard-grid { grid-template-columns:minmax(0,1fr); }
    .target-card { border-left:0; border-top:1px solid var(--ink); display:block; }
    .target-card::before { float:right; font-size:36px; margin:0; }
    .target-value { font-size:26px; margin:12px 0; }
    .target-card p { max-width:75ch; }
    .target-card p:last-child { margin-bottom:0; padding-top:10px; }
    .home-hero { grid-template-columns:minmax(0,1fr) 220px; }
}
@media(max-width:700px) {
    .site-topline { padding:7px 16px; } .site-topline span:last-child { display:none; }
    .site-masthead { padding:18px 16px; flex-wrap:wrap; gap:16px; }
    .masthead-caption { display:none; } .site-nav { width:100%; border-top:1px solid var(--line); padding-top:10px; }
    .site-nav a { flex:1; text-align:center; padding:10px; }
    .site-frame { display:block; } .site-index { display:none; }
    .site-main { padding:24px 16px 32px; }
    .page-intro { align-items:start; flex-direction:column; gap:16px; }
    .page-intro h1 { font-size:62px; }
    .page-intro p:last-child { max-width:38ch; }
    .dashboard-toolbar { align-items:stretch; flex-direction:column; padding:16px; gap:16px; }
    .control-stack { flex-direction:column; align-items:stretch; gap:8px; }
    #exerciseDropdown { width:100%; }
    .chart-card { padding:16px 6px 0; }
    .chart-heading { align-items:start; flex-direction:column; margin-left:8px; }
    .chart-heading h3 { font-size:21px; }
    .section-heading { padding:14px; align-items:start; flex-direction:column; gap:4px; }
    .table-wrapper { padding:14px 10px; }
    .dataTables_filter { text-align:left !important; float:none !important; }
    .dataTables_filter input { max-width:170px; }
    .site-footer { padding:16px; flex-direction:column; gap:8px; }
    .home-hero { grid-template-columns:minmax(0,1fr); }
    .home-hero h1 { font-size:clamp(64px,17vw,112px); }
    .home-hero .hero-copy { padding-right:0; }
    .home-field { border-left:0; border-top:1px solid var(--ink); padding:18px; margin-bottom:24px; }
    .home-field .field-number { float:right; font-size:54px; margin:0 0 0 14px; letter-spacing:-6px; }
    .home-field p { max-width:30ch; }
    .mode-grid,.home-imports,.method-strip { grid-template-columns:minmax(0,1fr); }
    .mode-card + .mode-card { border-left:0; border-top:1px solid var(--ink); }
    .mode-card { padding:22px; }
    .method-strip { gap:22px; }
    .upload-controls { align-items:stretch; flex-direction:column; }
}
@media(prefers-reduced-motion:reduce) { html { scroll-behavior:auto; } }
</style>
"""


def site_shell(content: str, *, mode: str = "home", assets: str = "") -> str:
    """Wrap page content in the shared navigation, index, and responsive shell."""
    home = mode == "home"
    prefix = "./" if home else "../"
    nav = []
    for key, label, href in (
        ("home", "00 / Index", prefix),
        ("lifting", "01 / Lifting", prefix + "lifting/"),
        ("running", "02 / Running", prefix + "running/"),
    ):
        current = ' aria-current="page"' if mode == key else ""
        nav.append(f'<a href="{href}"{current}>{label}</a>')
    links = (
        [
            ("modes", "01 / Choose a mode"),
            ("method", "02 / The method"),
            ("import", "03 / Bring your data"),
        ]
        if home
        else [
            ("performance", "01 / Performance"),
            ("targets", "02 / Target register"),
            ("import", "03 / Import data"),
        ]
    )
    index = "".join(
        f'<a class="index-link" href="#{anchor}">{label}</a>' for anchor, label in links
    )
    title = "Training, plotted." if home else f"{mode.title()} lab"
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="KaiserLift: explore your training history and find your next personal record.">
<title>{escape(title)} / KaiserLift</title>{SITE_STYLE}{assets}</head>
<body data-training-mode="{mode}">
<a class="skip-link" href="#main">Skip to content</a>
<div class="site-topline"><span>KAISERLIFT / PERSONAL PERFORMANCE SYSTEM</span><span>LESS GUESSWORK. MORE PROGRESS.</span></div>
<header class="site-masthead"><a class="wordmark" href="{prefix}" aria-label="KaiserLift home">KAISER<span>LIFT</span></a>
<span class="masthead-caption">A field guide to<br>your next personal record.</span>
<nav class="site-nav" aria-label="Main navigation">{"".join(nav)}</nav></header>
<div class="site-frame"><aside class="site-index" aria-label="On this page">
<p class="index-label">Directory / {mode}</p>{index}
<div class="index-note"><span class="index-square" aria-hidden="true"></span>RECORD.<br>READ.<br>REPEAT.<br><br>Built for the<br>long game.</div></aside>
<main id="main" class="site-main">{content}</main></div>
<footer class="site-footer"><span>KAISERLIFT / DATA IN. DIRECTION OUT.</span>
<a href="https://github.com/douglastkaiser/kaiserlift">Source & documentation ↗</a></footer>
</body></html>'''


def render_home(*, server: bool = False) -> str:
    """Render the same home page for the web server and static distribution."""
    imports = (
        """<div class="home-imports">
<form action="/upload" method="post" enctype="multipart/form-data">
<label for="home-lifting-file">01 / Lifting CSV</label><div class="upload-controls">
<input id="home-lifting-file" type="file" name="file" accept=".csv" required>
<button type="submit">Open lifting data ↗</button></div></form>
<form action="/upload-running" method="post" enctype="multipart/form-data">
<label for="home-running-file">02 / Running CSV</label><div class="upload-controls">
<input id="home-running-file" type="file" name="file" accept=".csv" required>
<button type="submit">Open running data ↗</button></div></form></div>"""
        if server
        else """
<p class="hero-copy">Have a FitNotes export? Open a lab, then choose <strong>Import data</strong>
to replace the example with your own training history.</p>
<a class="button secondary" href="lifting/#import">Import lifting data ↗</a>
<a class="button secondary" href="running/#import">Import running data ↗</a>"""
    )
    content = f"""
<section class="home-hero"><div><p class="eyebrow">Training intelligence / Est. one rep at a time</p>
<h1>Training,<br><em>plotted.</em></h1>
<p class="hero-copy">Your history is a map. Find the gaps, see your strongest sets,
and make your next move count.</p></div>
<aside class="home-field"><p class="eyebrow">The operating principle</p><div class="field-number" aria-hidden="true">+1</div>
<p>One more rep.<br>A little more weight.<br>A new distance.<br><br>Small steps. Visible progress.</p></aside></section>
<section id="modes" class="mode-grid" aria-label="Choose your training mode">
<article class="mode-card"><div><span class="section-code">01 / Strength</span><span class="mode-icon" aria-hidden="true">↗</span></div>
<h2>Lifting lab.</h2><p>Map weight against reps. Explore your best sets and the targets just beyond them.</p>
<a class="button" href="lifting/">Enter lifting lab <span aria-hidden="true">→</span></a></article>
<article class="mode-card"><div><span class="section-code">02 / Endurance</span><span class="mode-icon" aria-hidden="true">↔</span></div>
<h2>Running lab.</h2><p>Connect pace, distance, and time. See where your next running record could be.</p>
<a class="button" href="running/">Enter running lab <span aria-hidden="true">→</span></a></article></section>
<section id="method" class="method-strip" aria-label="How it works">
<div><h3>01. Bring the history</h3><p>Start with the sample data or import your FitNotes CSV.</p></div>
<div><h3>02. Read the pattern</h3><p>Performance curves show your records across reps and distances.</p></div>
<div><h3>03. Pick the next move</h3><p>Explore proposed targets and choose a challenge for your next session.</p></div></section>
<section id="import"><div class="page-intro"><div><p class="eyebrow">Your records belong here</p>
<h2>Bring your data.</h2></div><p>FitNotes CSV exports. No account required.</p></div>{imports}</section>"""
    return site_shell(content)
