"""Check the tables: rebuild the encoder bank words and the JPEG DHT body from BITS / HUFFVAL, verify Kraft and code lengths.
Usage: python navy_tables.py ../tables/navy-10bit.json"""
import json, sys, struct, zlib
t = json.load(open(sys.argv[1]))
bits, vals = t['bits'], t['huffval']
assert len(bits) == 16 and sorted(vals) == list(range(15)), 'must code categories 0..14 exactly once'
raw = bytes(bits) + bytes(vals) + bytes(48 - 31)                     # bank = 16 BITS + 15 HUFFVAL + zero pad, 12 LE words
bank = list(struct.unpack('<12I', raw))
assert ['%08X' % w for w in bank] == t['bank_words_le32'], 'bank words differ'
assert '%08X' % zlib.crc32(raw) == t['bank_crc32'], 'CRC differs'
kraft = sum(n / 2 ** (i + 1) for i, n in enumerate(bits)); assert kraft < 1, 'Kraft sum must stay below 1 (all-ones code reserved)'
L = {}; i = 0
for l, n in enumerate(bits, 1):
    for _ in range(n): L[vals[i]] = l; i += 1
dht = b'\xff\xc4' + struct.pack('>H', 2 + 2 * (1 + 16 + 15)) + b''.join(bytes([tc]) + bytes(bits) + bytes(vals) for tc in (0, 1))
print('%s: OK  bank CRC %s  Kraft %.6f  code length per category %s' % (t['name'], t['bank_crc32'], kraft, [L[c] for c in range(15)]))
print('DHT (two components):', dht.hex())
