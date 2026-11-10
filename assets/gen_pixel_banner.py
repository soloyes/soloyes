"""Pixel-art animated banner from Buran-19 sprites.
Renders every frame at 333x113, then ffmpeg upscales x3 (nearest) into a GIF.
Usage: python3 gen_pixel_banner.py <images_dir> <frames_dir> <TITLE> <SUBTITLE>
"""
import math, os, random, sys
from functools import lru_cache
from PIL import Image, ImageDraw

IMG, OUTD, TITLE, SUB = sys.argv[1:5]
W, H = 333, 113
FPS, DUR = 12, 16
NF = FPS * DUR  # 192 frames per loop
os.makedirs(OUTD, exist_ok=True)

OUTLINE = (16, 8, 38, 255)

# ---------------- 5x7 pixel font ----------------
F = {
 'A':"01110 10001 10001 11111 10001 10001 10001", 'B':"11110 10001 10001 11110 10001 10001 11110",
 'C':"01110 10001 10000 10000 10000 10001 01110", 'D':"11110 10001 10001 10001 10001 10001 11110",
 'E':"11111 10000 10000 11110 10000 10000 11111", 'F':"11111 10000 10000 11110 10000 10000 10000",
 'G':"01110 10001 10000 10111 10001 10001 01111", 'H':"10001 10001 10001 11111 10001 10001 10001",
 'I':"01110 00100 00100 00100 00100 00100 01110", 'J':"00111 00010 00010 00010 00010 10010 01100",
 'K':"10001 10010 10100 11000 10100 10010 10001", 'L':"10000 10000 10000 10000 10000 10000 11111",
 'M':"10001 11011 10101 10101 10001 10001 10001", 'N':"10001 10001 11001 10101 10011 10001 10001",
 'O':"01110 10001 10001 10001 10001 10001 01110", 'P':"11110 10001 10001 11110 10000 10000 10000",
 'Q':"01110 10001 10001 10001 10101 10010 01101", 'R':"11110 10001 10001 11110 10100 10010 10001",
 'S':"01111 10000 10000 01110 00001 00001 11110", 'T':"11111 00100 00100 00100 00100 00100 00100",
 'U':"10001 10001 10001 10001 10001 10001 01110", 'V':"10001 10001 10001 10001 10001 01010 00100",
 'W':"10001 10001 10001 10101 10101 10101 01010", 'X':"10001 10001 01010 00100 01010 10001 10001",
 'Y':"10001 10001 01010 00100 00100 00100 00100", 'Z':"11111 00001 00010 00100 01000 10000 11111",
 '0':"01110 10001 10011 10101 11001 10001 01110", '1':"00100 01100 00100 00100 00100 00100 01110",
 '2':"01110 10001 00001 00010 00100 01000 11111", '3':"11111 00010 00100 00010 00001 10001 01110",
 '4':"00010 00110 01010 10010 11111 00010 00010", '5':"11111 10000 11110 00001 00001 10001 01110",
 '6':"00110 01000 10000 11110 10001 10001 01110", '7':"11111 00001 00010 00100 01000 01000 01000",
 '8':"01110 10001 10001 01110 10001 10001 01110", '9':"01110 10001 10001 01111 00001 00010 01100",
 '+':"00000 00100 00100 11111 00100 00100 00000", '-':"00000 00000 00000 11111 00000 00000 00000",
 '·':"00000 00000 00000 00100 00000 00000 00000", '@':"01110 10001 10111 10101 10111 10000 01111",
 '/':"00001 00001 00010 00100 01000 10000 10000", ' ':"00000 00000 00000 00000 00000 00000 00000",
}

def text(img, s, x, y, scale, colors, shadow=None):
    """colors: list of 7 row colors (vertical gradient)."""
    px = img.load()
    for pass_ in ([1, 0] if shadow else [0]):
        cx = x
        for ch in s.upper():
            rows = F[ch].split()
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit == '1':
                        for sy in range(scale):
                            for sx in range(scale):
                                X, Y = cx + rx * scale + sx + pass_, y + ry * scale + sy + pass_
                                if 0 <= X < W and 0 <= Y < H:
                                    px[X, Y] = shadow if pass_ else colors[ry]
            cx += 6 * scale
    return cx

# ---------------- sprite pixelizer ----------------
def load(name):
    return Image.open(f"{IMG}/{name}.png").convert("RGBA")

