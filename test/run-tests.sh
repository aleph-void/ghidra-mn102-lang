#!/usr/bin/env bash
# MN10200 module test suite.   test/run-tests.sh [--real <workdir>]
# Needs GHIDRA_INSTALL_DIR (a Ghidra with this module under Ghidra/Processors/MN102 and its jar
# built by test/build-jar.sh), python3 and GNU objdump with the mn10200 target (OBJDUMP; binutils
# configured with --enable-targets=all). MAME unidasm is used when installed.
# --real <workdir> also assembles and checks test/real/routines.s (needs MN10200_BINUTILS).
set -euo pipefail
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
HERE=$(cd "$(dirname "$0")" && pwd)
MOD=$(cd "$HERE/.." && pwd)
OUT=${TMPDIR:-/tmp}/mn102-tests
mkdir -p "$OUT"
REAL=
[[ ${1:-} == --real ]] && REAL=$2

echo "## 1. spec compiles"
"$GHIDRA_INSTALL_DIR/support/sleigh" "$MOD/data/languages/MN102.slaspec" "$OUT/MN102.sla" >"$OUT/sleigh.log" 2>&1 \
	|| { tail -20 "$OUT/sleigh.log"; exit 1; }
echo "  MN102.slaspec: $(stat -c %s "$OUT/MN102.sla") bytes"

echo "## 2. emulator cases (and one deliberately broken expectation)"
"$HERE/emu-test.sh" "$OUT"
"$HERE/emu-test.sh" --broken "$OUT"

echo "## 3. every constructor reached"
"$HERE/every-entry.sh" "$OUT"

echo "## 4. decode differential (objdump, MAME)"
"$HERE/decode-diff.sh" "$OUT/decode"

if [[ -n $REAL ]]; then
	echo "## 5. assembled programs"
	"$HERE/real-tests.sh" "$REAL"
fi
echo "all tests passed"
