use numpy::ndarray::{ArrayView2, ArrayView3, Axis};
use numpy::{PyReadonlyArray2, PyReadonlyArray3};
use pyo3::prelude::*;

#[derive(Clone)]
struct Cfg {
    beam_width: usize, beam_depth: usize, check_every: usize,
    speed: f64,
    scr_w: f64, scr_h: f64, ctr_x: f64, ctr_y: f64,
    danger_base: f64, safety_margin: f64,
    wall_penalty: f64, wall_margin: f64,
    collision_val: f64,
    hit_x1: f64, hit_x2: f64, hit_y1: f64, hit_y2: f64,
    tw_base: f64, tw_rate: f64,
    center_pull_enabled: bool, wall_penalty_enabled: bool,
    early_exit_enabled: bool, early_exit_buffer: f64,
    partial_sort_enabled: bool,
}

impl Default for Cfg {
    fn default() -> Self {
        Cfg {
            beam_width: 12, beam_depth: 120, check_every: 1, speed: 1.0,
            scr_w: 304.0, scr_h: 224.0, ctr_x: 152.0, ctr_y: 112.0,
            danger_base: 2000.0, safety_margin: 2.0,
            wall_penalty: 5000.0, wall_margin: 40.0,
            collision_val: 1e8,
            hit_x1: 2.0, hit_x2: 13.0, hit_y1: 0.0, hit_y2: 10.0,
            tw_base: 0.5, tw_rate: 0.0,
            center_pull_enabled: true, wall_penalty_enabled: true,
            early_exit_enabled: true, early_exit_buffer: 50000.0,
            partial_sort_enabled: true,
        }
    }
}

impl Cfg {
    fn from_kwargs(kw: &Bound<'_, PyAny>) -> PyResult<Self> {
        let mut c = Cfg::default();
        macro_rules! get { ($f:ident, $t:ty) => {
            if let Ok(v) = kw.get_item(stringify!($f)) { c.$f = v.extract::<$t>()?; }
        }}
        get!(beam_width, usize); get!(beam_depth, usize); get!(check_every, usize);
        get!(danger_base, f64); get!(safety_margin, f64);
        get!(wall_penalty, f64); get!(wall_margin, f64);
        get!(tw_base, f64); get!(tw_rate, f64);
        get!(early_exit_enabled, bool); get!(early_exit_buffer, f64);
        get!(partial_sort_enabled, bool);
        get!(center_pull_enabled, bool); get!(wall_penalty_enabled, bool);
        Ok(c)
    }
}

fn score_pos(px: f64, py: f64, bullets: ArrayView2<'_, f64>, cfg: &Cfg) -> (f64, bool) {
    let n = bullets.shape()[0];
    let mut danger = 0.0f64;
    let mut wc = 0.0;
    if cfg.center_pull_enabled {
        wc += (px - cfg.ctr_x).abs() * 0.3 + (py - cfg.ctr_y).abs() * 0.3;
    }
    if cfg.wall_penalty_enabled {
        if px < cfg.wall_margin { wc += (cfg.wall_margin - px) * cfg.wall_penalty; }
        else if px > cfg.scr_w - cfg.wall_margin { wc += (px - (cfg.scr_w - cfg.wall_margin)) * cfg.wall_penalty; }
        if py < cfg.wall_margin { wc += (cfg.wall_margin - py) * cfg.wall_penalty; }
        else if py > cfg.scr_h - cfg.wall_margin { wc += (py - (cfg.scr_h - cfg.wall_margin)) * cfg.wall_penalty; }
    }
    let hx1 = cfg.hit_x1 - cfg.safety_margin;
    let hx2 = cfg.hit_x2 + cfg.safety_margin;
    let hy1 = cfg.hit_y1 - cfg.safety_margin;
    let hy2 = cfg.hit_y2 + cfg.safety_margin;
    for i in 0..n {
        let bx = bullets[[i, 0]]; let by = bullets[[i, 1]];
        let dx = bx - px; let dy = by - py;
        if dx >= hx1 && dx < hx2 && dy >= hy1 && dy < hy2 { return (cfg.collision_val, true); }
        let mut d2 = dx * dx + dy * dy;
        if d2 < 4.0 { d2 = 4.0; }
        danger += cfg.danger_base / d2;
    }
    (danger + wc, false)
}

