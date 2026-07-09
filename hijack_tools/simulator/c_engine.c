/*
 * c_engine.c — Core 99.exe game simulator in C.
 * Compile: tcc -shared -o sim_core.dll c_engine.c
 *
 * API (all functions extern "C"):
 *   void* sim_create(int difficulty, int seed);
 *   void  sim_destroy(void* sim);
 *   void  sim_reset(void* sim);
 *   int   sim_step(void* sim, int input_bits);  // returns 1=alive, 0=dead
 *   void  sim_get_player(void* sim, int* px, int* py);
 *   int   sim_get_bullet_count(void* sim);
 *   void  sim_get_bullet(void* sim, int idx, int* x, int* y, int* type, int* angle, int* vx, int* vy);
 *   int   sim_get_graze(void* sim);
 *   int   sim_get_frame(void* sim);
 */

#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>

/* ── Constants (from config.py) ─────────────────────────── */
#define SCR_W           304
#define SCR_H           224
#define RAW_MAX_X       0x5101   /* off-screen threshold    */
#define RAW_MAX_Y       0x3D01   /* off-screen threshold    */
#define RAW_SPAWN_X     0x5100   /* spawn edge modulo       */
#define RAW_SPAWN_Y     0x3D00   /* spawn edge position     */
#define MAX_ENTITIES    300
#define MAX_BULLETS     299
#define NUM_ANGLES      64
#define RAW_SHIFT       6
#define PIXEL_OFFSET    4
#define PLAYER_CX       6
#define INACTIVE        0xFF

#define TYPE_NORMAL     0
#define TYPE_HOMING     1
#define TYPE_H_ACCEL    2
#define TYPE_ACCEL      3

#define HIT_X1          2
#define HIT_X2          13
#define HIT_Y1          0
#define HIT_Y2          10

#define LCG_MULT        0x343FD
#define LCG_ADD         0x269EC3
#define LCG_MASK        0x7FFF

#define SPAWN_EDGES     4
#define PATTERN_CHANCE  0x3000
#define STEER_NEAR      0x19
#define STEER_LOSE      0x28
#define HOMING_MASK     0x7
#define VX_CAP          96
#define MAX_BOUNCE      4

/* ── Velocity tables (from binary) ──────────────────────── */
static const int VEL_TABLE[64][2] = {
    {64,0},{63,6},{62,12},{61,18},{59,24},{56,30},{53,35},{49,40},
    {45,45},{40,49},{35,53},{30,56},{24,59},{18,61},{12,62},{6,63},
    {0,64},{-6,63},{-12,62},{-18,61},{-24,59},{-30,56},{-35,53},{-40,49},
    {-45,45},{-49,40},{-53,35},{-56,30},{-59,24},{-61,18},{-62,12},{-63,6},
    {-64,0},{-63,-6},{-62,-12},{-61,-18},{-59,-24},{-56,-30},{-53,-35},{-49,-40},
    {-45,-45},{-40,-49},{-35,-53},{-30,-56},{-24,-59},{-18,-61},{-12,-62},{-6,-63},
    {0,-64},{6,-63},{12,-62},{18,-61},{24,-59},{30,-56},{35,-53},{40,-49},
    {45,-45},{49,-40},{53,-35},{56,-30},{59,-24},{61,-18},{62,-12},{63,-6},
};

static const int ACCEL_TABLE[64][2] = {
    {80,0},{79,7},{78,15},{76,23},{73,30},{70,37},{66,44},{61,50},
    {56,56},{50,61},{44,66},{37,70},{30,73},{23,76},{15,78},{7,79},
    {0,80},{-7,79},{-15,78},{-23,76},{-30,73},{-37,70},{-44,66},{-50,61},
    {-56,56},{-61,50},{-66,44},{-70,37},{-73,30},{-76,23},{-78,15},{-79,7},
    {-80,0},{-79,-7},{-78,-15},{-76,-23},{-73,-30},{-70,-37},{-66,-44},{-61,-50},
    {-56,-56},{-50,-61},{-44,-66},{-37,-70},{-30,-73},{-23,-76},{-15,-78},{-7,-79},
    {0,-80},{7,-79},{15,-78},{23,-76},{30,-73},{37,-70},{44,-66},{50,-61},
    {56,-56},{61,-50},{66,-44},{70,-37},{73,-30},{76,-23},{78,-15},{79,-7},
};

