"""Explained difference classes between Ghidra and GNU objdump -m mn10200."""
import re
NUM = re.compile(r'(-?)(0x[0-9a-f]+|\d+)')

def nums(t):
    out = []
    for m in NUM.finditer(t.lower()):
        v = int(m.group(2), 0)
        out.append(-v if m.group(1) else v)
    return out

def shape(t):
    return NUM.sub('#', re.sub(r'\s+', '', t.lower()))



def classify(off, rn, rt, gn, gt, data):
    b = data[off:off + 8] if data else b''
    r, g = rt.lower(), gt.lower()
    rm, gm = r.split(' ')[0], g.split(' ')[0]
    if (rn == 0 or r.startswith('unknown')) and gn > 0:
        return 'MN102H/MN102L-extended instruction binutils (MN10200 base) does not decode; MAME decodes it'
    if rm == gm and rn == gn and shape(r) == shape(g):
        rv, gv = nums(r), nums(g)
        if len(rv) == len(gv):
            ok = True
            for a, c in zip(rv, gv):
                if (a - c) & 0xffffff == 0:
                    continue
                if a in (c & 0xff, c & 0xffff):
                    continue  # objdump printed a sign-extended field unsigned
                d = (a - c) & 0xffffff
                if d in (0x100, 0x10000) and (rm.startswith('b') or rm in ('jmp', 'jsr')):
                    continue  # branch target computed with an unsigned displacement
                ok = False
            if ok:
                return 'binutils bug: sign-extended 8/16-bit fields (d8, d16, imm8, branch displacements) printed and used unsigned'
    return None