def pixelize(hd, size, ncol=10, outline=True):
    im = hd.copy()
    im.thumbnail((size, size), Image.BOX)
    a = im.split()[3].point(lambda v: 255 if v > 110 else 0)
    rgb = im.convert("RGB").quantize(ncol, method=Image.MEDIANCUT).convert("RGB")
    out = Image.new("RGBA", (im.width + 2, im.height + 2), (0, 0, 0, 0))
    spr = rgb.convert("RGBA"); spr.putalpha(a)
    if outline:
        m = Image.new("RGBA", out.size, (0, 0, 0, 0))
        sil = Image.new("RGBA", im.size, OUTLINE); sil.putalpha(a)
        for dx, dy in ((0, 1), (1, 0), (2, 1), (1, 2)):
            m.alpha_composite(sil, (dx, dy))
        out = m
    out.alpha_composite(spr, (1, 1))
    return out

HD = {
    "buran": load("buran"),
    "rocket": load("rocket").crop((0, 0, 128, 128)),
    "crate": load("crate"),
    "fuel": load("fuelbox"),
    "hole": load("blackhole"),
}
sheet = load("astronaut")
for i in range(5):
    HD[f"astro{i}"] = sheet.crop((i * 256, 0, i * 256 + 256, 256))
sp = load("blackholespiral")
r, g, b, a = sp.split()
HD["spiral"] = Image.merge("RGBA", (r.point(lambda v: int(v * .5)), g.point(lambda v: int(v * .4)), b, a.point(lambda v: 255 if v > 60 else 0)))
AST = {k: load(n) for k, n in (("m", "asteroidmetal"), ("n", "asteroidmineral"))}

@lru_cache(maxsize=None)
def spr(name, size, ang=0, ncol=10, outline=True):
    hd = HD[name]
    if ang:
        hd = hd.rotate(-ang, resample=Image.BICUBIC, expand=True)
    return pixelize(hd, size, ncol, outline)

@lru_cache(maxsize=None)
def ast(kind, frame, size):
    fx, fy = frame % 8, frame // 8
    return pixelize(AST[kind].crop((fx * 128, fy * 128, fx * 128 + 128, fy * 128 + 128)), size, 6)

def blit(img, s, cx, cy):
    img.alpha_composite(s, (int(round(cx - s.width / 2)), int(round(cy - s.height / 2)))) if \
        -s.width < cx < W + s.width and -s.height < cy < H + s.height else None

# ---------------- background ----------------
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
PURPLE = [(11, 7, 32), (24, 12, 58), (42, 20, 96), (66, 30, 138), (96, 44, 170)]
BLUE = [(11, 7, 32), (14, 20, 66), (20, 38, 112), (30, 64, 168), (60, 100, 210)]
MAG = [(11, 7, 32), (40, 12, 52), (78, 22, 92), (120, 40, 130)]

def blob(x, y, cx, cy, rx, ry):
    return math.exp(-(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))

bg = Image.new("RGBA", (W, H))
bp = bg.load()
random.seed(7)
for y in range(H):
    for x in range(W):
        p = 0.95 * blob(x, y, 80, 35, 110, 45) + 0.35 * blob(x, y, 150, 95, 60, 25)
        bl = 0.95 * blob(x, y, 265, 80, 100, 45)
        m = 0.6 * blob(x, y, 185, 15, 50, 18)
        t = (BAYER[y % 4][x % 4] + .5) / 16
        best, ramp = max((p, PURPLE), (bl, BLUE), (m, MAG), key=lambda z: z[0])
        idx = min(int(best * (len(ramp) - 1) * 1.05 + t), len(ramp) - 1)
        bp[x, y] = ramp[idx] + (255,)

STAR_COLS = [(255, 255, 255), (207, 224, 255), (255, 233, 201), (224, 201, 255)]
layers = []
for speed, count in ((0, 55), (1, 30), (2, 14)):
    stars = []
    for _ in range(count):
        stars.append(dict(x=random.randrange(W), y=random.randrange(H), c=random.choice(STAR_COLS),
                          big=(speed == 2 and random.random() < .5) or random.random() < .06,
                          tw=random.choice([0, 0, 0, 16, 24, 32, 48]), ph=random.randrange(48)))
    layers.append((speed, stars))

