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
 * C INFERENCE ENGINE — runs trained PyTorch model in pure C
 * Network: 404→256→256→128→9 (ReLU hidden, linear output)
 * ═══════════════════════════════════════════════════════════ */

#define C_STATE_DIM  404
#define C_N_ACTIONS  9
#define C_H1         256
#define C_H2         256
#define C_H3         128

static float c_w1[C_STATE_DIM * C_H1];
static float c_b1[C_H1];
static float c_w2[C_H1 * C_H2];
static float c_b2[C_H2];
static float c_w3[C_H2 * C_H3];
static float c_b3[C_H3];
static float c_w4[C_H3 * C_N_ACTIONS];
static float c_b4[C_N_ACTIONS];
static int c_weights_loaded = 0;
static int c_bits_map[9] = {0, 1, 8, 2, 4, 3, 5, 10, 12};

EXPORT void sim_load_weights(const float *data, int len) {
    /* data layout: w1, b1, w2, b2, w3, b3, w4, b4 */
    int off = 0;
    int s1 = C_STATE_DIM * C_H1;     memcpy(c_w1, data + off, s1 * 4); off += s1;
    int s2 = C_H1;                   memcpy(c_b1, data + off, s2 * 4); off += s2;
    int s3 = C_H1 * C_H2;            memcpy(c_w2, data + off, s3 * 4); off += s3;
    int s4 = C_H2;                   memcpy(c_b2, data + off, s4 * 4); off += s4;
    int s5 = C_H2 * C_H3;            memcpy(c_w3, data + off, s5 * 4); off += s5;
    int s6 = C_H3;                   memcpy(c_b3, data + off, s6 * 4); off += s6;
    int s7 = C_H3 * C_N_ACTIONS;     memcpy(c_w4, data + off, s7 * 4); off += s7;
    int s8 = C_N_ACTIONS;            memcpy(c_b4, data + off, s8 * 4); off += s8;
    c_weights_loaded = 1;
}

static void c_relu(float *x, int n) {
    for (int i = 0; i < n; i++)
        if (x[i] < 0) x[i] = 0;
}

static int c_inference(const float *state) {
    /* Layer 1: h1 = relu(state @ w1 + b1) */
    float h1[C_H1];
    for (int i = 0; i < C_H1; i++) {
        float sum = c_b1[i];
        for (int j = 0; j < C_STATE_DIM; j++)
            sum += state[j] * c_w1[j * C_H1 + i];
        h1[i] = sum;
    }
    c_relu(h1, C_H1);

    /* Layer 2: h2 = relu(h1 @ w2 + b2) */
    float h2[C_H2];
    for (int i = 0; i < C_H2; i++) {
        float sum = c_b2[i];
        for (int j = 0; j < C_H1; j++)
            sum += h1[j] * c_w2[j * C_H2 + i];
        h2[i] = sum;
    }
    c_relu(h2, C_H2);

    /* Layer 3: h3 = relu(h2 @ w3 + b3) */
    float h3[C_H3];
    for (int i = 0; i < C_H3; i++) {
        float sum = c_b3[i];
        for (int j = 0; j < C_H2; j++)
            sum += h2[j] * c_w3[j * C_H3 + i];
        h3[i] = sum;
    }
    c_relu(h3, C_H3);

    /* Layer 4: q = h3 @ w4 + b4 → argmax */
    float best_q = c_b4[0];
    int best_a = 0;
    for (int i = 0; i < C_N_ACTIONS; i++) {
        float sum = c_b4[i];
        for (int j = 0; j < C_H3; j++)
            sum += h3[j] * c_w4[j * C_N_ACTIONS + i];
        if (i == 0 || sum > best_q) {
            best_q = sum;
            best_a = i;
        }
    }
    return best_a;
}

EXPORT int sim_inference(const float *state) {
    return c_inference(state);
}

