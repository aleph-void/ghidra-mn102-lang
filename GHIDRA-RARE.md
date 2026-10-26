# Matsushita/Panasonic MN10200 (MN102L/MN102H) processor module for Ghidra

SLEIGH processor module for the MN10200 family, the 24-bit predecessor of the MN10300: the
MN102L instruction set plus the MN102H extensions (bit test/branch, bit set/clear on memory,
`mulq` hardware-multiplier instructions, `pxst`). Target: **Ghidra 12.1.4** (also builds for
12.1.3 and 12.2).

This is the community module [Pokechu22/ghidra-mn102-lang](https://github.com/Pokechu22/ghidra-mn102-lang)
by Pokechu22 (Apache-2.0, written for the GameCube DVD drive's MN102H60), verified and fixed by
Ghidra-Rare. See [CREDITS.md](CREDITS.md) for provenance and the list of changes.

## Language

One language, `MN102:BE:24:default` (the ID is upstream's; the processor is little-endian and the
language is defined as such). 213 constructors.

- **Registers.** d0-d3, a0-a3 (a3 is the stack pointer; upstream called it SP, objdump and MAME
  `a3`), pc, mdr (16 bits), psw with the 16-bit flags VF/CF/NF/ZF and the 24-bit flags
  VX/CX/NX/ZX kept as separate registers.
- **ELF.** Opinion for `e_machine` 90 and the old 0xdead; relocation handler for the eight
  MN10200 relocation types (`R_MN10200_8/16/24/32`, PC-relative 8/16/24 relative to the end of
  the field).

## Semantics

Everything is p-code except `break` (debugger), `syscall` (simulator call) and `pxst` (switches
the saturation mode of the next add/sub; the available documents do not describe it further).

- Add, subtract and compare set all eight flags (16-bit and 24-bit carry, overflow, sign,
  zero), including the immediate forms; `addc`/`subc` keep ZF only if it was set (multi-word
  zero test). Logic operations, `not`, `btst`, one-bit shifts and rotates work on the low 16
  bits, keep the upper 8 bits and set NF/ZF with VF and CF cleared. `mul`/`mulu` put the 32-bit
  product's high half in MDR; `divu` divides MDR:Dn by Dm and sets VF on a zero divisor or a
  quotient wider than 16 bits.
- Loads sign- or zero-extend as their mnemonics say (`mov` 16-bit sign-extending, `movb`,
  `movbu`, `movx` 24-bit); `jsr` pushes the 24-bit return address in a 4-byte slot and `rts`
  pops it; `rti` restores PSW and PC and drops 6 bytes.
- MN102H: `tbz`/`tbnz` test a memory bit and branch, `bset`/`bclr` set or clear one, the
  `mulq`/`mulql`/`mulqh` forms as upstream read them from the MN102H LSI manual's tables.

## Calling convention

gcc's mn10200 port (gcc 3.3, `config/mn10200`): the first two argument words in D0 and D1, the
rest on the stack after the 4-byte return-address slot; results in D0, 24-bit pointers in A0;
D2, D3, A1, A2 preserved.

## Testing

```
GHIDRA_INSTALL_DIR=<ghidra with this module in Ghidra/Processors/MN102> test/build-jar.sh
GHIDRA_INSTALL_DIR=... test/run-tests.sh [--real <workdir>]     (MN10200_BINUTILS for --real)
```

1. The spec compiles (`MN102.sla` 16 KB).
2. `test/emu-test.sh`: 30 emulator cases with hand-computed results, then the same run with one
   wrong expectation, which must be the only failure.
3. `test/every-entry.sh`: every constructor is reached (213/213).
4. `test/decode-diff.sh`: the decode differential against GNU objdump 2.45 (`-m mn10200`) and
   MAME `unidasm -arch mn10200`.
5. `--real`: `test/real-tests.sh` assembles `test/real/routines.s` with GNU as/ld, imports the
   executable and the object file, decompiles them and compares the listing with objdump.

## Results

### Decode

Two corpora of 8-byte slots: every first byte, every two-byte prefix of the F0-F7 pages, the
F3 FE/FF and F5 three-byte prefixes, with random tails, plus 40,000 resp. 200,000 random slots
(295,296 slots). Numbers are compared as 24-bit values.

| Reference | Slots | Exact | Semantic | Both invalid | Explained | Unexplained |
|---|---|---|---|---|---|---|
| objdump `-m mn10200` | 295,296 | 137,027 | 78,796 | 11,061 | 68,412 | 0 |
| MAME `unidasm -arch mn10200` | 295,296 | 239,741 | 39,510 | 11,061 | 4,984 | 0 |

Every constructor is reached: 213/213.

Explained differences:

- binutils (54,338): the 8- and 16-bit displacements and immediates the manual sign-extends
  (`d8`, `d16`, `imm8`, branch displacements) are printed unsigned, and branch targets are
  computed with the unsigned displacement (`bne` back to 0x80000 prints `bne 80100`). MAME's
  disassembler and its MN10200 core sign-extend them, and so does the hardware (upstream's
  GameCube memset example loops back with `bcs` and a negative displacement).
- binutils (14,074): the MN102H/MN102L-extended instructions (bit test/branch, bit set/clear on
  memory, `mulq`, `pxst`) are not in binutils' MN10200 table; MAME decodes them.
- MAME bugs: `bset`/`bclr (abs24)bit` read the address one byte early (from the opcode byte;
  its own `tbz`/`tbnz (abs24)` use the right bytes); `mulq`/`mulql`/`mulqh Dm,Dn` take Dm from
  bits 4-3 (so it is always d0 or d1); `bset`/`bclr imm8,(abs16)` reported as 6 bytes although
  it reads 5; no decode of `break` (0xff) or `syscall` (F0 10), which binutils decodes. Display
  differences: `move` for `mov imm16,An`, bit masks in hex without `0x`, the `mulql`/`mulqh`
  immediate printed signed (no available manual says which; see Unverified).

### Semantics

30/30 emulator cases (`test/emu/cases.txt`): 16- and 24-bit carry and overflow, borrow,
`addc` with the sticky ZF, `subc` operand order, `cmp` with `beq` and the 24-bit `bltx`,
`mul`/`mulu`/`divu` (with MDR and overflow), logic keeping the upper byte, `asr`/`lsr`/`rol`/
`ror`, sign- and zero-extending loads, 24-bit `movx`, absolute and displacement stores,
`jsr`/`rts` with the stack slot, `rti`, PSW round trip, `ext`/`extx*`, `btst`/`bset`,
`addnf` leaving the flags, immediate sign extension, MN102H `tbz (d8,An)` and `bset (abs16)bit`.
Broken expectation detected.

### Real code

No freely licensed MN10200 binaries were found (the GameCube drive firmware is Nintendo's), and
GCC dropped the mn10200 port in 2003, so the real-code check uses `test/real/routines.s`
(fill, length, a 16-bit multiply and a jump-table dispatch, written to gcc's convention),
assembled and linked with GNU binutils 2.45: imported without forcing the language (ELF
opinion), 54 instructions, all identical to objdump apart from objdump's unsigned-displacement
bug (5), 0 bad instructions, 5/5 functions decompiled, the jump table recovered as a `switch`;
the object file's 14 relocations applied.

## Doesn't work

- `pxst` is a p-code operation: it changes how the following add/sub saturates, which none of
  the available documents describes.
- `break` and `syscall` are p-code operations (debugger and simulator traps).

## Unverified

- The MN102H extensions (bit operations, `mulq` forms, `pxst`) against hardware or the MN102H
  instruction manual: only upstream's reading of the MN102H LSI manual's instruction tables and
  MAME's disassembler (with the bugs above) cover them. Whether the `mulql`/`mulqh` immediates and
  the `mulq` operands are signed is not documented in the available sources.
- Real compiled code: no freely licensed binaries, no maintained compiler.
- The calling convention of Panasonic's own compiler (the GameCube firmware's).
- DWARF register mapping: there is no compiler to produce DWARF for MN10200 any more.
