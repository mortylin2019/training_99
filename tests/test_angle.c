/* test_angle.c — Exact C implementation of FUN_00402d68 + FUN_00402000 from 99.exe
   Compile: C:\tcc\tcc\tcc.exe test_angle.c -o test_angle.exe
   Run:     test_angle.exe <bullet_raw_x> <bullet_raw_y> <player_px> <player_py> <spread> <rng_seed>
   Output:  angle_index (0-63)
*/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

/* ── Velocity table from 0x00405d74 (64 entries × 3 i32s: vx, vy, tan_ratio) ── */
int vel_table[64][3] = {
    {   64,     0,  65536},  // 0
    {   63,     6,  10752},  // 1
    {   62,    12,   5290},  // 2
    {   61,    18,   3470},  // 3
    {   59,    24,   2517},  // 4
    {   56,    30,   1911},  // 5
    {   53,    35,   1550},  // 6
    {   49,    40,   1254},  // 7
    {   45,    45,   1024},  // 8
    {   40,    49,    835},  // 9
    {   35,    53,    676},  // 10
    {   30,    56,    548},  // 11
    {   24,    59,    416},  // 12
    {   18,    61,    302},  // 13
    {   12,    62,    198},  // 14
    {    6,    63,     97},  // 15
    {    0,    64,      0},  // 16
    {   -6,    63,     97},  // 17
    {  -12,    62,    198},  // 18
    {  -18,    61,    302},  // 19
    {  -24,    59,    416},  // 20
    {  -30,    56,    548},  // 21
    {  -35,    53,    676},  // 22
    {  -40,    49,    835},  // 23
    {  -45,    45,   1024},  // 24
    {  -49,    40,   1254},  // 25
    {  -53,    35,   1550},  // 26
    {  -56,    30,   1911},  // 27
    {  -59,    24,   2517},  // 28
    {  -61,    18,   3470},  // 29
    {  -62,    12,   5290},  // 30
    {  -63,     6,  10752},  // 31
    {  -64,     0,  65536},  // 32
    {  -63,    -6,  10752},  // 33
    {  -62,   -12,   5290},  // 34
    {  -61,   -18,   3470},  // 35
    {  -59,   -24,   2517},  // 36
    {  -56,   -30,   1911},  // 37
    {  -53,   -35,   1550},  // 38
    {  -49,   -40,   1254},  // 39
    {  -45,   -45,   1024},  // 40
    {  -40,   -49,    835},  // 41
    {  -35,   -53,    676},  // 42
    {  -30,   -56,    548},  // 43
    {  -24,   -59,    416},  // 44
    {  -18,   -61,    302},  // 45
    {  -12,   -62,    198},  // 46
    {   -6,   -63,     97},  // 47
    {    0,   -64,      0},  // 48
    {    6,   -63,     97},  // 49
    {   12,   -62,    198},  // 50
    {   18,   -61,    302},  // 51
    {   24,   -59,    416},  // 52
    {   30,   -56,    548},  // 53
    {   35,   -53,    676},  // 54
    {   40,   -49,    835},  // 55
    {   45,   -45,   1024},  // 56
    {   49,   -40,   1254},  // 57
    {   53,   -35,   1550},  // 58
    {   56,   -30,   1911},  // 59
    {   59,   -24,   2517},  // 60
    {   61,   -18,   3470},  // 61
    {   62,   -12,   5290},  // 62
    {   63,    -6,  10752},  // 63
};

/* ── FUN_00402000: LCG RNG ─────────────────────────────── */
unsigned int rng_state = 0;

unsigned int rng_next(void) {
    rng_state = rng_state * 0x343FD + 0x269EC3;
    return (rng_state >> 16) & 0x7FFF;
}

