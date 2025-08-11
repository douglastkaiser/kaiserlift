function calculate1RM(weight, reps) {
    weight = parseFloat(weight);
    reps = parseInt(reps);
    if (!weight || !reps || reps <= 0 || weight < 0) {
        if (weight === 0 && reps > 0) { return 0; }
        return NaN;
    }
    if (reps === 1) { return weight; }
    return weight * (1 + reps / 30.0);
}

function highestWeightPerRep(data) {
    const groups = {};
    data.forEach(row => {
        const ex = row.Exercise;
        if (!groups[ex]) { groups[ex] = []; }
        groups[ex].push(row);
    });
    const result = [];
    Object.values(groups).forEach(rows => {
        const byRep = {};
        rows.forEach(r => {
            const reps = parseInt(r.Reps);
            const weight = parseFloat(r.Weight);
            if (!byRep[reps] || weight > byRep[reps].Weight) {
                byRep[reps] = { ...r, Reps: reps, Weight: weight };
            }
        });
        const candidates = Object.values(byRep);
        candidates.forEach(c => {
            const superseded = candidates.some(o => o.Reps > c.Reps && o.Weight >= c.Weight);
            if (!superseded) { result.push(c); }
        });
    });
    return result;
}

function dfNextPareto(records) {
    const groups = {};
    records.forEach(r => {
        const ex = r.Exercise;
        if (!groups[ex]) { groups[ex] = []; }
        groups[ex].push(r);
    });
    const rows = [];
    Object.entries(groups).forEach(([ex, arr]) => {
        arr.sort((a, b) => a.Reps - b.Reps);
        const ws = arr.map(r => r.Weight);
        const rs = arr.map(r => r.Reps);
        rows.push({ Exercise: ex, Weight: ws[0] + 5, Reps: 1 });
        for (let i = 0; i < rs.length - 1; i++) {
            if (rs[i + 1] > rs[i] + 1) {
                const nr = rs[i] + 1;
                const c1 = ws[i];
                const c2 = ws[i + 1] + 5;
                rows.push({ Exercise: ex, Weight: Math.min(c1, c2), Reps: nr });
            }
        }
        rows.push({ Exercise: ex, Weight: ws[ws.length - 1], Reps: rs[rs.length - 1] + 1 });
    });
    rows.forEach(r => { r["1RM"] = calculate1RM(r.Weight, r.Reps); });
    return rows;
}

function slugify(name) {
    return name.toString().toLowerCase()
        .replace(/[^\w]+/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_|_$/g, '');
}
