typedef unsigned char   undefined;

typedef unsigned char    byte;
typedef unsigned int    dword;
typedef pointer32 ImageBaseOffset32;

typedef unsigned char    uchar;
typedef unsigned int    uint;
typedef unsigned long    ulong;
typedef unsigned char    undefined1;
typedef unsigned short    undefined2;
typedef unsigned int    undefined4;
typedef unsigned long long    undefined8;
typedef unsigned short    ushort;
typedef unsigned short    word;
typedef unsigned short    wchar16;
typedef union IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryUnion IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryUnion, *PIMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryUnion;

typedef struct IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct, *PIMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct;

struct IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct {
    dword OffsetToDirectory:31;
    dword DataIsDirectory:1;
};

union IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryUnion {
    dword OffsetToData;
    struct IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryStruct;
};

typedef struct tagMSG tagMSG, *PtagMSG;

typedef struct tagMSG MSG;

typedef struct HWND__ HWND__, *PHWND__;

typedef struct HWND__ *HWND;

typedef uint UINT;

typedef uint UINT_PTR;

typedef UINT_PTR WPARAM;

typedef long LONG_PTR;

typedef LONG_PTR LPARAM;

typedef ulong DWORD;

typedef struct tagPOINT tagPOINT, *PtagPOINT;

typedef struct tagPOINT POINT;

typedef long LONG;

struct tagPOINT {
    LONG x;
    LONG y;
};

struct tagMSG {
    HWND hwnd;
    UINT message;
    WPARAM wParam;
    LPARAM lParam;
    DWORD time;
    POINT pt;
};

struct HWND__ {
    int unused;
};

typedef struct tagPAINTSTRUCT tagPAINTSTRUCT, *PtagPAINTSTRUCT;

typedef struct tagPAINTSTRUCT PAINTSTRUCT;

typedef struct HDC__ HDC__, *PHDC__;

typedef struct HDC__ *HDC;

typedef int BOOL;

typedef struct tagRECT tagRECT, *PtagRECT;

typedef struct tagRECT RECT;

typedef uchar BYTE;

struct HDC__ {
    int unused;
};

struct tagRECT {
    LONG left;
    LONG top;
    LONG right;
    LONG bottom;
};

struct tagPAINTSTRUCT {
    HDC hdc;
    BOOL fErase;
    RECT rcPaint;
    BOOL fRestore;
    BOOL fIncUpdate;
    BYTE rgbReserved[32];
};

typedef struct tagWNDCLASSA tagWNDCLASSA, *PtagWNDCLASSA;

typedef LONG_PTR LRESULT;

typedef LRESULT (*WNDPROC)(HWND, UINT, WPARAM, LPARAM);

typedef struct HINSTANCE__ HINSTANCE__, *PHINSTANCE__;

typedef struct HINSTANCE__ *HINSTANCE;

typedef struct HICON__ HICON__, *PHICON__;

typedef struct HICON__ *HICON;

typedef HICON HCURSOR;

typedef struct HBRUSH__ HBRUSH__, *PHBRUSH__;

typedef struct HBRUSH__ *HBRUSH;

typedef char CHAR;

typedef CHAR *LPCSTR;

struct HBRUSH__ {
    int unused;
};

struct tagWNDCLASSA {
    UINT style;
    WNDPROC lpfnWndProc;
    int cbClsExtra;
    int cbWndExtra;
    HINSTANCE hInstance;
    HICON hIcon;
    HCURSOR hCursor;
    HBRUSH hbrBackground;
    LPCSTR lpszMenuName;
    LPCSTR lpszClassName;
};

struct HICON__ {
    int unused;
};

struct HINSTANCE__ {
    int unused;
};

typedef struct tagMSG *LPMSG;

typedef struct tagWNDCLASSA WNDCLASSA;

typedef struct tagPAINTSTRUCT *LPPAINTSTRUCT;

typedef struct tagRGBQUAD tagRGBQUAD, *PtagRGBQUAD;

typedef struct tagRGBQUAD RGBQUAD;

struct tagRGBQUAD {
    BYTE rgbBlue;
    BYTE rgbGreen;
    BYTE rgbRed;
    BYTE rgbReserved;
};

typedef struct tagLOGFONTA tagLOGFONTA, *PtagLOGFONTA;

struct tagLOGFONTA {
    LONG lfHeight;
    LONG lfWidth;
    LONG lfEscapement;
    LONG lfOrientation;
    LONG lfWeight;
    BYTE lfItalic;
    BYTE lfUnderline;
    BYTE lfStrikeOut;
    BYTE lfCharSet;
    BYTE lfOutPrecision;
    BYTE lfClipPrecision;
    BYTE lfQuality;
    BYTE lfPitchAndFamily;
    CHAR lfFaceName[32];
};

typedef struct tagLOGFONTA LOGFONTA;

typedef struct tagBITMAPINFO tagBITMAPINFO, *PtagBITMAPINFO;

typedef struct tagBITMAPINFO BITMAPINFO;

typedef struct tagBITMAPINFOHEADER tagBITMAPINFOHEADER, *PtagBITMAPINFOHEADER;

typedef struct tagBITMAPINFOHEADER BITMAPINFOHEADER;

typedef ushort WORD;

struct tagBITMAPINFOHEADER {
    DWORD biSize;
    LONG biWidth;
    LONG biHeight;
    WORD biPlanes;
    WORD biBitCount;
    DWORD biCompression;
    DWORD biSizeImage;
    LONG biXPelsPerMeter;
    LONG biYPelsPerMeter;
    DWORD biClrUsed;
    DWORD biClrImportant;
};

struct tagBITMAPINFO {
    BITMAPINFOHEADER bmiHeader;
    RGBQUAD bmiColors[1];
};

typedef struct HFONT__ HFONT__, *PHFONT__;

typedef struct HFONT__ *HFONT;

struct HFONT__ {
    int unused;
};

typedef struct HBITMAP__ HBITMAP__, *PHBITMAP__;

struct HBITMAP__ {
    int unused;
};

typedef struct tagSIZE tagSIZE, *PtagSIZE;

struct tagSIZE {
    LONG cx;
    LONG cy;
};

typedef void *LPVOID;

typedef HINSTANCE HMODULE;

typedef struct tagSIZE *LPSIZE;

typedef struct HMENU__ HMENU__, *PHMENU__;

typedef struct HMENU__ *HMENU;

struct HMENU__ {
    int unused;
};

typedef WORD ATOM;

typedef struct tagRECT *LPRECT;

typedef void *HGDIOBJ;

typedef struct HBITMAP__ *HBITMAP;

typedef DWORD COLORREF;

typedef struct IMAGE_OPTIONAL_HEADER32 IMAGE_OPTIONAL_HEADER32, *PIMAGE_OPTIONAL_HEADER32;

typedef struct IMAGE_DATA_DIRECTORY IMAGE_DATA_DIRECTORY, *PIMAGE_DATA_DIRECTORY;

struct IMAGE_DATA_DIRECTORY {
    ImageBaseOffset32 VirtualAddress;
    dword Size;
};

struct IMAGE_OPTIONAL_HEADER32 {
    word Magic;
    byte MajorLinkerVersion;
    byte MinorLinkerVersion;
    dword SizeOfCode;
    dword SizeOfInitializedData;
    dword SizeOfUninitializedData;
    ImageBaseOffset32 AddressOfEntryPoint;
    ImageBaseOffset32 BaseOfCode;
    ImageBaseOffset32 BaseOfData;
    pointer32 ImageBase;
    dword SectionAlignment;
    dword FileAlignment;
    word MajorOperatingSystemVersion;
    word MinorOperatingSystemVersion;
    word MajorImageVersion;
    word MinorImageVersion;
    word MajorSubsystemVersion;
    word MinorSubsystemVersion;
    dword Win32VersionValue;
    dword SizeOfImage;
    dword SizeOfHeaders;
    dword CheckSum;
    word Subsystem;
    word DllCharacteristics;
    dword SizeOfStackReserve;
    dword SizeOfStackCommit;
    dword SizeOfHeapReserve;
    dword SizeOfHeapCommit;
    dword LoaderFlags;
    dword NumberOfRvaAndSizes;
    struct IMAGE_DATA_DIRECTORY DataDirectory[16];
};

typedef struct Var Var, *PVar;

struct Var {
    word wLength;
    word wValueLength;
    word wType;
};

typedef struct IMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct IMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct, *PIMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct;

struct IMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct {
    dword NameOffset:31;
    dword NameIsString:1;
};

typedef struct IMAGE_FILE_HEADER IMAGE_FILE_HEADER, *PIMAGE_FILE_HEADER;

struct IMAGE_FILE_HEADER {
    word Machine; // 332
    word NumberOfSections;
    dword TimeDateStamp;
    dword PointerToSymbolTable;
    dword NumberOfSymbols;
    word SizeOfOptionalHeader;
    word Characteristics;
};

typedef struct IMAGE_NT_HEADERS32 IMAGE_NT_HEADERS32, *PIMAGE_NT_HEADERS32;

struct IMAGE_NT_HEADERS32 {
    char Signature[4];
    struct IMAGE_FILE_HEADER FileHeader;
    struct IMAGE_OPTIONAL_HEADER32 OptionalHeader;
};

typedef struct StringFileInfo StringFileInfo, *PStringFileInfo;

struct StringFileInfo {
    word wLength;
    word wValueLength;
    word wType;
};

typedef struct IMAGE_RESOURCE_DIRECTORY_ENTRY IMAGE_RESOURCE_DIRECTORY_ENTRY, *PIMAGE_RESOURCE_DIRECTORY_ENTRY;

typedef union IMAGE_RESOURCE_DIRECTORY_ENTRY_NameUnion IMAGE_RESOURCE_DIRECTORY_ENTRY_NameUnion, *PIMAGE_RESOURCE_DIRECTORY_ENTRY_NameUnion;

union IMAGE_RESOURCE_DIRECTORY_ENTRY_NameUnion {
    struct IMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct IMAGE_RESOURCE_DIRECTORY_ENTRY_NameStruct;
    dword Name;
    word Id;
};

struct IMAGE_RESOURCE_DIRECTORY_ENTRY {
    union IMAGE_RESOURCE_DIRECTORY_ENTRY_NameUnion NameUnion;
    union IMAGE_RESOURCE_DIRECTORY_ENTRY_DirectoryUnion DirectoryUnion;
};

