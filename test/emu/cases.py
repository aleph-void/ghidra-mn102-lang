#!/usr/bin/env python3
"""Emulator cases for the MN10200 module. Each case is assembly (assembled once with GNU as for
mn10200-elf and linked at 0x1000; the bytes are kept in cases.txt so the test needs no
toolchain; MN102H/L-extended instructions, which gas does not know, are written as .byte),
initial registers/memory, and results worked out by hand from the instruction descriptions
(the MN10200 manual's operation and flag rules as MAME's MN10200 core implements them:
16-bit flags VF/CF/NF/ZF, 24-bit flags VX/CX/NX/ZX).

  cases.py --assemble <as> <ld> <objcopy>   regenerate cases.txt (needs mn10200-elf binutils)
  cases.py --broken                          print cases.txt with one expectation made wrong
Execution starts at 0x1000 and stops at label 'end'. A3 (sp) starts at 0x9800. The value END
in a memory setting stands for the address of 'end'."""
import os, subprocess, sys, tempfile

END = -1
CASES = [
 ('add_carry16', 'add d0,d1', {'D0': 0x00ffff, 'D1': 1},
  {'D1': 0x010000, 'CF': 1, 'ZF': 1, 'NF': 0, 'VF': 0, 'CX': 0, 'ZX': 0, 'NX': 0, 'VX': 0}),
 ('add_overflow24', 'add 1,d0', {'D0': 0x7fffff},
  {'D0': 0x800000, 'VX': 1, 'NX': 1, 'CX': 0, 'ZX': 0, 'CF': 1, 'ZF': 1, 'VF': 0}),
 ('sub_borrow', 'sub d1,d0', {'D0': 1, 'D1': 2},
  {'D0': 0xffffff, 'CF': 1, 'CX': 1, 'NF': 1, 'NX': 1, 'ZF': 0, 'ZX': 0}),
 ('addc_sticky_z', 'addc d1,d0', {'D0': 0xffff, 'D1': 0, 'CF': 1, 'ZF': 1},
  {'D0': 0x010000, 'CF': 1, 'ZF': 1, 'ZX': 0}),
 ('subc_order', 'subc d1,d0', {'D0': 5, 'D1': 3, 'CF': 1}, {'D0': 1, 'CF': 0, 'ZF': 0}),
 ('cmp_beq', 'cmp 5,d0\n beq hit\n mov 1,d1\n bra end\nhit: mov 2,d1', {'D0': 5}, {'D1': 2, 'ZF': 1}),
 ('cmp24_bltx', 'cmp 0x800000,d0\n bltx hit\n mov 1,d1\n bra end\nhit: mov 2,d1', {'D0': 0x7fffff},
  {'D1': 1, 'VX': 1, 'NX': 1}),
 ('mul_signed', 'mul d0,d1', {'D0': 0xfffe, 'D1': 3}, {'D1': 0xfffffa, 'MDR': 0xffff, 'NF': 1, 'ZF': 0}),
 ('mulu', 'mulu d0,d1', {'D0': 0xffff, 'D1': 2}, {'D1': 0x01fffe, 'MDR': 1}),
 ('divu', 'divu d0,d1', {'MDR': 1, 'D1': 0, 'D0': 3}, {'D1': 0x5555, 'MDR': 1, 'VF': 0}),
 ('divu_overflow', 'divu d0,d1', {'MDR': 5, 'D1': 0, 'D0': 2}, {'VF': 1, 'D1': 0, 'MDR': 5}),
 ('and_keeps_upper', 'and 15,d0', {'D0': 0x12ff34}, {'D0': 0x120004, 'ZF': 0, 'NF': 0}),
 ('or_xor', 'or 128,d0\n xor 0x0081,d0', {'D0': 0x120000}, {'D0': 0x120001}),
 ('asr', 'asr d0', {'D0': 0x128001}, {'D0': 0x12c000, 'CF': 1, 'NF': 1}),
 ('lsr', 'lsr d0', {'D0': 0x128001}, {'D0': 0x124000, 'CF': 1, 'NF': 0}),
 ('rol_carry', 'rol d0', {'D0': 0x008000, 'CF': 1}, {'D0': 0x000001, 'CF': 1}),
 ('ror_zero', 'ror d0', {'D0': 0x000001}, {'D0': 0, 'CF': 1, 'ZF': 1}),
 ('movb_movbu', 'movb (0,a0),d0\n movbu (0,a0),d1', {'A0': 0x9000, 'ram:9000/1': 0x80},
  {'D0': 0xffff80, 'D1': 0x80}),
 ('mov_load_sext16', 'mov (a0),d1', {'A0': 0x9000, 'ram:9000/2': 0x8001}, {'D1': 0xff8001}),
 ('movx_store24', 'movx d0,(4,a3)\n movx (4,a3),d1', {'D0': 0x123456},
  {'ram:9804/3': 0x123456, 'D1': 0x123456}),
 ('mov_abs16_store', 'mov d0,(0x9200)\n mov a0,(4,a1)', {'D0': 0x123456, 'A0': 0xabcdef, 'A1': 0x9300},
  {'ram:9200/2': 0x3456, 'ram:9304/3': 0xabcdef}),
 ('jsr_rts', 'jsr func\n bra end\nfunc: add 1,d0\n rts', {'D0': 41},
  {'D0': 42, 'A3': 0x9800, 'ram:97fc/3': 0x1003}),
 ('rti', 'rti', {'ram:9800/2': 0x000f, 'ram:9802/3': END},
  {'A3': 0x9806, 'ZF': 1, 'NF': 1, 'CF': 1, 'VF': 1, 'ZX': 0}),
 ('psw_roundtrip', 'mov psw,d0\n mov d1,psw', {'ZF': 1, 'CX': 1, 'D1': 0x000a},
  {'D0': 0x41, 'VF': 1, 'NF': 1, 'ZF': 0, 'CX': 0}),
 ('ext_extx', 'ext d0\n extxbu d1\n extx d2', {'D0': 0x8000, 'D1': 0x1ff, 'D2': 0x008000},
  {'MDR': 0xffff, 'D1': 0xff, 'D2': 0xff8000}),
 ('btst_bset', 'btst 0x10,d0\n bset d1,(a0)', {'D0': 0x10, 'D1': 0x02, 'A0': 0x9000, 'ram:9000/1': 0x40},
  {'ZF': 1, 'ram:9000/1': 0x42}),
 ('addnf_keeps_flags', 'addnf 8,a3', {'ZF': 1, 'CF': 1}, {'A3': 0x9808, 'ZF': 1, 'CF': 1}),
 ('mov_imm_sext', 'mov -2,d0\n mov -32768,d1\n mov 0x8000,a0\n mov 0x8000,d2', {}, {'D0': 0xfffffe, 'D1': 0xff8000, 'A0': 0x008000, 'D2': 0x008000}),
 ('tbz_d8_taken', '.byte 0xf5,0x83,0x04,2\n mov 1,d1\nhit: mov 2,d2', {'A0': 0x9000, 'ram:9004/1': 0x00},
  {'D1': 0, 'D2': 2, 'ZF': 1}),
 ('bset_abs16_bit', '.byte 0xf5,0xd5,0x00,0x90', {'ram:9000/1': 0x01}, {'ram:9000/1': 0x21}),
]

