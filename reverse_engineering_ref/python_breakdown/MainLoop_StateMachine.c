void MainLoop_StateMachine(void)

{
  HANDLE pvVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  BOOL BVar5;
  undefined4 extraout_ECX;
  undefined2 *puVar6;
  undefined2 *puVar7;
  undefined2 *puVar8;
  char *pcVar9;
  DWORD DVar10;
  SIZE_T dwBytes;
  int nPriority;
  int local_40;
  undefined2 *local_34;
  char *local_30;
  MSG local_2c;
  
  ShowCursor(0);
  Game_Init();
  if (DAT_00406dc8 == 0) {
    G_ScoreMultiplier = 0x10;
  }
  else if (DAT_00406dc8 == 1) {
    G_ScoreMultiplier = 0xc;
  }
  else if (DAT_00406dc8 == 2) {
    G_ScoreMultiplier = 0;
  }
  if (DAT_00406dc4 == 0) {
    G_HeapMemory = (LPVOID)0x0;
  }
  else {
    dwBytes = 0x12c00;
    DVar10 = 0;
    pvVar1 = GetProcessHeap();
    G_HeapMemory = HeapAlloc(pvVar1,DVar10,dwBytes);
    thunk_FUN_0040215a(extraout_ECX,0x12c00);
    puVar7 = &DAT_00406afe;
    local_40 = 0;
    pcVar9 = &DAT_00406acc;
    local_30 = &DAT_00406bc6;
    local_34 = &DAT_00406b62;
    puVar8 = &DAT_00406a68;
    puVar6 = &DAT_00406a04;
    do {
      uVar2 = Util_Random();
      uVar3 = Util_Random();
      uVar4 = Util_Random();
      *(char *)((int)G_HeapMemory + (int)uVar2 % 0x140 + ((int)uVar3 % 0xf0) * 0x140) =
           (char)((int)uVar4 % 0xe) + '\x01';
      uVar2 = Util_Random();
      *puVar6 = (short)((int)uVar2 % 0x140);
      uVar2 = Util_Random();
      *puVar8 = (short)((int)uVar2 % 0xf0);
      uVar2 = Util_Random();
      *pcVar9 = (char)((int)uVar2 % 0xe) + '\x01';
      uVar2 = Util_Random();
      *puVar7 = (short)((int)uVar2 % 0x140);
      uVar2 = Util_Random();
      *local_34 = (short)((int)uVar2 % 0xf0);
      uVar2 = Util_Random();
      puVar7 = puVar7 + 1;
      pcVar9 = pcVar9 + 1;
      puVar8 = puVar8 + 1;
      *local_30 = (char)((int)uVar2 % 0xe) + '\x01';
      puVar6 = puVar6 + 1;
      local_40 = local_40 + 1;
      local_30 = local_30 + 1;
      local_34 = local_34 + 1;
    } while (local_40 < 0x32);
  }
  G_ActiveEntityCount = 0;
  G_TotalEntitiesSpawned = 0;
  G_PatternCounter = 0;
  G_SomePatternCounter = 0;
  G_PatternTimer2 = 0;
  G_Score_Time = 0;
  G_PatternDuration = 0;
  G_GameState = 2;
  G_SubState = 0;
  G_GameOverFlag = 0;
  G_PlayerX = 0x98;
  G_PlayerY = 0x2c;
  Sleep(1);
  while (BVar5 = PeekMessageA(&local_2c,(HWND)0x0,0,0,1), BVar5 != 0) {
    TranslateMessage(&local_2c);
    DispatchMessageA(&local_2c);
  }
  G_GameStartTime = timeGetTime();
  G_DeathTime = 0;
  G_CurrentTime_Tick = 0;
  G_NextSpawnTime = G_GameStartTime + 3000;
  G_NextPatternTime = G_GameStartTime + 5000;
  G_IsGameRunning = 1;
  G_PauseFlag = 1;
  DAT_00406d9c = 0;
  DAT_00406da0 = G_GameStartTime;
  if (G_HighPriorityMode != 0) {
    DVar10 = 0x80;
    pvVar1 = GetCurrentProcess();
    SetPriorityClass(pvVar1,DVar10);
  }
  nPriority = 2;
  pvVar1 = GetCurrentThread();
  SetThreadPriority(pvVar1,nPriority);
  return;
}



void FUN_00404590(void)

{
  HWND in_EAX;
  HANDLE pvVar1;
  BOOL BVar2;
  DWORD DVar3;
  int nPriority;
  LPVOID lpMem;
  tagMSG local_20;
  
  ShowCursor(1);
  if (G_HighPriorityMode != 0) {
    DVar3 = 0x20;
    pvVar1 = GetCurrentProcess();
    SetPriorityClass(pvVar1,DVar3);
  }
  nPriority = 0;
  pvVar1 = GetCurrentThread();
  SetThreadPriority(pvVar1,nPriority);
  if (G_HeapMemory != (LPVOID)0x0) {
    DVar3 = 0;
    lpMem = G_HeapMemory;
    pvVar1 = GetProcessHeap();
    HeapFree(pvVar1,DVar3,lpMem);
    G_HeapMemory = (LPVOID)0x0;
  }
  G_CurrentTime_Tick = 0;
  do {
    BVar2 = PeekMessageA(&local_20,in_EAX,0x100,0x108,1);
  } while (BVar2 != 0);
  if (G_GameOverFlag == 0) {
    DrawStartScreen();
  }
  else {
    BitBlt(G_BackBufferDC,0,0,0x140,0xf0,G_SpriteDC,0,0,0xcc0020);
    DrawGameOver(G_GameStartTime,G_DeathTime - G_GameStartTime);
  }
  return;
}