typedef struct StringTable StringTable, *PStringTable;

struct StringTable {
    word wLength;
    word wValueLength;
    word wType;
};

typedef struct IMAGE_SECTION_HEADER IMAGE_SECTION_HEADER, *PIMAGE_SECTION_HEADER;

typedef union Misc Misc, *PMisc;

typedef enum SectionFlags {
    IMAGE_SCN_TYPE_NO_PAD=8,
    IMAGE_SCN_RESERVED_0001=16,
    IMAGE_SCN_CNT_CODE=32,
    IMAGE_SCN_CNT_INITIALIZED_DATA=64,
    IMAGE_SCN_CNT_UNINITIALIZED_DATA=128,
    IMAGE_SCN_LNK_OTHER=256,
    IMAGE_SCN_LNK_INFO=512,
    IMAGE_SCN_RESERVED_0040=1024,
    IMAGE_SCN_LNK_REMOVE=2048,
    IMAGE_SCN_LNK_COMDAT=4096,
    IMAGE_SCN_GPREL=32768,
    IMAGE_SCN_MEM_16BIT=131072,
    IMAGE_SCN_MEM_PURGEABLE=131072,
    IMAGE_SCN_MEM_LOCKED=262144,
    IMAGE_SCN_MEM_PRELOAD=524288,
    IMAGE_SCN_ALIGN_1BYTES=1048576,
    IMAGE_SCN_ALIGN_2BYTES=2097152,
    IMAGE_SCN_ALIGN_4BYTES=3145728,
    IMAGE_SCN_ALIGN_8BYTES=4194304,
    IMAGE_SCN_ALIGN_16BYTES=5242880,
    IMAGE_SCN_ALIGN_32BYTES=6291456,
    IMAGE_SCN_ALIGN_64BYTES=7340032,
    IMAGE_SCN_ALIGN_128BYTES=8388608,
    IMAGE_SCN_ALIGN_256BYTES=9437184,
    IMAGE_SCN_ALIGN_512BYTES=10485760,
    IMAGE_SCN_ALIGN_1024BYTES=11534336,
    IMAGE_SCN_ALIGN_2048BYTES=12582912,
    IMAGE_SCN_ALIGN_4096BYTES=13631488,
    IMAGE_SCN_ALIGN_8192BYTES=14680064,
    IMAGE_SCN_LNK_NRELOC_OVFL=16777216,
    IMAGE_SCN_MEM_DISCARDABLE=33554432,
    IMAGE_SCN_MEM_NOT_CACHED=67108864,
    IMAGE_SCN_MEM_NOT_PAGED=134217728,
    IMAGE_SCN_MEM_SHARED=268435456,
    IMAGE_SCN_MEM_EXECUTE=536870912,
    IMAGE_SCN_MEM_READ=1073741824,
    IMAGE_SCN_MEM_WRITE=2147483648
} SectionFlags;

union Misc {
    dword PhysicalAddress;
    dword VirtualSize;
};

struct IMAGE_SECTION_HEADER {
    char Name[8];
    union Misc Misc;
    ImageBaseOffset32 VirtualAddress;
    dword SizeOfRawData;
    dword PointerToRawData;
    dword PointerToRelocations;
    dword PointerToLinenumbers;
    word NumberOfRelocations;
    word NumberOfLinenumbers;
    enum SectionFlags Characteristics;
};

typedef struct VS_VERSION_INFO VS_VERSION_INFO, *PVS_VERSION_INFO;

struct VS_VERSION_INFO {
    word StructLength;
    word ValueLength;
    word StructType;
    wchar16 Info[16];
    byte Padding[2];
    dword Signature;
    word StructVersion[2];
    word FileVersion[4];
    word ProductVersion[4];
    dword FileFlagsMask[2];
    dword FileFlags;
    dword FileOS;
    dword FileType;
    dword FileSubtype;
    dword FileTimestamp;
};

typedef struct IMAGE_RESOURCE_DATA_ENTRY IMAGE_RESOURCE_DATA_ENTRY, *PIMAGE_RESOURCE_DATA_ENTRY;

struct IMAGE_RESOURCE_DATA_ENTRY {
    dword OffsetToData;
    dword Size;
    dword CodePage;
    dword Reserved;
};

typedef struct VarFileInfo VarFileInfo, *PVarFileInfo;

struct VarFileInfo {
    word wLength;
    word wValueLength;
    word wType;
};

typedef struct IMAGE_RESOURCE_DIRECTORY IMAGE_RESOURCE_DIRECTORY, *PIMAGE_RESOURCE_DIRECTORY;

struct IMAGE_RESOURCE_DIRECTORY {
    dword Characteristics;
    dword TimeDateStamp;
    word MajorVersion;
    word MinorVersion;
    word NumberOfNamedEntries;
    word NumberOfIdEntries;
};

typedef struct StringInfo StringInfo, *PStringInfo;

struct StringInfo {
    word wLength;
    word wValueLength;
    word wType;
};

typedef CHAR *LPSTR;

typedef void *HANDLE;

typedef struct IMAGE_DOS_HEADER IMAGE_DOS_HEADER, *PIMAGE_DOS_HEADER;

struct IMAGE_DOS_HEADER {
    char e_magic[2]; // Magic number
    word e_cblp; // Bytes of last page
    word e_cp; // Pages in file
    word e_crlc; // Relocations
    word e_cparhdr; // Size of header in paragraphs
    word e_minalloc; // Minimum extra paragraphs needed
    word e_maxalloc; // Maximum extra paragraphs needed
    word e_ss; // Initial (relative) SS value
    word e_sp; // Initial SP value
    word e_csum; // Checksum
    word e_ip; // Initial IP value
    word e_cs; // Initial (relative) CS value
    word e_lfarlc; // File address of relocation table
    word e_ovno; // Overlay number
    word e_res[4][4]; // Reserved words
    word e_oemid; // OEM identifier (for e_oeminfo)
    word e_oeminfo; // OEM information; e_oemid specific
    word e_res2[10][10]; // Reserved words
    dword e_lfanew; // File address of new exe header
    byte e_program[48]; // Actual DOS program
};

typedef ulong ULONG_PTR;

typedef ULONG_PTR SIZE_T;



int DAT_00405c00;
HMODULE DAT_004069d8;
HWND DAT_004069dc;
DWORD DAT_00406da4;
int DAT_00406d90;
int DAT_00406d9c;
int DAT_00406d8c;
LPCSTR lpText_00405c3e;
LPCSTR lpWindowName_00405c51;
uint DAT_00406da0;
HINSTANCE DAT_004069d8;
string s_wcTKKN_00405c56;
DWORD DAT_00405c00;
undefined DAT_00406bf8;
undefined4 DAT_00406dcc;
undefined4 DAT_00406dc0;
undefined4 DAT_00406dc4;
undefined4 DAT_00406d84;
undefined DAT_00000065;
undefined DAT_00007f00;
undefined4 DAT_00405d78;
undefined1 DAT_004063e4;
undefined4 DAT_00406bfc;
undefined FUN_00402318;
int DAT_00406d84;
uint DAT_00406d7c;
HBITMAP DAT_004069ec;
HBITMAP DAT_004069f4;
HDC DAT_004069e0;
HDC DAT_004069e4;
HDC DAT_004069e8;
HGDIOBJ DAT_004069f0;
int DAT_00406ddc;
int DAT_00406dd0;
int DAT_00406dd4;
int DAT_00406dd8;
int DAT_00406de0;
int DAT_00406de4;
int DAT_00406de8;
int DAT_00406dec;
int DAT_00406df0;
int DAT_00406df4;
int DAT_00406df8;
HBITMAP DAT_004069f8;
undefined4 DAT_00406d90;
undefined DAT_00405c5d;
undefined DAT_00405c61;
undefined DAT_00405c6b;
undefined DAT_00405c77;
undefined DAT_00405c7d;
LOGFONTA *lplf_00406374;
undefined DAT_00405c81;
void * *ppvBits_004069fc;
LPVOID DAT_00406a00;
HGDIOBJ DAT_004069ec;
HGDIOBJ DAT_004069f4;
HGDIOBJ DAT_004069f8;
int DAT_004069c0;
int DAT_004069c4;
undefined4 DAT_00406dc8;
pointer PTR_DAT_004063b0;
int DAT_00406d70;
int DAT_00406d6c;
undefined4 DAT_00405d74;
undefined4 DAT_00406dbc;
uint DAT_00406dac;
uint DAT_00406da4;
uint DAT_00406da8;
uint DAT_00406dfc;
int DAT_00406dbc;
uint DAT_00406e00;
int DAT_00406d80;
undefined DAT_00406db0;
int DAT_00406dac;
int DAT_00406db4;
uint DAT_00406d98;
int DAT_00406db8;
undefined4 DAT_00406e04;
uint DAT_00406e08;
uint DAT_00406e0c;
undefined4 DAT_00405c04;
undefined DAT_00406074;
undefined DAT_00406078;
undefined4 DAT_00406e10;
int DAT_00406dc4;
LPCSTR param_2_00405c90;
int DAT_004069d4;
int DAT_004069c8;
undefined1 *DAT_00406a00;
int DAT_004069cc;
int DAT_004069d0;
undefined lpCaption_00405c50;
int DAT_00406e04;
int DAT_00406e0c;
int DAT_00406d88;
int DAT_00406d74;
ushort DAT_00406d78;
undefined DAT_00405000;
undefined DAT_00405c12;
undefined2 DAT_00406a04;
undefined2 DAT_00406a68;
undefined1 DAT_00406acc;
undefined2 DAT_00406afe;
undefined2 DAT_00406b62;
undefined1 DAT_00406bc6;
int DAT_00406dc0;
int DAT_00406dcc;
int DAT_00406dc8;
undefined4 DAT_00406d7c;
undefined DAT_00000050;
LPCSTR lpchText_00405ca3;
LPCSTR lpchText_00405cb6;
LPCSTR lpchText_00405cc3;
LPCSTR lpchText_00405ccc;
LPCSTR lpchText_00405cd5;
LPCSTR lpchText_00405cec;
LPCSTR lpchText_00405d04;
LPCSTR lpchText_00405d15;
LPCSTR param_2_00405d2a;
LPCSTR param_2_00405d3d;
undefined4 DAT_00406da8;
LPCSTR param_2_00405d50;
LPCSTR param_2_00405d5a;
string s_%d.%03dfps_00405d66;
LPCSTR lpchText_00405d25;
uint DAT_00406d88;
int DAT_00406d98;
int DAT_00406d94;
undefined4 DAT_004067a3;
undefined4 DAT_00406db4;
undefined4 DAT_00406db8;
undefined4 DAT_00406e0c;
undefined4 DAT_00406e08;
undefined4 DAT_00406d88;
undefined4 DAT_00406d74;
undefined2 DAT_00406d78;
undefined4 DAT_00406d80;
undefined4 DAT_00406d6c;
undefined4 DAT_00406d70;
DWORD DAT_00406d94;
undefined4 DAT_00406d98;
undefined4 DAT_00406da4;
DWORD DAT_00406da0;
int DAT_00406dfc;
int DAT_00406e00;
undefined4 DAT_00406d9c;
undefined4 DAT_00406d8c;
undefined4 DAT_00406dac;
DWORD DAT_00406d9c;
int DAT_00406da0;
int DAT_00406e08;

