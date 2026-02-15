void Entity_Type1_Homing(void)

{
  HWND in_EAX;
  HDC hdc;
  tagPAINTSTRUCT tStack_50;
  
  hdc = BeginPaint(in_EAX,&tStack_50);
  if ((G_IsGameRunning == 0) || (DAT_00406d9c != 0)) {
    BitBlt(hdc,tStack_50.rcPaint.left,tStack_50.rcPaint.top,
           tStack_50.rcPaint.right - tStack_50.rcPaint.left,
           tStack_50.rcPaint.bottom - tStack_50.rcPaint.top,G_BackBufferDC,tStack_50.rcPaint.left,
           tStack_50.rcPaint.top,0xcc0020);
  }
  else {
    BitBlt(hdc,tStack_50.rcPaint.left,tStack_50.rcPaint.top,
           tStack_50.rcPaint.right - tStack_50.rcPaint.left,
           tStack_50.rcPaint.bottom - tStack_50.rcPaint.top,G_SpriteDC,tStack_50.rcPaint.left,
           tStack_50.rcPaint.top,0xcc0020);
  }
  EndPaint(in_EAX,&tStack_50);
  return;
}



void __fastcall FUN_00402abc(undefined4 param_1,ushort param_2)

{
  uint uVar1;
  undefined **ppuVar2;
  int iVar3;
  int iVar4;
  int local_18;
  undefined **local_14;
  
  if (G_PauseFlag == 0) {
    uVar1 = (uint)param_2;
    if ((int)(char)(&PTR_DAT_004063b0)[DAT_004069c0][DAT_004069c4] == uVar1) {
      DAT_004069c4 = DAT_004069c4 + 1;
LAB_00402b09:
      if ((&PTR_DAT_004063b0)[DAT_004069c0][DAT_004069c4] == '\0') {
        switch(DAT_004069c0) {
        case 0:
          DAT_00406dc8 = 0;
          DAT_00406dc4 = 2;
          G_DifficultyMode = 1;
          G_HighPriorityMode = 1;
          break;
        case 1:
          DAT_00406dc8 = 1;
          break;
        case 2:
          DAT_00406dc4 = 0;
          break;
        case 3:
          DAT_00406dc4 = 1;
          break;
        case 4:
          DAT_00406dc4 = 2;
          break;
        case 5:
          G_DifficultyMode = 0;
          break;
        case 6:
          G_DifficultyMode = 2;
          break;
        case 7:
          G_DifficultyMode = 3;
          break;
        case 8:
          DAT_00406dc8 = 2;
          DAT_00406dc4 = 2;
          G_DifficultyMode = 2;
          break;
        case 9:
          DAT_00406dc8 = 2;
          DAT_00406dc4 = 2;
          G_DifficultyMode = 1;
          break;
        case 10:
          G_HighPriorityMode = 1;
          break;
        case 0xb:
          G_HighPriorityMode = 0;
          break;
        case 0xc:
          DAT_00406dc8 = 2;
          DAT_00406dc4 = 2;
          G_DifficultyMode = 3;
        }
        DrawStartScreen();
      }
    }
    else {
      if (DAT_004069c4 != 0) {
        local_18 = 0;
        local_14 = &PTR_DAT_004063b0;
        do {
          for (iVar4 = 0; iVar4 < DAT_004069c4; iVar4 = iVar4 + 1) {
            for (iVar3 = 0; iVar3 < DAT_004069c4 - iVar4; iVar3 = iVar3 + 1) {
              if ((&PTR_DAT_004063b0)[DAT_004069c0][iVar4 + iVar3] != (*local_14)[iVar3])
              goto LAB_00402cf1;
            }
            if ((int)(char)(*local_14)[iVar3] == uVar1) {
              DAT_004069c0 = local_18;
              DAT_004069c4 = iVar3 + 1;
              goto LAB_00402b09;
            }
LAB_00402cf1:
          }
          local_18 = local_18 + 1;
          local_14 = local_14 + 1;
        } while (local_18 < 0xd);
      }
      ppuVar2 = &PTR_DAT_004063b0;
      local_18 = 0;
      do {
        if ((int)(char)**ppuVar2 == uVar1) {
          DAT_004069c0 = local_18;
          DAT_004069c4 = 1;
          goto LAB_00402b09;
        }
        local_18 = local_18 + 1;
        ppuVar2 = ppuVar2 + 1;
      } while (local_18 < 0xd);
      DAT_004069c4 = 0;
    }
  }
  return;
}



