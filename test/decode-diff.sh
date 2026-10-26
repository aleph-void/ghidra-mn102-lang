#!/usr/bin/env bash
# Decode differential: test/decode-diff.sh <outdir>
# Two corpora of 8-byte slots (every first byte, every two-byte prefix of the F0-F7 pages, the F3
# FE/FF and F5 three-byte prefixes, all with random tails, plus 40,000 and 200,000 random slots)
# are decoded by Ghidra and by GNU objdump -m mn10200 ($OBJDUMP) and MAME unidasm -arch mn10200
# (skipped when not installed). Numbers are compared as 24-bit values; every difference must
# fall in an explained class (test/explain_*.py).
set -euo pipefail
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
HERE=$(cd "$(dirname "$0")" && pwd)
OUTD=$(readlink -m "${1:-${TMPDIR:-/tmp}/mn102-decode}")
mkdir -p "$OUTD"
rc=0
for seed in 1:40000 2:200000; do
	n=${seed%%:*}
	c=$OUTD/corpus$n.bin
	python3 "$HERE/gen_corpus.py" "$c" "$n" "${seed##*:}" >/dev/null
	g=$OUTD/gh_$n.txt
	"$HERE/ghidra-slots.sh" MN102:BE:24:default "$c" 8 "$g"
	python3 "$HERE/ref_slots.py" objdump:mn10200 "$c" "$OUTD/od_$n.txt" "$OUTD"
	python3 "$HERE/compare.py" "$g" "$OUTD/od_$n.txt" "$c" --bits 24 --explain "$HERE/explain_objdump.py" > "$OUTD/cmp_od_$n.txt" || rc=1
	echo "objdump -m mn10200, corpus $n: $(head -1 "$OUTD/cmp_od_$n.txt")"
	if command -v unidasm >/dev/null; then
		python3 "$HERE/ref_slots.py" unidasm:mn10200 "$c" "$OUTD/ud_$n.txt" "$OUTD"
		python3 "$HERE/compare.py" "$g" "$OUTD/ud_$n.txt" "$c" --bits 24 --explain "$HERE/explain_mame.py" > "$OUTD/cmp_mame_$n.txt" || rc=1
		echo "MAME unidasm -arch mn10200, corpus $n: $(head -1 "$OUTD/cmp_mame_$n.txt")"
	else
		echo "MAME unidasm not installed: skipped"
	fi
done
exit $rc
