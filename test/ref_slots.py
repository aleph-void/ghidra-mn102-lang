#!/usr/bin/env python3
"""Run a reference disassembler over a corpus of 8-byte slots and print "<slot-offset> <len> <text>"
lines, the format test/compare.py reads.
  ref_slots.py <tool>:<arch> <corpus.bin> <out.txt> [workdir]
    tool unidasm: MAME unidasm -arch <arch> (mn10300, mn10200)
    tool objdump: GNU objdump -b binary -m <arch> -D ($OBJDUMP; mn10300, am33, am33-2, mn10200)
Both decode a stream, so each slot is copied into a 16-byte cell followed by 8 nop bytes (0xcb
on MN10300, 0xf6 on MN10200) that resynchronise the stream before the next cell (the longest
instruction is 7 bytes); only the instruction at the start of each cell is kept, and branch
targets are moved from the cell address to the slot address."""
import os, re, subprocess, sys, tempfile
tool, arch = sys.argv[1].split(':')
src, outp = sys.argv[2], sys.argv[3]
work = sys.argv[4] if len(sys.argv) > 4 else tempfile.gettempdir()
nop = b'\xf6' if arch == 'mn10200' else b'\xcb'
data = open(src, 'rb').read()
n = len(data) // 8
cells = b''.join(data[i * 8:i * 8 + 8] + nop * 8 for i in range(n))
tmp = os.path.join(work, 'unidasm_cells.bin')
open(tmp, 'wb').write(cells)
if tool == 'unidasm':
    res = subprocess.run(['unidasm', '-arch', arch, tmp], capture_output=True, text=True).stdout
else:
    od = os.environ.get('OBJDUMP', os.path.expanduser('~/.cache/ghidra-rare-scratch/tools/binutils-all/bin/objdump'))
    res = subprocess.run([od, '-b', 'binary', '-m', arch, '-D', '-z', tmp], capture_output=True, text=True).stdout
    # "   10:\tf8 fe 04 \tadd\t4,sp" -> unidasm-like "10: f8 fe 04  add 4,sp"
    lines = []
    for l in res.splitlines():
        mo = re.match(r'^\s*([0-9a-f]+):\t((?:[0-9a-f]{2} )+)\s*\t?(.*)$', l)
        if not mo:
            continue
        if mo.group(3).strip() == '' and lines:
            # continuation line with more bytes of the previous instruction
            a, b, t = lines[-1]
            lines[-1] = (a, b + mo.group(2), t)
        else:
            lines.append((mo.group(1), mo.group(2), mo.group(3).replace(chr(9), ' ')))
    lines = [f'{a}: {b} {t}' for a, b, t in lines]
    res = '\n'.join(lines)
os.unlink(tmp)
BRANCH = {'jmp', 'call', 'calls', 'jsr'}
got = {}
for line in res.splitlines():
    m = re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(.*)$', line)
    if not m:
        continue
    off = int(m.group(1), 16)
    if off % 16:
        continue
    i = off // 16
    # branch targets were computed at the cell address; move them to the slot address
    txt = m.group(3).strip()
    if tool == 'unidasm' and arch == 'mn10200':
        # MAME's mn10200 disassembler prints $hex; unknown opcodes as dc.b
        if txt.startswith('dc.b'):
            txt = '(bad)'
        txt = re.sub(r'\$([0-9a-f]+)', r'0x\1', txt)
    mn = txt.split(' ')[0]
    if mn in BRANCH or (mn.startswith('b') and mn not in ('bset', 'bclr', 'btst', 'break', 'bsch')) \
            or mn.startswith('fb') or mn.startswith('tb'):
        mask = 0xffffff if arch == 'mn10200' else 0xffffffff
        fix = lambda t: '0x%x' % ((int(t.group(1), 16) - i * 8) & mask)
        if mn.startswith('tb'):
            txt = re.sub(r'0x([0-9a-f]+)$', fix, txt)          # target is the last operand
        else:
            txt = re.sub(r'0x([0-9a-f]+)', fix, txt, count=1)   # target is the first operand
    got[i] = (len(m.group(2).split()), txt)
with open(outp, 'w') as f:
    for i in range(n):
        ln, txt = got.get(i, (0, '(bad)'))
        f.write(f'{i * 8:08x} {ln} {txt}\n')