uint FUN_00402000(void)

{
  DAT_00405c00 = DAT_00405c00 * 0x343fd + 0x269ec3;
  return DAT_00405c00 >> 0x10 & 0x7fff;
}



void entry(void)

{
  ATOM AVar1;
  undefined2 extraout_var;
  BOOL BVar2;
  undefined4 extraout_ECX;
  tagMSG local_20;
  
  DAT_004069d8 = GetModuleHandleA((LPCSTR)0x0);
  AVar1 = FUN_00402208();
  if (CONCAT22(extraout_var,AVar1) == 0) {
    MessageBoxA((HWND)0x0,(LPCSTR)&lpText_00405c3e,(LPCSTR)&lpWindowName_00405c51,0x10);
    local_20.wParam = 1;
  }
  else {
    DAT_004069dc = FUN_00402170();
    if (DAT_004069dc == (HWND)0x0) {
      MessageBoxA((HWND)0x0,(LPCSTR)&lpText_00405c3e,(LPCSTR)&lpWindowName_00405c51,0x10);
      local_20.wParam = 1;
    }
    else {
      while( true ) {
        while( true ) {
          BVar2 = PeekMessageA(&local_20,(HWND)0x0,0,0,1);
          if (BVar2 != 0) break;
          DAT_00406da4 = timeGetTime();
          if ((DAT_00406d90 == 0) || (DAT_00406d9c != 0)) {
            WaitMessage();
          }
          else if ((DAT_00406d8c == 0) || (DAT_00406da0 <= DAT_00406da4)) {
            Sleep(0);
            FUN_00403400(extraout_ECX);
            DAT_00406da0 = DAT_00406da0 + DAT_00406d8c;
          }
        }
        if (local_20.message == 0x12) break;
        TranslateMessage(&local_20);
        DispatchMessageA(&local_20);
      }
    }
  }
                    // WARNING: Subroutine does not return
  ExitProcess(local_20.wParam);
}



void __fastcall FUN_00402120(int param_1,undefined1 *param_2)

{
  undefined1 uVar1;
  undefined1 *in_EAX;
  undefined1 *puVar2;
  undefined1 *puVar3;
  
  if (param_1 != 0) {
    if (param_2 < in_EAX) {
      puVar3 = param_2 + param_1;
      puVar2 = in_EAX + param_1;
      while (param_1 != 0) {
        puVar2 = puVar2 + -1;
        puVar3 = puVar3 + -1;
        *puVar2 = *puVar3;
        param_1 = param_1 + -1;
      }
      return;
    }
    while (param_1 != 0) {
      uVar1 = *param_2;
      param_2 = param_2 + 1;
      *in_EAX = uVar1;
      in_EAX = in_EAX + 1;
      param_1 = param_1 + -1;
    }
  }
  return;
}



void __fastcall thunk_FUN_0040215a(undefined4 param_1,int param_2)

{
  undefined1 *in_EAX;
  
  while (0 < param_2) {
    *in_EAX = 0;
    in_EAX = in_EAX + 1;
    param_2 = param_2 + -1;
  }
  return;
}



void __fastcall FUN_0040215a(undefined4 param_1,int param_2)

{
  undefined1 *in_EAX;
  
  while (0 < param_2) {
    *in_EAX = 0;
    in_EAX = in_EAX + 1;
    param_2 = param_2 + -1;
  }
  return;
}



HWND FUN_00402170(void)

{
  HWND hWnd;
  tagRECT local_14;
  
  local_14.top = 0;
  local_14.left = 0;
  local_14.right = 0x140;
  local_14.bottom = 0xf0;
  AdjustWindowRectEx(&local_14,0xca0000,0,0);
  hWnd = CreateWindowExA(0,s_wcTKKN_00405c56,(LPCSTR)&lpWindowName_00405c51,0xca0000,-0x80000000,
                         -0x80000000,local_14.right - local_14.left,local_14.bottom - local_14.top,
                         (HWND)0x0,(HMENU)0x0,DAT_004069d8,(LPVOID)0x0);
  ShowWindow(hWnd,10);
  return hWnd;
}



int FUN_004021f4(void)

