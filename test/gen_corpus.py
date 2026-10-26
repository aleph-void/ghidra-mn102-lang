#!/usr/bin/env python3
"""gen_corpus.py <out.bin> <seed> <nrandom>: 8-byte slots for MN10200. Enumerates every first byte,
every two-byte prefix of the F0-F7 pages and every three-byte prefix of F3 FE/FF and F5 xx (with
random tails), then adds <nrandom> random slots."""
import random, sys
out, seed, nrand = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
r = random.Random(seed)
def tail(n): return bytes(r.randrange(256) for _ in range(n))
slots = []
for b0 in range(256):
    for _ in range(8): slots.append(bytes([b0]) + tail(7))
for b0 in range(0xf0, 0xf8):
    for b1 in range(256):
        for _ in range(4): slots.append(bytes([b0, b1]) + tail(6))
for b1 in (0xfe, 0xff):
    for b2 in range(256):
        for _ in range(2): slots.append(bytes([0xf3, b1, b2]) + tail(5))
for b1 in range(256):
    for b2 in range(0, 256, 4):
        slots.append(bytes([0xf5, b1, b2]) + tail(5))
for _ in range(nrand): slots.append(tail(8))
open(out, 'wb').write(b''.join(slots))
print(len(slots), 'slots')
