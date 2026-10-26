#!/usr/bin/env bash
# Real-code check on assembled programs:  test/real-tests.sh <workdir>
# No freely licensed MN10200 binaries and no maintained compiler exist (GCC dropped the port in
# 2003), so test/real/routines.s (gcc calling convention, a 24-bit-bounded jump table) is
# assembled and linked with GNU as/ld for mn10200-elf (MN10200_BINUTILS: their bin directory),
# imported without forcing the language, analysed, decompiled, and its listing compared with
# objdump -d (24-bit values, test/explain_objdump.py). The object file is imported as well
# (relocations).
set -euo pipefail
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
: "${MN10200_BINUTILS:?set MN10200_BINUTILS to the bin directory of binutils for mn10200-elf}"
HERE=$(cd "$(dirname "$0")" && pwd)
W=$(readlink -m "$1"); mkdir -p "$W"
B=$MN10200_BINUTILS
OBJDUMP=${OBJDUMP:-$B/mn10200-elf-objdump}
"$B/mn10200-elf-as" "$HERE/real/routines.s" -o "$W/routines.o"
"$B/mn10200-elf-ld" -Ttext=0x80000 -Tdata=0x84000 "$W/routines.o" -o "$W/routines.elf"
rc=0
for f in routines.elf routines.o; do
	echo "== $f"
	"$HERE/ghidra-elf.sh" "$W/$f" RealCheck.java "$W/$f.summary" "$W/$f.dis" "$W/$f.c" 60 2>/dev/null
	grep -E '^(language|functions|instructions|bad-instruction|error bookmarks|relocations|decompile|functions whose)' "$W/$f.summary"
	grep -q '^language: MN102:BE:24:default ' "$W/$f.summary" || { echo "wrong language"; rc=1; }
	grep -q '^bad-instruction bookmarks: 0 ' "$W/$f.summary" || rc=1
	grep -q ', 0 failed,' "$W/$f.summary" || rc=1
done
# listing vs objdump at the same addresses (the linked file)
awk '{print $1, length($2) / 2, substr($0, index($0, $3))}' "$W/routines.elf.dis" > "$W/gh.txt"
"$OBJDUMP" -d "$W/routines.elf" | python3 -c '
import re, sys
out, last = [], None
for l in sys.stdin:
    m = re.match(r"^\s*([0-9a-f]+):\t((?:[0-9a-f]{2} )+)\s*(?:\t(.*))?$", l)
    if not m:
        continue
    if m.group(3) is None:
        if out: out[-1][1] += len(m.group(2).split())
        continue
    t = re.sub(r"\s*<[^>]*>", "", m.group(3)).replace("\t", " ")
    mn, _, ops = t.partition(" ")
    if mn in ("jmp", "jsr") or (mn.startswith("b") and mn not in ("bset", "bclr", "btst", "break")):
        ops = re.sub(r"^([0-9a-f]+)$", r"0x\1", ops.strip())
    ops = re.sub(r"\((?![ad][0-3]\))([0-9a-f]{3,})\)", r"(0x\1)", ops)
    out.append([int(m.group(1), 16), len(m.group(2).split()), (mn + " " + ops).strip()])
for a, n, t in out:
    print("%08x %d %s" % (a, n, t))
' > "$W/od.txt"
python3 "$HERE/compare.py" "$W/gh.txt" "$W/od.txt" --bits 24 --explain "$HERE/explain_objdump.py" | tee "$W/cmp.txt" | head -6
grep -q ' unexplained 0' "$W/cmp.txt" || rc=1
exit $rc