{
  byte *in_EAX;
  int iVar1;
  
  iVar1 = 1;
  for (; *in_EAX != 0; in_EAX = in_EAX + 1) {
    *in_EAX = *in_EAX ^ 0xff;
    iVar1 = iVar1 + 1;
  }
  return iVar1;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address

ATOM FUN_00402208(void)

{
  ATOM AVar1;
  int iVar2;
  int *piVar3;
  int iVar4;
  char *pcVar5;
  undefined4 *puVar6;
  WNDCLASSA local_34;
  
  DAT_00405c00 = timeGetTime();
  iVar4 = 0;
  do {
    FUN_004021f4();
    iVar4 = iVar4 + 1;
  } while (iVar4 < 0xd);
  _DAT_00406bf8 = 0;
  puVar6 = &DAT_00406bfc;
  for (pcVar5 = &DAT_004063e4; *pcVar5 != '\0'; pcVar5 = pcVar5 + iVar4) {
    iVar4 = FUN_004021f4();
    *puVar6 = pcVar5;
    puVar6 = puVar6 + 1;
  }
  iVar4 = 0;
  piVar3 = &DAT_00405d78;
  do {
    if (*piVar3 == 0) {
      piVar3[1] = 0x10000;
    }
    else {
      iVar2 = (piVar3[-1] << 10) / *piVar3;
      piVar3[1] = iVar2;
      if (iVar2 < 0) {
        piVar3[1] = -iVar2;
      }
    }
    iVar4 = iVar4 + 1;
    piVar3 = piVar3 + 3;
  } while (iVar4 < 0x40);
  DAT_00406dcc = 1;
  DAT_00406dc0 = 1;
  DAT_00406dc4 = 2;
  DAT_00406d84 = 0;
  local_34.style = 0xb;
  local_34.lpfnWndProc = FUN_00402318;
  local_34.cbClsExtra = 0;
  local_34.cbWndExtra = 0;
  local_34.hInstance = DAT_004069d8;
  local_34.hIcon = LoadIconA(DAT_004069d8,&lpIconName_00000065);
  local_34.hCursor = LoadCursorA((HINSTANCE)0x0,&lpCursorName_00007f00);
  local_34.hbrBackground = (HBRUSH)0x0;
  local_34.lpszMenuName = (LPCSTR)0x0;
  local_34.lpszClassName = s_wcTKKN_00405c56;
  AVar1 = RegisterClassA(&local_34);
  return AVar1;
}



LRESULT __thiscall FUN_00402318(void *this,HWND param_1,UINT param_2,WPARAM param_3,int param_4)

{
  LRESULT LVar1;
  
  if (0x101 < (int)param_2) {
    if (param_2 == 0x102) {
      if (param_4 == 0x40000000) {
        return 0;
      }
      FUN_00402abc(this,(ushort)param_3);
      return 0;
    }
    if (1 < param_2 - 0x104) {
      if (param_2 == 0x111) {
        FUN_00402d5c(param_4,param_3);
        return 0;
      }
      if (param_2 != 0x112) goto LAB_00402592;
    }
    if (DAT_00406d9c == 0) {
      FUN_004046cc();
      LVar1 = DefWindowProcA(param_1,param_2,param_3,param_4);
      FUN_004046cc();
      return LVar1;
    }
LAB_00402592:
    LVar1 = DefWindowProcA(param_1,param_2,param_3,param_4);
    return LVar1;
  }
  if (param_2 != 0x101) {
    if ((int)param_2 < 7) {
      if (param_2 == 6) {
        FUN_004046cc();
        return 0;
      }
      if (param_2 == 1) {
        FUN_004025b0();
        return 0;
      }
      if (param_2 == 2) {
        FUN_00402978();
        return 0;
      }
    }
    else {
      if (param_2 == 0xf) {
        FUN_00402a30();
        return 0;
      }
      if (param_2 == 0x100) {
        if (param_4 == 0x40000000) {
          return 0;
        }
        if ((int)param_3 < 0x28) {
          if (param_3 == 0x27) {
LAB_004024b9:
            DAT_00406d7c = DAT_00406d7c | 8;
            return 0;
          }
          if ((int)param_3 < 0x21) {
            if ((param_3 != 0x20) && (param_3 != 0xd)) {
              if (param_3 != 0x1b) {
                return 0;
              }
              FUN_004046cc();
              ShowWindow(param_1,6);
              return 0;
            }
            if (DAT_00406d84 == 0) {
              FUN_004042f0();
              return 0;
            }
            if (DAT_00406d84 != 1) {
              if (DAT_00406d84 == 5) {
                FUN_00404050();
                return 0;
              }
              if (DAT_00406d84 != 6) {
                return 0;
              }
              FUN_00403ac0();
              return 0;
            }
            if (DAT_00406d9c != 0) {
              FUN_004046cc();
              return 0;
            }
            FUN_004046cc();
            return 0;
          }
          if (param_3 != 0x25) {
            if (param_3 != 0x26) {
              return 0;
            }
LAB_004024c5:
            DAT_00406d7c = DAT_00406d7c | 4;
            return 0;
          }
        }
        else {
          if (100 < (int)param_3) {
            if (param_3 != 0x66) {
              if (param_3 != 0x68) {
                return 0;
              }
              goto LAB_004024c5;
            }
            goto LAB_004024b9;
          }
          if (param_3 != 100) {
            if ((param_3 != 0x28) && (param_3 != 0x62)) {
              return 0;
            }
            DAT_00406d7c = DAT_00406d7c | 2;
            return 0;
          }
        }
        DAT_00406d7c = DAT_00406d7c | 1;
        return 0;
      }
    }
    goto LAB_00402592;
  }
  if ((int)param_3 < 99) {
    if (param_3 != 0x62) {
      if (param_3 == 0x25) goto LAB_0040252a;
      if (param_3 == 0x26) goto LAB_0040253c;
      if (param_3 == 0x27) goto LAB_00402533;
      if (param_3 != 0x28) {
        return 0;
      }
    }
    DAT_00406d7c = DAT_00406d7c & 0xfffffffd;
  }
  else {
    if (param_3 != 100) {
      if (param_3 == 0x66) {
LAB_00402533:
        DAT_00406d7c = DAT_00406d7c & 0xfffffff7;
        return 0;
      }
      if (param_3 != 0x68) {
        return 0;
      }
LAB_0040253c:
      DAT_00406d7c = DAT_00406d7c & 0xfffffffb;
      return 0;
    }
LAB_0040252a:
    DAT_00406d7c = DAT_00406d7c & 0xfffffffe;
  }
  return 0;
}



void FUN_004025b0(void)

{
  byte bVar1;
  HWND in_EAX;
  HANDLE pvVar2;
  BITMAPINFO *lpbmi;
  BYTE *pBVar3;
  HDC hdc;
  HFONT h;
  HGDIOBJ pvVar4;
  undefined4 extraout_ECX;
  undefined4 extraout_ECX_00;
  uint uVar5;
  DWORD DVar6;
  SIZE_T dwBytes;
  BITMAPINFO *lpMem;
  tagSIZE local_18;
  
  dwBytes = 0x428;
  DVar6 = 0;
  pvVar2 = GetProcessHeap();
  lpbmi = HeapAlloc(pvVar2,DVar6,dwBytes);
  thunk_FUN_0040215a(extraout_ECX,0x28);
  (lpbmi->bmiHeader).biSize = 0x28;
  (lpbmi->bmiHeader).biWidth = 0x140;
  (lpbmi->bmiHeader).biHeight = 0xf0;
  (lpbmi->bmiHeader).biPlanes = 1;
  (lpbmi->bmiHeader).biBitCount = 8;
  (lpbmi->bmiHeader).biCompression = 0;
  uVar5 = 0;
  (lpbmi->bmiHeader).biClrUsed = 0x10;
  pBVar3 = &lpbmi->bmiColors[0].rgbRed;
  do {
    *pBVar3 = (BYTE)((uVar5 & 0xffffff01) << 7);
    bVar1 = (byte)uVar5;
    pBVar3[0x20] = -(bVar1 & 1);
    pBVar3[-1] = '\0';
    pBVar3[0x1f] = -(bVar1 & 2);
    ((RGBQUAD *)(pBVar3 + -2))->rgbBlue = '\0';
    uVar5 = uVar5 + 1;
    pBVar3[0x1e] = -(bVar1 & 4);
    pBVar3 = pBVar3 + 4;
  } while ((int)uVar5 < 8);
  *(undefined1 *)((int)&lpbmi[1].bmiHeader.biXPelsPerMeter + 2) = 0xc0;
  *(undefined1 *)((int)&lpbmi[1].bmiHeader.biXPelsPerMeter + 1) = 0xc0;
  *(undefined1 *)&lpbmi[1].bmiHeader.biXPelsPerMeter = 0xc0;
  *(undefined1 *)((int)&lpbmi[1].bmiHeader.biYPelsPerMeter + 2) = 0x80;
  *(undefined1 *)((int)&lpbmi[1].bmiHeader.biYPelsPerMeter + 1) = 0x80;
  *(undefined1 *)&lpbmi[1].bmiHeader.biYPelsPerMeter = 0x80;
  hdc = GetDC(in_EAX);
  DAT_004069ec = CreateDIBSection(hdc,lpbmi,0,&ppvBits_004069fc,(HANDLE)0x0,0);
  DAT_004069f4 = CreateCompatibleBitmap(hdc,0x140,0xf0);
  DVar6 = 0;
  lpMem = lpbmi;
  pvVar2 = GetProcessHeap();
  HeapFree(pvVar2,DVar6,lpMem);
  thunk_FUN_0040215a(extraout_ECX_00,0x12c00);
  DAT_004069e0 = CreateCompatibleDC(hdc);
  DAT_004069e4 = CreateCompatibleDC(hdc);
  DAT_004069e8 = CreateCompatibleDC(hdc);
  SaveDC(DAT_004069e0);
  SaveDC(DAT_004069e4);
  SaveDC(DAT_004069e8);
  DAT_004069f0 = SelectObject(DAT_004069e0,DAT_004069ec);
  SetDIBColorTable(DAT_004069e0,0,0x10,lpbmi->bmiColors);
  SelectObject(DAT_004069e4,DAT_004069f4);
  lplf_00406374 = (LOGFONTA *)0x10;
  h = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  pvVar4 = SelectObject(DAT_004069e4,h);
  GetTextExtentPoint32A(DAT_004069e4,&DAT_00405c5d,0xe,&local_18);
  DAT_00406ddc = local_18.cx;
  GetTextExtentPoint32A(DAT_004069e4,&DAT_00405c5d,4,&local_18);
  DAT_00406dd0 = local_18.cx;
  GetTextExtentPoint32A(DAT_004069e4,&DAT_00405c61,10,&local_18);
  DAT_00406dd4 = local_18.cx;
  GetTextExtentPoint32A(DAT_004069e4,&DAT_00405c6b,0xc,&local_18);
  DAT_00406dd8 = local_18.cx;
  GetTextExtentPoint32A(DAT_004069e4,&DAT_00405c77,6,&local_18);
  DAT_00406de0 = DAT_00406ddc + DAT_00406dd8;
  DAT_00406de4 = local_18.cx;
  GetTextExtentPoint32A(DAT_004069e4,&DAT_00405c7d,4,&local_18);
  DAT_00406de8 = DAT_00406de0 + DAT_00406de4;
  DAT_00406dec = local_18.cx;
  GetTextExtentPoint32A(DAT_004069e4,&DAT_00405c81,4,&local_18);
  DAT_00406df0 = DAT_00406de8 + DAT_00406dec;
  DAT_00406df4 = local_18.cx;
  GetTextExtentPoint32A(DAT_004069e4,&DAT_00405c81,5,&local_18);
  DAT_00406df8 = local_18.cx - DAT_00406dec;
  GetTextExtentPoint32A(DAT_004069e0,&DAT_00405c5d,0x32,&local_18);
  SelectObject(DAT_004069e0,pvVar4);
  DAT_004069f8 = CreateCompatibleBitmap(hdc,local_18.cx,0x10);
  SelectObject(DAT_004069e8,DAT_004069f8);
  pvVar4 = SelectObject(DAT_004069e8,h);
  SetTextColor(DAT_004069e8,0xffffff);
  SetBkColor(DAT_004069e8,0);
  TextOutA(DAT_004069e8,0,0,&DAT_00405c5d,0x32);
  SelectObject(DAT_004069e8,pvVar4);
  DeleteObject(h);
  ReleaseDC(in_EAX,hdc);
  DAT_00406d90 = 0;
  FUN_00403ac0();
  return;
}



void FUN_00402978(void)

{
  HANDLE hHeap;
  DWORD dwFlags;
  LPVOID lpMem;
  
  if (DAT_00406a00 != (LPVOID)0x0) {
    dwFlags = 0;
    lpMem = DAT_00406a00;
    hHeap = GetProcessHeap();
    HeapFree(hHeap,dwFlags,lpMem);
    DAT_00406a00 = (LPVOID)0x0;
  }
  RestoreDC(DAT_004069e0,-1);
  RestoreDC(DAT_004069e4,-1);
  RestoreDC(DAT_004069e8,-1);
  SelectObject(DAT_004069e0,DAT_004069f0);
  DeleteObject(DAT_004069ec);
  DeleteObject(DAT_004069f4);
  DeleteDC(DAT_004069e0);
  DeleteDC(DAT_004069e4);
  DeleteDC(DAT_004069e8);
  DeleteObject(DAT_004069f8);
  DAT_00406d90 = 0;
  PostQuitMessage(0);
  return;
}



void FUN_00402a30(void)

{
  HWND in_EAX;
  HDC hdc;
  tagPAINTSTRUCT tStack_50;
  
  hdc = BeginPaint(in_EAX,&tStack_50);
  if ((DAT_00406d90 == 0) || (DAT_00406d9c != 0)) {
    BitBlt(hdc,tStack_50.rcPaint.left,tStack_50.rcPaint.top,
           tStack_50.rcPaint.right - tStack_50.rcPaint.left,
           tStack_50.rcPaint.bottom - tStack_50.rcPaint.top,DAT_004069e4,tStack_50.rcPaint.left,
           tStack_50.rcPaint.top,0xcc0020);
  }
  else {
    BitBlt(hdc,tStack_50.rcPaint.left,tStack_50.rcPaint.top,
           tStack_50.rcPaint.right - tStack_50.rcPaint.left,
           tStack_50.rcPaint.bottom - tStack_50.rcPaint.top,DAT_004069e0,tStack_50.rcPaint.left,
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
  
  if (DAT_00406d84 == 0) {
    uVar1 = (uint)param_2;
    if ((int)(char)(&PTR_DAT_004063b0)[DAT_004069c0][DAT_004069c4] == uVar1) {
      DAT_004069c4 = DAT_004069c4 + 1;
LAB_00402b09:
      if ((&PTR_DAT_004063b0)[DAT_004069c0][DAT_004069c4] == '\0') {
        switch(DAT_004069c0) {
        case 0:
          DAT_00406dc8 = 0;
          DAT_00406dc4 = 2;
          DAT_00406dc0 = 1;
          DAT_00406dcc = 1;
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
          DAT_00406dc0 = 0;
          break;
        case 6:
          DAT_00406dc0 = 2;
          break;
        case 7:
          DAT_00406dc0 = 3;
          break;
        case 8:
          DAT_00406dc8 = 2;
          DAT_00406dc4 = 2;
          DAT_00406dc0 = 2;
          break;
        case 9:
          DAT_00406dc8 = 2;
          DAT_00406dc4 = 2;
          DAT_00406dc0 = 1;
          break;
        case 10:
          DAT_00406dcc = 1;
          break;
        case 0xb:
          DAT_00406dcc = 0;
          break;
        case 0xc:
          DAT_00406dc8 = 2;
          DAT_00406dc4 = 2;
          DAT_00406dc0 = 3;
        }
        FUN_00403ac0();
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
  
  iVar6 = (DAT_00406d70 + 6) - (in_EAX[1] >> 6);
  iVar2 = (DAT_00406d6c + 6) - (*in_EAX >> 6);
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
    uVar1 = FUN_00402000();
    uVar4 = CONCAT31((int3)(uVar4 >> 8),
                     ((char)uVar4 + (char)((int)uVar1 % param_2) + '\x01') - (char)(param_2 >> 1)) &
            0xffffff3f;
  }
  return CONCAT44(local_10,uVar4);
}



void FUN_00402e88(void)

{
  int *in_EAX;
  uint uVar1;
  undefined4 extraout_ECX;
  undefined4 uVar2;
  undefined4 extraout_ECX_00;
  int iVar3;
  undefined8 uVar4;
  
  uVar1 = FUN_00402000();
  uVar1 = uVar1 & 3;
  if (uVar1 == 0) {
    uVar1 = FUN_00402000();
    uVar2 = 0x5100;
    *in_EAX = (int)uVar1 % 0x5100;
    in_EAX[1] = 0;
  }
  else if (uVar1 == 1) {
    uVar1 = FUN_00402000();
    uVar2 = 0x5100;
    *in_EAX = (int)uVar1 % 0x5100;
    in_EAX[1] = 0x3d00;
  }
  else if (uVar1 == 2) {
    *in_EAX = 0;
    uVar1 = FUN_00402000();
    uVar2 = 0x3d00;
    in_EAX[1] = (int)uVar1 % 0x3d00;
  }
  else {
    uVar2 = extraout_ECX;
    if (uVar1 == 3) {
      *in_EAX = 0x5100;
      uVar1 = FUN_00402000();
      uVar2 = 0x3d00;
      in_EAX[1] = (int)uVar1 % 0x3d00;
    }
  }
  *(undefined1 *)((int)in_EAX + 0xb) = 0;
  *(undefined1 *)(in_EAX + 3) = 0;
  *(undefined1 *)((int)in_EAX + 9) = 0;
  *(undefined1 *)((int)in_EAX + 10) = 0;
  iVar3 = 5;
  switch(DAT_00406dbc) {
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
    uVar1 = FUN_00402000();
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

void FUN_00402fbc(void)

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
  
  uVar2 = DAT_00406da4;
  puVar12 = &DAT_00405c04;
  pcVar10 = local_1c;
  for (iVar7 = 4; iVar7 != 0; iVar7 = iVar7 + -1) {
    *(undefined4 *)pcVar10 = *puVar12;
    puVar12 = puVar12 + 1;
    pcVar10 = pcVar10 + 4;
  }
  local_2c = &DAT_00406e10;
  local_24 = 0;
  do {
    if (DAT_00406da8 <= local_24) {
      if (((DAT_00406dfc < uVar2) && (DAT_00406da8 < 299)) && (DAT_00406dbc != 7)) {
        FUN_00402e88();
        DAT_00406da8 = DAT_00406da8 + 1;
        DAT_00406dfc = uVar2 + 3000;
      }
      if (DAT_00406e00 < uVar2) {
        if (DAT_00406dbc == 0) {
          uVar6 = FUN_00402000();
          if (uVar6 < 0x3000) {
            DAT_00406dbc = uVar6 % 7 + 1;
            if (DAT_00406dbc == 0) {
              DAT_00406d80 = 1;
            }
            _DAT_00406db0 = 100;
            DAT_00406e00 = uVar2 + 10000;
          }
          else {
            DAT_00406e00 = uVar2 + 5000;
          }
        }
        else {
          DAT_00406dbc = 0;
          DAT_00406e00 = uVar2 + 5000;
          _DAT_00406db0 = 100;
        }
      }
      return;
    }
    uVar6 = (uint)(byte)local_2c[2];
    if (uVar6 == 0xff) {
      FUN_00402e88();
      return;
    }
    if ((*local_2c < 0x5101) && (local_2c[1] < 0x3d01)) {
      iVar7 = (local_2c[1] >> 6) - 4;
      iVar11 = (*local_2c >> 6) - 4;
      if (DAT_00406d80 == 0) {
        iVar4 = iVar11 - DAT_00406d6c;
        uVar8 = iVar7 - DAT_00406d70;
        if ((iVar4 + 4U < 0x17) && (uVar8 + 6 < 0x14)) {
          if (*(char *)((int)local_2c + 9) == '\0') {
            DAT_00406db4 = DAT_00406db4 + 1;
            *(undefined1 *)((int)local_2c + 9) = 1;
          }
          if ((iVar4 - 2U < 0xb) && (uVar8 < 10)) {
            DAT_00406d98 = uVar2;
            DAT_00406d80 = 1;
          }
        }
        else if (*(char *)((int)local_2c + 9) != '\0') {
          *(undefined1 *)((int)local_2c + 9) = 0;
          DAT_00406db4 = DAT_00406db4 + -1;
          if (DAT_00406db4 != 0) {
            DAT_00406db8 = DAT_00406db8 + DAT_00406db4;
            DAT_00406e04 = 100;
            if (uVar2 < DAT_00406e08) {
              if (DAT_00406e0c < 10) {
                DAT_00406e0c = DAT_00406e0c + 1;
              }
            }
            else {
              DAT_00406e0c = 1;
            }
            DAT_00406e08 = uVar2 + 1000;
          }
        }
      }
      cVar1 = *(char *)((int)local_2c + 10);
      if (cVar1 == '\x01') {
        *(char *)(local_2c + 3) = (char)local_2c[3] + '\x01';
        if (*(char *)((int)local_2c + 0xb) == (char)local_2c[3]) {
          uVar8 = FUN_00402000();
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
        if (iVar11 < DAT_00406d6c + 6) {
          if (*(char *)((int)local_2c + 0xd) < '`') {
            *(char *)((int)local_2c + 0xd) = *(char *)((int)local_2c + 0xd) + '\x01';
          }
        }
        else if (-0x60 < *(char *)((int)local_2c + 0xd)) {
          *(char *)((int)local_2c + 0xd) = *(char *)((int)local_2c + 0xd) + -1;
        }
        if (iVar7 < DAT_00406d70 + 6) {
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
      FUN_00402e88();
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
      FUN_00402120(0x12c00,DAT_00406a00);
    }
    else {
      puVar4 = DAT_00406a00 + DAT_004069c8 * 0x140;
      ppvVar8 = ppvBits_004069fc;
      for (iVar3 = (0xf0 - DAT_004069c8) * 0x140; 0 < iVar3; iVar3 = iVar3 + -1) {
        *(undefined1 *)ppvVar8 = *puVar4;
        puVar4 = puVar4 + 1;
        ppvVar8 = (void **)((int)ppvVar8 + 1);
      }
      puVar4 = DAT_00406a00;
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
  FUN_00402fbc();
  if (DAT_00406d80 == 0) {
    DAT_00406d88 = DAT_00406d88 + 1;
    iVar3 = (uint)((DAT_00406d7c & 8) != 0) - (uint)((DAT_00406d7c & 1) != 0);
    switch(DAT_00406d74) {
    case 0:
      if (-1 < iVar3) {
        DAT_00406d78 = 4;
        DAT_00406d74 = 1;
      }
      break;
    case 1:
      if (DAT_00406d78 < 5) {
        if (iVar3 < 0) {
          DAT_00406d78 = DAT_00406d78 + 1;
        }
        else if (DAT_00406d78 == 0) {
          DAT_00406d74 = 2;
        }
        else {
          DAT_00406d78 = DAT_00406d78 - 1;
        }
      }
      else {
        DAT_00406d74 = 0;
      }
      break;
    case 2:
      DAT_00406d74 = DAT_00406d74 + iVar3;
      break;
    case 3:
      if (DAT_00406d78 < 5) {
        if (iVar3 < 1) {
          if (DAT_00406d78 == 0) {
            DAT_00406d74 = 2;
          }
          else {
            DAT_00406d78 = DAT_00406d78 - 1;
          }
        }
        else {
          DAT_00406d78 = DAT_00406d78 + 1;
        }
      }
      else {
        DAT_00406d74 = 4;
      }
      break;
    case 4:
      if (iVar3 < 1) {
        DAT_00406d78 = 4;
        DAT_00406d74 = 3;
      }
    }
    DAT_00406d6c = DAT_00406d6c + iVar3;
    DAT_00406d70 = DAT_00406d70 +
                   ((uint)((DAT_00406d7c & 4) != 0) - (uint)((DAT_00406d7c & 2) != 0));
    if (DAT_00406d6c < 0) {
      DAT_00406d6c = 0;
    }
    if (DAT_00406d70 < 0) {
      DAT_00406d70 = 0;
    }
    if (0x130 < DAT_00406d6c) {
      DAT_00406d6c = 0x130;
    }
    if (0xe0 < DAT_00406d70) {
      DAT_00406d70 = 0xe0;
    }
    uVar1 = *(ushort *)(DAT_00406d74 * 2 + 0x405c34);
  }
  else {
    if (DAT_00406d80 == 0x11) {
      DAT_00406d90 = 0;
      FUN_00404590();
      return;
    }
    uVar1 = *(ushort *)(&DAT_00405c12 + DAT_00406d80 * 2);
    DAT_00406d80 = DAT_00406d80 + 1;
  }
  pcVar6 = &DAT_00405000 + uVar1;
  pcVar10 = (char *)((int)ppvBits_004069fc + DAT_00406d70 * 0x140 + DAT_00406d6c);
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
  if (DAT_00406dbc != 0) {
    BitBlt(DAT_004069e4,0,0,0x140,0x10,DAT_004069e0,0,0,0xcc0020);
    bVar2 = true;
    _DAT_00406db0 = _DAT_00406db0 + -1;
    if (DAT_00406dbc == 1) {
      BitBlt(DAT_004069e4,0x140 - DAT_00406dd8,0,DAT_00406dd8,0x10,DAT_004069e8,DAT_00406ddc,0,
             0xee0086);
    }
    else if (DAT_00406dbc - 2U < 4) {
      BitBlt(DAT_004069e4,0x140 - DAT_00406dd4,0,DAT_00406dd4,0x10,DAT_004069e8,DAT_00406dd0,0,
             0xee0086);
    }
    else if (DAT_00406dbc == 6) {
      BitBlt(DAT_004069e4,0x140 - DAT_00406de4,0,DAT_00406de4,0x10,DAT_004069e8,DAT_00406de0,0,
             0xee0086);
    }
    else if (DAT_00406dbc - 2U == 5) {
      BitBlt(DAT_004069e4,0x140 - DAT_00406ddc,0,DAT_00406ddc,0x10,DAT_004069e8,0,0,0xee0086);
    }
    else {
      wsprintfA(local_30,(LPCSTR)&param_2_00405c90,DAT_00406dbc);
      MessageBoxA(DAT_004069dc,local_30,&lpCaption_00405c50,0);
      BitBlt(DAT_004069e4,0x140 - DAT_00406dec,0,DAT_00406dec,0x10,DAT_004069e8,DAT_00406de8,0,
             0xee0086);
    }
  }
  if (DAT_00406e04 != 0) {
    if (!bVar2) {
      BitBlt(DAT_004069e4,0,0,0x140,0x10,DAT_004069e0,0,0,0xcc0020);
    }
    DAT_00406e04 = DAT_00406e04 + -1;
    bVar2 = true;
    BitBlt(DAT_004069e4,0,0,DAT_00406e0c * DAT_00406df8 + DAT_00406df4,0x10,DAT_004069e8,
           DAT_00406df0,0,0xee0086);
  }
  hdc = GetDC(DAT_004069dc);
  if (bVar2) {
    BitBlt(hdc,0,0,0x140,0x10,DAT_004069e4,0,0,0xcc0020);
    BitBlt(hdc,0,0x10,0x140,0xf0,DAT_004069e0,0,0x10,0xcc0020);
  }
  else {
    BitBlt(hdc,0,0,0x140,0xf0,DAT_004069e0,0,0,0xcc0020);
  }
  ReleaseDC(DAT_004069dc,hdc);
  return;
}



void FUN_00403ac0(void)

{
  HWND in_EAX;
  HFONT h;
  HFONT h_00;
  HFONT h_01;
  HGDIOBJ h_02;
  HDC hdc;
  tagRECT local_20;
  
  lplf_00406374 = (LOGFONTA *)&DAT_00000050;
  h = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  lplf_00406374 = (LOGFONTA *)0xe;
  h_00 = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  lplf_00406374 = (LOGFONTA *)0x14;
  h_01 = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  PatBlt(DAT_004069e4,0,0,0x140,0xf0,0x42);
  h_02 = SelectObject(DAT_004069e4,h);
  SetTextColor(DAT_004069e4,0xffffff);
  SetBkColor(DAT_004069e4,0);
  local_20.left = 0;
  local_20.top = 0;
  local_20.right = 0x140;
  local_20.bottom = 0x78;
  DrawTextA(DAT_004069e4,(LPCSTR)&lpWindowName_00405c51,4,&local_20,0x825);
  SelectObject(DAT_004069e4,h_00);
  local_20.top = local_20.bottom;
  local_20.bottom = 0xf0;
  if (DAT_00406dc0 == 0) {
    DrawTextA(DAT_004069e4,(LPCSTR)((int)&param_2_00405c90 + 3),-1,&local_20,0x821);
LAB_00403c17:
    local_20.top = local_20.top + 0x14;
  }
  else {
    if (DAT_00406dc0 == 2) {
      DrawTextA(DAT_004069e4,(LPCSTR)&lpchText_00405ca3,-1,&local_20,0x821);
      goto LAB_00403c17;
    }
    if (DAT_00406dc0 == 3) {
      DrawTextA(DAT_004069e4,(LPCSTR)&lpchText_00405cb6,-1,&local_20,0x821);
      goto LAB_00403c17;
    }
  }
  if (DAT_00406dc4 == 0) {
    DrawTextA(DAT_004069e4,(LPCSTR)&lpchText_00405cc3,-1,&local_20,0x821);
LAB_00403c66:
    local_20.top = local_20.top + 0x14;
  }
  else if (DAT_00406dc4 == 1) {
    DrawTextA(DAT_004069e4,(LPCSTR)&lpchText_00405ccc,-1,&local_20,0x821);
    goto LAB_00403c66;
  }
  if (DAT_00406dcc == 0) {
    DrawTextA(DAT_004069e4,(LPCSTR)&lpchText_00405cd5,-1,&local_20,0x821);
    local_20.top = local_20.top + 0x14;
  }
  if (DAT_00406dc8 == 1) {
    DrawTextA(DAT_004069e4,(LPCSTR)&lpchText_00405cec,-1,&local_20,0x821);
  }
  else {
    if (DAT_00406dc8 != 2) goto LAB_00403ce5;
    DrawTextA(DAT_004069e4,(LPCSTR)&lpchText_00405d04,-1,&local_20,0x821);
  }
  local_20.top = local_20.top + 0x14;
LAB_00403ce5:
  SelectObject(DAT_004069e4,h_01);
  local_20.top = 200;
  DrawTextA(DAT_004069e4,(LPCSTR)&lpchText_00405d15,0xf,&local_20,0x821);
  SelectObject(DAT_004069e4,h_02);
  DeleteObject(h_01);
  DeleteObject(h);
  hdc = GetDC(in_EAX);
  BitBlt(hdc,0,0,0x140,0xf0,DAT_004069e4,0,0,0xcc0020);
  ReleaseDC(in_EAX,hdc);
  DAT_00406d7c = 0;
  DAT_00406d84 = 0;
  DAT_00406d90 = 0;
  return;
}



void __fastcall FUN_00403d84(undefined4 param_1,uint param_2)

{
  HWND in_EAX;
  HFONT h;
  HFONT h_00;
  HGDIOBJ h_01;
  int iVar1;
  HDC hdc;
  tagRECT local_120;
  CHAR local_110 [256];
  
  lplf_00406374 = (LOGFONTA *)&DAT_00000050;
  h = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  lplf_00406374 = (LOGFONTA *)0x10;
  h_00 = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  h_01 = SelectObject(DAT_004069e4,h);
  SetTextColor(DAT_004069e4,0xffffff);
  SetBkMode(DAT_004069e4,1);
  local_120.left = 0;
  local_120.top = 0;
  local_120.right = 0x140;
  local_120.bottom = 0x78;
  DrawTextA(DAT_004069e4,(LPCSTR)&lpchText_00405d25,4,&local_120,0x825);
  local_120.top = local_120.bottom;
  local_120.bottom = 0xf0;
  SelectObject(DAT_004069e4,h_00);
  iVar1 = wsprintfA(local_110,(LPCSTR)&param_2_00405d2a,param_2 / 1000,param_2 % 1000);
  DrawTextA(DAT_004069e4,local_110,iVar1,&local_120,0x821);
  local_120.top = local_120.top + 0x20;
  if (DAT_00406d8c != 0) {
    DAT_00406d88 = DAT_00406d88 * DAT_00406d8c;
  }
  iVar1 = wsprintfA(local_110,(LPCSTR)&param_2_00405d3d,DAT_00406d88 / 1000,DAT_00406d88 % 1000);
  DrawTextA(DAT_004069e4,local_110,iVar1,&local_120,0x821);
  local_120.top = local_120.top + 0x20;
  iVar1 = wsprintfA(local_110,(LPCSTR)&param_2_00405d50,DAT_00406da8);
  DrawTextA(DAT_004069e4,local_110,iVar1,&local_120,0x821);
  if (DAT_00406db8 != 0) {
    local_120.top = local_120.top + 0x20;
    iVar1 = wsprintfA(local_110,(LPCSTR)&param_2_00405d5a,DAT_00406db8);
    DrawTextA(DAT_004069e4,local_110,iVar1,&local_120,0x821);
  }
  if (DAT_00406d8c == 0) {
    iVar1 = wsprintfA(local_110,s__d__03dfps_00405d66,(uint)(DAT_00406d88 * 1000) / param_2,
                      (int)(((ulonglong)(uint)(DAT_00406d88 * 1000000) / (ulonglong)param_2) % 1000)
                     );
    DrawTextA(DAT_004069e4,local_110,iVar1,&local_120,0x829);
  }
  SelectObject(DAT_004069e4,h_01);
  DeleteObject(h);
  DeleteObject(h_00);
  hdc = GetDC(in_EAX);
  BitBlt(hdc,0,0,0x140,0xf0,DAT_004069e4,0,0,0xcc0020);
  ReleaseDC(in_EAX,hdc);
  DAT_00406d7c = 0;
  DAT_00406d84 = 5;
  DAT_00406d90 = 0;
  return;
}



void FUN_00404050(void)

{
  HWND in_EAX;
  uint *puVar1;
  HFONT h;
  int iVar2;
  HDC hdc;
  LPCSTR lpchText;
  uint uVar3;
  LPCSTR lpString;
  LPCSTR lpString_00;
  LPCSTR lpString_01;
  HFONT local_38;
  HGDIOBJ local_34;
  tagSIZE local_28;
  tagRECT local_20;
  
  uVar3 = DAT_00406d88;
  if (DAT_00406d8c == 0) {
    uVar3 = DAT_00406d98 - DAT_00406d94;
  }
  for (puVar1 = &DAT_004067a3; uVar3 < *puVar1; puVar1 = puVar1 + 2) {
  }
  if ((char)puVar1[1] == '\0') {
    lpString = (LPCSTR)0x0;
  }
  else {
    lpString = *(LPCSTR *)(&DAT_00406bf8 + (char)puVar1[1] * 4);
  }
  if (*(char *)((int)puVar1 + 5) == '\0') {
    lpString_01 = (LPCSTR)0x0;
  }
  else {
    lpString_01 = *(LPCSTR *)(&DAT_00406bf8 + *(char *)((int)puVar1 + 5) * 4);
  }
  if (*(char *)((int)puVar1 + 6) == '\0') {
    lpString_00 = (LPCSTR)0x0;
  }
  else {
    lpString_00 = *(LPCSTR *)(&DAT_00406bf8 + *(char *)((int)puVar1 + 6) * 4);
  }
  if (*(char *)((int)puVar1 + 7) == '\0') {
    lpchText = (LPCSTR)0x0;
  }
  else {
    lpchText = *(LPCSTR *)(&DAT_00406bf8 + *(char *)((int)puVar1 + 7) * 4);
  }
  PatBlt(DAT_004069e4,0,0,0x140,0xf0,0x42);
  lplf_00406374 = (LOGFONTA *)0x10;
  h = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
  SetTextColor(DAT_004069e4,0xffffff);
  SetBkMode(DAT_004069e4,1);
  if (lpString_00 == (LPCSTR)0x0) {
    local_34 = SelectObject(DAT_004069e4,h);
  }
  else {
    iVar2 = lstrlenA(lpString_00);
    lplf_00406374 = (LOGFONTA *)(0x1e0 / (longlong)iVar2);
    if (0x4f < (int)lplf_00406374) {
      lplf_00406374 = (LOGFONTA *)&DAT_00000050;
    }
    local_38 = CreateFontIndirectA((LOGFONTA *)&lplf_00406374);
    local_34 = SelectObject(DAT_004069e4,local_38);
    local_20.left = 0;
    local_20.top = 0x14;
    local_20.right = 0x140;
    local_20.bottom = 200;
    DrawTextA(DAT_004069e4,lpString_00,iVar2,&local_20,0x825);
    SelectObject(DAT_004069e4,h);
  }
  local_20.left = 0;
  local_20.top = 200;
  local_20.right = 0x140;
  local_20.bottom = 0xf0;
  if (lpchText != (LPCSTR)0x0) {
    DrawTextA(DAT_004069e4,lpchText,-1,&local_20,0x26);
  }
  local_28.cx = 0;
  if (lpString != (LPCSTR)0x0) {
    iVar2 = lstrlenA(lpString);
    GetTextExtentPoint32A(DAT_004069e4,lpString,iVar2,&local_28);
    TextOutA(DAT_004069e4,4,4,lpString,iVar2);
  }
  if (lpString_01 != (LPCSTR)0x0) {
    iVar2 = lstrlenA(lpString_01);
    TextOutA(DAT_004069e4,local_28.cx + 4,4,lpString_01,iVar2);
  }
  SelectObject(DAT_004069e4,local_34);
  hdc = GetDC(in_EAX);
  BitBlt(hdc,0,0,0x140,0xf0,DAT_004069e4,0,0,0xcc0020);
  ReleaseDC(in_EAX,hdc);
  DeleteObject(local_38);
  DeleteObject(h);
  DAT_00406d7c = 0;
  DAT_00406d84 = 6;
  DAT_00406d90 = 0;
  return;
}



// WARNING: Globals starting with '_' overlap smaller symbols at the same address

void FUN_004042f0(void)

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
  FUN_00404660();
  if (DAT_00406dc8 == 0) {
    DAT_00406d8c = 0x10;
  }
  else if (DAT_00406dc8 == 1) {
    DAT_00406d8c = 0xc;
  }
  else if (DAT_00406dc8 == 2) {
    DAT_00406d8c = 0;
  }
  if (DAT_00406dc4 == 0) {
    DAT_00406a00 = (LPVOID)0x0;
  }
  else {
    dwBytes = 0x12c00;
    DVar10 = 0;
    pvVar1 = GetProcessHeap();
    DAT_00406a00 = HeapAlloc(pvVar1,DVar10,dwBytes);
    thunk_FUN_0040215a(extraout_ECX,0x12c00);
    puVar7 = &DAT_00406afe;
    local_40 = 0;
    pcVar9 = &DAT_00406acc;
    local_30 = &DAT_00406bc6;
    local_34 = &DAT_00406b62;
    puVar8 = &DAT_00406a68;
    puVar6 = &DAT_00406a04;
    do {
      uVar2 = FUN_00402000();
      uVar3 = FUN_00402000();
      uVar4 = FUN_00402000();
      *(char *)((int)DAT_00406a00 + (int)uVar2 % 0x140 + ((int)uVar3 % 0xf0) * 0x140) =
           (char)((int)uVar4 % 0xe) + '\x01';
      uVar2 = FUN_00402000();
      *puVar6 = (short)((int)uVar2 % 0x140);
      uVar2 = FUN_00402000();
      *puVar8 = (short)((int)uVar2 % 0xf0);
      uVar2 = FUN_00402000();
      *pcVar9 = (char)((int)uVar2 % 0xe) + '\x01';
      uVar2 = FUN_00402000();
      *puVar7 = (short)((int)uVar2 % 0x140);
      uVar2 = FUN_00402000();
      *local_34 = (short)((int)uVar2 % 0xf0);
      uVar2 = FUN_00402000();
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
  DAT_00406db4 = 0;
  DAT_00406db8 = 0;
  DAT_00406e0c = 0;
  DAT_00406e04 = 0;
  DAT_00406e08 = 0;
  DAT_00406d88 = 0;
  _DAT_00406db0 = 0;
  DAT_00406d74 = 2;
  DAT_00406d78 = 0;
  DAT_00406d80 = 0;
  DAT_00406d6c = 0x98;
  DAT_00406d70 = 0x2c;
  Sleep(1);
  while (BVar5 = PeekMessageA(&local_2c,(HWND)0x0,0,0,1), BVar5 != 0) {
    TranslateMessage(&local_2c);
    DispatchMessageA(&local_2c);
  }
  DAT_00406d94 = timeGetTime();
  DAT_00406d98 = 0;
  DAT_00406da4 = 0;
  DAT_00406dfc = DAT_00406d94 + 3000;
  DAT_00406e00 = DAT_00406d94 + 5000;
  DAT_00406d90 = 1;
  DAT_00406d84 = 1;
  DAT_00406d9c = 0;
  DAT_00406da0 = DAT_00406d94;
  if (DAT_00406dcc != 0) {
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
  if (DAT_00406dcc != 0) {
    DVar3 = 0x20;
    pvVar1 = GetCurrentProcess();
    SetPriorityClass(pvVar1,DVar3);
  }
  nPriority = 0;
  pvVar1 = GetCurrentThread();
  SetThreadPriority(pvVar1,nPriority);
  if (DAT_00406a00 != (LPVOID)0x0) {
    DVar3 = 0;
    lpMem = DAT_00406a00;
    pvVar1 = GetProcessHeap();
    HeapFree(pvVar1,DVar3,lpMem);
    DAT_00406a00 = (LPVOID)0x0;
  }
  DAT_00406da4 = 0;
  do {
    BVar2 = PeekMessageA(&local_20,in_EAX,0x100,0x108,1);
  } while (BVar2 != 0);
  if (DAT_00406d80 == 0) {
    FUN_00403ac0();
  }
  else {
    BitBlt(DAT_004069e4,0,0,0x140,0xf0,DAT_004069e0,0,0,0xcc0020);
    FUN_00403d84(DAT_00406d94,DAT_00406d98 - DAT_00406d94);
  }
  return;
}



void FUN_00404660(void)

{
  undefined4 *puVar1;
  int iVar2;
  
  puVar1 = &DAT_00406e10;
  iVar2 = 0;
  do {
    *(undefined1 *)(puVar1 + 2) = 0xff;
    puVar1 = (undefined4 *)((int)puVar1 + 0xf);
    iVar2 = iVar2 + 1;
  } while (iVar2 < 300);
  if (DAT_00406dc0 == 0) {
    DAT_00406da8 = 0x1e;
    DAT_00406dac = 0;
    DAT_00406dbc = 0;
    return;
  }
  if (DAT_00406dc0 != 1) {
    if (DAT_00406dc0 == 2) {
      DAT_00406da8 = 100;
      DAT_00406dac = 0;
      DAT_00406dbc = 0;
      return;
    }
    if (DAT_00406dc0 == 3) {
      DAT_00406da8 = 200;
      DAT_00406dac = 0;
      DAT_00406dbc = 0;
      return;
    }
  }
  DAT_00406da8 = 0x32;
  DAT_00406dac = 0;
  DAT_00406dbc = 0;
  return;
}



void FUN_004046cc(void)

{
  int in_EAX;
  HANDLE pvVar1;
  DWORD DVar2;
  int iVar3;
  
  if (DAT_00406d84 == 1) {
    if (in_EAX == 0) {
      if (DAT_00406dcc != 0) {
        DVar2 = 0x80;
        pvVar1 = GetCurrentProcess();
        SetPriorityClass(pvVar1,DVar2);
      }
      iVar3 = 0;
      pvVar1 = GetCurrentThread();
      SetThreadPriority(pvVar1,iVar3);
      if (DAT_00406d9c != 0) {
        ShowCursor(0);
        DVar2 = timeGetTime();
        iVar3 = DVar2 - DAT_00406d9c;
        DAT_00406da0 = DAT_00406da0 + iVar3;
        DAT_00406dfc = DAT_00406dfc + iVar3;
        DAT_00406e00 = DAT_00406e00 + iVar3;
        DAT_00406e08 = DAT_00406e08 + iVar3;
        if (DAT_00406d98 == 0) {
          DAT_00406d94 = DAT_00406d94 + iVar3;
        }
        DAT_00406d9c = 0;
      }
    }
    else if (DAT_00406d9c == 0) {
      DAT_00406d9c = timeGetTime();
      ShowCursor(1);
      if (DAT_00406dcc != 0) {
        DVar2 = 0x20;
        pvVar1 = GetCurrentProcess();
        SetPriorityClass(pvVar1,DVar2);
      }
      iVar3 = 0;
      pvVar1 = GetCurrentThread();
      SetThreadPriority(pvVar1,iVar3);
      BitBlt(DAT_004069e4,0,0,0x140,0xf0,DAT_004069e0,0,0,0xcc0020);
      return;
    }
  }
  return;
}



int lstrlenA(LPCSTR lpString)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047c8. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = lstrlenA(lpString);
  return iVar1;
}



void Sleep(DWORD dwMilliseconds)

{
                    // WARNING: Could not recover jumptable at 0x004047ce. Too many branches
                    // WARNING: Treating indirect jump as call
  Sleep(dwMilliseconds);
  return;
}



BOOL SetThreadPriority(HANDLE hThread,int nPriority)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047d4. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = SetThreadPriority(hThread,nPriority);
  return BVar1;
}



BOOL SetPriorityClass(HANDLE hProcess,DWORD dwPriorityClass)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047da. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = SetPriorityClass(hProcess,dwPriorityClass);
  return BVar1;
}



BOOL HeapFree(HANDLE hHeap,DWORD dwFlags,LPVOID lpMem)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047e0. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = HeapFree(hHeap,dwFlags,lpMem);
  return BVar1;
}



LPVOID HeapAlloc(HANDLE hHeap,DWORD dwFlags,SIZE_T dwBytes)

{
  LPVOID pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047e6. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = HeapAlloc(hHeap,dwFlags,dwBytes);
  return pvVar1;
}



HANDLE GetProcessHeap(void)

{
  HANDLE pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047ec. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = GetProcessHeap();
  return pvVar1;
}



HMODULE GetModuleHandleA(LPCSTR lpModuleName)

{
  HMODULE pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047f2. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = GetModuleHandleA(lpModuleName);
  return pHVar1;
}



HANDLE GetCurrentThread(void)

{
  HANDLE pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047f8. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = GetCurrentThread();
  return pvVar1;
}



HANDLE GetCurrentProcess(void)

{
  HANDLE pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x004047fe. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = GetCurrentProcess();
  return pvVar1;
}



void ExitProcess(UINT uExitCode)

{
                    // WARNING: Could not recover jumptable at 0x00404804. Too many branches
                    // WARNING: Subroutine does not return
                    // WARNING: Treating indirect jump as call
  ExitProcess(uExitCode);
  return;
}



int __cdecl wsprintfA(LPSTR param_1,LPCSTR param_2,...)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040480a. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = wsprintfA(param_1,param_2);
  return iVar1;
}



BOOL WaitMessage(void)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404810. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = WaitMessage();
  return BVar1;
}



BOOL TranslateMessage(MSG *lpMsg)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404816. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = TranslateMessage(lpMsg);
  return BVar1;
}



BOOL ShowWindow(HWND hWnd,int nCmdShow)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040481c. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = ShowWindow(hWnd,nCmdShow);
  return BVar1;
}



int ShowCursor(BOOL bShow)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404822. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = ShowCursor(bShow);
  return iVar1;
}



int ReleaseDC(HWND hWnd,HDC hDC)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404828. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = ReleaseDC(hWnd,hDC);
  return iVar1;
}



ATOM RegisterClassA(WNDCLASSA *lpWndClass)

{
  ATOM AVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040482e. Too many branches
                    // WARNING: Treating indirect jump as call
  AVar1 = RegisterClassA(lpWndClass);
  return AVar1;
}



void PostQuitMessage(int nExitCode)

{
                    // WARNING: Could not recover jumptable at 0x00404834. Too many branches
                    // WARNING: Treating indirect jump as call
  PostQuitMessage(nExitCode);
  return;
}



BOOL PeekMessageA(LPMSG lpMsg,HWND hWnd,UINT wMsgFilterMin,UINT wMsgFilterMax,UINT wRemoveMsg)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040483a. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = PeekMessageA(lpMsg,hWnd,wMsgFilterMin,wMsgFilterMax,wRemoveMsg);
  return BVar1;
}



int MessageBoxA(HWND hWnd,LPCSTR lpText,LPCSTR lpCaption,UINT uType)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404840. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = MessageBoxA(hWnd,lpText,lpCaption,uType);
  return iVar1;
}



HICON LoadIconA(HINSTANCE hInstance,LPCSTR lpIconName)

{
  HICON pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404846. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = LoadIconA(hInstance,lpIconName);
  return pHVar1;
}



HCURSOR LoadCursorA(HINSTANCE hInstance,LPCSTR lpCursorName)

{
  HCURSOR pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040484c. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = LoadCursorA(hInstance,lpCursorName);
  return pHVar1;
}



HDC GetDC(HWND hWnd)

{
  HDC pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404852. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = GetDC(hWnd);
  return pHVar1;
}



BOOL EndPaint(HWND hWnd,PAINTSTRUCT *lpPaint)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404858. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = EndPaint(hWnd,lpPaint);
  return BVar1;
}