void __fastcall FUN_00402d5c(undefined4 param_1,int param_2)

{
  if (param_2 == 1) {
    FUN_00404590();
  }
  return;
}



undefined8 __fastcall FUN_00402d68(undefined4 param_1,int param_2)

{
  uint *in_EAX;
  uint uVar1;
  int iVar2;
  undefined4 *puVar3;
  undefined4 unaff_EBX;
  undefined3 uVar5;
  uint uVar4;
  int iVar6;
  int iVar7;
  int local_10;
  
  iVar6 = (G_PlayerY + 6) - (in_EAX[1] >> 6);
  iVar2 = (G_PlayerX + 6) - (*in_EAX >> 6);
  uVar5 = (undefined3)((uint)unaff_EBX >> 8);
  if (iVar2 < 0) {
    if (iVar6 < 1) {
      if (iVar2 < iVar6) {
        uVar4 = CONCAT31(uVar5,0x20);
        iVar7 = iVar6;
joined_r0x00402dd6:
        if (iVar7 == 0) goto LAB_00402e5f;
      }
      else {
        uVar4 = CONCAT31(uVar5,0x28);
      }
    }
    else if (iVar2 < -iVar6) {
      uVar4 = CONCAT31(uVar5,0x18);
      if (-iVar2 == iVar6) goto LAB_00402e5f;
    }
    else {
      uVar4 = CONCAT31(uVar5,0x10);
    }
  }
  else if (iVar6 < 0) {
    if (iVar2 < -iVar6) {
      uVar4 = CONCAT31(uVar5,0x30);
      iVar7 = iVar2;
      goto joined_r0x00402dd6;
    }
    uVar4 = CONCAT31(uVar5,0x38);
  }
  else {
    if (iVar2 == 0) {
      uVar4 = CONCAT31(uVar5,0x10);
      goto LAB_00402e5f;
    }
    if (iVar6 == 0) {
      uVar4 = 0;
      goto LAB_00402e5f;
    }
    if (iVar2 < iVar6) {
      uVar4 = CONCAT31(uVar5,8);
    }
    else {
      uVar4 = 0;
    }
  }
  iVar6 = (iVar2 * 0x400) / iVar6;
  if (iVar6 < 0) {
    iVar6 = -iVar6;
  }
  local_10 = 0x10000;
  puVar3 = &DAT_00405d74 + (uVar4 & 0xff) * 3;
  iVar2 = 0;
  do {
    if (puVar3[1] == 0) {
      iVar7 = 0xffff;
    }
    else {
      iVar7 = puVar3[2];
      if (iVar7 < iVar6) {
        iVar7 = iVar6 - iVar7;
      }
      else {
        iVar7 = iVar7 - iVar6;
      }
    }
    if (local_10 <= iVar7) break;
    puVar3 = puVar3 + 3;
    uVar4 = uVar4 + 1;
    iVar2 = iVar2 + 1;
    local_10 = iVar7;
  } while (iVar2 < 7);
LAB_00402e5f:
  if (param_2 != 0) {
    uVar1 = Util_Random();
    uVar4 = CONCAT31((int3)(uVar4 >> 8),
                     ((char)uVar4 + (char)((int)uVar1 % param_2) + '\x01') - (char)(param_2 >> 1)) &
            0xffffff3f;
  }
  return CONCAT44(local_10,uVar4);
}


