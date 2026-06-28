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

/* ── Constants (from config.py) ─────────────────────────── */
#define SCR_W           304
#define SCR_H           224
#define RAW_MAX_X       0x5101
#define RAW_MAX_Y       0x3D01
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

    /* Octant determination (exact assembly branches) */
    if (dx < 0) {
        if (dy <= 0) {
            if (dy < dx)      { octant = 0x20; divisor = dy; }
            else              { octant = 0x28; divisor = 0; }
        } else {
            if (dx < -dy)     { octant = 0x18; divisor = dy; }
            else              { octant = 0x10; divisor = dy; }
        }
    } else if (dy < 0) {
        if (dx < -dy)         { octant = 0x30; divisor = dx; }
        else                  { octant = 0x38; divisor = 0; }
    } else {
        if (dx == 0)          { octant = 0x10; divisor = 0; }
        else if (dy == 0)     { octant = 0;    divisor = 0; }
        else if (dy < dx)     { octant = 0;    divisor = dy; }
        else                  { octant = 8;    divisor = dy; }
    }

    int angle;
    if (divisor == 0) {
        angle = octant & 0xFF;
    } else {
        /* quotient = abs((dx * 0x400) / divisor) */
        int quotient = (dx * 0x400) / divisor;
        if (quotient < 0) quotient = -quotient;

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

    if (edge == 0)      { b->raw_x = rng_next(&s->rng_state) % RAW_MAX_X; b->raw_y = 0; }
    else if (edge == 1) { b->raw_x = rng_next(&s->rng_state) % RAW_MAX_X; b->raw_y = RAW_MAX_Y; }
    else if (edge == 2) { b->raw_x = 0; b->raw_y = rng_next(&s->rng_state) % RAW_MAX_Y; }
    else                { b->raw_x = RAW_MAX_X; b->raw_y = rng_next(&s->rng_state) % RAW_MAX_Y; }

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

    /* Player movement */
    int dx = (input_bits & 8 ? 1 : 0) - (input_bits & 1 ? 1 : 0);
    int dy = (input_bits & 4 ? 1 : 0) - (input_bits & 2 ? 1 : 0);
    s->px += dx;
    s->py += dy;
    if (s->px < 0) s->px = 0;
    if (s->px > SCR_W) s->px = SCR_W;
    if (s->py < 0) s->py = 0;
    if (s->py > SCR_H) s->py = SCR_H;

    /* Entity loop */
    for (int i = 0; i < MAX_ENTITIES; i++) {
        Bullet *b = &s->bullets[i];

        /* Spawn boundary */
        if (i >= s->bullet_count) {
            if (s->bullet_count < MAX_BULLETS && s->frame >= s->next_spawn && s->pattern != 7) {
                spawn_at(s, i);
                s->bullet_count++;
                s->next_spawn = s->frame + s->spawn_interval;
            }
            if (s->frame >= s->next_pattern) {
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
            return !s->dead;
        }

        /* Move */
        move_bullet(b, s->px, s->py, &s->rng_state);

        /* Off-screen */
        if (b->raw_x >= RAW_MAX_X || b->raw_y >= RAW_MAX_Y) {
            if (b->type == TYPE_H_ACCEL) s->bounce_limit--;
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