/* ── C inference episode runner (zero Python callbacks) ──── */
EXPORT int sim_run_episode_c(GameState* s, int max_frames, float epsilon) {
    if (!c_weights_loaded) return -1;
    reset_state(s);

    int bits_map[9] = {0, 1, 8, 2, 4, 3, 5, 10, 12};
    int graze = 0;

    for (int f = 0; f < max_frames; f++) {
        /* Build state vector (same as Python encode_state) */
        float state[C_STATE_DIM];
        for (int k = 0; k < C_STATE_DIM; k++) state[k] = 0.0f;

        int n = 0;
        int base = 0;  /* bullet features start at 0 */
        for (int i = 0; i < s->bullet_count && i < MAX_ENTITIES && n < 100; i++) {
            Bullet *b = &s->bullets[i];
            if (b->angle_index == INACTIVE) continue;
            int bx = (b->raw_x >> RAW_SHIFT) - PIXEL_OFFSET;
            int by = (b->raw_y >> RAW_SHIFT) - PIXEL_OFFSET;
            int vx = 0, vy = 0;
            if (b->type == TYPE_H_ACCEL) { vx = b->vx; vy = b->vy; }
            else if (b->type == TYPE_ACCEL) {
                int idx = b->angle_index & 63;
                vx = ACCEL_TABLE[idx][0]; vy = ACCEL_TABLE[idx][1];
            } else {
                int idx = b->angle_index & 63;
                vx = VEL_TABLE[idx][0]; vy = VEL_TABLE[idx][1];
            }
            int off = n * 4;
            state[off]     = bx / 304.0f;
            state[off + 1] = by / 224.0f;
            state[off + 2] = vx / 8.0f;
            state[off + 3] = vy / 8.0f;
            n++;
        }

        /* Player info at end */
        int base_p = 100 * 4;
        state[base_p]     = s->px / 304.0f;
        state[base_p + 1] = s->py / 224.0f;
        state[base_p + 2] = (graze < 50 ? graze / 50.0f : 1.0f);
        state[base_p + 3] = (f < 8000 ? f / 8000.0f : 1.0f);

        /* Epsilon-greedy action */
        int action;
        if (((rng_next(&s->rng_state) & 0x7FFF) / 32767.0f) < epsilon) {
            action = rng_next(&s->rng_state) % C_N_ACTIONS;
        } else {
            action = c_inference(state);
        }

        int bits = bits_map[action];
        if (!sim_step(s, bits))
            return f;
        graze = s->active_near;
    }
    return max_frames;
}

/* ── Combined step + grid state (eliminates Python encode_state) ── */
#define GRID_W 32
#define GRID_H 24
#define GRID_CH 4

EXPORT int sim_step_with_grid(GameState* s, int input_bits, float* grid_out) {
    int alive = sim_step(s, input_bits);

    float cell_w = (float)SCR_W / GRID_W;
    float cell_h = (float)SCR_H / GRID_H;
    int total = GRID_CH * GRID_H * GRID_W;
    for (int k = 0; k < total; k++) grid_out[k] = 0.0f;

    /* Channel 0: bullet density */
    float counts[GRID_H][GRID_W];
    for (int gy = 0; gy < GRID_H; gy++)
        for (int gx = 0; gx < GRID_W; gx++)
            counts[gy][gx] = 0.0f;

    for (int i = 0; i < s->bullet_count && i < MAX_ENTITIES; i++) {
        Bullet *b = &s->bullets[i];
        if (b->angle_index == INACTIVE) continue;
        int bx = (b->raw_x >> RAW_SHIFT) - PIXEL_OFFSET;
        int by = (b->raw_y >> RAW_SHIFT) - PIXEL_OFFSET;
        int gx = (int)(bx / cell_w); if (gx < 0) gx = 0; if (gx >= GRID_W) gx = GRID_W - 1;
        int gy = (int)(by / cell_h); if (gy < 0) gy = 0; if (gy >= GRID_H) gy = GRID_H - 1;
        counts[gy][gx] += 1.0f;
    }
    for (int gy = 0; gy < GRID_H; gy++)
        for (int gx = 0; gx < GRID_W; gx++) {
            float d = counts[gy][gx] / 5.0f;
            grid_out[gy * GRID_W + gx] = (d > 1.0f) ? 1.0f : d;
        }

    /* Channel 2: player position (Gaussian blob) */
    int off2 = 2 * GRID_H * GRID_W;
    float px_cell = s->px / cell_w, py_cell = s->py / cell_h;
    for (int gy = 0; gy < GRID_H; gy++)
        for (int gx = 0; gx < GRID_W; gx++) {
            float dx = gx - px_cell, dy = gy - py_cell;
            grid_out[off2 + gy * GRID_W + gx] = exp(-(dx*dx + dy*dy) / 2.0f);
        }

    /* Channel 3: wall proximity */
    int off3 = 3 * GRID_H * GRID_W;
    float wdx = GRID_W * 0.15f, wdy = GRID_H * 0.15f;
    if (wdx < 1) wdx = 1; if (wdy < 1) wdy = 1;
    for (int gy = 0; gy < GRID_H; gy++)
        for (int gx = 0; gx < GRID_W; gx++) {
            float dx = (gx < GRID_W - 1 - gx) ? gx : (GRID_W - 1 - gx);
            float dy = (gy < GRID_H - 1 - gy) ? gy : (GRID_H - 1 - gy);
            dx /= wdx; dy /= wdy;
            float m = (dx < dy) ? dx : dy; if (m > 1.0f) m = 1.0f;
            grid_out[off3 + gy * GRID_W + gx] = 1.0f - m;
        }

    return alive;
}