def draw_stars(img, f):
    px = img.load()
    for speed, stars in layers:
        shift = speed * W * f / NF
        for s in stars:
            x = int((s["x"] - shift) % W); y = s["y"]
            c = s["c"]
            if s["tw"] and ((f + s["ph"]) % s["tw"]) < s["tw"] // 3:
                c = tuple(v // 3 for v in c)
            dim = tuple(v * 2 // 3 for v in c) if speed == 0 else c
            px[x, y] = dim + (255,)
            if s["big"]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    X, Y = (x + dx) % W, y + dy
                    if 0 <= Y < H:
                        px[X, Y] = tuple(v // 2 for v in c) + (255,)

# ---------------- motion ----------------
def path(t):
    x = -55 + 445 * t
    y = 71 + 19 * math.sin(2 * math.pi * (t * 1.15 + 0.05)) + 6 * math.sin(2 * math.pi * t * 3.1)
    return x, y

def angle(t, dt=0.004):
    (x0, y0), (x1, y1) = path(max(t - dt, 0)), path(min(t + dt, 1))
    return math.degrees(math.atan2(y1 - y0, x1 - x0))

def qa(a, step=10):
    return int(round(a / step)) * step % 360

def circle_pts(r):
    pts = set()
    for i in range(int(2 * math.pi * r * 2) + 8):
        a = 2 * math.pi * i / (int(2 * math.pi * r * 2) + 8)
        pts.add((int(round(r * math.cos(a))), int(round(r * math.sin(a)))))
    return pts

def line_pts(x0, y0, x1, y1):
    x0, y0, x1, y1 = map(int, map(round, (x0, y0, x1, y1)))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, pts = dx + dy, []
    while True:
        pts.append((x0, y0))
        if (x0, y0) == (x1, y1): break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy
    return pts

def put(img, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img.putpixel((int(x), int(y)), c + (255,) if len(c) == 3 else c)

SPEC = [(0.30, 0, 31), (0.47, 1, 31), (0.63, 2, -31)]
CAP = 0.055
ASTRO_POS = []
for tc, idx, off in SPEC:
    sx, sy = path(tc)
    ASTRO_POS.append((tc, idx, sx + 10, min(max(sy + off, 18), 98)))

ASTEROIDS = [  # kind, y0, y1, crossings per loop, size, rot dir
    ("m", 14, 40, 1, 20, 1), ("n", 100, 70, 1, 16, -1), ("m", 63, 100, 2, 12, 1)]

BX, BY = 293, 85

# ---------------- anomalies & rockets (shuttle fires homing rockets at anomalies) ----------------
ANOM_SHEETS = {k: (load(k), cols, rows) for k, cols, rows in
               (("radiation", 4, 4), ("electric", 4, 4), ("magnetic", 4, 4), ("corrosive", 4, 3))}

@lru_cache(maxsize=None)
def anom(kind, fr, size):
    sh, cols, rows = ANOM_SHEETS[kind]
    fw, fh = sh.width // cols, sh.height // rows
    fr %= cols * rows
    cx, cy = fr % cols, fr // cols
    m = 0.18  # crop empty margins so the anomaly core reads at pixel size
    return pixelize(sh.crop((int(cx * fw + fw * m), int(cy * fh + fh * m), int(cx * fw + fw * (1 - m)), int(cy * fh + fh * (1 - m)))), size, 10, True)

# kind, x, y, size, launch time (fraction of loop), respawn time
ANOMALIES = [("radiation", 128, 98, 26, 0.16, 0.62), ("magnetic", 214, 100, 26, 0.40, 0.90),
             ("electric", 262, 26, 26, 0.66, 0.97), ("corrosive", 52, 99, 24, 0.11, 0.45)]

def anom_pos(a, f):
    kind, x, y, size, *_ = a
    return x + 2 * math.sin(2 * math.pi * f / 96 + x), y + 2 * math.cos(2 * math.pi * f / 64 + y)

def simulate_rocket(a):
    """Launch from the shuttle along its heading, steer toward the anomaly like Rocket.update() in the game."""
    tl = a[4]
    x, y = path(tl); ang = math.radians(angle(tl))
    vx, vy = 70 * math.cos(ang), 70 * math.sin(ang)
    f0 = int(round(tl * NF)); traj = []
    f = f0
    while f < f0 + NF // 2:
        tx, ty = anom_pos(a, f % NF)
        for _ in range(4):
            dt = 1 / FPS / 4
            dx, dy = tx - x, ty - y; d = math.hypot(dx, dy) or 1
            sp = min(150, math.hypot(vx, vy) + 160 * dt)   # accelerate
            dvx, dvy = dx / d * sp, dy / d * sp              # desired velocity toward target
            k = min(1, 5.5 * dt)                             # steering strength
            vx += (dvx - vx) * k; vy += (dvy - vy) * k
            x += vx * dt; y += vy * dt
        traj.append((f % NF, x, y, math.degrees(math.atan2(vy, vx))))
        if math.hypot(tx - x, ty - y) < 5:
            break
        f += 1
    return traj

ROCKETS = []
for a in ANOMALIES:
    tr = simulate_rocket(a)
    ROCKETS.append((a, {fr: (x, y, an) for fr, x, y, an in tr}, tr[-1][0]))

def alive(a, f, hit_f):
    resp = int(round(a[5] * NF)) % NF
    # alive outside the window (hit_f, resp) on the circular timeline
    if hit_f <= resp:
        return not (hit_f < f < resp)
    return resp <= f <= hit_f

def explosion(img, x, y, k, seed):
    rnd = random.Random(seed)
    cols = [(255, 255, 255), (255, 246, 160), (255, 200, 70), (255, 120, 30), (200, 50, 30), (110, 35, 50)]
    def chunk(px_, py_, c):
        for ddx in (0, 1):
            for ddy in (0, 1):
                put(img, px_ + ddx, py_ + ddy, c)
    if k < .4:  # white-hot core
        r0 = 7 * (1 - k * 1.5)
        for dy in range(-7, 8):
            for dx in range(-7, 8):
                d2 = dx * dx + dy * dy
                if d2 <= r0 * r0:
                    put(img, x + dx, y + dy, cols[0] if d2 < r0 * r0 * .3 else cols[1 + int(k * 5)])
    if k < .5:  # shock ring
        for dx, dy in circle_pts(int(4 + 22 * k)):
            if (dx + dy) % 2 == 0:
                put(img, x + dx, y + dy, cols[2])
    for i in range(26):  # debris
        a = rnd.uniform(0, 2 * math.pi); sp = rnd.uniform(8, 22)
        r = sp * (1 - (1 - k) ** 2)
        c = cols[min(int(k * 6) + (i % 2), 5)]
        chunk(x + r * math.cos(a), y + r * math.sin(a), c)


def frame(f):
    t = f / NF
    img = bg.copy()
    draw_stars(img, f)
    # asteroids & fuel box
    for kind, y0, y1, k, size, d in ASTEROIDS:
        u = (t * k + size / 50) % 1
        x = W + 20 - (W + 40) * u; y = y0 + (y1 - y0) * u
        blit(img, ast(kind, (f // 3 * d) % 64, size), x, y)
    u = (t + .4) % 1
    blit(img, spr("fuel", 14, qa(360 * t * 2, 15), 6), -15 + (W + 30) * u, 108 - 25 * u)
    # black hole
    blit(img, spr("spiral", 62, qa(-360 * (f % 64) / 64, 360 / 32), 6, False), BX, BY)
    blit(img, spr("hole", 46, 0, 4, False), BX, BY)
    # crate spiralling in (2 per loop)
    k = (f % 96) / 96
    if k < .93:
        rr = 50 * (1 - k) + 1; a = -2.6 * math.pi * k + 2.2
        size = max(4, int(14 * (1 - k * .8)))
        blit(img, spr("crate", size, qa(-720 * k, 15), 6), BX + rr * math.cos(a), BY + rr * .8 * math.sin(a))
    # anomalies, homing rockets, explosions
    for a, traj, hit_f in ROCKETS:
        kind, ax_, ay_, size = a[0], *anom_pos(a, f), a[3]
        resp_f = int(round(a[5] * NF)) % NF
        if alive(a, f, hit_f):
            since = (f - resp_f) % NF
            sz = size if since >= 6 else max(4, int(size * (since + 1) / 7))
            blit(img, anom(kind, f // 2, sz), ax_, ay_)
        dt_hit = (f - hit_f) % NF
        if dt_hit < 12:
            explosion(img, ax_, ay_, dt_hit / 12, hash(kind) & 0xffff)
    # title
    tg = [(255, 255, 255), (255, 255, 255), (236, 232, 255), (214, 206, 255), (190, 180, 255), (160, 150, 250), (127, 255, 232)]
    text(img, TITLE, 14, 11, 2, tg, shadow=(40, 18, 90, 255))
    for li, line in enumerate(SUB.split('|')):
        text(img, line, 14, 33 + li * 10, 1, [(201, 194, 255) if li == 0 else (127, 255, 232)] * 7, shadow=(20, 10, 50, 255))
    # astronauts + beams
    flashes = []
    for tc, idx, ax, ay in ASTRO_POS:
        t0 = tc - CAP
        sx, sy = path(t)
        wob = 18 * math.sin(2 * math.pi * f / (64 + idx * 32))
        bob = round(2 * math.sin(2 * math.pi * f / 48 + idx))
        if t <= t0:
            px_, py_ = ax, ay + bob
        elif t < tc:
            kk = ((t - t0) / CAP) ** 2
            px_, py_ = ax + (sx - ax) * kk, ay + (sy - ay) * kk
        else:
            px_ = None
        if px_ is not None:
            if t0 < t < tc:
                for i, (x, y) in enumerate(line_pts(sx, sy, px_, py_)):
                    if (i + f * 2) % 6 < 3:
                        put(img, x, y + 1, (20, 120, 50)); put(img, x, y, (77, 255, 122))
            if not (t > t0 + CAP * .75):
                blit(img, spr(f"astro{idx}", 24, qa(wob, 6), 8), px_, py_)
        if tc <= t < tc + 0.06:
            flashes.append((sx, sy, (t - tc) / 0.06))
    # exhaust puffs
    for i, lag in enumerate((0.012, 0.022, 0.032, 0.044)):
        tt = t - lag
        if tt < 0: continue
        x, y = path(tt); r = 4 - i // 2
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r and (i < 2 or (dx + dy + f) % 2 == 0):
                    put(img, x + dx, y + dy, (180, 172, 220) if i < 2 else (120, 110, 170))
    # rockets in flight (launched by the shuttle)
    for a, traj, hit_f in ROCKETS:
        if f in traj and f != hit_f:
            x, y, an = traj[f]
            ar_ = math.radians(an)
            for s_ in range(1, 5):
                put(img, x - s_ * 2 * math.cos(ar_), y - s_ * 2 * math.sin(ar_), (255, 176, 46) if s_ < 2 else (150, 140, 190))
            blit(img, spr("rocket", 14, qa(an, 15), 8), x, y)
    # shuttle
    x, y = path(t); a = angle(t); ar = math.radians(a)
    bx_, by_ = x - 13 * math.cos(ar), y - 13 * math.sin(ar)
    rnd = random.Random(f)
    for j, col in enumerate(((255, 61, 0), (255, 176, 46), (255, 246, 192))):
        ln = 6 - 2 * j + rnd.randint(0, 2)
        for s in range(ln):
            put(img, bx_ - s * math.cos(ar), by_ - s * math.sin(ar), col)
            if j == 0:
                put(img, bx_ - s * math.cos(ar) - math.sin(ar), by_ - s * math.sin(ar) + math.cos(ar), col)
                put(img, bx_ - s * math.cos(ar) + math.sin(ar), by_ - s * math.sin(ar) - math.cos(ar), col)
    blit(img, spr("buran", 38, qa(a)), x, y)
    rad = 19 + (1 if (f // 6) % 2 else 0)
    for i, (dx, dy) in enumerate(sorted(circle_pts(rad), key=lambda p: math.atan2(p[1], p[0]))):
        ang_ = math.degrees(math.atan2(dy, dx))
        hi = -150 < ang_ < -60
        if hi or i % 2 == 0:
            put(img, x + dx, y + dy, (127, 255, 232) if hi else (57, 200, 190))
    # pickup flashes
    for sx, sy, k in flashes:
        r = int(6 + 16 * k)
        if k < .6:
            for dx, dy in circle_pts(r):
                put(img, sx + dx, sy + dy, (125, 255, 154))
        text(img, "+1", int(sx) - 6, int(sy - 26 - 14 * k), 1, [(125, 255, 154)] * 7, shadow=(10, 60, 30, 255))
    # frame border
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W - 1, H - 1), outline=(70, 60, 160, 255))
    return img.convert("RGB")

for f in range(NF):
    frame(f).save(f"{OUTD}/f{f:03d}.png")
print("frames", NF, [(a[0], int(round(a[4]*NF)), h) for a, tr, h in ROCKETS])