fn score_pos_early_exit(px: f64, py: f64, bullets: ArrayView2<'_, f64>,
                         best_so_far: f64, buffer: f64, cfg: &Cfg) -> (f64, bool) {
    let n = bullets.shape()[0];
    let mut danger = 0.0f64;
    let mut wc = 0.0;
    if cfg.center_pull_enabled {
        wc += (px - cfg.ctr_x).abs() * 0.3 + (py - cfg.ctr_y).abs() * 0.3;
    }
    if cfg.wall_penalty_enabled {
        if px < cfg.wall_margin { wc += (cfg.wall_margin - px) * cfg.wall_penalty; }
        else if px > cfg.scr_w - cfg.wall_margin { wc += (px - (cfg.scr_w - cfg.wall_margin)) * cfg.wall_penalty; }
        if py < cfg.wall_margin { wc += (cfg.wall_margin - py) * cfg.wall_penalty; }
        else if py > cfg.scr_h - cfg.wall_margin { wc += (py - (cfg.scr_h - cfg.wall_margin)) * cfg.wall_penalty; }
    }
    let hx1 = cfg.hit_x1 - cfg.safety_margin;
    let hx2 = cfg.hit_x2 + cfg.safety_margin;
    let hy1 = cfg.hit_y1 - cfg.safety_margin;
    let hy2 = cfg.hit_y2 + cfg.safety_margin;
    for i in 0..n {
        let bx = bullets[[i, 0]]; let by = bullets[[i, 1]];
        let dx = bx - px; let dy = by - py;
        if dx >= hx1 && dx < hx2 && dy >= hy1 && dy < hy2 { return (cfg.collision_val, true); }
        let mut d2 = dx * dx + dy * dy;
        if d2 < 4.0 { d2 = 4.0; }
        danger += cfg.danger_base / d2;
        if danger + wc > best_so_far + buffer { return (danger + wc + buffer * 2.0, false); }
    }
    (danger + wc, false)
}

fn beam_search(px0: f64, py0: f64, paths: ArrayView3<'_, f64>, cfg: &Cfg) -> i32 {
    let k = cfg.beam_width;
    let depth = cfg.beam_depth;
    let t_total = paths.shape()[1];
    let step = cfg.check_every;
    let moves: [[f64; 2]; 9] = [
        [ 0.0,  0.0], [-1.0,  0.0], [ 1.0,  0.0],
        [ 0.0, -1.0], [ 0.0,  1.0],
        [-1.0, -1.0], [-1.0,  1.0], [ 1.0, -1.0], [ 1.0,  1.0],
    ];
    let mut b_px = vec![0.0f64; k];
    let mut b_py = vec![0.0f64; k];
    let mut b_first = vec![-1i32; k];
    let mut b_score = vec![1e30f64; k];
    b_px[0] = px0; b_py[0] = py0;
    b_first[0] = -1; b_score[0] = 0.0;
    let mut b_cnt = 1usize;
    let max_cand = k * 9;
    let mut c_px = vec![0.0f64; max_cand];
    let mut c_py = vec![0.0f64; max_cand];
    let mut c_first = vec![0i32; max_cand];
    let mut c_score = vec![0.0f64; max_cand];

    for d in 0..depth {
        let t = (d + 1) * step;
        if t >= t_total { break; }
        let bullets_t = paths.index_axis(Axis(1), t);
        let worst_beam = if b_cnt > 0 { b_score[b_cnt - 1] } else { 1e30 };
        let mut ci = 0usize;
        for bi in 0..b_cnt {
            for mi in 0..9 {
                let mut nx = b_px[bi] + moves[mi][0] * cfg.speed * step as f64;
                let mut ny = b_py[bi] + moves[mi][1] * cfg.speed * step as f64;
                if nx < 0.0 { nx = 0.0; } if nx > cfg.scr_w { nx = cfg.scr_w; }
                if ny < 0.0 { ny = 0.0; } if ny > cfg.scr_h { ny = cfg.scr_h; }
                let (s, fatal) = if cfg.early_exit_enabled {
                    score_pos_early_exit(nx, ny, bullets_t, worst_beam, cfg.early_exit_buffer, cfg)
                } else {
                    score_pos(nx, ny, bullets_t, cfg)
                };
                let s = if fatal { s + 1e9 } else { s };
                let w = 1.0 / (cfg.tw_base + t as f64 * cfg.tw_rate);
                let tb = (((nx * 7919.0) as u64 ^ (ny * 6271.0) as u64) & 0xFFF) as f64 * 1e-6;
                let total = b_score[bi] + s * w + tb;
                c_px[ci] = nx; c_py[ci] = ny;
                c_first[ci] = if b_first[bi] >= 0 { b_first[bi] } else { mi as i32 };
                c_score[ci] = total;
                ci += 1;
            }
        }
        if cfg.partial_sort_enabled {
            let mut top_k = vec![-1i32; k];
            let mut top_score = vec![1e30f64; k];
            for i in 0..ci {
                let score = c_score[i];
                for ki in 0..k {
                    if score < top_score[ki] {
                        for j in (ki + 1..k).rev() { top_k[j] = top_k[j - 1]; top_score[j] = top_score[j - 1]; }
                        top_k[ki] = i as i32; top_score[ki] = score;
                        break;
                    }
                }
            }
            let mut nc = 0usize;
            for ki in 0..k {
                if top_k[ki] < 0 { break; }
                let idx = top_k[ki] as usize;
                b_px[nc] = c_px[idx]; b_py[nc] = c_py[idx];
                b_first[nc] = c_first[idx]; b_score[nc] = c_score[idx];
                nc += 1;
            }
            b_cnt = nc;
        } else {
            let mut indices: Vec<usize> = (0..ci).collect();
            indices.sort_by(|&a, &b| c_score[a].partial_cmp(&c_score[b]).unwrap());
            let limit = k.min(indices.len());
            for ki in 0..limit {
                let idx = indices[ki];
                b_px[ki] = c_px[idx]; b_py[ki] = c_py[idx];
                b_first[ki] = c_first[idx]; b_score[ki] = c_score[idx];
            }
            b_cnt = limit;
        }
    }
    b_first[0]
}

