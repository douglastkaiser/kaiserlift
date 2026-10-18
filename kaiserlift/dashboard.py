"""Shared presentation and browser behavior for generated dashboards."""

DASHBOARD_STYLE = """
<style>
body { background: #f3f6f4; color: #213c32; max-width: 1440px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
h1, h2, h3 { font-family: inherit; text-transform: none; letter-spacing: -.025em; }
.page-header { position: relative; text-align: left; margin-bottom: 16px; padding-bottom: 16px; }
.back-link { margin-bottom: 12px; }
.page-header h1 { font-size: 1.6rem; margin-bottom: 2px; font-weight: 750; }
.page-header .subtitle { font-style: normal; font-weight: 400; }
.content-card { width: 100%; border-radius: 16px; box-shadow: none; padding: 24px; }
.dashboard-toolbar { display: flex; justify-content: space-between; gap: 24px;
    align-items: center; margin-bottom: 24px; }
.dashboard-toolbar .control-stack { margin: 0; min-width: min(100%, 320px); }
.dashboard-toolbar h2 { font-size: 1.8rem; font-weight: 700; }
.eyebrow { color: #4a7c59; font-size: .75rem; font-weight: 750;
    text-transform: uppercase; letter-spacing: .12em; }
.dashboard-grid { display: grid; grid-template-columns: minmax(0, 1fr) 270px;
    gap: 24px; align-items: start; }
.chart-card { min-width: 0; overflow: hidden; }
.chart-card h3 { font-size: 1.1rem; font-weight: 650; }
.figures-grid { display: block; min-width: 0; }
.target-card { background: #e8f2eb; border: 1px solid #cadfce; border-radius: 14px;
    padding: 24px; margin-top: 4px; }
.target-value { display: block; font-size: 1.8rem; line-height: 1.25;
    font-weight: 750; margin: 16px 0; }
.target-card p, .chart-help { font-size: .9rem; color: #51665b; }
.chart-help { margin-top: 16px; }
.chart-help summary { cursor: pointer; padding: 10px 0; }
.chart-help p { max-width: 70ch; }
.target-table h2 { font-size: 1.2rem; font-weight: 650; margin-bottom: 16px; }
.target-table tr.is-selected td { background: #dceee2 !important; }
.target-table tbody tr { cursor: pointer; }
.import-panel { margin-bottom: 20px; }
.import-panel summary { cursor: pointer; font-weight: 600; min-height: 24px; }
.dashboard-nav { display: flex; gap: 8px; margin-top: 12px; }
@media (min-width: 600px) { .dashboard-nav { position: absolute; right: 0; top: 0; margin-top: 0; } }
.dashboard-nav a { color: #365342; padding: 8px 16px; border-radius: 8px;
    text-decoration: none; border: 1px solid #d5dfd8; }
.dashboard-nav a[aria-current] { background: #244f39; color: white; }
:focus-visible { outline: 3px solid #477cbd; outline-offset: 3px; }
.exercise-figure, .running-figure { border: 0; padding: 0; box-shadow: none; margin: 12px 0; opacity: 1; animation: none; }
[data-exercise-panel][hidden] { display: none !important; }
select#exerciseDropdown { min-height: 44px; width: 100%; }
@media (max-width: 900px) {
    .dashboard-grid { grid-template-columns: minmax(0, 1fr); }
    .target-card { margin-top: 0; }
    .dashboard-toolbar { align-items: stretch; flex-direction: column; gap: 16px; }
    .content-card { padding: 16px; }
}
</style>
"""

DASHBOARD_SCRIPT = r"""
<script>
window.initializeDashboard = function(root = document) {
    const dropdown = root.querySelector('#exerciseDropdown');
    const tableEl = root.querySelector('#exerciseTable');
    const table = tableEl && window.jQuery && jQuery.fn.DataTable
        ? (jQuery.fn.DataTable.isDataTable(tableEl) ? jQuery(tableEl).DataTable()
            : jQuery(tableEl).DataTable({pageLength: 10, autoWidth: false})) : null;
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
    // Running charts do not need an exercise filter.
    root.querySelectorAll('.running-figure').forEach(hydrate);
    update();
};
document.addEventListener('DOMContentLoaded', () => window.initializeDashboard());
</script>
"""


def dashboard_assets() -> str:
    """Return shared styles and initialization for standalone viewers."""
    return DASHBOARD_STYLE + DASHBOARD_SCRIPT
