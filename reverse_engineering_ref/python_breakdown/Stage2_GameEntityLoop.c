void Game_EntityLoop(void)

{
  char cVar1;
  uint uVar2;
  byte bVar3;
  int iVar4;
  int iVar5;
  uint uVar6;
  int iVar7;
  undefined4 extraout_ECX;
  uint uVar8;
  uint uVar9;
  char *pcVar10;
  int iVar11;
  undefined4 *puVar12;
  char *pcVar13;
  char *pcVar14;
  undefined8 uVar15;
  uint *local_2c;
  uint local_24;
  char local_1c [16];
  
  uVar2 = G_CurrentTime_Tick;
  puVar12 = &DAT_00405c04;
  pcVar10 = local_1c;
  for (iVar7 = 4; iVar7 != 0; iVar7 = iVar7 + -1) {
    *(undefined4 *)pcVar10 = *puVar12;
    puVar12 = puVar12 + 1;
    pcVar10 = pcVar10 + 4;
  }
  local_2c = &G_EntityArray;
  local_24 = 0;
  do {
    if (G_CurrentBulletCount <= local_24) {
      if (((G_NextSpawnTime < uVar2) && (G_CurrentBulletCount < 299)) && (G_NextBulletPattern != 7)) {
        Entity_SpawnBullet();
        G_CurrentBulletCount = G_CurrentBulletCount + 1;
        G_NextSpawnTime = uVar2 + 3000;
      }
      if (G_NextPatternTime < uVar2) {
        if (G_NextBulletPattern == 0) {
          uVar6 = Util_Random();
          if (uVar6 < 0x3000) {
            G_NextBulletPattern = uVar6 % 7 + 1;
            if (G_NextBulletPattern == 0) {
              G_GameOverFlag = 1;
            }
            G_PatternDuration = 100;
            G_NextPatternTime = uVar2 + 10000;
          }
          else {
            G_NextPatternTime = uVar2 + 5000;
          }
        }
        else {
          G_NextBulletPattern = 0;
          G_NextPatternTime = uVar2 + 5000;
          G_PatternDuration = 100;
        }
      }
      return;
    }
    uVar6 = (uint)(byte)local_2c[2];
    if (uVar6 == 0xff) {
      Entity_SpawnBullet();
      return;
    }
    if ((*local_2c < 0x5101) && (local_2c[1] < 0x3d01)) {
      iVar7 = (local_2c[1] >> 6) - 4;
      iVar11 = (*local_2c >> 6) - 4;
      if (G_GameOverFlag == 0) {
        iVar4 = iVar11 - G_PlayerX;
        uVar8 = iVar7 - G_PlayerY;
        if ((iVar4 + 4U < 0x17) && (uVar8 + 6 < 0x14)) {
          if (*(char *)((int)local_2c + 9) == '\0') {
            G_ActiveEntityCount = G_ActiveEntityCount + 1;
            *(undefined1 *)((int)local_2c + 9) = 1;
          }
          if ((iVar4 - 2U < 0xb) && (uVar8 < 10)) {
            G_DeathTime = uVar2;
            G_GameOverFlag = 1;
          }
        }
        else if (*(char *)((int)local_2c + 9) != '\0') {
          *(undefined1 *)((int)local_2c + 9) = 0;
          G_ActiveEntityCount = G_ActiveEntityCount + -1;
          if (G_ActiveEntityCount != 0) {
            G_TotalEntitiesSpawned = G_TotalEntitiesSpawned + G_ActiveEntityCount;
            G_SomePatternCounter = 100;
            if (uVar2 < G_PatternTimer2) {
              if (G_PatternCounter < 10) {
                G_PatternCounter = G_PatternCounter + 1;
              }
            }
            else {
              G_PatternCounter = 1;
            }
            G_PatternTimer2 = uVar2 + 1000;
          }
        }
      }
      cVar1 = *(char *)((int)local_2c + 10);
      if (cVar1 == '\x01') {
        *(char *)(local_2c + 3) = (char)local_2c[3] + '\x01';
        if (*(char *)((int)local_2c + 0xb) == (char)local_2c[3]) {
          uVar8 = Util_Random();
          *(byte *)(local_2c + 3) = (byte)uVar8 & 7;
          uVar15 = FUN_00402d68(extraout_ECX,3);
          uVar9 = (uint)(byte)uVar15;
          uVar8 = (uint)(byte)local_2c[2];
          if (uVar8 != uVar9) {
            if (uVar9 < uVar8) {
              uVar8 = uVar8 - 0x40;
            }
            if ((int)(uVar9 - uVar8) < 0x19) {
              uVar8 = uVar8 + 1;
            }
            else if ((int)(uVar9 - uVar8) < 0x28) {
              *(undefined1 *)((int)local_2c + 10) = 0;
            }
            else {
              uVar8 = uVar8 - 1;
            }
            bVar3 = (byte)uVar8 & 0x3f;
            uVar6 = (uint)bVar3;
            *(byte *)(local_2c + 2) = bVar3;
          }
        }
LAB_0040326e:
        *local_2c = *local_2c + (&DAT_00405d74)[uVar6 * 3];
        local_2c[1] = local_2c[1] + (&DAT_00405d78)[uVar6 * 3];
      }
      else if (cVar1 == '\x02') {
        if (iVar11 < G_PlayerX + 6) {
          if (*(char *)((int)local_2c + 0xd) < '`') {
            *(char *)((int)local_2c + 0xd) = *(char *)((int)local_2c + 0xd) + '\x01';
          }
        }
        else if (-0x60 < *(char *)((int)local_2c + 0xd)) {
          *(char *)((int)local_2c + 0xd) = *(char *)((int)local_2c + 0xd) + -1;
        }
        if (iVar7 < G_PlayerY + 6) {
          if (*(char *)((int)local_2c + 0xe) < '`') {
            *(char *)((int)local_2c + 0xe) = *(char *)((int)local_2c + 0xe) + '\x01';
          }
        }
        else if (-0x60 < *(char *)((int)local_2c + 0xe)) {
          *(char *)((int)local_2c + 0xe) = *(char *)((int)local_2c + 0xe) + -1;
        }
        *local_2c = *local_2c + (int)*(char *)((int)local_2c + 0xd);
        local_2c[1] = local_2c[1] + (int)*(char *)((int)local_2c + 0xe);
      }
      else {
        if (cVar1 != '\x03') goto LAB_0040326e;
        *local_2c = *local_2c + *(int *)(&DAT_00406074 + uVar6 * 0xc);
        local_2c[1] = local_2c[1] + *(int *)(&DAT_00406078 + uVar6 * 0xc);
      }
      pcVar10 = local_1c;
      pcVar13 = (char *)((int)ppvBits_004069fc + iVar7 * 0x140 + iVar11);
      iVar4 = 0;
      do {
        if ((uint)(iVar7 + iVar4) < 0xf0) {
          iVar5 = 0;
          do {
            pcVar14 = pcVar13;
            if ((*pcVar10 != '\0') && ((uint)(iVar5 + iVar11) < 0x140)) {
              *pcVar14 = *pcVar10;
            }
            pcVar10 = pcVar10 + 1;
            iVar5 = iVar5 + 1;
            pcVar13 = pcVar14 + 1;
          } while (iVar5 < 4);
          pcVar13 = pcVar14 + 0x13d;
        }
        else {
          pcVar13 = pcVar13 + 0x140;
        }
        iVar4 = iVar4 + 1;
      } while (iVar4 < 4);
    }
    else {
      if ((*(byte *)((int)local_2c + 10) & 2) != 0) {
        DAT_00406dac = DAT_00406dac + -1;
      }
      Entity_SpawnBullet();
    }
    local_2c = (uint *)((int)local_2c + 0xf);
    local_24 = local_24 + 1;
  } while( true );
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address

void __fastcall FUN_00403400(undefined4 param_1)

{
  ushort uVar1;
  bool bVar2;
  int iVar3;
  HDC hdc;
  undefined1 *puVar4;
  ushort *puVar5;
  char *pcVar6;
  int iVar7;
  void **ppvVar8;
  ushort *puVar9;
  char *pcVar10;
  char *pcVar11;
  ushort *local_3c;
  undefined1 *local_38;
  ushort *local_34;
  CHAR local_30 [32];
  
  if (DAT_00406dc4 == 0) {
    thunk_FUN_0040215a(param_1,0x12c00);
  }
  else {
    switch(DAT_004069d4) {
    case 0:
      if (DAT_004069cc == 0) {
        DAT_004069cc = 0xef;
      }
      else {
        DAT_004069cc = DAT_004069cc + -1;
      }
    case 8:
      if (DAT_004069d0 == 0) {
        DAT_004069d0 = 0xef;
      }
      else {
        DAT_004069d0 = DAT_004069d0 + -1;
      }
    case 4:
    case 0xc:
      if (DAT_004069c8 < 0xef) {
        DAT_004069c8 = DAT_004069c8 + 1;
      }
      else {
        DAT_004069c8 = 0;
      }
    default:
      DAT_004069d4 = DAT_004069d4 + 1;
      break;
    case 0xf:
      DAT_004069d4 = 0;
    }
    if (DAT_004069c8 == 0) {
      FUN_00402120(0x12c00,G_HeapMemory);
    }
    else {
      puVar4 = G_HeapMemory + DAT_004069c8 * 0x140;
      ppvVar8 = ppvBits_004069fc;
      for (iVar3 = (0xf0 - DAT_004069c8) * 0x140; 0 < iVar3; iVar3 = iVar3 + -1) {
        *(undefined1 *)ppvVar8 = *puVar4;
        puVar4 = puVar4 + 1;
        ppvVar8 = (void **)((int)ppvVar8 + 1);
      }
      puVar4 = G_HeapMemory;
      for (iVar3 = DAT_004069c8 * 0x140; 0 < iVar3; iVar3 = iVar3 + -1) {
        *(undefined1 *)ppvVar8 = *puVar4;
        puVar4 = puVar4 + 1;
        ppvVar8 = (void **)((int)ppvVar8 + 1);
      }
    }
    if (DAT_00406dc4 == 2) {
      local_34 = &DAT_00406afe;
      local_38 = &DAT_00406bc6;
      local_3c = &DAT_00406b62;
      iVar3 = 0;
      puVar9 = &DAT_00406a04;
      puVar4 = &DAT_00406acc;
      puVar5 = &DAT_00406a68;
      do {
        iVar7 = (uint)*puVar5 + DAT_004069cc;
        if (0xef < iVar7) {
          iVar7 = iVar7 + -0xf0;
        }
        *(undefined1 *)((int)ppvBits_004069fc + iVar7 * 0x140 + (uint)*puVar9) = *puVar4;
        iVar7 = (uint)*local_3c + DAT_004069d0;
        if (0xef < iVar7) {
          iVar7 = iVar7 + -0xf0;
        }
        iVar3 = iVar3 + 1;
        puVar9 = puVar9 + 1;
        puVar4 = puVar4 + 1;
        puVar5 = puVar5 + 1;
        *(undefined1 *)((int)ppvBits_004069fc + iVar7 * 0x140 + (uint)*local_34) = *local_38;
        local_34 = local_34 + 1;
        local_38 = local_38 + 1;
        local_3c = local_3c + 1;
      } while (iVar3 < 0x32);
    }
  }
  Game_EntityLoop();
  if (G_GameOverFlag == 0) {
    G_Score_Time = G_Score_Time + 1;
    iVar3 = (uint)((G_InputState & 8) != 0) - (uint)((G_InputState & 1) != 0);
    switch(G_GameState) {
    case 0:
      if (-1 < iVar3) {
        G_SubState = 4;
        G_GameState = 1;
      }
      break;
    case 1:
      if (G_SubState < 5) {
        if (iVar3 < 0) {
          G_SubState = G_SubState + 1;
        }
        else if (G_SubState == 0) {
          G_GameState = 2;
        }
        else {
          G_SubState = G_SubState - 1;
        }
      }
      else {
        G_GameState = 0;
      }
      break;
    case 2:
      G_GameState = G_GameState + iVar3;
      break;
    case 3:
      if (G_SubState < 5) {
        if (iVar3 < 1) {
          if (G_SubState == 0) {
            G_GameState = 2;
          }
          else {
            G_SubState = G_SubState - 1;
          }
        }
        else {
          G_SubState = G_SubState + 1;
        }
      }
      else {
        G_GameState = 4;
      }
      break;
    case 4:
      if (iVar3 < 1) {
        G_SubState = 4;
        G_GameState = 3;
      }
    }
    G_PlayerX = G_PlayerX + iVar3;
    G_PlayerY = G_PlayerY +
                   ((uint)((G_InputState & 4) != 0) - (uint)((G_InputState & 2) != 0));
    if (G_PlayerX < 0) {
      G_PlayerX = 0;
    }
    if (G_PlayerY < 0) {
      G_PlayerY = 0;
    }
    if (0x130 < G_PlayerX) {
      G_PlayerX = 0x130;
    }
    if (0xe0 < G_PlayerY) {
      G_PlayerY = 0xe0;
    }
    uVar1 = *(ushort *)(G_GameState * 2 + 0x405c34);
  }
  else {
    if (G_GameOverFlag == 0x11) {
      G_IsGameRunning = 0;
      FUN_00404590();
      return;
    }
    uVar1 = *(ushort *)(&DAT_00405c12 + G_GameOverFlag * 2);
    G_GameOverFlag = G_GameOverFlag + 1;
  }
  pcVar6 = &DAT_00405000 + uVar1;
  pcVar10 = (char *)((int)ppvBits_004069fc + G_PlayerY * 0x140 + G_PlayerX);
  iVar3 = 0;
  do {
    iVar7 = 0;
    do {
      pcVar11 = pcVar10;
      if (*pcVar6 != '\0') {
        *pcVar11 = *pcVar6;
      }
      pcVar6 = pcVar6 + 1;
      iVar7 = iVar7 + 1;
      pcVar10 = pcVar11 + 1;
    } while (iVar7 < 0x10);
    pcVar10 = pcVar11 + 0x131;
    iVar3 = iVar3 + 1;
  } while (iVar3 < 0x10);
  bVar2 = false;
  if (G_NextBulletPattern != 0) {
    BitBlt(G_BackBufferDC,0,0,0x140,0x10,G_SpriteDC,0,0,0xcc0020);
    bVar2 = true;
    G_PatternDuration = G_PatternDuration + -1;
    if (G_NextBulletPattern == 1) {
      BitBlt(G_BackBufferDC,0x140 - DAT_00406dd8,0,DAT_00406dd8,0x10,DAT_004069e8,DAT_00406ddc,0,
             0xee0086);
    }
    else if (G_NextBulletPattern - 2U < 4) {
      BitBlt(G_BackBufferDC,0x140 - DAT_00406dd4,0,DAT_00406dd4,0x10,DAT_004069e8,DAT_00406dd0,0,
             0xee0086);
    }
    else if (G_NextBulletPattern == 6) {
      BitBlt(G_BackBufferDC,0x140 - DAT_00406de4,0,DAT_00406de4,0x10,DAT_004069e8,DAT_00406de0,0,
             0xee0086);
    }
    else if (G_NextBulletPattern - 2U == 5) {
      BitBlt(G_BackBufferDC,0x140 - DAT_00406ddc,0,DAT_00406ddc,0x10,DAT_004069e8,0,0,0xee0086);
    }
    else {
      wsprintfA(local_30,(LPCSTR)&param_2_00405c90,G_NextBulletPattern);
      MessageBoxA(DAT_004069dc,local_30,&lpCaption_00405c50,0);
      BitBlt(G_BackBufferDC,0x140 - DAT_00406dec,0,DAT_00406dec,0x10,DAT_004069e8,DAT_00406de8,0,
             0xee0086);
    }
  }
  if (G_SomePatternCounter != 0) {
    if (!bVar2) {
      BitBlt(G_BackBufferDC,0,0,0x140,0x10,G_SpriteDC,0,0,0xcc0020);
    }
    G_SomePatternCounter = G_SomePatternCounter + -1;
    bVar2 = true;
    BitBlt(G_BackBufferDC,0,0,G_PatternCounter * DAT_00406df8 + DAT_00406df4,0x10,DAT_004069e8,
           DAT_00406df0,0,0xee0086);
  }
  hdc = GetDC(DAT_004069dc);
  if (bVar2) {
    BitBlt(hdc,0,0,0x140,0x10,G_BackBufferDC,0,0,0xcc0020);
    BitBlt(hdc,0,0x10,0x140,0xf0,G_SpriteDC,0,0x10,0xcc0020);
  }
  else {
    BitBlt(hdc,0,0,0x140,0xf0,G_SpriteDC,0,0,0xcc0020);
  }
  ReleaseDC(DAT_004069dc,hdc);
  return;
}