/* Full VEL table with tan ratios for octant search */
static const int VEL_FULL[64][3] = {
    {64,0,65536},{63,6,10752},{62,12,5290},{61,18,3470},{59,24,2517},{56,30,1911},
    {53,35,1550},{49,40,1254},{45,45,1024},{40,49,835},{35,53,676},{30,56,548},
    {24,59,416},{18,61,302},{12,62,198},{6,63,97},{0,64,0},{-6,63,97},
    {-12,62,198},{-18,61,302},{-24,59,416},{-30,56,548},{-35,53,676},{-40,49,835},
    {-45,45,1024},{-49,40,1254},{-53,35,1550},{-56,30,1911},{-59,24,2517},{-61,18,3470},
    {-62,12,5290},{-63,6,10752},{-64,0,65536},{-63,-6,10752},{-62,-12,5290},{-61,-18,3470},
    {-59,-24,2517},{-56,-30,1911},{-53,-35,1550},{-49,-40,1254},{-45,-45,1024},{-40,-49,835},
    {-35,-53,676},{-30,-56,548},{-24,-59,416},{-18,-61,302},{-12,-62,198},{-6,-63,97},
    {0,-64,0},{6,-63,97},{12,-62,198},{18,-61,302},{24,-59,416},{30,-56,548},
    {35,-53,676},{40,-49,835},{45,-45,1024},{49,-40,1254},{53,-35,1550},{56,-30,1911},
    {59,-24,2517},{61,-18,3470},{62,-12,5290},{63,-6,10752},
};

/* Pattern info per index: type, timer, spread */
static const int PATTERN_INFO[8][3] = {
    {0,0,5}, {0,0,0}, {1,0x30,5}, {1,0x20,5},
    {1,0x10,5}, {1,0,5}, {3,0,5}, {2,0,0},
};

/* ── Bullet struct (15 bytes in original, padded here) ──── */
typedef struct {
    int raw_x, raw_y;
    unsigned char angle_index, grazed, type, timer, counter;
    char vx, vy;
} Bullet;

/* ── Game state ─────────────────────────────────────────── */
typedef struct {
    Bullet bullets[MAX_ENTITIES];
    int px, py;
    int frame;
    int dead;
    int bullet_count;
    int next_spawn;
    int next_pattern;
    int pattern;
    int bounce_limit;
    int active_near;
    int graze_total;
    int graze_chain;
    int graze_chain_time;
    unsigned int rng_state;
    int spawn_interval;
} GameState;


static void reset_state(GameState *s) {
    s->px = 152;
    s->py = 44;
    s->frame = 0;
    s->dead = 0;
    s->next_spawn = 0;
    s->next_pattern = 400;
    s->pattern = 0;
    s->bounce_limit = 0;
    s->active_near = 0;
    s->graze_total = 0;
    s->graze_chain = 0;
    s->graze_chain_time = 0;
    memset(s->bullets, 0xFF, sizeof(s->bullets));
}

/* ── Forward declarations ───────────────────────────────── */
static void spawn_at(GameState *s, int slot);
static void move_bullet(Bullet *b, int px, int py, unsigned int *rng);
static int compute_aimed_angle(int bx, int by, int px, int py,
                                unsigned int *rng, int spread);


/* ── RNG ────────────────────────────────────────────────── */
static unsigned int rng_next(unsigned int *state) {
    *state = (*state * LCG_MULT + LCG_ADD) & 0xFFFFFFFF;
    return (*state >> 16) & LCG_MASK;
}

/* ── Octant search (FUN_00402d68) ───────────────────────── */
static int compute_aimed_angle(int bx, int by, int px, int py,
                                unsigned int *rng, int spread) {
    int dx = (px + PLAYER_CX) - (bx >> RAW_SHIFT);
    int dy = (py + PLAYER_CX) - (by >> RAW_SHIFT);
    int octant, divisor;

    /* Octant determination — divisor=dy always (asm: idiv esi) */
    if (dx < 0) {
        if (dy <= 0) {
            octant = (dy < dx) ? 0x20 : 0x28;
            divisor = dy;
        } else {
            octant = (dx < -dy) ? 0x18 : 0x10;
            divisor = dy;
        }
    } else if (dy < 0) {
        octant = (dx < -dy) ? 0x30 : 0x38;
        divisor = dy;
    } else {
        if (dx == 0)          { octant = 0x10; divisor = dy; }
        else if (dy == 0)     { octant = 0;    divisor = 0;  }
        else                  { octant = (dx < dy) ? 8 : 0; divisor = dy; }
    }

    int angle;
    if (dy == 0) {
        angle = octant & 0xFF;
    } else {
        /* quotient = abs(dx * 0x400) / abs(dy) — truncation not floor */
        int quotient = abs(dx * 0x400) / abs(dy);

        int best_diff = 0x10000;
        int entry_idx = octant & 0xFF;
        int counter = 0;
        angle = octant & 0xFF;

        while (counter < 7) {
            int idx = (entry_idx % NUM_ANGLES);
            int vy = VEL_FULL[idx][1];
            int tan_ratio = VEL_FULL[idx][2];
            int diff;

            if (vy == 0) {
                diff = 0xFFFF;
            } else {
                if (quotient <= tan_ratio)
                    diff = tan_ratio - quotient;
                else
                    diff = quotient - tan_ratio;
            }

            /* jge -> break if diff >= best_diff */
            if (diff >= best_diff)
                break;

            best_diff = diff;
            entry_idx++;
            angle = (octant + counter + 1) & 0xFF;  /* inc ebx */
            counter++;
        }
    }

    /* Spread jitter */
    if (spread) {
        int rv = rng_next(rng);
        angle = (angle + (rv % spread) + 1 - (spread >> 1)) & 0x3F;
    }

    return angle & 0x3F;
}

