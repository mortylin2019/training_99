# reverse_engineering_ref/asm/ANNOTATED.md
# Register-level pseudocode for 99.exe key functions
# Generated from capstone disassembly of the real binary

## FUN_00402d68 — ComputeAimedAngle(eax=bullet_ptr, edx=spread) → eax=angle_index

```
Input:
  eax = pointer to bullet entity (raw_x at [eax], raw_y at [eax+4])
  edx = spread parameter (0=perfect, 5=normal, 3=homing)

Output:
  eax = angle_index (0-63)

Pseudocode:
  dy = G_PlayerY + 6 - (bullet_raw_y >> 6)   # esi
  dx = G_PlayerX + 6 - (bullet_raw_x >> 6)   # ecx

  # Octant determination (8 octants × 45° each)
  if dx < 0:
      if dy <= 0:
          if dx < dy:       octant = 0x20  # octant 4 (up-left)
          else:             octant = 0x28  # octant 5 (left)
      else:  # dy > 0
          if dx < -dy:      octant = 0x18  # octant 3 (down-left)
          else:             octant = 0x10  # octant 2 (down)
  elif dy < 0:
      if dx < -dy:          octant = 0x30  # octant 6 (up-right)
      else:                 octant = 0x38  # octant 7 (up)
  else:  # dx >= 0, dy >= 0
      if dx == 0:           octant = 0x10  # straight down
      elif dy == 0:         octant = 0     # straight right
      elif dx < dy:         octant = 8     # octant 1 (down-right)
      else:                 octant = 0     # octant 0 (right)

  # If divisor (dy) is zero, skip search — use octant directly
  if dy == 0: goto done

  # Compute tan ratio: abs(dx * 1024 / dy)
  tan = abs((dx << 10) / dy)

  # Search ±3 entries from octant base in velocity table
  # Table: 64 entries × 12 bytes (vx:i32, vy:i32, precomputed_tan:i32)
  best_diff = 0x10000
  entry = &VEL_TABLE[octant]
  for i in range(7):
      if entry.vy == 0:
          diff = 0xFFFF  # worst score
      else:
          diff = abs(entry.precomputed_tan - tan)
      if diff >= best_diff:
          break  # diffs stopped improving
      best_diff = diff
      entry += 12 bytes  # next table entry
      angle++             # BUG: increments even for first (bad) match

  done:
  # Spread jitter
  if spread != 0:
      r = RNG() % spread
      angle = (angle + r + 1 - spread/2) & 0x3F

  return angle
```

## FUN_00402e88 — SpawnBullet(eax=entity_slot_ptr)

```
Pseudocode:
  edge = RNG() & 3   # 0=Top, 1=Bottom, 2=Left, 3=Right

  if edge == 0:    # Top
      slot.raw_x = RNG() % 0x5100
      slot.raw_y = 0
  elif edge == 1:  # Bottom
      slot.raw_x = RNG() % 0x5100
      slot.raw_y = 0x3D00
  elif edge == 2:  # Left
      slot.raw_x = 0
      slot.raw_y = RNG() % 0x3D00
  else:            # Right
      slot.raw_x = 0x5100
      slot.raw_y = RNG() % 0x3D00

  # Clear fields
  slot.timer = 0
  slot.counter = 0
  slot.grazed = 0
  slot.type = 0

  # Pattern-specific setup
  spread = 5  # default
  switch G_CurrentPattern:
      case 0: type=0, timer=0, spread=5
      case 1: type=0, timer=0, spread=0     # PERFECT aim!
      case 2: type=1, timer=0x30            # Homing 48f
      case 3: type=1, timer=0x20            # Homing 32f
      case 4: type=1, timer=0x10            # Homing 16f
      case 5: type=1, timer=((RNG()&3)+1)*16 # Homing random
      case 6: type=3                         # Accelerating
      case 7:
          if G_BounceLimit < 4:
              G_BounceLimit++
              slot.type = 2
              slot.vx = 0
              slot.vy = 0
              return  # NO aiming for Type 2
          # else: type=0, fall through to aiming

  # Compute aimed angle (call FUN_00402d68)
  slot.angle_index = ComputeAimedAngle(slot_ptr, spread)
```

