#!/usr/bin/env python3
"""news-image-20261127: draw one 1024x1024 PNG summing up the world news
of Friday 27 November 2026. Pure standard library: no PIL, no network.
A tiny 5x7 bitmap font, a bytearray canvas, and a hand-rolled PNG writer.
Deterministic: same input, same bytes, every run."""
import os
import struct
import zlib

W, H = 1024, 1024

# 5x7 font: each glyph is 7 rows of 5 bits, top row first.
F = {
"A": (14, 17, 17, 31, 17, 17, 17), "B": (30, 17, 17, 30, 17, 17, 30),
"C": (14, 17, 16, 16, 16, 17, 14), "D": (30, 17, 17, 17, 17, 17, 30),
"E": (31, 16, 16, 30, 16, 16, 31), "F": (31, 16, 16, 30, 16, 16, 16),
"G": (14, 17, 16, 23, 17, 17, 15), "H": (17, 17, 17, 31, 17, 17, 17),
"I": (14, 4, 4, 4, 4, 4, 14), "J": (7, 2, 2, 2, 2, 18, 12),
"K": (17, 18, 20, 24, 20, 18, 17), "L": (16, 16, 16, 16, 16, 16, 31),
"M": (17, 27, 21, 21, 17, 17, 17), "N": (17, 25, 21, 19, 17, 17, 17),
"O": (14, 17, 17, 17, 17, 17, 14), "P": (30, 17, 17, 30, 16, 16, 16),
"Q": (14, 17, 17, 17, 21, 18, 13), "R": (30, 17, 17, 30, 20, 18, 17),
"S": (15, 16, 16, 14, 1, 1, 30), "T": (31, 4, 4, 4, 4, 4, 4),
"U": (17, 17, 17, 17, 17, 17, 14), "V": (17, 17, 17, 17, 17, 10, 4),
"W": (17, 17, 17, 21, 21, 21, 10), "X": (17, 17, 10, 4, 10, 17, 17),
"Y": (17, 17, 10, 4, 4, 4, 4), "Z": (31, 1, 2, 4, 8, 16, 31),
"a": (0, 0, 14, 1, 15, 17, 15), "b": (16, 16, 22, 25, 17, 17, 30),
"c": (0, 0, 14, 17, 16, 17, 14), "d": (1, 1, 13, 19, 17, 17, 15),
"e": (0, 0, 14, 17, 31, 16, 14), "f": (6, 9, 8, 30, 8, 8, 8),
"g": (0, 14, 17, 17, 15, 1, 30), "h": (16, 16, 22, 25, 17, 17, 17),
"i": (4, 0, 12, 4, 4, 4, 14), "j": (2, 0, 6, 2, 2, 18, 12),
"k": (16, 16, 18, 20, 24, 20, 18), "l": (12, 4, 4, 4, 4, 4, 14),
"m": (0, 0, 26, 21, 21, 21, 21), "n": (0, 0, 22, 25, 17, 17, 17),
"o": (0, 0, 14, 17, 17, 17, 14), "p": (0, 0, 22, 25, 17, 30, 16),
"q": (0, 0, 13, 19, 17, 15, 1), "r": (0, 0, 23, 25, 16, 16, 16),
"s": (0, 0, 15, 16, 14, 1, 30), "t": (8, 8, 28, 8, 8, 8, 6),
"u": (0, 0, 17, 17, 17, 19, 13), "v": (0, 0, 17, 17, 17, 10, 4),
"w": (0, 0, 17, 21, 21, 21, 10), "x": (0, 0, 17, 10, 4, 10, 17),
"y": (0, 0, 17, 17, 15, 1, 14), "z": (0, 0, 31, 2, 4, 8, 31),
"0": (14, 17, 19, 21, 25, 17, 14), "1": (4, 12, 4, 4, 4, 4, 14),
"2": (14, 17, 1, 6, 8, 16, 31), "3": (31, 2, 4, 2, 1, 17, 14),
"4": (2, 6, 10, 18, 31, 2, 2), "5": (31, 16, 30, 1, 1, 17, 14),
"6": (6, 8, 16, 30, 17, 17, 14), "7": (31, 1, 2, 4, 8, 8, 8),
"8": (14, 17, 17, 14, 17, 17, 14), "9": (14, 17, 17, 15, 1, 2, 12),
" ": (0, 0, 0, 0, 0, 0, 0), ".": (0, 0, 0, 0, 0, 12, 12),
",": (0, 0, 0, 0, 12, 4, 8), "'": (4, 4, 8, 0, 0, 0, 0),
"-": (0, 0, 0, 14, 0, 0, 0), ":": (0, 12, 12, 0, 0, 12, 12),
";": (0, 12, 12, 0, 12, 4, 8), "!": (4, 4, 4, 4, 4, 0, 4),
"?": (14, 17, 1, 6, 4, 0, 4), "&": (12, 18, 20, 8, 21, 18, 13),
"(": (2, 4, 8, 8, 8, 4, 2), ")": (8, 4, 2, 2, 2, 4, 8),
"/": (1, 1, 2, 4, 8, 16, 16), "%": (25, 25, 2, 4, 8, 19, 19),
"+": (0, 4, 4, 31, 4, 4, 0), "=": (0, 0, 31, 0, 31, 0, 0),
'"': (10, 10, 10, 0, 0, 0, 0), "$": (4, 15, 20, 14, 5, 30, 4),
}