/* ── Spawn one bullet into slot ─────────────────────────── */
static void spawn_at(GameState *s, int slot) {
    Bullet *b = &s->bullets[slot];
    int edge = rng_next(&s->rng_state) & (SPAWN_EDGES - 1);

    if (edge == 0)      { b->raw_x = rng_next(&s->rng_state) % RAW_SPAWN_X; b->raw_y = 0; }
    else if (edge == 1) { b->raw_x = rng_next(&s->rng_state) % RAW_SPAWN_X; b->raw_y = RAW_SPAWN_Y; }
    else if (edge == 2) { b->raw_x = 0; b->raw_y = rng_next(&s->rng_state) % RAW_SPAWN_Y; }
    else                { b->raw_x = RAW_SPAWN_X; b->raw_y = rng_next(&s->rng_state) % RAW_SPAWN_Y; }

    int pat = s->pattern;
    if (pat < 0 || pat > 7) pat = 0;
    b->type = PATTERN_INFO[pat][0];
    b->timer = PATTERN_INFO[pat][1];
    b->counter = 0;
    b->grazed = 0;
    b->vx = 0;
    b->vy = 0;

    if (pat == 5)
        b->timer = ((rng_next(&s->rng_state) & 3) + 1) * 16;

    if (pat == 7) {
        if (s->bounce_limit >= MAX_BOUNCE) b->type = TYPE_NORMAL;
        else s->bounce_limit++;
        b->angle_index = 0;
        return;
    }

    b->angle_index = compute_aimed_angle(b->raw_x, b->raw_y, s->px, s->py,
                                          &s->rng_state, PATTERN_INFO[pat][2]);
}

/* ── Move one bullet ────────────────────────────────────── */
static void move_bullet(Bullet *b, int px, int py, unsigned int *rng) {
    int idx;
    switch (b->type) {
    case TYPE_HOMING:
        b->counter++;
        if (b->counter >= b->timer) {
            b->counter = rng_next(rng) & HOMING_MASK;
            int target = compute_aimed_angle(b->raw_x, b->raw_y, px, py, rng, 3);
            int cur = b->angle_index;
            if (target != cur) {
                if (target < cur) cur = (cur - NUM_ANGLES) & 0xFF;
                int diff = (target - cur) & 0xFF;
                if (diff < STEER_NEAR)
                    b->angle_index = (b->angle_index + 1) & (NUM_ANGLES - 1);
                else if (diff < STEER_LOSE)
                    b->type = TYPE_NORMAL;
                else
                    b->angle_index = (b->angle_index - 1) & (NUM_ANGLES - 1);
            }
        }
        idx = b->angle_index & (NUM_ANGLES - 1);
        b->raw_x += VEL_TABLE[idx][0];
        b->raw_y += VEL_TABLE[idx][1];
        break;

    case TYPE_H_ACCEL: {
        int bx = (b->raw_x >> RAW_SHIFT) - PIXEL_OFFSET;
        int by = (b->raw_y >> RAW_SHIFT) - PIXEL_OFFSET;
        int tx = px + PLAYER_CX;
        int ty = py + PLAYER_CX;
        if (bx < tx) { if (b->vx < VX_CAP) b->vx++; }
        else if (b->vx > -VX_CAP) b->vx--;
        if (by < ty) { if (b->vy < VX_CAP) b->vy++; }
        else if (b->vy > -VX_CAP) b->vy--;
        b->raw_x += b->vx;
        b->raw_y += b->vy;
        break;
    }

    case TYPE_ACCEL:
        idx = b->angle_index & (NUM_ANGLES - 1);
        b->raw_x += ACCEL_TABLE[idx][0];
        b->raw_y += ACCEL_TABLE[idx][1];
        break;

    default:
        idx = b->angle_index & (NUM_ANGLES - 1);
        b->raw_x += VEL_TABLE[idx][0];
        b->raw_y += VEL_TABLE[idx][1];
        break;
    }
}