int DrawTextA(HDC hdc,LPCSTR lpchText,int cchText,LPRECT lprc,UINT format)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040485e. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = DrawTextA(hdc,lpchText,cchText,lprc,format);
  return iVar1;
}



LRESULT DispatchMessageA(MSG *lpMsg)

{
  LRESULT LVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404864. Too many branches
                    // WARNING: Treating indirect jump as call
  LVar1 = DispatchMessageA(lpMsg);
  return LVar1;
}



LRESULT DefWindowProcA(HWND hWnd,UINT Msg,WPARAM wParam,LPARAM lParam)

{
  LRESULT LVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040486a. Too many branches
                    // WARNING: Treating indirect jump as call
  LVar1 = DefWindowProcA(hWnd,Msg,wParam,lParam);
  return LVar1;
}



HWND CreateWindowExA(DWORD dwExStyle,LPCSTR lpClassName,LPCSTR lpWindowName,DWORD dwStyle,int X,
                    int Y,int nWidth,int nHeight,HWND hWndParent,HMENU hMenu,HINSTANCE hInstance,
                    LPVOID lpParam)

{
  HWND pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404870. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = CreateWindowExA(dwExStyle,lpClassName,lpWindowName,dwStyle,X,Y,nWidth,nHeight,hWndParent,
                           hMenu,hInstance,lpParam);
  return pHVar1;
}