# (accent colour, tag, headline, summary) -- all events of 27 Nov 2026.
STORIES = [
((229, 72, 77), "CONFLICT", "Kuwait drone strike kills two Italians",
 "Two Italian technicians maintaining air-defence equipment died in the attack. Rome confirmed the deaths; Iran denied any role."),
((76, 154, 255), "DIPLOMACY", "Trump: Putin 'would like a deal' on Ukraine",
 "In a Thanksgiving message, Trump said Russia's president wants a deal to end the war, and warned Iran the US has 'victory at hand'."),
((232, 185, 62), "ECONOMY", "De Cos chosen to lead Europe's central bank",
 "European leaders picked Spain's Pablo Hernandez de Cos as the next president of the European Central Bank."),
((63, 178, 127), "HEALTH", "Ebola in Congo passes 12,000 cases",
 "The outbreak has killed nearly 6,000 people, aid groups say, as fighting in Ituri forces health workers to pull out."),
((155, 126, 222), "POLITICS", "New Zealand coalition one seat short",
 "Final election results leave PM Luxon's centre-right bloc a seat short of a majority, with the Opportunity Party holding the balance of power."),
((56, 189, 248), "WEATHER", "Thanksgiving storm cuts power to 724,000",
 "A powerful storm battered the eastern US, knocking out power for more than 724,000 homes and shutting major bridges."),
((240, 140, 60), "DISASTER", "Ship capsizes off Ibiza; oil spill race",
 "A diesel tanker capsized off Ibiza, killing one crew member, as Spain raced to stop the fuel spreading."),
]
ALSO = ("Also today: Russian military plane crashes in Siberia, 19 killed - "
        "US clears SpaceX to launch up to a million data-centre satellites.")

BG = (14, 27, 46)
PANEL = (20, 38, 64)
WHITE = (245, 247, 250)
MUTED = (168, 184, 205)
GOLD = (232, 185, 62)
RED = (229, 72, 77)

px = bytearray(W * H * 3)


def fill(x, y, w, h, c):
    for yy in range(y, min(y + h, H)):
        base = (yy * W + x) * 3
        for xx in range(max(x, 0), min(x + w, W)):
            o = base + (xx - x) * 3
            px[o], px[o + 1], px[o + 2] = c


def text(s, x, y, scale, c):
    cx = x
    for ch in s:
        g = F.get(ch, F["?"])
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row >> (4 - col) & 1:
                    fill(cx + col * scale, y + r * scale, scale, scale, c)
        cx += 6 * scale
    return cx


def tw(s, scale):
    return len(s) * 6 * scale - scale


def wrap(s, width, scale):
    lines, cur = [], ""
    for word in s.split(" "):
        t = word if not cur else cur + " " + word
        if tw(t, scale) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw():
    fill(0, 0, W, H, BG)
    # Header.
    fill(0, 0, W, 6, RED)
    t = "THE WORLD TODAY"
    text(t, (W - tw(t, 4)) // 2, 26, 4, WHITE)
    d = "FRIDAY 27 NOVEMBER 2026"
    text(d, (W - tw(d, 3)) // 2, 68, 3, GOLD)
    fill(72, 108, W - 144, 3, (52, 74, 106))
    # Story rows.
    y = 132
    rh = 108
    for i, (accent, tag, head, summ) in enumerate(STORIES):
        fill(28, y, W - 56, rh - 14, PANEL)
        fill(28, y, 8, rh - 14, accent)
        # Number chip.
        fill(52, y + 22, 50, 50, accent)
        n = str(i + 1)
        text(n, 52 + (50 - tw(n, 3)) // 2, y + 36, 3, WHITE)
        # Tag.
        text(tag, 120, y + 14, 2, accent)
        # Headline, up to two lines.
        hl = wrap(head, W - 120 - 36, 3)
        hy = y + 34
        for line in hl[:2]:
            text(line, 120, hy, 3, WHITE)
            hy += 24
        # Summary, up to two lines.
        sl = wrap(summ, W - 120 - 36, 2)
        sy = y + 34 + 24 * len(hl[:2]) + 2
        for line in sl[:2]:
            text(line, 120, sy, 2, MUTED)
            sy += 17
        y += rh
    # Footer.
    fill(28, 906, W - 56, 2, (52, 74, 106))
    fl = wrap(ALSO, W - 56, 2)
    fy = 924
    for line in fl:
        text(line, 28, fy, 2, MUTED)
        fy += 19
    src = "All events happened or were first reported on Friday 27 November 2026."
    text(src, 28, 984, 2, GOLD)


def png_bytes():
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += px[yy * W * 3:(yy + 1) * W * 3]

    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(
            ">I", zlib.crc32(c) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    draw()
    out = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out:
        out = "/output" if os.path.isdir("/output") else "out"
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "entry.png"), "wb") as f:
        f.write(png_bytes())


if __name__ == "__main__":
    main()