/* ═══════════════════════════════════════════════════════════
 * PUBLIC API
 * ═══════════════════════════════════════════════════════════ */

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

EXPORT GameState* sim_create(int difficulty, int seed) {
    GameState *s = (GameState*)calloc(1, sizeof(GameState));
    if (!s) return NULL;

    int bullets[] = {30, 50, 100, 200};
    s->bullet_count = bullets[(difficulty >= 0 && difficulty <= 3) ? difficulty : 1];
    s->rng_state = seed & 0xFFFFFFFF;
    s->spawn_interval = 240;
    reset_state(s);

    /* Pre-fill all bullet slots — match real game's immediate spawn */
    for (int i = 0; i < s->bullet_count; i++) {
        spawn_at(s, i);
    }
    return s;
}

EXPORT void sim_destroy(GameState* s) {
    free(s);
}

EXPORT void sim_reset(GameState* s) {
    reset_state(s);
}

EXPORT int sim_step(GameState* s, int input_bits) {
    if (s->dead) return 0;
    s->frame++;

    /* ── Entity loop (real game order: entities FIRST, then player) ── */
    for (int i = 0; i < MAX_ENTITIES; i++) {
        Bullet *b = &s->bullets[i];

        /* Spawn boundary */
        if (i >= s->bullet_count) {
            if (s->bullet_count < MAX_BULLETS && s->frame > s->next_spawn && s->pattern != 7) {
                spawn_at(s, i);
                s->bullet_count++;
                s->next_spawn = s->frame + s->spawn_interval;
            }
            if (s->frame > s->next_pattern) {
                if (s->pattern == 0) {
                    if (rng_next(&s->rng_state) < PATTERN_CHANCE) {
                        s->pattern = (rng_next(&s->rng_state) % 7) + 1;
                        s->next_pattern = s->frame + 800;
                    } else {
                        s->next_pattern = s->frame + 400;
                    }
                } else {
                    s->pattern = 0;
                    s->next_pattern = s->frame + 400;
                }
            }
            break;
        }

        /* Inactive slot → respawn one */
        if (b->angle_index == INACTIVE) {
            spawn_at(s, i);
            goto apply_input;
        }

        /* Move */
        move_bullet(b, s->px, s->py, &s->rng_state);

        /* Off-screen — use unsigned comparison to match real game (ja instruction).
           Bullets going off left/top edges produce negative signed values,
           which are large unsigned values > RAW_MAX, correctly caught. */
        if ((unsigned int)b->raw_x >= RAW_MAX_X ||
            (unsigned int)b->raw_y >= RAW_MAX_Y) {
            if (b->type & 2) s->bounce_limit--;  /* type 2 (H-Accel) or type 3 (Accel) — matches asm: test [ecx+0xa],2 */
            spawn_at(s, i);
            continue;
        }

        /* Collision + graze */
        int bpx = (b->raw_x >> RAW_SHIFT) - PIXEL_OFFSET;
        int bpy = (b->raw_y >> RAW_SHIFT) - PIXEL_OFFSET;
        int dbx = bpx - s->px;
        int dby = bpy - s->py;

        if (dbx + 4 < 23 && dby + 6 < 20) {
            if (!b->grazed) {
                b->grazed = 1;
                s->active_near++;
            }
            if (dbx >= HIT_X1 && dbx < HIT_X2 && dby >= HIT_Y1 && dby < HIT_Y2) {
                s->dead = 1;
            }
        } else if (b->grazed) {
            b->grazed = 0;
            s->active_near--;
            if (s->active_near > 0) {
                s->graze_total += s->active_near;
                if (s->frame < s->graze_chain_time) {
                    if (s->graze_chain < 10) s->graze_chain++;
                } else {
                    s->graze_chain = 1;
                }
                s->graze_chain_time = s->frame + 80;
            }
        }
    }

    /* ── Player movement (AFTER entity loop, matching real game Order) ── */
apply_input:
    { int dx = (input_bits & 8 ? 1 : 0) - (input_bits & 1 ? 1 : 0);
      int dy = (input_bits & 4 ? 1 : 0) - (input_bits & 2 ? 1 : 0);
      s->px += dx; s->py += dy;
      if (s->px < 0) s->px = 0;
      if (s->px > SCR_W) s->px = SCR_W;
      if (s->py < 0) s->py = 0;
      if (s->py > SCR_H) s->py = SCR_H; }

    return !s->dead;
}

