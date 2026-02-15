# String Dump from 99.exe

## Findings
- **Plain Text Found**: The executable contains plain text Shift-JIS strings, not just XORed ones.
- **Offset**: `0x4115` contains `Enter` (ASCII), followed by `で` (`82 C5`)?
  - Actually, `82 C5` is Shift-JIS for `で`.
    - Wait, I checked. `82 C5` is `で` in some tables? Usually `82 68`.
    - `82 C5` is `ﾅ`. No. Shift-JIS is 2 bytes.
    - Let's re-verify the bytes: `82 C5`.
    - Standard Hiragana range is `82 9F - 82 F1`. `で` is `82 C5`. YES!
    - So `82 68` was wrong (maybe EUC-JP or something else).

- **Tokkun (Training)**:
  - Expected: `93 42 8C 56`.
  - Found: `93 C1 8C 50`.
  - Wait, if `Tokkun` is defined as `93 4C`...
  - Let's just trust the bytes found in file are valid Shift-JIS and dump them.

- **Shikkaku (Disqualified)**:
  - Bytes `8E B8 8A 69`.
  - `8E B8` = 失.
  - `8A 69` = 格.
  - This matches perfectly.

## Conclusions
The binary contains **Standard Shift-JIS** encoded strings for UI elements. No complex XOR obfuscation seems necessary for these menu strings.

## Next Steps
Use `dump_strings.py` to extract all valid Shift-JIS strings from the binary to document all game text.