/* ── Batch episode runner (eliminates per-frame ctypes overhead) ── */
EXPORT int sim_run_episode(GameState* s, int max_frames,
    int (*ai_callback)(int px, int py, int n,
                       int* bx, int* by, int* types, int* angles,
                       int* vx, int* vy, int graze, int frame))
{
    reset_state(s);
    int graze = 0;

    for (int f = 0; f < max_frames; f++) {
        /* Collect active bullet data for AI */
        int n = 0;
        int bx_buf[200], by_buf[200], types_buf[200];
        int angles_buf[200], vx_buf[200], vy_buf[200];

        for (int i = 0; i < s->bullet_count && i < MAX_ENTITIES && n < 200; i++) {
            Bullet *b = &s->bullets[i];
            if (b->angle_index == INACTIVE) continue;
            bx_buf[n] = (b->raw_x >> RAW_SHIFT) - PIXEL_OFFSET;
            by_buf[n] = (b->raw_y >> RAW_SHIFT) - PIXEL_OFFSET;
            types_buf[n] = b->type;
            angles_buf[n] = b->angle_index;
            vx_buf[n] = b->vx;
            vy_buf[n] = b->vy;
            n++;
        }

        /* Call AI (Python callback via ctypes) */
        int bits = ai_callback(s->px, s->py, n,
                               bx_buf, by_buf, types_buf, angles_buf,
                               vx_buf, vy_buf, graze, f);

        /* Step the simulation */
        if (!sim_step(s, bits))
            return f;  /* died at this frame */
        graze = s->active_near;
    }
    return max_frames;
}

/* ═══════════════════════════════════════════════════════════
 * BEAM SEARCH — CHECK_EVERY=1, DEPTH=160 (2s), WIDTH=12
 * Linear bullet prediction using velocity tables.
 * Returns bitmask for best first move (0-12).
 * ═══════════════════════════════════════════════════════════ */
#define BS_DEPTH  160   /* 2.0s at 80 FPS              */
#define BS_WIDTH  12    /* top-K paths                 */
#define BS_MAX_B  150   /* max bullets to predict      */

/* ── Scoring toggles (match algo_config.py) ──────────────── */
#define USE_INVERSE_SQUARE 1    /* 1/d² bullet danger         */
#define USE_COLLISION      1    /* hitbox instant-death       */
#define USE_CENTER_PULL    1    /* gentle pull to center      */
#define USE_WALL_PENALTY   1    /* edge penalty               */
#define USE_SAFETY_MARGIN  1    /* extra hitbox clearance     */
#define USE_TIME_WEIGHTING 1    /* future discount            */
#define USE_TIEBREAK       1    /* positional hash            */

/* Strong center pull (matching algo_config.py CENTER_PULL=5.0) */
#define BS_CENTER_PULL    0.3
/* Danger: 1/r² with 2px clamp */
#define BS_DANGER_BASE    2000.0
#define BS_DANGER_POWER   2    /* 1=1/r, 2=1/r² */

static const int bs_moves[9][2] = {
    {0,0}, {-1,0}, {1,0}, {0,-1}, {0,1},
    {-1,-1}, {-1,1}, {1,-1}, {1,1}
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
    double px0 = (double)px;
    double py0 = (double)py;

    /* Limit bullet count */
    int nb = n_bullets;
    if (nb > BS_MAX_B) nb = BS_MAX_B;

    /* Compute velocities from angle indices */
    double bvx[BS_MAX_B], bvy[BS_MAX_B];
    for (int i = 0; i < nb; i++) {
        int idx = angle_indices[i] & 63;
        bvx[i] = VEL_TABLE[idx][0] / 64.0;
        bvy[i] = VEL_TABLE[idx][1] / 64.0;
    }

    /* ── Precompute bullet paths ── */
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
    beam_first[0] = -1;  beam_score[0] = 0.0;
    for (int i = 1; i < BS_WIDTH; i++) beam_score[i] = 1e30;
    beam_count = 1;

    double cand_px[BS_WIDTH * 9], cand_py[BS_WIDTH * 9];
    int    cand_first[BS_WIDTH * 9];
    double cand_score[BS_WIDTH * 9];

    /* ── Beam search loop ───────────────────────────────── */
    for (int d = 0; d < BS_DEPTH; d++) {
        int t = d + 1;
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
        int top[BS_WIDTH];
        for (int k = 0; k < BS_WIDTH; k++) top[k] = -1;
        for (int i = 0; i < ci; i++) {
            for (int k = 0; k < BS_WIDTH; k++) {
                if (top[k] < 0 || cand_score[i] < cand_score[top[k]]) {
                    for (int j = BS_WIDTH - 1; j > k; j--) top[j] = top[j - 1];
                    top[k] = i;  break;
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