EXPORT void sim_get_player(GameState* s, int* px, int* py) {
    *px = s->px;
    *py = s->py;
}

EXPORT int sim_get_bullet_count(GameState* s) {
    int n = 0;
    for (int i = 0; i < s->bullet_count && i < MAX_ENTITIES; i++) {
        if (s->bullets[i].angle_index != INACTIVE) n++;
    }
    return n;
}

EXPORT void sim_get_bullet(GameState* s, int idx, int* x, int* y,
                            int* type, int* angle, int* vx, int* vy) {
    if (idx < 0 || idx >= MAX_ENTITIES) {
        *x = *y = *type = *angle = *vx = *vy = 0;
        return;
    }
    Bullet *b = &s->bullets[idx];
    *x = (b->raw_x >> RAW_SHIFT) - PIXEL_OFFSET;
    *y = (b->raw_y >> RAW_SHIFT) - PIXEL_OFFSET;
    *type = b->type;
    *angle = b->angle_index;
    *vx = b->vx;
    *vy = b->vy;
}

EXPORT int sim_get_graze(GameState* s) { return s->active_near; }
EXPORT int sim_get_frame(GameState* s) { return s->frame; }
EXPORT int sim_get_bullet_size(void) { return sizeof(Bullet); }
EXPORT unsigned int sim_get_rng(GameState* s) { return s->rng_state; }

/* ── State loading (for real-game replay) ───────────────── */
EXPORT void sim_set_player(GameState* s, int px, int py) {
    s->px = px;  s->py = py;
}

EXPORT void sim_set_rng(GameState* s, unsigned int rng) {
    s->rng_state = rng;
}

EXPORT void sim_set_pattern(GameState* s, int pattern, int next_pattern) {
    s->pattern = pattern;
    s->next_pattern = next_pattern;
}

EXPORT void sim_set_next_spawn(GameState* s, int next_spawn) {
    s->next_spawn = next_spawn;
}

EXPORT void sim_set_frame(GameState* s, int frame) {
    s->frame = frame;
}

EXPORT void sim_load_bullets(GameState* s, int n,
                              int* raw_x, int* raw_y,
                              int* angle, int* type,
                              int* timer, int* counter,
                              int* vx, int* vy) {
    /* Clear all bullets first */
    for (int i = 0; i < MAX_ENTITIES; i++) {
        s->bullets[i].angle_index = INACTIVE;
    }
    s->bullet_count = n;
    if (n > MAX_BULLETS) n = MAX_BULLETS;
    for (int i = 0; i < n; i++) {
        Bullet *b = &s->bullets[i];
        b->raw_x = raw_x[i];
        b->raw_y = raw_y[i];
        b->angle_index = (unsigned char)(angle[i] & 0xFF);
        b->type = (unsigned char)(type[i] & 0xFF);
        b->timer = (unsigned char)(timer[i] & 0xFF);
        b->counter = (unsigned char)(counter[i] & 0xFF);
        b->vx = (char)(vx[i] & 0xFF);
        b->vy = (char)(vy[i] & 0xFF);
        b->grazed = 0;
    }
}

/* ═══════════════════════════════════════════════════════════
 * BEAM SEARCH — CHECK_EVERY=1, DEPTH=160 (2s), WIDTH=12
 * Linear bullet prediction using velocity tables.
 * Returns bitmask for best first move (0-12).
 * ═══════════════════════════════════════════════════════════ */
/******************************************************************************
 * Beam Search — faithful port of Python JIT _beam_search (ai_beam.py)
 * Verified against Python output on 98K+ samples (Gate 0-3 of port plan).
 *
 * Constants match algo_config.py + hardcoded Python _score_pos values:
 *   BEAM_WIDTH=50, BEAM_DEPTH=20, CHECK_EVERY=4
 *   WALL_MARGIN=40.0, SAFETY_MARGIN=2.0, CENTER_PULL=0.3
 ******************************************************************************/
#define BS_WIDTH          50
#define BS_DEPTH          20
#define BS_CHECK_EVERY     4
#define BS_MAX_B          300

#define BS_DANGER_BASE     2000.0
#define BS_COLLISION_VAL   1e8
#define BS_SAFETY_MARGIN   2.0
#define BS_CENTER_PULL     0.3
#define BS_WALL_PENALTY    5000.0
#define BS_WALL_MARGIN     40.0
#define BS_TIME_BASE       0.5
#define BS_TIME_RATE       0.03

static const int bs_moves[9][2] = {
    { 0,  0}, {-1,  0}, { 1,  0}, { 0, -1}, { 0,  1},
    {-1, -1}, {-1,  1}, { 1, -1}, { 1,  1},
};
static const int bs_bits[9] = {0, 1, 8, 2, 4, 3, 5, 10, 12};

