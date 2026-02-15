void Entity_SpawnBullet(void)

{
  int *in_EAX;
  uint uVar1;
  undefined4 extraout_ECX;
  undefined4 uVar2;
  undefined4 extraout_ECX_00;
  int iVar3;
  undefined8 uVar4;
  
  uVar1 = Util_Random();
  uVar1 = uVar1 & 3;
  if (uVar1 == 0) {
    uVar1 = Util_Random();
    uVar2 = 0x5100;
    *in_EAX = (int)uVar1 % 0x5100;
    in_EAX[1] = 0;
  }
  else if (uVar1 == 1) {
    uVar1 = Util_Random();
    uVar2 = 0x5100;
    *in_EAX = (int)uVar1 % 0x5100;
    in_EAX[1] = 0x3d00;
  }
  else if (uVar1 == 2) {
    *in_EAX = 0;
    uVar1 = Util_Random();
    uVar2 = 0x3d00;
    in_EAX[1] = (int)uVar1 % 0x3d00;
  }
  else {
    uVar2 = extraout_ECX;
    if (uVar1 == 3) {
      *in_EAX = 0x5100;
      uVar1 = Util_Random();
      uVar2 = 0x3d00;
      in_EAX[1] = (int)uVar1 % 0x3d00;
    }
  }
  *(undefined1 *)((int)in_EAX + 0xb) = 0;
  *(undefined1 *)(in_EAX + 3) = 0;
  *(undefined1 *)((int)in_EAX + 9) = 0;
  *(undefined1 *)((int)in_EAX + 10) = 0;
  iVar3 = 5;
  switch(G_NextBulletPattern) {
  case 1:
    iVar3 = 0;
    break;
  case 2:
    *(undefined1 *)((int)in_EAX + 10) = 1;
    *(undefined1 *)((int)in_EAX + 0xb) = 0x30;
    break;
  case 3:
    *(undefined1 *)((int)in_EAX + 10) = 1;
    *(undefined1 *)((int)in_EAX + 0xb) = 0x20;
    break;
  case 4:
    *(undefined1 *)((int)in_EAX + 10) = 1;
    *(undefined1 *)((int)in_EAX + 0xb) = 0x10;
    break;
  case 5:
    *(undefined1 *)((int)in_EAX + 10) = 1;
    uVar1 = Util_Random();
    uVar1 = uVar1 & 0x80000003;
    if ((int)uVar1 < 0) {
      uVar1 = (uVar1 - 1 | 0xfffffffc) + 1;
    }
    *(char *)((int)in_EAX + 0xb) = ((char)uVar1 + '\x01') * '\x10';
    uVar2 = extraout_ECX_00;
    break;
  case 6:
    *(undefined1 *)((int)in_EAX + 10) = 3;
    break;
  case 7:
    if (DAT_00406dac < 4) {
      DAT_00406dac = DAT_00406dac + 1;
      *(undefined1 *)((int)in_EAX + 10) = 2;
      *(undefined1 *)((int)in_EAX + 0xd) = 0;
      *(undefined1 *)((int)in_EAX + 0xe) = 0;
      return;
    }
  }
  uVar4 = FUN_00402d68(uVar2,iVar3);
  *(char *)(in_EAX + 2) = (char)uVar4;
  return;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address
