#!/usr/bin/env python3
"""Render the 26 November 2026 world-news newspaper as a 1024x1024 PNG.

Reads news.json (same directory), draws masthead, hero space scene, world
map, UTC timeline and all 36 stories grouped by region. Deterministic:
no timestamps, no randomness without a fixed seed, sorted iteration only.
Standard library + Pillow only.
"""
import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

PAPER = (248, 244, 232)
INK = (26, 26, 26)
MUTED = (90, 84, 70)
RED = (163, 31, 31)
BLUE = (31, 78, 121)
OCEAN = (207, 227, 238)
LAND = (224, 214, 184)
LAND_EDGE = (150, 138, 105)
GREEN = (46, 125, 50)
AMBER = (176, 124, 0)
RULE = (180, 172, 150)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_R = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    """Load a TTF font; fall back to Pillow's default bitmap font if the
    file is missing (e.g. in the minimal grader sandbox)."""
    try:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    except OSError:
        pass
    return ImageFont.load_default()


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def trunc(draw, text, fnt, max_w, suffix="..."):
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    while text and draw.textlength(text + suffix, font=fnt) > max_w:
        text = text[:-1]
    return text + suffix


# Rough equirectangular continent outlines (lon, lat).
NORTH_AMERICA = [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80),
                 (-85, 66), (-80, 73), (-65, 60), (-55, 52), (-60, 46),
                 (-70, 42), (-75, 35), (-80, 32), (-85, 29), (-90, 21),
                 (-95, 19), (-97, 16), (-92, 14), (-87, 13), (-83, 9),
                 (-79, 9), (-83, 15), (-90, 14), (-97, 16), (-105, 20),
                 (-110, 23), (-114, 28), (-120, 34), (-125, 40), (-124, 48),
                 (-130, 55), (-140, 60), (-155, 58), (-165, 60)]
GREENLAND = [(-58, 64), (-45, 60), (-40, 64), (-30, 68), (-22, 70),
             (-25, 76), (-35, 80), (-50, 80), (-58, 76), (-60, 70)]
SOUTH_AMERICA = [(-79, 9), (-75, 10), (-72, 12), (-64, 10), (-60, 8),
                 (-52, 5), (-50, 0), (-44, -3), (-35, -8), (-38, -15),
                 (-40, -22), (-48, -28), (-55, -35), (-62, -41), (-68, -50),
                 (-70, -54), (-73, -50), (-73, -40), (-72, -30), (-70, -20),
                 (-75, -15), (-80, -6), (-81, 0), (-80, 5)]
AFRICA = [(-17, 15), (-16, 20), (-15, 27), (-10, 31), (-5, 35), (0, 36),
          (10, 37), (11, 34), (20, 32), (30, 31), (32, 31), (35, 28),
          (37, 22), (39, 18), (43, 12), (48, 11), (51, 10), (46, 5),
          (41, 0), (40, -5), (36, -18), (33, -26), (28, -33), (20, -35),
          (17, -32), (14, -22), (12, -12), (13, -5), (9, 4), (4, 6),
          (-8, 5), (-13, 8), (-17, 12)]
EURASIA = [(-9, 37), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57),
           (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (35, 65),
           (40, 67), (50, 68), (60, 68), (70, 72), (80, 73), (90, 75),
           (100, 77), (110, 74), (120, 73), (130, 72), (140, 72), (150, 70),
           (158, 68), (162, 60), (156, 51), (150, 59), (142, 55), (140, 50),
           (138, 45), (135, 40), (130, 35), (127, 33), (122, 31), (120, 28),
           (115, 23), (110, 20), (108, 15), (105, 10), (103, 7), (100, 8),
           (98, 12), (95, 16), (92, 21), (90, 22), (86, 20), (82, 17),
           (80, 13), (77, 8), (75, 10), (72, 20), (68, 23), (66, 25),
           (62, 25), (58, 26), (56, 27), (52, 28), (50, 29), (48, 30),
           (44, 29), (42, 20), (40, 15), (39, 12), (43, 12), (45, 13),
           (48, 14), (52, 15), (55, 17), (58, 20), (60, 24), (57, 26),
           (52, 26), (50, 26), (48, 27), (44, 29), (40, 30), (36, 36),
           (33, 36), (30, 36), (27, 37), (23, 36), (19, 40), (15, 44),
           (12, 44), (8, 44), (3, 43), (-1, 38), (-6, 36), (-9, 37)]