HDC BeginPaint(HWND hWnd,LPPAINTSTRUCT lpPaint)

{
  HDC pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404876. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = BeginPaint(hWnd,lpPaint);
  return pHVar1;
}



BOOL AdjustWindowRectEx(LPRECT lpRect,DWORD dwStyle,BOOL bMenu,DWORD dwExStyle)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040487c. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = AdjustWindowRectEx(lpRect,dwStyle,bMenu,dwExStyle);
  return BVar1;
}



DWORD timeGetTime(void)

{
  DWORD DVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404882. Too many branches
                    // WARNING: Treating indirect jump as call
  DVar1 = timeGetTime();
  return DVar1;
}



BOOL TextOutA(HDC hdc,int x,int y,LPCSTR lpString,int c)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404888. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = TextOutA(hdc,x,y,lpString,c);
  return BVar1;
}



COLORREF SetTextColor(HDC hdc,COLORREF color)

{
  COLORREF CVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040488e. Too many branches
                    // WARNING: Treating indirect jump as call
  CVar1 = SetTextColor(hdc,color);
  return CVar1;
}



UINT SetDIBColorTable(HDC hdc,UINT iStart,UINT cEntries,RGBQUAD *prgbq)

{
  UINT UVar1;
  
                    // WARNING: Could not recover jumptable at 0x00404894. Too many branches
                    // WARNING: Treating indirect jump as call
  UVar1 = SetDIBColorTable(hdc,iStart,cEntries,prgbq);
  return UVar1;
}



