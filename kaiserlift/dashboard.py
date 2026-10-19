"""Shared presentation and browser behavior for generated dashboards."""

from .site import site_shell
from .plot_utils import get_plotly_cdn_html

DASHBOARD_SCRIPT = r"""
<script>
window.initializeDashboard = function(root = document) {
    const dropdown = root.querySelector('#exerciseDropdown');
    const tableEl = root.querySelector('#exerciseTable');
    const table = tableEl && window.jQuery && jQuery.fn.DataTable
        ? (jQuery.fn.DataTable.isDataTable(tableEl) ? jQuery(tableEl).DataTable()
            : jQuery(tableEl).DataTable({pageLength: 10, autoWidth: false})) : null;
    const runningTable = root.querySelector('#runningTable');
    if (runningTable && window.jQuery && jQuery.fn.DataTable && !jQuery.fn.DataTable.isDataTable(runningTable)) {
        jQuery(runningTable).DataTable({pageLength: 10, autoWidth: false, order: [[4, 'desc']]});
    }
    const panels = root.querySelectorAll('[data-exercise-panel]');
    function selectTarget(weight, reps, panel) {
        const output = panel.querySelector('.target-value');
        if (output) output.textContent = `${weight} lbs × ${reps} reps`;
        const label = panel.querySelector('[data-target-label]');
        if (label) label.textContent = 'Selected target';
        const explanation = panel.querySelector('[data-target-explanation]');
        if (explanation) explanation.textContent = 'A proposed new record at this weight and rep count.';
        const plot = panel.querySelector('[data-plot]');
        if (plot && plot.data && window.Plotly) {
            const index = plot.data.findIndex(trace => trace.name === 'Selected target');
            if (index >= 0) Plotly.restyle(plot, {x: [[Number(reps)]], y: [[Number(weight)]]}, [index]);
        }
        if (!table) return;
        const headings = Array.from(tableEl.querySelectorAll('thead th')).map(th => th.textContent.trim());
        const wi = headings.indexOf('Weight'), ri = headings.indexOf('Reps');
        const rows = table.rows({search: 'applied'});
        let selectedIndex = null;
        rows.every(function() {
            const data = this.data();
            const selected = Number(data[wi]) === Number(weight) && Number(data[ri]) === Number(reps);
            this.node().classList.toggle('is-selected', selected);
            if (selected) selectedIndex = this.index();
        });
        if (selectedIndex !== null) {
            const indexes = table.rows({search: 'applied', order: 'applied'}).indexes().toArray();
            table.page(Math.floor(indexes.indexOf(selectedIndex) / table.page.len())).draw(false);
        }
    }
    function hydrate(panel) {
        if (!window.Plotly) return;
        panel.querySelectorAll('[data-plot]').forEach(el => {
            if (el.dataset.ready) { Plotly.Plots.resize(el); return; }
            el.dataset.ready = 'true';
            const spec = JSON.parse(el.querySelector('script[type="application/json"]').textContent);
            Plotly.newPlot(el, spec.data, spec.layout, {
                responsive: true, displaylogo: false, displayModeBar: false
            }).then(() => {
                el.on('plotly_click', event => {
                    const point = event.points[0];
                    if (point.data.name === 'Targets' || point.data.name === 'Recommended target') {
                        selectTarget(point.y, point.x, panel);
                    }
                });
            }).catch(() => { delete el.dataset.ready; });
        });
    }
    function update() {
        const selected = dropdown ? dropdown.value : null;
        panels.forEach(panel => {
            const visible = !dropdown || panel.dataset.exercisePanel === selected;
            panel.hidden = !visible;
            if (visible) hydrate(panel);
        });
        if (table && dropdown) {
            const escaped = jQuery.fn.dataTable.util.escapeRegex(selected);
            table.column(0).search('^' + escaped + '$', true, false).draw();
        }
    }
    if (dropdown && !dropdown.dataset.dashboardBound) {
        dropdown.dataset.dashboardBound = 'true';
        dropdown.addEventListener('change', update);
    }
    if (tableEl && !tableEl.dataset.dashboardBound) {
        tableEl.dataset.dashboardBound = 'true';
        tableEl.addEventListener('click', event => {
            const row = event.target.closest('tbody tr');
            if (!row || !table) return;
            const data = table.row(row).data();
            if (!data) return;
            const headings = Array.from(tableEl.querySelectorAll('thead th')).map(th => th.textContent.trim());
            const panel = Array.from(panels).find(panel => !panel.hidden);
            if (panel) selectTarget(Number(data[headings.indexOf('Weight')]), Number(data[headings.indexOf('Reps')]), panel);
        });
    }
    root.querySelectorAll('[data-chart-action]').forEach(button => {
        if (button.dataset.bound) return;
        button.dataset.bound = 'true';
        button.addEventListener('click', () => {
            const panel = button.closest('[data-exercise-panel], .running-workspace');
            const plot = panel && panel.querySelector('[data-plot]');
            if (!plot || !plot.data || !window.Plotly) return;
            if (button.dataset.chartAction === 'reset') {
                const reset = {};
                Object.keys(plot.layout).filter(key => /^([xy]axis)([0-9]*)$/.test(key))
                    .forEach(axis => { reset[axis + '.autorange'] = true; });
                Plotly.relayout(plot, reset);
            } else {
                Plotly.downloadImage(plot, {format: 'png', filename: 'kaiserlift-performance', scale: 2});
            }
        });
    });
    // Fragment identifiers also open imports when arriving from the home page.
    const openImport = () => {
        const importer = document.querySelector('#import');
        if (importer && location.hash === '#import') importer.open = true;
    };
    openImport();
    if (!window.dashboardHashBound) {
        window.addEventListener('hashchange', openImport);
        window.dashboardHashBound = true;
    }
    // Running charts do not need an exercise filter.
    root.querySelectorAll('.running-figure').forEach(hydrate);
    update();
};
document.addEventListener('DOMContentLoaded', () => window.initializeDashboard());
</script>
"""