/* ── FUN_00402d68: Compute aimed angle ─────────────────── */
/* Exactly matches decompiled C at lines 1344-1441 of 99.exe.c */
int compute_aimed_angle(int bullet_raw_x, int bullet_raw_y,
                         int player_px, int player_py,
                         int spread) {
    int dx, dy;
    unsigned int octant_base;
    int iVar6, iVar7;
    int *puVar3;
    int local_10;
    unsigned int uVar4;
    int iVar2;

    /* C: dx = (player_px + 6) - (bullet_raw_x >> 6) */
    /* C: dy = (player_py + 6) - (bullet_raw_y >> 6) */
    dx = (player_px + 6) - (bullet_raw_x >> 6);
    dy = (player_py + 6) - (bullet_raw_y >> 6);

    /* Octant determination — C lines 1358-1399 */
    if (dx < 0) {
        if (dy < 1) {
            if (dx < dy) {
                octant_base = 0x20;  /* octant 4 */
                iVar7 = dy;
                goto check_zero;
            } else {
                octant_base = 0x28;  /* octant 5 */
            }
        } else if (dx < -dy) {
            octant_base = 0x18;  /* octant 3 */
            if (-dx == dy) goto done_search;
        } else {
            octant_base = 0x10;  /* octant 2 */
        }
    } else if (dy < 0) {
        if (dx < -dy) {
            octant_base = 0x30;  /* octant 6 */
            iVar7 = dx;
            goto check_zero;
        }
        octant_base = 0x38;  /* octant 7 */
    } else {
        if (dx == 0) {
            octant_base = 0x10;  /* octant 2 */
            goto done_search;
        }
        if (dy == 0) {
            octant_base = 0;
            goto done_search;
        }
        if (dx < dy) {
            octant_base = 8;  /* octant 1 */
        } else {
            octant_base = 0;  /* octant 0 */
        }
    }

check_zero:
    if (iVar7 == 0) goto done_search;

    /* C: iVar6 = (dx * 0x400) / dy */
    iVar6 = (dx * 0x400) / dy;
    if (iVar6 < 0) {
        iVar6 = -iVar6;
    }

    /* Search within ±3 entries of octant base */
    local_10 = 0x10000;
    puVar3 = &vel_table[octant_base & 0xff][0];
    iVar2 = 0;
    uVar4 = octant_base & 0xff;

    do {
        if (puVar3[1] == 0) {
            iVar7 = 0xffff;
        } else {
            iVar7 = puVar3[2];  /* tan_ratio from table */
            if (iVar7 < iVar6) {
                iVar7 = iVar6 - iVar7;
            } else {
                iVar7 = iVar7 - iVar6;
            }
        }
        if (local_10 <= iVar7) break;
        puVar3 = puVar3 + 3;  /* next entry (3 ints) */
        uVar4 = uVar4 + 1;
        iVar2 = iVar2 + 1;
        local_10 = iVar7;
    } while (iVar2 < 7);

done_search:
    /* Spread jitter */
    if (spread != 0) {
        unsigned int rv = rng_next();
        uVar4 = (unsigned int)(((int)(uVar4 & 0xFF) + (int)(rv % spread) + 1 - (spread / 2)) & 0x3F);
    }

    return (int)(uVar4 & 0x3F);
}


/* ── Main: test harness ────────────────────────────────── */
int main(int argc, char **argv) {
    if (argc == 1) {
        /* Batch mode: generate test vectors for key inputs */
        printf("# angle_test_vectors: bullet_raw_x bullet_raw_y player_px player_py spread seed -> angle\n");

        int test_cases[][6] = {
            /* {bul_x, bul_y, pl_x, pl_y, spread, seed} */
            /* Cardinal directions from player start (152,44) */
            {0,       44*64,  152, 44, 0, 0},    /* left edge → right */
            {300*64,  44*64,  152, 44, 0, 0},    /* right edge → left */
            {152*64,  0,      152, 44, 0, 0},    /* top edge → down */
            {152*64,  224*64, 152, 44, 0, 0},    /* bottom edge → up */
            /* With spread=5 (normal pattern) */
            {0,       44*64,  152, 44, 5, 0},
            {300*64,  44*64,  152, 44, 5, 0},
            {152*64,  0,      152, 44, 5, 0},
            {152*64,  224*64, 152, 44, 5, 0},
            /* With spread=3 (homing re-target) */
            {0,       44*64,  152, 44, 3, 100},
            /* Different player positions */
            {0,       0,      300, 200, 5, 42},
            {200*64,  100*64, 50,   50, 5, 99},
            /* Edge-case: bullet at same position as player */
            {152*64,  44*64,  152, 44, 5, 777},
            /* Multiple seeds for spread=5 to show jitter range */
            {0, 44*64, 152, 44, 5, 0},
            {0, 44*64, 152, 44, 5, 1},
            {0, 44*64, 152, 44, 5, 2},
            {0, 44*64, 152, 44, 5, 3},
            {0, 44*64, 152, 44, 5, 4},
            {0, 44*64, 152, 44, 5, 5},
            {0, 44*64, 152, 44, 5, 6},
            {0, 44*64, 152, 44, 5, 7},
        };
        int n = sizeof(test_cases) / sizeof(test_cases[0]);

        for (int i = 0; i < n; i++) {
            rng_state = test_cases[i][5];  /* seed */
            int angle = compute_aimed_angle(
                test_cases[i][0], test_cases[i][1],
                test_cases[i][2], test_cases[i][3],
                test_cases[i][4]);
            printf("%d %d %d %d %d %d -> %d\n",
                test_cases[i][0], test_cases[i][1],
                test_cases[i][2], test_cases[i][3],
                test_cases[i][4], test_cases[i][5],
                angle);
        }
    } else if (argc == 7) {
        /* Single test mode */
        rng_state = atoi(argv[6]);
        int angle = compute_aimed_angle(
            atoi(argv[1]), atoi(argv[2]),
            atoi(argv[3]), atoi(argv[4]),
            atoi(argv[5]));
        printf("%d\n", angle);
    } else {
        printf("Usage: %s <bul_x> <bul_y> <pl_x> <pl_y> <spread> <seed>\n", argv[0]);
        return 1;
    }
    return 0;
}