int SetBkMode(HDC hdc,int mode)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x0040489a. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = SetBkMode(hdc,mode);
  return iVar1;
}



COLORREF SetBkColor(HDC hdc,COLORREF color)

{
  COLORREF CVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048a0. Too many branches
                    // WARNING: Treating indirect jump as call
  CVar1 = SetBkColor(hdc,color);
  return CVar1;
}



HGDIOBJ SelectObject(HDC hdc,HGDIOBJ h)

{
  HGDIOBJ pvVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048a6. Too many branches
                    // WARNING: Treating indirect jump as call
  pvVar1 = SelectObject(hdc,h);
  return pvVar1;
}



int SaveDC(HDC hdc)

{
  int iVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048ac. Too many branches
                    // WARNING: Treating indirect jump as call
  iVar1 = SaveDC(hdc);
  return iVar1;
}



BOOL RestoreDC(HDC hdc,int nSavedDC)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048b2. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = RestoreDC(hdc,nSavedDC);
  return BVar1;
}



BOOL PatBlt(HDC hdc,int x,int y,int w,int h,DWORD rop)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048b8. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = PatBlt(hdc,x,y,w,h,rop);
  return BVar1;
}



BOOL GetTextExtentPoint32A(HDC hdc,LPCSTR lpString,int c,LPSIZE psizl)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048be. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = GetTextExtentPoint32A(hdc,lpString,c,psizl);
  return BVar1;
}



