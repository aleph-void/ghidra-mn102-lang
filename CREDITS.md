# Credits

## Upstream

This module is the MN102 processor specification from
[Pokechu22/ghidra-mn102-lang](https://github.com/Pokechu22/ghidra-mn102-lang), imported at commit
`669bee8581e7314353d50dc9e1fd832ca42e55ad` (2020-12-16, "Fix README link typo"). License:
Apache License 2.0 (`LICENSE.txt` is Ghidra's module license template, unchanged; `LICENSE` holds
the Apache-2.0 text).

Original author (from the upstream history):

- Pokechu22 ([@Pokechu22](https://github.com/Pokechu22)): the specification, its instruction
  decode (including the MN102H extensions read from the MN102H LSI manuals and the corrected
  `MOVB Dm,(An)` encoding), the register and I/O symbols of `MN102.pspec`, the manual index and
  the README's notes on the manuals and the GameCube drive firmware.

Upstream files keep their copyright and license headers. Changes made here are also licensed
under Apache-2.0 and exist as commits on top of the upstream history (branch `ghidra-rare`).

No other MN10200 module for Ghidra was found (GitHub searches for "ghidra mn10200",
"mn10200 sleigh", "ghidra mn102" and code search for `MN10200` in `.slaspec` files). A closed,
unmerged upstream pull request (AKuHAK, a GitHub Actions build) is not used.

## Reference material

- GNU objdump 2.45 (`-m mn10200`) and GNU as/ld 2.45 (`mn10200-elf`) as decode oracle and to
  build test programs. binutils is GPL; nothing from it is copied into this module.
- MAME's MN10200 disassembler and CPU core (`src/devices/cpu/mn10200`, BSD-3-Clause,
  Olivier Galibert, R. Belmont, hap) as the second decode oracle and the behavioural reference
  for flags and operations. Not copied into this module.
- gcc 3.3's `config/mn10200/mn10200.h` for the calling convention.
- *MN102L Series Instruction Manual* (Pub.No.12250-030E, front matter only available) for the
  flag notation.

## Ghidra-Rare changes

Commits on branch `ghidra-rare` (on top of upstream `669bee8`):

1. `067890e` Registers and flags in the register space (the flags were in a RAM "hack" space),
   A3 as the stack pointer's name, flag semantics for every add/sub/cmp form (the immediate forms
   set none), SUBC (operands reversed, wrong flags), ADDC/SUBC sticky ZF, DIVU overflow, logic and
   shift flags, JSR/RTS stack effects, BREAK/PXST/SYSCALL as p-code operations instead of
   `unimpl`; decode fixes found by the objdump/MAME differential (`(0,An)` display, signed
   `mov` immediates, `BLCR` typo, `mulql`/`mulqh` immediate encodings).
2. `4f26bbb` Calling convention of gcc's mn10200 port; the register space removed from the
   compiler spec's global ranges (the cause of the README's "registers show up in
   decompilation").
3. `2761ef4` ELF opinion (`e_machine` 90 and 0xdead) and `MN10200_ElfRelocationHandler`.
4. `24bdd26` README: release zips, ELF import, state of the two known issues.

Ghidra-Rare-only additions: `GHIDRA-RARE.md`, this file, `LICENSE`, `build.gradle` (upstream had
none; it was installed by copying into `Ghidra/Processors`), `extension.properties` and
everything under `test/`.