fn max_gap_move(px: f64, py: f64, bullets: ArrayView2<'_, f64>) -> i32 {
    let n = bullets.shape()[0];
    if n == 0 { return 0; }
    let r2: f64 = 60.0 * 60.0;
    let mut angles: Vec<f64> = Vec::with_capacity(n);
    for i in 0..n {
        let dx = bullets[[i, 0]] - px; let dy = bullets[[i, 1]] - py;
        if dx * dx + dy * dy < r2 { angles.push(dy.atan2(dx)); }
    }
    let n = angles.len();
    if n == 0 { return 0; }
    angles.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let mut best_gap = 0.0f64; let mut best_mid = 0.0f64;
    for i in 0..n - 1 {
        let gap = angles[i + 1] - angles[i];
        if gap > best_gap { best_gap = gap; best_mid = (angles[i] + angles[i + 1]) * 0.5; }
    }
    let wrap_gap = angles[0] + 2.0 * std::f64::consts::PI - angles[n - 1];
    if wrap_gap > best_gap { best_gap = wrap_gap; best_mid = angles[n - 1] + wrap_gap * 0.5;
        if best_mid > std::f64::consts::PI { best_mid -= 2.0 * std::f64::consts::PI; } }
    let cos_a = best_mid.cos(); let sin_a = best_mid.sin();
    let (mx, my) = if cos_a.abs() > sin_a.abs() {
        (if cos_a > 0.0 { 1 } else { -1 },
         if sin_a > 0.4 { 1 } else if sin_a < -0.4 { -1 } else { 0 })
    } else {
        let my_dir = if sin_a > 0.0 { 1 } else { -1 };
        (if cos_a > 0.4 { 1 } else if cos_a < -0.4 { -1 } else { 0 }, my_dir)
    };
    let moves: [[i32; 2]; 9] = [[ 0,  0], [-1,  0], [ 1,  0], [ 0, -1], [ 0,  1], [-1, -1], [-1,  1], [ 1, -1], [ 1,  1]];
    for mi in 0..9 { if moves[mi][0] == mx && moves[mi][1] == my { return mi as i32; } }
    0
}

#[pyfunction]
#[pyo3(signature = (px, py, paths, **kwargs))]
fn beam_search_py(px: f64, py: f64, paths: PyReadonlyArray3<'_, f64>,
                  kwargs: Option<&Bound<'_, PyAny>>) -> PyResult<i32> {
    let cfg = kwargs.map_or(Ok(Cfg::default()), |kw| Cfg::from_kwargs(kw))?;
    Ok(beam_search(px, py, paths.as_array(), &cfg))
}

#[pyfunction]
#[pyo3(signature = (px, py, bullets, **kwargs))]
fn score_pos_py(px: f64, py: f64, bullets: PyReadonlyArray2<'_, f64>,
                kwargs: Option<&Bound<'_, PyAny>>) -> PyResult<(f64, bool)> {
    let cfg = kwargs.map_or(Ok(Cfg::default()), |kw| Cfg::from_kwargs(kw))?;
    Ok(score_pos(px, py, bullets.as_array(), &cfg))
}

#[pyfunction]
fn max_gap_move_py(px: f64, py: f64, bullets: PyReadonlyArray2<'_, f64>) -> PyResult<i32> {
    Ok(max_gap_move(px, py, bullets.as_array()))
}

#[pymodule]
fn beam_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(beam_search_py, m)?)?;
    m.add_function(wrap_pyfunction!(score_pos_py, m)?)?;
    m.add_function(wrap_pyfunction!(max_gap_move_py, m)?)?;
    Ok(())
}