BOOL DeleteObject(HGDIOBJ ho)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048c4. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = DeleteObject(ho);
  return BVar1;
}



BOOL DeleteDC(HDC hdc)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048ca. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = DeleteDC(hdc);
  return BVar1;
}



HFONT CreateFontIndirectA(LOGFONTA *lplf)

{
  HFONT pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048d0. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = CreateFontIndirectA(lplf);
  return pHVar1;
}



HBITMAP CreateDIBSection(HDC hdc,BITMAPINFO *lpbmi,UINT usage,void **ppvBits,HANDLE hSection,
                        DWORD offset)

{
  HBITMAP pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048d6. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = CreateDIBSection(hdc,lpbmi,usage,ppvBits,hSection,offset);
  return pHVar1;
}



HDC CreateCompatibleDC(HDC hdc)

{
  HDC pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048dc. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = CreateCompatibleDC(hdc);
  return pHVar1;
}



HBITMAP CreateCompatibleBitmap(HDC hdc,int cx,int cy)

{
  HBITMAP pHVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048e2. Too many branches
                    // WARNING: Treating indirect jump as call
  pHVar1 = CreateCompatibleBitmap(hdc,cx,cy);
  return pHVar1;
}



BOOL BitBlt(HDC hdc,int x,int y,int cx,int cy,HDC hdcSrc,int x1,int y1,DWORD rop)

{
  BOOL BVar1;
  
                    // WARNING: Could not recover jumptable at 0x004048e8. Too many branches
                    // WARNING: Treating indirect jump as call
  BVar1 = BitBlt(hdc,x,y,cx,cy,hdcSrc,x1,y1,rop);
  return BVar1;
}


