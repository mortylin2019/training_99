void Entity_Type2_Bounce(void)

{
  HANDLE hHeap;
  DWORD dwFlags;
  LPVOID lpMem;
  
  if (G_HeapMemory != (LPVOID)0x0) {
    dwFlags = 0;
    lpMem = G_HeapMemory;
    hHeap = GetProcessHeap();
    HeapFree(hHeap,dwFlags,lpMem);
    G_HeapMemory = (LPVOID)0x0;
  }
  RestoreDC(G_SpriteDC,-1);
  RestoreDC(G_BackBufferDC,-1);
  RestoreDC(DAT_004069e8,-1);
  SelectObject(G_SpriteDC,DAT_004069f0);
  DeleteObject(DAT_004069ec);
  DeleteObject(DAT_004069f4);
  DeleteDC(G_SpriteDC);
  DeleteDC(G_BackBufferDC);
  DeleteDC(DAT_004069e8);
  DeleteObject(DAT_004069f8);
  G_IsGameRunning = 0;
  PostQuitMessage(0);
  return;
}