def asm(case, tools, work):
    name, src = case[0], case[1]
    s = f'\t.text\n\t.global _start\n_start:\n\t{src}\nend:\n\tnop\n'
    p = os.path.join(work, name)
    open(p + '.s', 'w').write(s)
    subprocess.run([tools[0], p + '.s', '-o', p + '.o'], check=True)
    subprocess.run([tools[1], '-Ttext=0x1000', '-e', '_start', p + '.o', '-o', p + '.elf'], check=True)
    subprocess.run([tools[2], '-O', 'binary', '-j', '.text', p + '.elf', p + '.bin'], check=True)
    code = open(p + '.bin', 'rb').read()
    nm = subprocess.run([tools[1].replace('-ld', '-nm'), p + '.elf'], capture_output=True, text=True).stdout
    end = [int(l.split()[0], 16) for l in nm.splitlines() if l.endswith(' end')][0]
    return code[:-1], end - 0x1000

def emit(rows, broken=False):
    out = ['# generated by test/emu/cases.py; do not edit']
    for i, (name, src, code, main, st, ex) in enumerate(rows):
        out.append(f'case {name}')
        for l in src.split('\n'):
            out.append(f'#   {l.strip()}')
        out.append(f'code {code}')
        out.append(f'main {main}')
        for k, v in st.items():
            out.append(f'set {k} {v:#x}')
        for j, (k, v) in enumerate(ex.items()):
            if broken and i == 0 and j == 0:
                v ^= 1
            out.append(f'expect {k} {v:#x}')
        out.append('end')
    return '\n'.join(out) + '\n'

def load_txt(path):
    rows, cur = [], None
    for l in open(path):
        f = l.split()
        if not f or f[0] == '#':
            if cur and f and len(f) > 1 and l.startswith('#   '):
                cur[1].append(l[4:].rstrip('\n'))
            continue
        if f[0] == 'case':
            cur = [f[1], [], '', 0, {}, {}]
        elif f[0] == 'code':
            cur[2] = f[1]
        elif f[0] == 'main':
            cur[3] = int(f[1])
        elif f[0] == 'set':
            cur[4][f[1]] = int(f[2], 0)
        elif f[0] == 'expect':
            cur[5][f[1]] = int(f[2], 0)
        elif f[0] == 'end':
            rows.append((cur[0], '\n'.join(cur[1]), cur[2], cur[3], cur[4], cur[5]))
    return rows

here = os.path.dirname(os.path.abspath(__file__))
txt = os.path.join(here, 'cases.txt')
if sys.argv[1:2] == ['--assemble']:
    tools = sys.argv[2:5]
    with tempfile.TemporaryDirectory() as work:
        rows = []
        for c in CASES:
            code, main = asm(c, tools, work)
            st = {k: (0x1000 + main if v == END else v) for k, v in c[2].items()}
            rows.append((c[0], c[1], code.hex(), main, st, c[3]))
    open(txt, 'w').write(emit(rows))
elif sys.argv[1:2] == ['--broken']:
    sys.stdout.write(emit(load_txt(txt), broken=True))