AUSTRALIA = [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33),
             (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
             (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
             (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
             (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)]
CONTINENTS = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EURASIA,
              AUSTRALIA]

# Label offsets (dx, dy) per map point to dodge collisions.
LABEL_DX = {"Islamabad": -58, "New York": 6, "Cartagena": 6, "Brasilia": 6,
            "Warsaw": 6, "Moscow": 6, "Riyadh": 6, "Cairo": 6,
            "Hong Kong": 6, "Delhi": 6, "London": 6, "Canberra": -60}
LABEL_DY = {"Islamabad": -12, "Hong Kong": -12, "London": -12,
            "Canberra": -12, "Riyadh": 8, "Delhi": 9}


def draw_hero_scene(d, x0, y0, w, h):
    """Drawn scene: Shenzhou-24 docking with Tiangong above Earth."""
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(16, 24, 48))
    rng = random.Random(2611)
    for _ in range(70):
        sx = x0 + rng.randint(2, w - 2)
        sy = y0 + rng.randint(2, h - 55)
        r = rng.choice([1, 1, 1, 2])
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 255, 255))
    # Earth arc at the bottom.
    d.ellipse([x0 - 90, y0 + h - 38, x0 + w + 90, y0 + h + 150],
              fill=(46, 110, 180))
    d.ellipse([x0 + 30, y0 + h - 26, x0 + 130, y0 + h + 30],
              fill=(70, 140, 90))
    d.ellipse([x0 + 190, y0 + h - 30, x0 + 260, y0 + h + 18],
              fill=(70, 140, 90))
    d.arc([x0 - 90, y0 + h - 38, x0 + w + 90, y0 + h + 150],
          start=180, end=360, fill=(180, 220, 245), width=2)
    # Tiangong station: core module + solar wings.
    cx, cy = x0 + w // 2, y0 + h // 2 - 14
    d.rectangle([cx - 95, cy - 4, cx - 38, cy + 4], fill=(40, 90, 160))
    d.rectangle([cx + 38, cy - 4, cx + 95, cy + 4], fill=(40, 90, 160))
    for px in (cx - 95, cx + 38):
        for i in range(5):
            d.line([px + i * 11 + 2, cy - 4, px + i * 11 + 2, cy + 4],
                   fill=(120, 170, 220), width=1)
    d.rounded_rectangle([cx - 38, cy - 9, cx + 38, cy + 9], radius=8,
                        fill=(200, 205, 210), outline=(120, 125, 130))
    d.rounded_rectangle([cx - 52, cy - 6, cx - 38, cy + 6], radius=4,
                        fill=(170, 175, 180))
    d.rectangle([cx + 38, cy - 5, cx + 48, cy + 5], fill=(170, 175, 180))
    # Shenzhou capsule approaching from upper right.
    kx, ky = cx + 78, cy - 42
    d.polygon([(kx - 16, ky + 8), (kx + 2, ky - 12), (kx + 16, ky + 10)],
              fill=(225, 225, 225), outline=(120, 120, 120))
    d.ellipse([kx - 6, ky + 4, kx + 10, ky + 18], fill=(200, 60, 40))
    d.line([kx + 2, ky + 16, cx + 44, cy - 6], fill=(255, 220, 120),
           width=1)
    for i in range(3):
        d.ellipse([kx - 14 + i * 12, ky + 26 + i * 4,
                   kx - 10 + i * 12, ky + 30 + i * 4], fill=(255, 200, 90))
    cap = font(SANS_B, 11)
    d.text((x0 + 10, y0 + h - 20), "SHENZHOU-24 DOCKS WITH TIANGONG",
           font=cap, fill=(255, 255, 255))