EXPORT int sim_beam_search(GameState* s) {
    double px0 = (double)s->px;
    double py0 = (double)s->py;

    /* ── Collect active bullets + compute velocities ────── */
    int nb = 0;
    int bx[BS_MAX_B], by[BS_MAX_B];
    double bvx[BS_MAX_B], bvy[BS_MAX_B];
    for (int i = 0; i < s->bullet_count && i < MAX_ENTITIES && nb < BS_MAX_B; i++) {
        Bullet *b = &s->bullets[i];
        if (b->angle_index == INACTIVE) continue;
        bx[nb]  = (b->raw_x >> RAW_SHIFT) - PIXEL_OFFSET;
        by[nb]  = (b->raw_y >> RAW_SHIFT) - PIXEL_OFFSET;
        int idx = b->angle_index & 63;
        bvx[nb] = VEL_TABLE[idx][0] / 64.0;  /* px/frame */
        bvy[nb] = VEL_TABLE[idx][1] / 64.0;
        nb++;
    }

    /* ── Precompute bullet paths: [nb][BS_DEPTH+1][x,y] ── */
    int path_stride = BS_DEPTH + 1;
    double (*paths)[2] = (double(*)[2])malloc(nb * path_stride * 2 * sizeof(double));
    if (!paths) return 0;

    for (int i = 0; i < nb; i++) {
        for (int t = 0; t <= BS_DEPTH; t++) {
            paths[i * path_stride + t][0] = (double)bx[i] + bvx[i] * t;
            paths[i * path_stride + t][1] = (double)by[i] + bvy[i] * t;
        }
    }

    /* ── Beam arrays ────────────────────────────────────── */
    double beam_px[BS_WIDTH], beam_py[BS_WIDTH];
    int    beam_first[BS_WIDTH];
    double beam_score[BS_WIDTH];
    int    beam_count;

    beam_px[0] = px0;  beam_py[0] = py0;
    beam_first[0] = -1;
    beam_score[0] = 0.0;
    for (int i = 1; i < BS_WIDTH; i++) beam_score[i] = 1e30;
    beam_count = 1;

    /* Candidate buffers */
    double cand_px[BS_WIDTH * 9], cand_py[BS_WIDTH * 9];
    int    cand_first[BS_WIDTH * 9];
    double cand_score[BS_WIDTH * 9];

    /* ── Beam search loop ───────────────────────────────── */
    for (int d = 0; d < BS_DEPTH; d++) {
        int t = d + 1;  /* bullet path frame index */
        int ci = 0;

        for (int bi = 0; bi < beam_count; bi++) {
            for (int mi = 0; mi < 9; mi++) {
                double nx = beam_px[bi] + bs_moves[mi][0];
                double ny = beam_py[bi] + bs_moves[mi][1];
                if (nx < 0.0) nx = 0.0; if (nx > (double)SCR_W) nx = (double)SCR_W;
                if (ny < 0.0) ny = 0.0; if (ny > (double)SCR_H) ny = (double)SCR_H;

                /* Danger scoring (togglable) */
                double danger = 0.0;
                int fatal = 0;
                for (int i = 0; i < nb && !fatal; i++) {
                    double dx = paths[i * path_stride + t][0] - nx;
                    double dy = paths[i * path_stride + t][1] - ny;
#if USE_COLLISION
                    if (dx >= (double)HIT_X1 && dx < (double)HIT_X2
                            && dy >= (double)HIT_Y1 && dy < (double)HIT_Y2) {
                        danger = 1e8;  fatal = 1;  break;
                    }
#endif
#if USE_INVERSE_SQUARE
                    double d2 = dx * dx + dy * dy;
                    if (d2 < 4.0) d2 = 4.0;
                    danger += BS_DANGER_BASE / d2;
#endif
                }

#if USE_CENTER_PULL
                danger += fabs(nx - 152.0) * BS_CENTER_PULL;
                danger += fabs(ny - 112.0) * BS_CENTER_PULL;
#endif

#if USE_WALL_PENALTY
                if (nx < 10.0)      danger += (10.0 - nx) * 5000.0;
                else if (nx > 294.0) danger += (nx - 294.0) * 5000.0;
                if (ny < 10.0)      danger += (10.0 - ny) * 5000.0;
                else if (ny > 214.0) danger += (ny - 214.0) * 5000.0;
#endif

                /* Time weighting + deterministic tiebreak */
#if USE_TIME_WEIGHTING
                double w = 1.0 / (0.5 + t * 0.03);
#else
                double w = 1.0;
#endif
#if USE_TIEBREAK
                double tb = ((int)(nx * 7919) ^ (int)(ny * 6271)) & 0xFFF;
#else
                double tb = 0.0;
#endif
                double total = beam_score[bi] + danger * w + tb * 1e-6;

                cand_px[ci]    = nx;
                cand_py[ci]    = ny;
                cand_first[ci] = (beam_first[bi] >= 0) ? beam_first[bi] : mi;
                cand_score[ci] = total;
                ci++;
            }
        }

        /* Keep top BS_WIDTH */
        int top[BS_WIDTH];
        for (int k = 0; k < BS_WIDTH; k++) top[k] = -1;
        for (int i = 0; i < ci; i++) {
            for (int k = 0; k < BS_WIDTH; k++) {
                if (top[k] < 0 || cand_score[i] < cand_score[top[k]]) {
                    for (int j = BS_WIDTH - 1; j > k; j--) top[j] = top[j - 1];
                    top[k] = i;
                    break;
                }
            }
        }
        int nc = 0;
        for (int k = 0; k < BS_WIDTH && top[k] >= 0; k++) {
            beam_px[k]    = cand_px[top[k]];
            beam_py[k]    = cand_py[top[k]];
            beam_first[k] = cand_first[top[k]];
            beam_score[k] = cand_score[top[k]];
            nc++;
        }
        beam_count = nc;
    }

    free(paths);
    int best = (beam_first[0] >= 0) ? beam_first[0] : 0;
    return bs_bits[best];
}