def dashboard_assets() -> str:
    """Return shared styles and initialization for standalone viewers."""
    return DASHBOARD_SCRIPT


def render_dashboard(fragment: str, *, mode: str) -> str:
    """Render a complete lab with shared navigation, imports, and chart assets."""
    running = mode == "running"
    heading = "Running lab." if running else "Lifting lab."
    description = (
        "Distance. Time. Pace. Find the next line to cross."
        if running
        else "Your best sets, mapped. Your next personal record, in sight."
    )
    csv_hint = (
        "Use your FitNotes running export with distance and duration columns."
        if running
        else "Use your FitNotes export with Date, Exercise, Category, Weight, and Reps columns."
    )
    content = f"""
    <header class="page-intro"><div><p class="eyebrow">{"02 / Endurance" if running else "01 / Strength"} / Performance workspace</p>
    <h1>{heading}</h1></div><p>{description}</p></header>
    <div id="result">{fragment}</div>
    <details id="import" class="import-panel">
        <summary>03 / Import data — open a CSV export</summary>
        <div class="import-content"><p>{csv_hint}</p>
        <div id="importError" class="error-panel" role="alert" hidden></div>
        <div class="upload-controls">
            <label class="eyebrow" for="csvFile">Training file</label>
            <input type="file" id="csvFile" accept=".csv">
            <button id="uploadButton">Load training data ↗</button>
            <button id="clearButton" class="secondary">Clear saved data</button>
            <progress id="uploadProgress" value="0" max="100" style="display:none;" aria-label="Import progress"></progress>
        </div><p id="runtimeStatus" role="status">Preparing the CSV importer. You can explore the charts now.</p></div>
    </details>
    """
    assets = (
        get_plotly_cdn_html()
        + '<script src="https://code.jquery.com/jquery-3.7.1.min.js" defer></script>'
        + '<link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">'
        + '<script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js" defer></script>'
        + '<script type="module" src="../main.js"></script>'
        + dashboard_assets()
    )
    return site_shell(content, mode=mode, assets=assets)