## FUN_00402000 — RNG_Step() → eax=random

```
Pseudocode:
  G_RNG_State = (G_RNG_State * 0x343FD + 0x269EC3) & 0xFFFFFFFF
  return (G_RNG_State >> 16) & 0x7FFF
```

## FUN_00402fbc — EntityLoop() [main per-frame function]

```
Pseudocode:
  local_1c[16] = bullet_sprite_data  # 4×4 pixel pattern

  i = 0  # slot index
  while True:
      if i >= G_CurrentBulletCount:  # reached end of active slots
          # SPAWN CHECK
          if G_NextSpawnTime < G_CurrentTick AND
             G_CurrentBulletCount < 299 AND
             G_CurrentPattern != 7:
              SpawnBullet(slot i)
              G_CurrentBulletCount++
              G_NextSpawnTime = G_CurrentTick + 3000

          # PATTERN STATE MACHINE
          if G_NextPatternTime < G_CurrentTick:
              if G_CurrentPattern == 0:
                  if RNG() < 0x3000:  # 37.5% chance
                      G_CurrentPattern = (RNG() % 7) + 1
                      G_PatternDuration = 100
                      G_NextPatternTime = G_CurrentTick + 10000
                  else:
                      G_NextPatternTime = G_CurrentTick + 5000
              else:
                  G_CurrentPattern = 0
                  G_PatternDuration = 100
                  G_NextPatternTime = G_CurrentTick + 5000
          return  # exit entity loop for this frame

      # INACTIVE SLOT → refill (exactly ONE per frame)
      if slot.angle_index == 0xFF:
          SpawnBullet(slot i)
          return

      # ON-SCREEN check
      if slot.raw_x < 0x5101 AND slot.raw_y < 0x3D01:
          # MOVE BULLET (type-specific)
          switch slot.type:
              case 0:  # Normal
                  slot.raw_x += VEL_TABLE[angle*3+0]
                  slot.raw_y += VEL_TABLE[angle*3+1]
              case 1:  # Homing
                  slot.counter++
                  if slot.counter >= slot.timer:
                      slot.counter = RNG() & 7  # phase jitter!
                      target_angle = ComputeAimedAngle(slot_ptr, 3)
                      steer toward target ±1 or lose-lock→type0
                  slot.raw_x += VEL_TABLE[angle*3+0]
                  slot.raw_y += VEL_TABLE[angle*3+1]
              case 2:  # Homing-Accel
                  if slot.x < G_PlayerX+6: slot.vx++ (cap 96)
                  else: slot.vx--
                  if slot.y < G_PlayerY+6: slot.vy++ (cap 96)
                  else: slot.vy--
                  slot.raw_x += slot.vx
                  slot.raw_y += slot.vy
              case 3:  # Accelerating
                  slot.raw_x += ACCEL_TABLE[angle*12+0]
                  slot.raw_y += ACCEL_TABLE[angle*12+4]

          # RENDER 4×4 pixel block to DIB

          # GRAZE + COLLISION (only if G_GameOverFlag == 0)
          if not dead:
              if dx+4 < 23 AND dy+6 < 20:  # graze zone
                  if not slot.grazed:
                      slot.grazed = 1
                      G_ActiveEntityCount++
                  if 2 <= dx < 13 AND 0 <= dy < 10:  # hitbox
                      G_DeathTime = G_CurrentTick
                      G_GameOverFlag = 1
              elif slot.grazed:  # leaving graze zone
                  slot.grazed = 0
                  G_ActiveEntityCount--
                  if G_ActiveEntityCount > 0:
                      G_GrazeTotal += G_ActiveEntityCount
                      # chain logic (G_PatternCounter 1-10, 1000ms window)
      else:
          # OFF-SCREEN → respawn immediately
          if slot.type == 2: G_BounceLimit--
          SpawnBullet(slot i)

      i++  # next slot
      slot_ptr += 15 bytes
```