/* ── Raw beam search from bullet arrays (no GameState needed) ── */
EXPORT int sim_beam_search_raw(int px, int py,
                                int n_bullets,
                                int* bx, int* by, int* angle_indices) {
    /* ── Precompute bullet velocities ── */
    int nb = n_bullets;
    if (nb > BS_MAX_B) nb = BS_MAX_B;

    double bvx[BS_MAX_B], bvy[BS_MAX_B];
    for (int i = 0; i < nb; i++) {
        int idx = angle_indices[i] & 63;
        bvx[i] = VEL_TABLE[idx][0] / 64.0;
        bvy[i] = VEL_TABLE[idx][1] / 64.0;
    }

    /* ── Precompute bullet paths: [nb][BS_DEPTH*BS_CHECK_EVERY+1][2] ── */
    int T = BS_DEPTH * BS_CHECK_EVERY + 1;
    /* paths[i][t] = (bx[i] + vx*t, by[i] + vy*t) — computed on the fly */

    /* ── Beam arrays ── */
    double beam_px[BS_WIDTH], beam_py[BS_WIDTH];
    int    beam_first[BS_WIDTH];
    double beam_score[BS_WIDTH];
    int    beam_count;

    beam_px[0] = (double)px;  beam_py[0] = (double)py;
    beam_first[0] = -1;  beam_score[0] = 0.0;
    for (int i = 1; i < BS_WIDTH; i++) beam_score[i] = 1e30;
    beam_count = 1;

    int step = BS_CHECK_EVERY;
    int K = BS_WIDTH;

    /* Expand buffers: K beam elements × 9 moves */
    double cand_px[BS_WIDTH * 9], cand_py[BS_WIDTH * 9];
    int    cand_first[BS_WIDTH * 9];
    double cand_score[BS_WIDTH * 9];

    /* ── Beam search loop ── */
    for (int d = 0; d < BS_DEPTH; d++) {
        int t_frame = (d + 1) * step;
        if (t_frame >= T) break;

        int ci = 0;
        for (int bi = 0; bi < beam_count; bi++) {
            for (int mi = 0; mi < 9; mi++) {
                double nx = beam_px[bi] + bs_moves[mi][0] * step;
                double ny = beam_py[bi] + bs_moves[mi][1] * step;
                if (nx < 0.0) nx = 0.0;
                if (nx > (double)SCR_W) nx = (double)SCR_W;
                if (ny < 0.0) ny = 0.0;
                if (ny > (double)SCR_H) ny = (double)SCR_H;

                /* ── Intermediate frame checking (between beam steps) ── */
                int fatal_intermediate = 0;
                if (step > 1) {
                    int prev_t = d * step;
                    for (int sub_t = prev_t + 1; sub_t < t_frame; sub_t++) {
                        if (sub_t >= T) break;
                        double frac = (double)(sub_t - prev_t) / (double)step;
                        double mid_x = beam_px[bi] + bs_moves[mi][0] * step * frac;
                        double mid_y = beam_py[bi] + bs_moves[mi][1] * step * frac;
                        if (mid_x < 0.0) mid_x = 0.0;
                        if (mid_x > (double)SCR_W) mid_x = (double)SCR_W;
                        if (mid_y < 0.0) mid_y = 0.0;
                        if (mid_y > (double)SCR_H) mid_y = (double)SCR_H;

                        /* Check collision at intermediate position */
                        for (int i = 0; i < nb && !fatal_intermediate; i++) {
                            double bx_t = (double)bx[i] + bvx[i] * sub_t;
                            double by_t = (double)by[i] + bvy[i] * sub_t;
                            double dx = bx_t - mid_x;
                            double dy = by_t - mid_y;
                            if (dx >= HIT_X1 - BS_SAFETY_MARGIN
                                && dx < HIT_X2 + BS_SAFETY_MARGIN
                                && dy >= HIT_Y1 - BS_SAFETY_MARGIN
                                && dy < HIT_Y2 + BS_SAFETY_MARGIN) {
                                fatal_intermediate = 1;
                            }
                        }
                    }
                }

                if (fatal_intermediate) continue;

                /* ── Score position at checkpoint ── */
                double danger = 0.0;
                int fatal = 0;
                for (int i = 0; i < nb && !fatal; i++) {
                    double bx_t = (double)bx[i] + bvx[i] * t_frame;
                    double by_t = (double)by[i] + bvy[i] * t_frame;
                    double dx = bx_t - nx;
                    double dy = by_t - ny;
                    /* Collision check with safety margin */
                    if (dx >= HIT_X1 - BS_SAFETY_MARGIN
                        && dx < HIT_X2 + BS_SAFETY_MARGIN
                        && dy >= HIT_Y1 - BS_SAFETY_MARGIN
                        && dy < HIT_Y2 + BS_SAFETY_MARGIN) {
                        danger = BS_COLLISION_VAL;
                        fatal = 1;
                        break;
                    }
                    /* Inverse-square danger */
                    double d2 = dx * dx + dy * dy;
                    if (d2 < 4.0) d2 = 4.0;
                    danger += BS_DANGER_BASE / d2;
                }

                if (!fatal) {
                    /* Center pull (hardcoded 0.3 in Python) */
                    danger += fabs(nx - 152.0) * BS_CENTER_PULL;
                    danger += fabs(ny - 112.0) * BS_CENTER_PULL;
                    /* Wall penalty */
                    if (nx < BS_WALL_MARGIN)
                        danger += (BS_WALL_MARGIN - nx) * BS_WALL_PENALTY;
                    else if (nx > (double)SCR_W - BS_WALL_MARGIN)
                        danger += (nx - ((double)SCR_W - BS_WALL_MARGIN)) * BS_WALL_PENALTY;
                    if (ny < BS_WALL_MARGIN)
                        danger += (BS_WALL_MARGIN - ny) * BS_WALL_PENALTY;
                    else if (ny > (double)SCR_H - BS_WALL_MARGIN)
                        danger += (ny - ((double)SCR_H - BS_WALL_MARGIN)) * BS_WALL_PENALTY;
                }

                if (fatal) danger += 1e9;

                /* Time weighting */
                double w = 1.0 / (BS_TIME_BASE + t_frame * BS_TIME_RATE);
                /* Tiebreak hash */
                double tb = ((int)(nx * 7919) ^ (int)(ny * 6271)) & 0xFFF;
                double total = beam_score[bi] + danger * w + tb * 1e-6;

                cand_px[ci]    = nx;
                cand_py[ci]    = ny;
                cand_first[ci] = (beam_first[bi] >= 0) ? beam_first[bi] : mi;
                cand_score[ci] = total;
                ci++;
            }
        }

        /* ── Keep top K candidates (insertion sort) ── */
        int top[BS_WIDTH];
        for (int k = 0; k < BS_WIDTH; k++) top[k] = -1;
        for (int i = 0; i < ci; i++) {
            for (int k = 0; k < BS_WIDTH; k++) {
                if (top[k] < 0 || cand_score[i] < cand_score[top[k]]) {
                    for (int j = BS_WIDTH - 1; j > k; j--) top[j] = top[j - 1];
                    top[k] = i;
                    break;
                }
            }
        }
        int nc = 0;
        for (int k = 0; k < BS_WIDTH && top[k] >= 0; k++) {
            int idx = top[k];
            beam_px[k]    = cand_px[idx];
            beam_py[k]    = cand_py[idx];
            beam_first[k] = cand_first[idx];
            beam_score[k] = cand_score[idx];
            nc++;
        }
        beam_count = nc;
    }

    int best = (beam_first[0] >= 0) ? beam_first[0] : 0;
    return bs_bits[best];
}
