use numpy::ndarray::{Array2, ArrayView2, ArrayView3, Axis};
use numpy::{IntoPyArray, PyReadonlyArray2, PyReadonlyArray3};
use pyo3::prelude::*;
use rayon::prelude::*;

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
    directional_weight: f64,
}

impl Default for Cfg {
    fn default() -> Self {
        Cfg {
            beam_width: 12, beam_depth: 40, check_every: 4, speed: 1.0,
            scr_w: 304.0, scr_h: 224.0, ctr_x: 152.0, ctr_y: 112.0,
            danger_base: 3000.0, safety_margin: 2.0,
            wall_penalty: 5000.0, wall_margin: 20.0,
            collision_val: 1e8,
            hit_x1: 2.0, hit_x2: 13.0, hit_y1: 0.0, hit_y2: 10.0,
            tw_base: 0.5, tw_rate: 0.0,
            center_pull_enabled: true, wall_penalty_enabled: true,
            early_exit_enabled: true, early_exit_buffer: 50000.0,
            partial_sort_enabled: true,
            directional_weight: 0.0,
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
        get!(directional_weight, f64);
        Ok(c)
    }
}

fn score_pos(px: f64, py: f64, bullets: ArrayView2<'_, f64>,
             velocities: Option<ArrayView2<'_, f64>>, cfg: &Cfg) -> (f64, bool) {
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
    let dir_w = cfg.directional_weight;

    for i in 0..n {
        let bx = bullets[[i, 0]]; let by = bullets[[i, 1]];
        let dx = bx - px; let dy = by - py;
        if dx >= hx1 && dx < hx2 && dy >= hy1 && dy < hy2 { return (cfg.collision_val, true); }
        let mut d2 = dx * dx + dy * dy;
        if d2 < 4.0 { d2 = 4.0; }
        let mut mult = 1.0;
        if dir_w > 0.0 && let Some(v) = velocities {
            let vx = v[[i, 0]]; let vy = v[[i, 1]];
            let dot = dx * vx + dy * vy;
            if dot < 0.0 {
                let speed = (vx * vx + vy * vy).sqrt().max(0.001);
                let toward = (-dot) / (d2.sqrt().max(0.001) * speed);
                mult += dir_w * toward;
            }
        }
        danger += cfg.danger_base / d2 * mult;
    }
    (danger + wc, false)
}

fn score_pos_early_exit(px: f64, py: f64, bullets: ArrayView2<'_, f64>,
                         velocities: Option<ArrayView2<'_, f64>>,
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
    let dir_w = cfg.directional_weight;

    for i in 0..n {
        let bx = bullets[[i, 0]]; let by = bullets[[i, 1]];
        let dx = bx - px; let dy = by - py;
        if dx >= hx1 && dx < hx2 && dy >= hy1 && dy < hy2 { return (cfg.collision_val, true); }
        let mut d2 = dx * dx + dy * dy;
        if d2 < 4.0 { d2 = 4.0; }
        let mut mult = 1.0;
        if dir_w > 0.0 && let Some(v) = velocities {
            let vx = v[[i, 0]]; let vy = v[[i, 1]];
            let dot = dx * vx + dy * vy;
            if dot < 0.0 {
                let speed = (vx * vx + vy * vy).sqrt().max(0.001);
                let toward = (-dot) / (d2.sqrt().max(0.001) * speed);
                mult += dir_w * toward;
            }
        }
        danger += cfg.danger_base / d2 * mult;
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

    let n_bullets = paths.shape()[0];
    let mut vel_data: Vec<f64> = if cfg.directional_weight > 0.0 {
        vec![0.0; n_bullets * 2]
    } else { vec![] };

    for d in 0..depth {
        let t = (d + 1) * step;
        if t >= t_total { break; }
        let bullets_t = paths.index_axis(Axis(1), t);
        let vel_opt: Option<ArrayView2<'_, f64>> = if cfg.directional_weight > 0.0 && t + 1 < t_total {
            let next = paths.index_axis(Axis(1), t + 1);
            for i in 0..n_bullets {
                vel_data[i * 2] = next[[i, 0]] - bullets_t[[i, 0]];
                vel_data[i * 2 + 1] = next[[i, 1]] - bullets_t[[i, 1]];
            }
            Some(ArrayView2::from_shape((n_bullets, 2), &vel_data).unwrap())
        } else { None };
        let worst_beam = if b_cnt > 0 { b_score[b_cnt - 1] } else { 1e30 };
        let mut ci = 0usize;
        for bi in 0..b_cnt {
            for mi in 0..9 {
                let mut nx = b_px[bi] + moves[mi][0] * cfg.speed * step as f64;
                let mut ny = b_py[bi] + moves[mi][1] * cfg.speed * step as f64;
                if nx < 0.0 { nx = 0.0; } if nx > cfg.scr_w { nx = cfg.scr_w; }
                if ny < 0.0 { ny = 0.0; } if ny > cfg.scr_h { ny = cfg.scr_h; }
                let (s, fatal) = if cfg.early_exit_enabled {
                    score_pos_early_exit(nx, ny, bullets_t, vel_opt, worst_beam, cfg.early_exit_buffer, cfg)
                } else {
                    score_pos(nx, ny, bullets_t, vel_opt, cfg)
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

fn beam_search_forced(px0: f64, py0: f64, paths: ArrayView3<'_, f64>, cfg: &Cfg, force_move: usize) -> f64 {
    let k = cfg.beam_width;
    let depth = cfg.beam_depth;
    let t_total = paths.shape()[1];
    let step = cfg.check_every;
    let moves: [[f64; 2]; 9] = [
        [ 0.0,  0.0], [-1.0,  0.0], [ 1.0,  0.0],
        [ 0.0, -1.0], [ 0.0,  1.0],
        [-1.0, -1.0], [-1.0,  1.0], [ 1.0, -1.0], [ 1.0,  1.0],
    ];

    let t = step;
    if t >= t_total { return 1e30; }
    let mut nx = px0 + moves[force_move][0] * cfg.speed * step as f64;
    let mut ny = py0 + moves[force_move][1] * cfg.speed * step as f64;
    if nx < 0.0 { nx = 0.0; } if nx > cfg.scr_w { nx = cfg.scr_w; }
    if ny < 0.0 { ny = 0.0; } if ny > cfg.scr_h { ny = cfg.scr_h; }

    let bullets_t = paths.index_axis(Axis(1), t);
    let (s0, fatal) = score_pos(nx, ny, bullets_t, None, cfg);
    if fatal { return 1e30; }
    let w0 = 1.0 / (cfg.tw_base + t as f64 * cfg.tw_rate);
    let mut b_score = s0 * w0;

    let mut b_px = vec![0.0f64; k];
    let mut b_py = vec![0.0f64; k];
    let mut b_score_arr = vec![1e30f64; k];
    b_px[0] = nx; b_py[0] = ny; b_score_arr[0] = b_score;
    let mut b_cnt = 1usize;

    let max_cand = k * 9;
    let mut c_px = vec![0.0f64; max_cand];
    let mut c_py = vec![0.0f64; max_cand];
    let mut c_score = vec![0.0f64; max_cand];

    let n_b_forced = paths.shape()[0];
    let mut vel_fdata: Vec<f64> = if cfg.directional_weight > 0.0 {
        vec![0.0; n_b_forced * 2]
    } else { vec![] };

    for d in 1..depth {
        let t = (d + 1) * step;
        if t >= t_total { break; }
        let bullets_t = paths.index_axis(Axis(1), t);
        let vel_opt: Option<ArrayView2<'_, f64>> = if cfg.directional_weight > 0.0 && t + 1 < t_total {
            let next = paths.index_axis(Axis(1), t + 1);
            for i in 0..n_b_forced {
                vel_fdata[i * 2] = next[[i, 0]] - bullets_t[[i, 0]];
                vel_fdata[i * 2 + 1] = next[[i, 1]] - bullets_t[[i, 1]];
            }
            Some(ArrayView2::from_shape((n_b_forced, 2), &vel_fdata).unwrap())
        } else { None };
        let worst_beam = if b_cnt > 0 { b_score_arr[b_cnt - 1] } else { 1e30 };
        let mut ci = 0usize;

        for bi in 0..b_cnt {
            for mi in 0..9 {
                let mut nx = b_px[bi] + moves[mi][0] * cfg.speed * step as f64;
                let mut ny = b_py[bi] + moves[mi][1] * cfg.speed * step as f64;
                if nx < 0.0 { nx = 0.0; } if nx > cfg.scr_w { nx = cfg.scr_w; }
                if ny < 0.0 { ny = 0.0; } if ny > cfg.scr_h { ny = cfg.scr_h; }

                let (s, fatal) = if cfg.early_exit_enabled {
                    score_pos_early_exit(nx, ny, bullets_t, vel_opt, worst_beam, cfg.early_exit_buffer, cfg)
                } else {
                    score_pos(nx, ny, bullets_t, vel_opt, cfg)
                };
                let s = if fatal { s + 1e9 } else { s };
                let w = 1.0 / (cfg.tw_base + t as f64 * cfg.tw_rate);
                let tb = (((nx * 7919.0) as u64 ^ (ny * 6271.0) as u64) & 0xFFF) as f64 * 1e-6;
                c_px[ci] = nx; c_py[ci] = ny;
                c_score[ci] = b_score_arr[bi] + s * w + tb;
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
                b_score_arr[nc] = c_score[idx];
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
                b_score_arr[ki] = c_score[idx];
            }
            b_cnt = limit;
        }
    }

    if b_cnt > 0 { b_score_arr[0] } else { 1e30 }
}

fn multi_beam(px0: f64, py0: f64, paths: ArrayView3<'_, f64>, cfg: &Cfg) -> i32 {
    let scores: Vec<(usize, f64)> = (0..9).into_par_iter().map(|mi| {
        let s = beam_search_forced(px0, py0, paths, cfg, mi);
        (mi, s)
    }).collect();

    scores.into_iter()
        .min_by(|a, b| a.1.partial_cmp(&b.1).unwrap())
        .map(|(mi, _)| mi as i32)
        .unwrap_or(0)
}

// ── MCTS (Monte Carlo Tree Search) ───────────────────────────────────────────

const MOVES: [[f64; 2]; 9] = [
    [ 0.0,  0.0], [-1.0,  0.0], [ 1.0,  0.0],
    [ 0.0, -1.0], [ 0.0,  1.0],
    [-1.0, -1.0], [-1.0,  1.0], [ 1.0, -1.0], [ 1.0,  1.0],
];

/// MCTS tree node. Uses a flat Vec<MctsNode> arena for heap allocation efficiency.
struct MctsNode {
    px: f64, py: f64,
    move_idx: usize,       // which move was taken to reach this node (0-8)
    parent: usize,          // parent node index (usize::MAX for root)
    visits: u32,
    total_value: f64,       // sum of rollout scores (lower = better for danger minimization)
    children: Vec<usize>,   // expanded child indices
    unexpanded: Vec<usize>, // move indices not yet tried from this node
}

/// Fast inline collision check — no danger score, just fatal yes/no.
#[inline(always)]
fn collision(px: f64, py: f64, bullets: ArrayView2<'_, f64>, cfg: &Cfg) -> bool {
    let hx1 = cfg.hit_x1 - cfg.safety_margin;
    let hx2 = cfg.hit_x2 + cfg.safety_margin;
    let hy1 = cfg.hit_y1 - cfg.safety_margin;
    let hy2 = cfg.hit_y2 + cfg.safety_margin;
    for i in 0..bullets.shape()[0] {
        let dx = bullets[[i, 0]] - px;
        let dy = bullets[[i, 1]] - py;
        if dx >= hx1 && dx < hx2 && dy >= hy1 && dy < hy2 { return true; }
    }
    false
}

/// Run N random rollouts of depth D for a single first move. Returns survival count.
fn rollouts(px0: f64, py0: f64, first_move: usize, paths: ArrayView3<'_, f64>,
            cfg: &Cfg, n: usize, seed: u64) -> usize {
    let t_total = paths.shape()[1];
    let depth = cfg.beam_depth.min(t_total - 1);
    let hx1 = cfg.hit_x1 - cfg.safety_margin;
    let hx2 = cfg.hit_x2 + cfg.safety_margin;
    let hy1 = cfg.hit_y1 - cfg.safety_margin;
    let hy2 = cfg.hit_y2 + cfg.safety_margin;

    // Apply first move
    let nx0 = px0 + MOVES[first_move][0];
    let ny0 = py0 + MOVES[first_move][1];

    let mut survived = 0usize;
    let mut rng_state = seed.wrapping_mul(6364136223846793005).wrapping_add(1);

    for _ in 0..n {
        let mut cx = nx0;
        let mut cy = ny0;
        let mut alive = true;

        // Check collision at t=1 (after first move)
        if 1 < t_total {
            let bt = paths.index_axis(Axis(1), 1);
            for i in 0..bt.shape()[0] {
                let dx = bt[[i, 0]] - cx;
                let dy = bt[[i, 1]] - cy;
                if dx >= hx1 && dx < hx2 && dy >= hy1 && dy < hy2 { alive = false; break; }
            }
        }

        // Continue random walk
        let mut t = 2;
        while alive && t <= depth && t < t_total {
            // Fast LCG random move
            rng_state = rng_state.wrapping_mul(6364136223846793005).wrapping_add(1);
            let mi = (rng_state >> 58) as usize % 9;
            cx += MOVES[mi][0];
            cy += MOVES[mi][1];
            if cx < 0.0 { cx = 0.0; } if cx > cfg.scr_w { cx = cfg.scr_w; }
            if cy < 0.0 { cy = 0.0; } if cy > cfg.scr_h { cy = cfg.scr_h; }

            let bt = paths.index_axis(Axis(1), t);
            for i in 0..bt.shape()[0] {
                let dx = bt[[i, 0]] - cx;
                let dy = bt[[i, 1]] - cy;
                if dx >= hx1 && dx < hx2 && dy >= hy1 && dy < hy2 { alive = false; break; }
            }
            t += 1;
        }
        if alive { survived += 1; }
    }
    survived
}

fn mcts(px0: f64, py0: f64, paths: ArrayView3<'_, f64>, cfg: &Cfg, rollouts_per_move: usize) -> (i32, Vec<usize>) {
    let counts: Vec<usize> = (0..9).into_par_iter().map(|mi| {
        let seed = (mi as u64) ^ ((px0 * 1e6) as u64) ^ ((py0 * 1e6) as u64);
        rollouts(px0, py0, mi, paths, cfg, rollouts_per_move, seed)
    }).collect();

    let best = counts.iter().enumerate()
        .max_by_key(|(_, c)| *c)
        .map(|(i, _)| i as i32)
        .unwrap_or(0);
    (best, counts)
}

/// Profile: run rollouts for time_budget_ms, return total count.
fn bench_rollouts(px0: f64, py0: f64, paths: ArrayView3<'_, f64>, cfg: &Cfg, budget_ms: u64) -> usize {
    use std::time::Instant;
    let total: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
    let start = Instant::now();

    (0..9).into_par_iter().for_each(|mi| {
        let seed = (mi as u64) ^ ((px0 * 1e6) as u64);
        let mut rng = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
        let t_total = paths.shape()[1];
        let depth = cfg.beam_depth.min(t_total - 1);
        let hx1 = cfg.hit_x1 - cfg.safety_margin;
        let hx2 = cfg.hit_x2 + cfg.safety_margin;
        let hy1 = cfg.hit_y1 - cfg.safety_margin;
        let hy2 = cfg.hit_y2 + cfg.safety_margin;
        let nx0 = px0 + MOVES[mi][0];
        let ny0 = py0 + MOVES[mi][1];
        let mut cnt = 0usize;

        loop {
            if start.elapsed().as_millis() as u64 >= budget_ms { break; }
            let mut cx = nx0;
            let mut cy = ny0;
            let mut alive = true;
            let mut t = 1;
            while alive && t < t_total {
                rng = rng.wrapping_mul(6364136223846793005).wrapping_add(1);
                let rm = (rng >> 58) as usize % 9;
                cx += MOVES[rm][0]; cy += MOVES[rm][1];
                if cx < 0.0 { cx = 0.0; } if cx > cfg.scr_w { cx = cfg.scr_w; }
                if cy < 0.0 { cy = 0.0; } if cy > cfg.scr_h { cy = cfg.scr_h; }
                let bt = paths.index_axis(Axis(1), t);
                for i in 0..bt.shape()[0] {
                    let dx = bt[[i, 0]] - cx;
                    let dy = bt[[i, 1]] - cy;
                    if dx >= hx1 && dx < hx2 && dy >= hy1 && dy < hy2 { alive = false; break; }
                }
                t += 1;
            }
            cnt += 1;
        }
        total.fetch_add(cnt, std::sync::atomic::Ordering::Relaxed);
    });

    total.load(std::sync::atomic::Ordering::Relaxed)
}

fn guided_rollout(px0: f64, py0: f64, first_move: usize, paths: ArrayView3<'_, f64>,
                  cfg: &Cfg, seed: u64, temperature: f64) -> bool {
    let t_total = paths.shape()[1];
    let depth = cfg.beam_depth.min(t_total - 1);
    let n_bullets = paths.shape()[0];
    let mut vel_data: Vec<f64> = if cfg.directional_weight > 0.0 {
        vec![0.0; n_bullets * 2]
    } else { vec![] };
    let mut rng = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
    let mut cx = px0 + MOVES[first_move][0];
    let mut cy = py0 + MOVES[first_move][1];
    if cx < 0.0 { cx = 0.0; } if cx > cfg.scr_w { cx = cfg.scr_w; }
    if cy < 0.0 { cy = 0.0; } if cy > cfg.scr_h { cy = cfg.scr_h; }

    for t in 1..=depth {
        if t >= t_total { break; }
        let bt = paths.index_axis(Axis(1), t);
        let vel_opt: Option<ArrayView2<'_, f64>> = if cfg.directional_weight > 0.0 && t + 1 < t_total {
            let next = paths.index_axis(Axis(1), t + 1);
            for i in 0..n_bullets {
                vel_data[i * 2] = next[[i, 0]] - bt[[i, 0]];
                vel_data[i * 2 + 1] = next[[i, 1]] - bt[[i, 1]];
            }
            Some(ArrayView2::from_shape((n_bullets, 2), &vel_data).unwrap())
        } else { None };
        // Score all 9 moves, pick via softmax
        let mut scores = [0.0f64; 9];
        let mut min_s = f64::MAX;
        for mi in 0..9 {
            let mut nx = cx + MOVES[mi][0]; let mut ny = cy + MOVES[mi][1];
            if nx < 0.0 { nx = 0.0; } if nx > cfg.scr_w { nx = cfg.scr_w; }
            if ny < 0.0 { ny = 0.0; } if ny > cfg.scr_h { ny = cfg.scr_h; }
            let (s, fatal) = score_pos(nx, ny, bt, vel_opt, cfg);
            scores[mi] = if fatal { 1e30 } else { s };
            if scores[mi] < min_s { min_s = scores[mi]; }
        }
        // Softmax: exp(-(s - min_s) / temp)
        let mut total_w = 0.0f64;
        let mut weights = [0.0f64; 9];
        for mi in 0..9 {
            let w = (-(scores[mi] - min_s) / temperature.max(0.001)).exp();
            weights[mi] = w;
            total_w += w;
        }
        // Sample
        rng = rng.wrapping_mul(6364136223846793005).wrapping_add(1);
        let r = (rng as f64 / u64::MAX as f64) * total_w;
        let mut cum = 0.0;
        let mut pick = 0usize;
        for mi in 0..9 {
            cum += weights[mi];
            if r <= cum { pick = mi; break; }
        }
        cx += MOVES[pick][0]; cy += MOVES[pick][1];
        if cx < 0.0 { cx = 0.0; } if cx > cfg.scr_w { cx = cfg.scr_w; }
        if cy < 0.0 { cy = 0.0; } if cy > cfg.scr_h { cy = cfg.scr_h; }
    }
    true // survived full depth
}

fn guided_mcts(px0: f64, py0: f64, paths: ArrayView3<'_, f64>, cfg: &Cfg,
               rollouts_per_move: usize, temperature: f64) -> (i32, Vec<usize>) {
    let counts: Vec<usize> = (0..9).into_par_iter().map(|mi| {
        let mut survived = 0usize;
        for r in 0..rollouts_per_move {
            let seed = (mi as u64) ^ ((r as u64) << 16) ^ ((px0 * 1e6) as u64) ^ ((py0 * 1e6) as u64);
            if guided_rollout(px0, py0, mi, paths, cfg, seed, temperature) {
                survived += 1;
            }
        }
        survived
    }).collect();
    let best = counts.iter().enumerate()
        .max_by_key(|(_, c)| *c)
        .map(|(i, _)| i as i32)
        .unwrap_or(0);
    (best, counts)
}

fn guided_rollout_score(px0: f64, py0: f64, first_move: usize, paths: ArrayView3<'_, f64>,
                        cfg: &Cfg, seed: u64, tau_start: f64, tau_end: f64) -> f64 {
    let t_total = paths.shape()[1];
    let depth = cfg.beam_depth.min(t_total - 1);
    let depth_f = depth as f64;
    let n_bullets = paths.shape()[0];
    let step = cfg.check_every.max(1) as f64;
    let mut vel_data: Vec<f64> = if cfg.directional_weight > 0.0 {
        vec![0.0; n_bullets * 2]
    } else { vec![] };
    let mut rng = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
    let mut cx = px0 + MOVES[first_move][0] * step;
    let mut cy = py0 + MOVES[first_move][1] * step;
    if cx < 0.0 { cx = 0.0; } if cx > cfg.scr_w { cx = cfg.scr_w; }
    if cy < 0.0 { cy = 0.0; } if cy > cfg.scr_h { cy = cfg.scr_h; }

    // Score first move
    let mut total_danger = 0.0f64;
    if 1 < t_total {
        let bt = paths.index_axis(Axis(1), 1);
        let vel_opt: Option<ArrayView2<'_, f64>> = if cfg.directional_weight > 0.0 && 2 < t_total {
            let next = paths.index_axis(Axis(1), 2);
            for i in 0..n_bullets {
                vel_data[i * 2] = next[[i, 0]] - bt[[i, 0]];
                vel_data[i * 2 + 1] = next[[i, 1]] - bt[[i, 1]];
            }
            Some(ArrayView2::from_shape((n_bullets, 2), &vel_data).unwrap())
        } else { None };
        let (s, fatal) = score_pos(cx, cy, bt, vel_opt, cfg);
        // Depth-proportional death penalty: dying at t=1 in a deep rollout
        // scores worse than dying at t=1 in a shallow rollout.
        // Formula: 1e30 * (depth - t + 1) / (depth + 1), t=1 → depth/(depth+1).
        if fatal { return total_danger + 1e30 * depth as f64 / (depth + 1) as f64; }
        total_danger += s;
    }

    for t in 2..=depth {
        if t >= t_total { break; }
        // Temperature annealing: exponential decay tau_start → tau_end
        let tau = tau_start * (tau_end / tau_start).powf(t as f64 / depth_f);
        let bt = paths.index_axis(Axis(1), t);
        let vel_opt: Option<ArrayView2<'_, f64>> = if cfg.directional_weight > 0.0 && t + 1 < t_total {
            let next = paths.index_axis(Axis(1), t + 1);
            for i in 0..n_bullets {
                vel_data[i * 2] = next[[i, 0]] - bt[[i, 0]];
                vel_data[i * 2 + 1] = next[[i, 1]] - bt[[i, 1]];
            }
            Some(ArrayView2::from_shape((n_bullets, 2), &vel_data).unwrap())
        } else { None };
        let mut scores = [0.0f64; 9];
        let mut min_s = f64::MAX;
        for mi in 0..9 {
            let mut nx = cx + MOVES[mi][0] * step; let mut ny = cy + MOVES[mi][1] * step;
            if nx < 0.0 { nx = 0.0; } if nx > cfg.scr_w { nx = cfg.scr_w; }
            if ny < 0.0 { ny = 0.0; } if ny > cfg.scr_h { ny = cfg.scr_h; }
            if mi == 0 || min_s >= 1e20 {
                let (s, fatal) = score_pos(nx, ny, bt, vel_opt, cfg);
                scores[mi] = if fatal { 1e30 } else { s };
            } else {
                let (s, fatal) = score_pos_early_exit(nx, ny, bt, vel_opt, min_s + 10000.0, 5000.0, cfg);
                scores[mi] = if fatal { 1e30 } else { s };
            }
            if scores[mi] < min_s { min_s = scores[mi]; }
        }
        let mut total_w = 0.0f64;
        let mut weights = [0.0f64; 9];
        for mi in 0..9 {
            let w = (-(scores[mi] - min_s) / tau.max(0.001)).exp();
            weights[mi] = w; total_w += w;
        }
        rng = rng.wrapping_mul(6364136223846793005).wrapping_add(1);
        let r = (rng as f64 / u64::MAX as f64) * total_w;
        let mut cum = 0.0; let mut pick = 0usize;
        for mi in 0..9 { cum += weights[mi]; if r <= cum { pick = mi; break; } }
        cx += MOVES[pick][0] * step; cy += MOVES[pick][1] * step;
    }
    total_danger
}

fn guided_mcts_score(px0: f64, py0: f64, paths: ArrayView3<'_, f64>, cfg: &Cfg,
                     rollouts_per_move: usize, tau_start: f64, tau_end: f64) -> (i32, Vec<f64>) {
    let scores: Vec<f64> = (0..9).into_par_iter().map(|mi| {
        let mut sum = 0.0f64;
        for r in 0..rollouts_per_move {
            let seed = (mi as u64) ^ ((r as u64) << 16) ^ ((px0 * 1e6) as u64) ^ ((py0 * 1e6) as u64);
            sum += guided_rollout_score(px0, py0, mi, paths, cfg, seed, tau_start, tau_end);
        }
        sum / rollouts_per_move as f64
    }).collect();
    let best = scores.iter().enumerate()
        .min_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
        .map(|(i, _)| i as i32)
        .unwrap_or(0);
    (best, scores)
}

fn mcts_ucb(px0: f64, py0: f64, paths: ArrayView3<'_, f64>, cfg: &Cfg,
            iterations: usize, tau_start: f64, tau_end: f64, c: f64) -> (i32, Vec<f64>) {
    let mut arena: Vec<MctsNode> = Vec::with_capacity(iterations * 40);

    // Root node: index 0, position before any move is taken
    arena.push(MctsNode {
        px: px0, py: py0,
        move_idx: 0,
        parent: usize::MAX,
        visits: 0,
        total_value: 0.0,
        children: Vec::new(),
        unexpanded: (0..9).collect(),
    });

    for iter in 0..iterations {
        // ── SELECTION ──────────────────────────────────────────────────────
        // Traverse from root, selecting child with highest UCB,
        // until a node with untried moves (or a leaf) is reached.
        let mut node_idx = 0usize;
        loop {
            if !arena[node_idx].unexpanded.is_empty() {
                // EXPANSION: pick first untried move, create child node
                let mi = arena[node_idx].unexpanded.remove(0);
                let px = arena[node_idx].px;
                let py = arena[node_idx].py;
                let speed = cfg.speed;
                let mut nx = px + MOVES[mi][0] * speed;
                let mut ny = py + MOVES[mi][1] * speed;
                if nx < 0.0 { nx = 0.0; } if nx > cfg.scr_w { nx = cfg.scr_w; }
                if ny < 0.0 { ny = 0.0; } if ny > cfg.scr_h { ny = cfg.scr_h; }

                let new_idx = arena.len();
                arena[node_idx].children.push(new_idx);
                arena.push(MctsNode {
                    px: nx, py: ny,
                    move_idx: mi,
                    parent: node_idx,
                    visits: 0,
                    total_value: 0.0,
                    children: Vec::new(),
                    unexpanded: (0..9).collect(),
                });
                node_idx = new_idx;
                break;
            }

            if arena[node_idx].children.is_empty() {
                // Leaf (no children, no unexpanded) — simulate from here
                break;
            }

            // UCB1 among children: value = -avg_danger + c*sqrt(2*ln(parent_N)/child_N)
            let parent_visits = arena[node_idx].visits as f64;
            let ln_n = if parent_visits > 0.0 { parent_visits.ln() } else { 0.0 };
            let mut best_child = arena[node_idx].children[0];
            let mut best_ucb = f64::NEG_INFINITY;
            for &child_idx in &arena[node_idx].children {
                let cv = arena[child_idx].visits;
                if cv == 0 {
                    best_child = child_idx;
                    break;
                }
                let avg_danger = arena[child_idx].total_value / cv as f64;
                let ucb = -avg_danger + c * (2.0 * ln_n / cv as f64).sqrt();
                if ucb > best_ucb {
                    best_ucb = ucb;
                    best_child = child_idx;
                }
            }
            node_idx = best_child;
        }

        // ── SIMULATION ─────────────────────────────────────────────────────
        let seed = (node_idx as u64) ^ ((iter as u64) << 32);
        let value = guided_rollout_score(
            arena[node_idx].px, arena[node_idx].py, 0,
            paths, cfg, seed, tau_start, tau_end,
        );

        // ── BACKPROP ───────────────────────────────────────────────────────
        let mut bp = node_idx;
        loop {
            arena[bp].visits += 1;
            arena[bp].total_value += value;
            if arena[bp].parent == usize::MAX { break; }
            bp = arena[bp].parent;
        }
    }

    // ── BEST MOVE ──────────────────────────────────────────────────────────
    let root = &arena[0];
    let mut visit_counts = vec![0.0f64; 9];
    let mut best_move = 0i32;
    let mut best_avg = f64::INFINITY;

    for &child in &root.children {
        let child_node = &arena[child];
        let mi = child_node.move_idx;
        visit_counts[mi] = child_node.visits as f64;
        if child_node.visits > 0 {
            let avg = child_node.total_value / child_node.visits as f64;
            if avg < best_avg {
                best_avg = avg;
                best_move = mi as i32;
            }
        }
    }

    (best_move, visit_counts)
}

/// Progressive widening: fast shallow beam filter narrows candidates to top-k,
/// then heavier guided rollouts evaluate only those moves.
fn mcts_progressive(px0: f64, py0: f64, paths: ArrayView3<'_, f64>, cfg: &Cfg,
                    _filter_width: usize, _filter_depth: usize,
                    top_k: usize, iterations: usize,
                    tau_start: f64, tau_end: f64, verify_tau: f64) -> (i32, Vec<f64>) {
    let t_total = paths.shape()[1];
    let filter_step = cfg.check_every.max(1) as f64;
    let probe_ts = [1usize, 5, 10, 20];
    let mut move_scores: Vec<(usize, f64)> = Vec::with_capacity(9);
    for mi in 0..9 {
        let dx = MOVES[mi][0];
        let dy = MOVES[mi][1];
        let mut total = 0.0;
        for &t in &probe_ts {
            if t >= t_total { break; }
            let mut nx = px0 + dx * t as f64 * filter_step;
            let mut ny = py0 + dy * t as f64 * filter_step;
            if nx < 0.0 { nx = 0.0; } if nx > cfg.scr_w { nx = cfg.scr_w; }
            if ny < 0.0 { ny = 0.0; } if ny > cfg.scr_h { ny = cfg.scr_h; }
            let bt = paths.index_axis(Axis(1), t);
            let (s, fatal) = score_pos(nx, ny, bt, None, cfg);
            if fatal { total += 1e10; break; }
            total += s;
        }
        move_scores.push((mi, total));
    }
    move_scores.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());
    let best_heuristic = move_scores[0].1;
    let threshold = if best_heuristic > 0.0 { best_heuristic * 5.0 } else { 1e6 };

    let mut top: Vec<usize> = Vec::with_capacity(top_k);
    for (mi, score) in move_scores.iter().take(top_k) {
        if *score <= threshold { top.push(*mi); } else { break; }
    }
    if top.is_empty() { top.push(move_scores[0].0); }
    let mut visit_counts = vec![0.0f64; 9];
    let mut best_move = 0i32;
    let mut best_score = f64::INFINITY;

    let verify_cfg = cfg.clone();
    let per_move = (iterations / top.len().max(1)).max(3);

    let results: Vec<(usize, f64)> = top.par_iter().map(|&mi| {
        let step = cfg.check_every.max(1) as f64;
        let mut nx = px0 + MOVES[mi][0] * step;
        let mut ny = py0 + MOVES[mi][1] * step;
        if nx < 0.0 { nx = 0.0; } if nx > cfg.scr_w { nx = cfg.scr_w; }
        if ny < 0.0 { ny = 0.0; } if ny > cfg.scr_h { ny = cfg.scr_h; }

        let mut sum = 0.0;
        for r in 0..per_move {
            let seed = (mi as u64) ^ ((r as u64) << 24) ^ ((px0 * 1e6) as u64) ^ ((py0 * 1e6) as u64);
            sum += guided_rollout_score(nx, ny, 0, paths, &verify_cfg, seed, verify_tau, verify_tau);
        }
        (mi, sum / per_move as f64)
    }).collect();

    for (mi, avg) in results {
        visit_counts[mi] = per_move as f64;
        if avg < best_score {
            best_score = avg;
            best_move = mi as i32;
        }
    }

    (best_move, visit_counts)
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
    Ok(score_pos(px, py, bullets.as_array(), None, &cfg))
}

#[pyfunction]
fn max_gap_move_py(px: f64, py: f64, bullets: PyReadonlyArray2<'_, f64>) -> PyResult<i32> {
    Ok(max_gap_move(px, py, bullets.as_array()))
}

#[pyfunction]
#[pyo3(signature = (px, py, paths, **kwargs))]
fn multi_beam_py(px: f64, py: f64, paths: PyReadonlyArray3<'_, f64>,
                 kwargs: Option<&Bound<'_, PyAny>>) -> PyResult<i32> {
    let cfg = kwargs.map_or(Ok(Cfg::default()), |kw| Cfg::from_kwargs(kw))?;
    Ok(multi_beam(px, py, paths.as_array(), &cfg))
}

#[pyfunction]
#[pyo3(signature = (px, py, paths, rollouts_per_move, **kwargs))]
fn mcts_py(px: f64, py: f64, paths: PyReadonlyArray3<'_, f64>,
           rollouts_per_move: usize,
           kwargs: Option<&Bound<'_, PyAny>>) -> PyResult<(i32, Vec<usize>)> {
    let cfg = kwargs.map_or(Ok(Cfg::default()), |kw| Cfg::from_kwargs(kw))?;
    Ok(mcts(px, py, paths.as_array(), &cfg, rollouts_per_move))
}

#[pyfunction]
#[pyo3(signature = (px, py, paths, budget_ms, **kwargs))]
fn bench_rollouts_py(px: f64, py: f64, paths: PyReadonlyArray3<'_, f64>,
                     budget_ms: u64,
                     kwargs: Option<&Bound<'_, PyAny>>) -> PyResult<usize> {
    let cfg = kwargs.map_or(Ok(Cfg::default()), |kw| Cfg::from_kwargs(kw))?;
    Ok(bench_rollouts(px, py, paths.as_array(), &cfg, budget_ms))
}

#[pyfunction]
#[pyo3(signature = (px, py, paths, rollouts_per_move, temperature, **kwargs))]
fn guided_mcts_py(px: f64, py: f64, paths: PyReadonlyArray3<'_, f64>,
                  rollouts_per_move: usize, temperature: f64,
                  kwargs: Option<&Bound<'_, PyAny>>) -> PyResult<(i32, Vec<usize>)> {
    let cfg = kwargs.map_or(Ok(Cfg::default()), |kw| Cfg::from_kwargs(kw))?;
    Ok(guided_mcts(px, py, paths.as_array(), &cfg, rollouts_per_move, temperature))
}

#[pyfunction]
#[pyo3(signature = (px, py, paths, rollouts_per_move, tau_start, tau_end, **kwargs))]
fn guided_mcts_score_py(px: f64, py: f64, paths: PyReadonlyArray3<'_, f64>,
                        rollouts_per_move: usize, tau_start: f64, tau_end: f64,
                        kwargs: Option<&Bound<'_, PyAny>>) -> PyResult<(i32, Vec<f64>)> {
    let cfg = kwargs.map_or(Ok(Cfg::default()), |kw| Cfg::from_kwargs(kw))?;
    Ok(guided_mcts_score(px, py, paths.as_array(), &cfg, rollouts_per_move, tau_start, tau_end))
}

#[pyfunction]
#[pyo3(signature = (px, py, paths, iterations, tau_start, tau_end, c, **kwargs))]
fn mcts_ucb_py(px: f64, py: f64, paths: PyReadonlyArray3<'_, f64>,
               iterations: usize, tau_start: f64, tau_end: f64, c: f64,
               kwargs: Option<&Bound<'_, PyAny>>) -> PyResult<(i32, Vec<f64>)> {
    let cfg = kwargs.map_or(Ok(Cfg::default()), |kw| Cfg::from_kwargs(kw))?;
    Ok(mcts_ucb(px, py, paths.as_array(), &cfg, iterations, tau_start, tau_end, c))
}

#[pyfunction]
#[pyo3(signature = (px, py, paths, filter_width, filter_depth, top_k, iterations, tau_start, tau_end, verify_tau, **kwargs))]
fn mcts_progressive_py(px: f64, py: f64, paths: PyReadonlyArray3<'_, f64>,
                       filter_width: usize, filter_depth: usize, top_k: usize,
                       iterations: usize, tau_start: f64, tau_end: f64, verify_tau: f64,
                       kwargs: Option<&Bound<'_, PyAny>>) -> PyResult<(i32, Vec<f64>)> {
    let cfg = kwargs.map_or(Ok(Cfg::default()), |kw| Cfg::from_kwargs(kw))?;
    Ok(mcts_progressive(px, py, paths.as_array(), &cfg, filter_width, filter_depth, top_k, iterations, tau_start, tau_end, verify_tau))
}

#[pymodule]
fn beam_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(beam_search_py, m)?)?;
    m.add_function(wrap_pyfunction!(score_pos_py, m)?)?;
    m.add_function(wrap_pyfunction!(max_gap_move_py, m)?)?;
    m.add_function(wrap_pyfunction!(multi_beam_py, m)?)?;
    m.add_function(wrap_pyfunction!(mcts_py, m)?)?;
    m.add_function(wrap_pyfunction!(bench_rollouts_py, m)?)?;
    m.add_function(wrap_pyfunction!(guided_mcts_py, m)?)?;
    m.add_function(wrap_pyfunction!(guided_mcts_score_py, m)?)?;
    m.add_function(wrap_pyfunction!(mcts_ucb_py, m)?)?;
    m.add_function(wrap_pyfunction!(mcts_progressive_py, m)?)?;
    Ok(())
}

// ── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use numpy::ndarray::Array3;

    fn cfg() -> Cfg {
        Cfg::default()
    }

    // ── collision ─────────────────────────────────────────────────────────

    /// Bullet inside player hitbox → collision returns true.
    #[test]
    fn collision_true() {
        let c = cfg();
        let px = 100.0;
        let py = 100.0;
        // dx = 5, dy = 5 → inside hitbox [0,15) × [-2,12)
        let bullets = Array2::from_shape_vec((1, 2), vec![105.0, 105.0]).unwrap();
        assert!(collision(px, py, bullets.view(), &c));
    }

    /// Bullet far from player → collision returns false.
    #[test]
    fn collision_false() {
        let c = cfg();
        let px = 100.0;
        let py = 100.0;
        // dx = 100, dy = 100 → outside hitbox
        let bullets = Array2::from_shape_vec((1, 2), vec![200.0, 200.0]).unwrap();
        assert!(!collision(px, py, bullets.view(), &c));
    }

    // ── rollouts ──────────────────────────────────────────────────────────

    /// All bullets far from player at every timestep → every rollout survives.
    #[test]
    fn rollouts_all_survive() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;
        // Shape: (1 bullet, 4 timesteps, 2 coords). All positions far away.
        let data = vec![
            200.0, 200.0, // t=0
            200.0, 200.0, // t=1
            200.0, 200.0, // t=2
            200.0, 200.0, // t=3
        ];
        let paths = Array3::from_shape_vec((1, 4, 2), data).unwrap();
        let n = 10;
        let survived = rollouts(px0, py0, 0, paths.view(), &c, n, 42);
        assert_eq!(survived, n, "all {n} rollouts should survive");
    }

    /// Bullet overlaps player hitbox at t=1 → every rollout dies.
    #[test]
    fn rollouts_all_die() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;
        // Shape: (1 bullet, 2 timesteps, 2 coords). t=1 hits player.
        let data = vec![
            200.0, 200.0, // t=0 (not checked)
            105.0, 105.0, // t=1: dx=5, dy=5 → collision
        ];
        let paths = Array3::from_shape_vec((1, 2, 2), data).unwrap();
        let n = 10;
        let survived = rollouts(px0, py0, 0, paths.view(), &c, n, 42);
        assert_eq!(survived, 0, "all rollouts should die on collision");
    }

    // ── guided_rollout ────────────────────────────────────────────────────

    /// guided_rollout with far bullets always completes the full depth.
    #[test]
    fn guided_rollout_always_survives() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;
        let data = vec![
            200.0, 200.0,
            200.0, 200.0,
            200.0, 200.0,
            200.0, 200.0,
        ];
        let paths = Array3::from_shape_vec((1, 4, 2), data).unwrap();
        assert!(guided_rollout(px0, py0, 0, paths.view(), &c, 42, 1.0));
    }

    // ── guided_rollout_score ──────────────────────────────────────────────

    /// Far bullets → accumulated danger score stays low (≪ 1e30 fatal marker).
    #[test]
    fn guided_rollout_score_survival() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;
        let data = vec![
            200.0, 200.0,
            200.0, 200.0,
            200.0, 200.0,
            200.0, 200.0,
        ];
        let paths = Array3::from_shape_vec((1, 4, 2), data).unwrap();
        let score = guided_rollout_score(px0, py0, 0, paths.view(), &c, 42, 1.0, 1.0);
        assert!(score > 0.0, "score should be positive (center pull), got {score}");
        assert!(score < 1e6, "score should be low for survival, got {score}");
    }

    /// Bullet hits player at t=1 → returns depth-proportional fatal score.
    #[test]
    fn guided_rollout_score_fatal() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;
        let data = vec![
            200.0, 200.0,
            105.0, 105.0, // t=1: dx=5, dy=5 → collision
        ];
        let paths = Array3::from_shape_vec((1, 2, 2), data).unwrap();
        let score = guided_rollout_score(px0, py0, 0, paths.view(), &c, 42, 1.0, 1.0);
        // t_total=2, depth=min(120,1)=1, penalty = 1e30 * 1/(1+1) = 0.5e30
        assert!((score - 0.5e30).abs() < 1e25, "expected ~0.5e30, got {score}");
    }

    /// Deeper rollouts that die at t=1 get proportionally larger penalties.
    /// Survival always scores better than any death.
    #[test]
    fn death_depth_proportional() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;

        // Shallow death: t_total=5, depth=min(120,4)=4, penalty = 1e30 * 4/5 = 0.8e30
        let data4: Vec<f64> = (0..5).flat_map(|_| [105.0_f64, 105.0]).collect();
        let paths4 = Array3::from_shape_vec((1, 5, 2), data4).unwrap();
        let score4 = guided_rollout_score(px0, py0, 0, paths4.view(), &c, 42, 1.0, 1.0);
        assert!((score4 - 0.8e30).abs() < 1e25, "depth=4 death: expected ~0.8e30, got {score4}");

        // Deeper death: t_total=41, depth=min(120,40)=40, penalty = 1e30 * 40/41 ≈ 0.9756e30
        let data40: Vec<f64> = (0..41).flat_map(|_| [105.0_f64, 105.0]).collect();
        let paths40 = Array3::from_shape_vec((1, 41, 2), data40).unwrap();
        let score40 = guided_rollout_score(px0, py0, 0, paths40.view(), &c, 42, 1.0, 1.0);
        let expected40 = 1e30 * 40.0 / 41.0;
        assert!((score40 - expected40).abs() < 1e25, "depth=40 death: expected ~{expected40}, got {score40}");

        // Full survival: far bullets at all frames → score ≪ 1e30
        let data_far: Vec<f64> = (0..5).flat_map(|_| [200.0_f64, 200.0]).collect();
        let paths_far = Array3::from_shape_vec((1, 5, 2), data_far).unwrap();
        let score_far = guided_rollout_score(px0, py0, 0, paths_far.view(), &c, 42, 1.0, 1.0);
        assert!(score_far < 1e6, "survival should score < 1e6, got {score_far}");
        assert!(score_far < score4, "survival ({score_far}) should be better than death ({score4})");
    }

    // ── guided_mcts_score ─────────────────────────────────────────────────

    /// Returns a vector of 9 scores (one per move direction) with finite values.
    #[test]
    fn guided_mcts_score_returns_9_scores() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;
        let data = vec![
            200.0, 200.0,
            200.0, 200.0,
            200.0, 200.0,
            200.0, 200.0,
        ];
        let paths = Array3::from_shape_vec((1, 4, 2), data).unwrap();
        let (best_move, scores) = guided_mcts_score(
            px0, py0, paths.view(), &c, 5, 1.0, 1.0,
        );
        assert_eq!(scores.len(), 9, "should return 9 scores (one per move)");
        assert!((0..9).contains(&(best_move as usize)), "best_move must be 0..8, got {best_move}");
        for (i, s) in scores.iter().enumerate() {
            assert!(s.is_finite(), "score[{i}] = {s} should be finite");
            assert!(*s < 1e6, "score[{i}] = {s} should be low (far bullets)");
        }
    }

    // ── mcts_ucb ───────────────────────────────────────────────────────────

    /// 50 iterations with far bullets → returns a valid move in 0..8.
    #[test]
    fn mcts_ucb_returns_valid_move() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;
        let data: Vec<f64> = (0..5).flat_map(|_| [200.0_f64, 200.0]).collect();
        let paths = Array3::from_shape_vec((1, 5, 2), data).unwrap();
        let (best, visits) = mcts_ucb(px0, py0, paths.view(), &c, 50, 1.0, 1.0, 2.0);
        assert!((0..9).contains(&(best as usize)), "best move {best} must be in 0..8");
        assert_eq!(visits.len(), 9);
        assert!(visits.iter().sum::<f64>() > 0.0, "should have non-zero visits");
    }

    /// 200 iterations with c=10.0 → all 9 moves explored at least once.
    #[test]
    fn mcts_ucb_explores_all() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;
        let data: Vec<f64> = (0..5).flat_map(|_| [200.0_f64, 200.0]).collect();
        let paths = Array3::from_shape_vec((1, 5, 2), data).unwrap();
        let (_best, visits) = mcts_ucb(px0, py0, paths.view(), &c, 200, 1.0, 1.0, 10.0);
        let visited_count = visits.iter().filter(|&&v| v > 0.0).count();
        assert_eq!(visited_count, 9, "all 9 moves should be visited with high c, got visits: {visits:?}");
    }

    /// 500 iterations → best move gets most visits and total visits = 500.
    #[test]
    fn mcts_ucb_converges() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;
        let data: Vec<f64> = (0..5).flat_map(|_| [200.0_f64, 200.0]).collect();
        let paths = Array3::from_shape_vec((1, 5, 2), data).unwrap();
        let (best, visits) = mcts_ucb(px0, py0, paths.view(), &c, 500, 0.1, 0.1, 2.0);
        let total: f64 = visits.iter().sum();
        assert!((total - 500.0).abs() < 1e-10,
            "total visits {total} should equal iterations 500");
        let best_visits = visits[best as usize];
        assert!(best_visits > 50.0,
            "best move should have substantial visits, got {best_visits}");
        let max_visits = visits.iter().cloned().fold(0.0f64, f64::max);
        assert!((best_visits - max_visits).abs() < 1e-10,
            "best move should have most visits, got: best={best}({best_visits}) max={max_visits} visits={visits:?}");
    }

    /// Progressive widening: beam filter identifies top-3, then only those get visited.
    #[test]
    fn mcts_progressive_returns_valid_move() {
        let c = cfg();
        let px0 = 100.0;
        let py0 = 100.0;
        let data: Vec<f64> = (0..5).flat_map(|_| [200.0_f64, 200.0]).collect();
        let paths = Array3::from_shape_vec((1, 5, 2), data).unwrap();
        let (best_move, counts) = mcts_progressive(
            px0, py0, paths.view(), &c, 2, 10, 3, 100, 1.0, 1.0, 2.0,
        );
        assert!(best_move >= 0 && best_move < 9);
        assert_eq!(counts.len(), 9);
        let visited = counts.iter().filter(|&&v| v > 0.0).count();
        assert!(visited <= 3, "only top-3 moves should be visited, got {visited}");
    }
}
