#!/usr/bin/env bash
# Every-entry test: test/every-entry.sh [outdir]
# For each language, CoverageCheck.java builds instructions from every root-table pattern of the
# SLEIGH decision tree (random free bits) and lists the constructors (in every subtable) that no
# decode reached, i.e. shadowed or unreachable entries.
set -euo pipefail
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
HERE=$(cd "$(dirname "$0")" && pwd)
OUTD=$(readlink -m "${1:-${TMPDIR:-/tmp}/mn102-every}")
mkdir -p "$OUTD"
head -c 64 /dev/zero > "$OUTD/z.bin"
rc=0
for v in default; do
	"$HERE/ghidra-script.sh" raw MN102:BE:24:default "$OUTD/z.bin" CoverageCheck.java "$OUTD/cov_$v.txt" 64 1
	echo "$v: $(tail -1 "$OUTD/cov_$v.txt")"
	grep -q ' 0 unreached' "$OUTD/cov_$v.txt" || { grep unreached "$OUTD/cov_$v.txt" | head; rc=1; }
done
exit $rc