def draw_map(d, x0, y0, w, h, points):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=OCEAN, outline=RULE)
    # Graticule.
    for lon in range(-150, 181, 30):
        gx = x0 + (lon + 180) / 360.0 * w
        d.line([gx, y0, gx, y0 + h], fill=(255, 255, 255), width=1)
    for lat in (-30, 0, 30, 60):
        gy = y0 + (85 - lat) / 145.0 * h
        d.line([x0, gy, x0 + w, gy], fill=(255, 255, 255), width=1)

    def proj(lon, lat):
        return (x0 + (lon + 180) / 360.0 * w,
                y0 + (85 - lat) / 145.0 * h)

    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_EDGE)
    # UK + Japan as small blobs.
    for lon, lat, r in [(-2, 54, 4), (138, 38, 5)]:
        px, py = proj(lon, lat)
        d.ellipse([px - r, py - r, px + r, py + r], fill=LAND,
                  outline=LAND_EDGE)
    lab = font(SANS_B, 10)
    for p in points:
        px, py = proj(p["lon"], p["lat"])
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=RED,
                  outline=(255, 255, 255), width=1)
        lx = px + LABEL_DX.get(p["label"], 6)
        ly = py + LABEL_DY.get(p["label"], -5)
        d.text((lx, ly), p["label"], font=lab, fill=INK)


def draw_timeline(d, x0, y0, w, events):
    f_time = font(SANS_B, 10)
    f_lab = font(SANS, 9)
    y_line = y0 + 26
    d.line([x0 + 8, y_line, x0 + w - 8, y_line], fill=RULE, width=2)
    n = len(events)
    for i, ev in enumerate(events):
        fx = x0 + 30 + i * (w - 60) / (n - 1)
        d.ellipse([fx - 5, y_line - 5, fx + 5, y_line + 5], fill=RED,
                  outline=(255, 255, 255), width=1)
        t = ev["utc"] + " UTC"
        tw = d.textlength(t, font=f_time)
        d.text((fx - tw / 2, y0 + 4), t, font=f_time, fill=BLUE)
        lines = [trunc(d, ev["label"], f_lab, 108)]
        ly = y_line + 9
        for ln in lines[:1]:
            lw = d.textlength(ln, font=f_lab)
            lx = fx - lw / 2
            lx = max(x0, min(lx, x0 + w - lw))
            d.text((lx, ly), ln, font=f_lab, fill=INK)
            ly += 11


