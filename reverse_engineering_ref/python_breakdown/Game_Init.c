void Game_Init(void)

{
  undefined4 *puVar1;
  int iVar2;
  
  puVar1 = &G_EntityArray;
  iVar2 = 0;
  do {
    *(undefined1 *)(puVar1 + 2) = 0xff;
    puVar1 = (undefined4 *)((int)puVar1 + 0xf);
    iVar2 = iVar2 + 1;
  } while (iVar2 < 300);
  if (G_DifficultyMode == 0) {
    G_CurrentBulletCount = 0x1e;
    DAT_00406dac = 0;
    G_NextBulletPattern = 0;
    return;
  }
  if (G_DifficultyMode != 1) {
    if (G_DifficultyMode == 2) {
      G_CurrentBulletCount = 100;
      DAT_00406dac = 0;
      G_NextBulletPattern = 0;
      return;
    }
    if (G_DifficultyMode == 3) {
      G_CurrentBulletCount = 200;
      DAT_00406dac = 0;
      G_NextBulletPattern = 0;
      return;
    }
  }
  G_CurrentBulletCount = 0x32;
  DAT_00406dac = 0;
  G_NextBulletPattern = 0;
  return;
}


