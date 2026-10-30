"""Generates app/icon.png (80px) and app/largeIcon.png (130px) with the standard library only."""
import os
import struct
import zlib

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
BG = (15, 22, 38)
TILE = (245, 246, 248)
ACCENT = (250, 35, 59)


def chunk(tag, data):
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def inside(x, y, x0, y0, x1, y1, r):
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def make(size, path):
    g = size / 80
    tiles = [
        (14, 16, 38, 38, TILE),
        (42, 16, 66, 38, ACCENT),
        (14, 42, 38, 64, TILE),
        (42, 42, 66, 64, TILE),
    ]
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            color = BG
            for x0, y0, x1, y1, c in tiles:
                if inside(x, y, x0 * g, y0 * g, x1 * g, y1 * g, 4 * g):
                    color = c
            row += bytes(color)
        rows.append(bytes(row))
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


make(80, os.path.join(ROOT, "icon.png"))
make(130, os.path.join(ROOT, "largeIcon.png"))