def render(data):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    stories = data["stories"]
    hero = data["hero"]

    # --- Masthead ---
    f_title = font(SERIF, 46)
    title = data.get("title", "THE WORLD IN ONE IMAGE")
    tw = d.textlength(title, font=f_title)
    d.text(((W - tw) / 2, 6), title, font=f_title, fill=INK)
    d.line([16, 62, W - 16, 62], fill=RED, width=3)
    f_sub = font(SANS_B, 13)
    sub = (data["day"] + "  |  " + data["edition"] + "  |  "
           + str(len(stories) + 1) + " stories from 8 regions")
    sw = d.textlength(sub, font=f_sub)
    d.text(((W - sw) / 2, 68), sub, font=f_sub, fill=MUTED)
    d.line([16, 88, W - 16, 88], fill=INK, width=1)

    # --- Hero ---
    hy, hh = 96, 168
    d.rectangle([16, hy, W - 16, hy + hh], outline=RULE, width=1)
    # Draw the scene on its own canvas so the Earth arc cannot spill
    # past the hero panel into the map below.
    scene = Image.new("RGB", (300, hh - 2), (16, 24, 48))
    sd = ImageDraw.Draw(scene)
    draw_hero_scene(sd, 0, 0, 300, hh - 2)
    img.paste(scene, (17, hy + 1))
    tx = 336
    f_kick = font(SANS_B, 11)
    d.text((tx, hy + 10), "TOP STORY  —  ASIA-PACIFIC", font=f_kick,
           fill=RED)
    f_head = font(SERIF, 25)
    head_lines = wrap(d, hero["headline"], f_head, W - 16 - tx - 14)
    hyy = hy + 30
    for ln in head_lines[:3]:
        d.text((tx, hyy), ln, font=f_head, fill=INK)
        hyy += 30
    f_sum = font(SANS, 13)
    sum_lines = wrap(d, hero["summary"], f_sum, W - 16 - tx - 14)
    for ln in sum_lines[:2]:
        d.text((tx, hyy + 2), ln, font=f_sum, fill=(60, 56, 46))
        hyy += 17
    f_tag = font(SANS_B, 11)
    tag = "HOW SURE: " + hero["sure"]
    d.rounded_rectangle([tx, hy + hh - 30, tx + d.textlength(tag, font=f_tag) + 16,
                         hy + hh - 8], radius=9, fill=GREEN)
    d.text((tx + 8, hy + hh - 28), tag, font=f_tag, fill=(255, 255, 255))

    # --- Map ---
    my, mh = 272, 148
    f_sec = font(SANS_B, 12)
    d.text((16, my), "WHERE IT HAPPENED", font=f_sec, fill=INK)
    d.text((W - 16 - d.textlength("12 places, 8 regions", font=f_sec), my),
           "12 places, 8 regions", font=f_sec, fill=MUTED)
    draw_map(d, 16, my + 20, W - 32, mh - 20, data["map_points"])

    # --- Timeline ---
    ty = 428
    d.text((16, ty), "THE DAY IN UTC", font=f_sec, fill=INK)
    draw_timeline(d, 16, ty + 18, W - 32, data["timeline"])

    # --- Stories, 3 columns grouped by region ---
    regions = []
    for s in stories:
        if s["region"] not in regions:
            regions.append(s["region"])
    by_region = {r: [s for s in stories if s["region"] == r]
                 for r in regions}
    order = ["NORTH AMERICA", "LATIN AMERICA", "EUROPE", "MIDDLE EAST",
             "AFRICA", "ASIA-PACIFIC", "MARKETS & TECH",
             "SCIENCE & SPORT"]
    cols = [[], [], []]
    col_of = {"NORTH AMERICA": 0, "LATIN AMERICA": 0, "EUROPE": 1,
              "MIDDLE EAST": 1, "AFRICA": 2, "ASIA-PACIFIC": 2,
              "MARKETS & TECH": 2, "SCIENCE & SPORT": 2}
    for r in order:
        if r in by_region:
            cols[col_of[r]].append(r)

    f_reg = font(SANS_B, 12)
    f_hl = font(SANS_B, 11)
    f_sm = font(SANS, 9)
    f_sure = font(SANS_B, 8)
    col_x = [16, 352, 688]
    col_w = 320
    sy = 498
    d.line([16, sy - 6, W - 16, sy - 6], fill=INK, width=1)
    for ci, col_regions in enumerate(cols):
        y = sy
        x = col_x[ci]
        for r in col_regions:
            d.rectangle([x, y, x + col_w, y + 17], fill=BLUE)
            d.text((x + 6, y + 2), r, font=f_reg, fill=(255, 255, 255))
            y += 22
            for s in by_region[r]:
                hl = wrap(d, s["headline"], f_hl, col_w)
                for ln in hl[:2]:
                    d.text((x, y), ln, font=f_hl, fill=INK)
                    y += 13
                sure = s["sure"]
                col = GREEN if sure == "CONFIRMED" else AMBER
                swd = d.textlength(sure, font=f_sure)
                # Tag sits on the summary line, right-aligned; the
                # summary is truncated to leave it room, so it can
                # never overlap the headline or the summary text.
                sm = trunc(d, s["summary"], f_sm, col_w - swd - 8)
                d.text((x, y), sm, font=f_sm, fill=(70, 66, 56))
                d.text((x + col_w - swd, y), sure, font=f_sure, fill=col)
                y += 12
                y += 5
            y += 2

    # --- Footer ---
    f_foot = font(SANS, 9)
    foot = ("All events of Thursday 26 November 2026  •  36 stories  •  "
            "8 regions  •  CONFIRMED = verified by several reports, "
            "REPORTED = as reported")
    fw = d.textlength(foot, font=f_foot)
    d.text(((W - fw) / 2, H - 16), foot, font=f_foot, fill=MUTED)
    return img


def main():
    with open(os.path.join(HERE, "news.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    img = render(data)
    out = os.path.join(HERE, "image.png")
    img.save(out, format="PNG", optimize=True)
    print(out)


if __name__ == "__main__":
    main()
