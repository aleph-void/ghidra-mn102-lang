"""Explained difference classes between Ghidra and MAME unidasm -arch mn10200.
classify() returns a reason string, or None for an unexplained difference."""
import re

def _nums(t):
    return [int(x, 16) for x in re.findall(r'0x([0-9a-f]+)', t)]

def classify(off, rn, rt, gn, gt, data):
    b = data[off:off + 8] if data else b''
    r, g = rt.lower(), gt.lower()
    rm, gm = r.split(' ')[0], g.split(' ')[0]
    if rm == 'move' and gm == 'mov' and rn == gn:
        return 'MAME prints mov imm16,An (DC-DF) as "move"'
    if b[:1] == b'\xff' and gm == 'break':
        return 'MAME does not decode break (0xff), which binutils decodes'
    if b[:2] == b'\xf0\x10' and gm == 'syscall':
        return 'MAME does not decode syscall (F0 10), which binutils decodes'
    if b[:1] == b'\xf4' and b[1] in (0x4b, 0x4f) and rm == gm and rn == gn:
        m = re.match(r'b(set|clr) ([0-9a-f]+), \(0x([0-9a-f]+)\)', r)
        if m and _nums(g) == [int(m.group(2), 16), int(m.group(3), 16)]:
            return 'display only: MAME prints the bset/bclr imm8 mask in hex without 0x'
    if b[:1] == b'\xf5' and (b[1] & 0xf0) in (0x40, 0x60) and rm == gm and rn == gn:
        return 'MAME bug: mulq/mulql/mulqh Dm,Dn take Dm from bits 4-3 (always d0/d1); every other two-register form uses bits 3-2'
    if b[:2] == b'\xf3\xfe' and 0xd0 <= b[2] <= 0xdf and rm == gm and rn == gn:
        return 'MAME bug: bset/bclr (abs24)bit read the address from bytes 2-4 (including the opcode byte); tbz/tbnz (abs24) use bytes 3-5'
    if b[:2] in (b'\xf4\xe3', b'\xf4\xe7') and rm == gm and rn == 6 and gn == 5:
        return ('MAME bug: bset/bclr imm8,(abs16) (F4 E3/E7) reported as 6 bytes long; it reads only '
                'bytes 2-4 (abs16, imm8), so the instruction is 5 bytes')
    if b[:1] == b'\xf5' and (b[1] & 0xf8) == 0xf0 and rm == gm and rn == gn:
        return ('MAME prints the mulql/mulqh immediate signed, Ghidra unsigned (upstream reads it as '
                'unsigned; no available manual says which)')
    return None
