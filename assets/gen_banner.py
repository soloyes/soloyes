"""Animated SVG banner from Buran-19 sprites. Usage: python3 gen_banner.py <images_dir> <out.svg> <title> <subtitle>"""
import base64, io, math, random, sys
from PIL import Image, ImageOps

IMG, OUT, TITLE, SUB = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
W, H = 1000, 340
DUR = 16  # seconds per loop
random.seed(19)


def b64(im, size):
    im = im.convert("RGBA")
    im.thumbnail(size, Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


def load(name):
    return Image.open(f"{IMG}/{name}.png")


buran, bsz = b64(load("buran"), (120, 120))
astro_sheet = load("astronaut")
astros = [b64(astro_sheet.crop((i * 256, 0, i * 256 + 256, 256)), (70, 70)) for i in range(5)]
ast_m = b64(load("asteroidmetal").crop((0, 0, 128, 128)), (64, 64))
ast_n = b64(load("asteroidmineral").crop((0, 0, 128, 128)), (64, 64))
crate = b64(load("crate"), (40, 40))
fuel = b64(load("fuelbox"), (44, 44))
rocket = b64(load("rocket").crop((0, 0, 128, 128)), (54, 54))
# black hole: tint white spiral purple-blue
sp = load("blackholespiral").convert("RGBA")
r, g, b_, a = sp.split()
tint = Image.merge("RGBA", (r.point(lambda v: int(v * 0.55)), g.point(lambda v: int(v * 0.45)), b_, a))
spiral = b64(tint, (190, 190))
hole = b64(load("blackhole"), (150, 150))


# ---- shuttle path (sampled keyframes) ----
N = 96
def path(t):
    x = -160 + 1320 * t
    y = 190 + 70 * math.sin(2 * math.pi * (t * 1.15 + 0.05)) + 18 * math.sin(2 * math.pi * t * 3.1)
    return x, y

times = [i / (N - 1) for i in range(N)]
pts = [path(t) for t in times]
def angle(t, dt=0.004):
    (x0, y0), (x1, y1) = path(max(t - dt, 0)), path(min(t + dt, 1))
    return math.degrees(math.atan2(y1 - y0, x1 - x0))
angs = [angle(t) for t in times]
kt = ";".join(f"{t:.4f}" for t in times)

def fmt_tr(lag=0.0):
    vals = []
    for t in times:
        tt = t - lag
        if tt < 0:
            vals.append("-400,-400")
        else:
            x, y = path(tt)
            vals.append(f"{x:.1f},{y:.1f}")
    return ";".join(vals)

def fmt_rot(lag=0.0):
    return ";".join(f"{angle(max(t - lag, 0)):.1f}" for t in times)

out = []
o = out.append
o(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
o("""<defs>
<radialGradient id="neb1" cx="25%" cy="30%" r="55%"><stop offset="0" stop-color="#5b2a9e" stop-opacity=".75"/><stop offset="1" stop-color="#5b2a9e" stop-opacity="0"/></radialGradient>
<radialGradient id="neb2" cx="78%" cy="70%" r="50%"><stop offset="0" stop-color="#1f4fbf" stop-opacity=".7"/><stop offset="1" stop-color="#1f4fbf" stop-opacity="0"/></radialGradient>
<radialGradient id="neb3" cx="55%" cy="15%" r="40%"><stop offset="0" stop-color="#b03a8c" stop-opacity=".35"/><stop offset="1" stop-color="#b03a8c" stop-opacity="0"/></radialGradient>
<radialGradient id="shield" cx="50%" cy="50%" r="50%"><stop offset=".6" stop-color="#39e6c8" stop-opacity="0"/><stop offset=".92" stop-color="#39e6c8" stop-opacity=".35"/><stop offset="1" stop-color="#7fffe8" stop-opacity=".8"/></radialGradient>
<radialGradient id="flame" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff6c0"/><stop offset=".4" stop-color="#ffb02e"/><stop offset="1" stop-color="#ff3d00" stop-opacity="0"/></radialGradient>
<radialGradient id="flash" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#b6ff9e" stop-opacity=".9"/><stop offset="1" stop-color="#3cff6a" stop-opacity="0"/></radialGradient>
<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2"/></filter>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="frame"><rect width="1000" height="340" rx="18"/></clipPath>
</defs>""")
o('<g clip-path="url(#frame)">')
o('<rect width="1000" height="340" fill="#0b0720"/>')
o('<rect width="1000" height="340" fill="url(#neb1)"/><rect width="1000" height="340" fill="url(#neb2)"/><rect width="1000" height="340" fill="url(#neb3)"/>')

# starfield: 3 parallax layers, each tiled twice for seamless scroll
for layer, (count, rmax, speed, op) in enumerate([(70, 0.9, 60, 0.55), (40, 1.3, 32, 0.8), (18, 1.9, 18, 1.0)]):
    stars = []
    for _ in range(count):
        x, y, rr = random.uniform(0, W), random.uniform(0, H), random.uniform(0.4, rmax)
        col = random.choice(["#ffffff", "#ffffff", "#cfe0ff", "#ffe9c9", "#e0c9ff"])
        tw = ""
        if random.random() < 0.3:
            d = random.uniform(1.5, 4)
            tw = f'<animate attributeName="opacity" values="1;.2;1" dur="{d:.1f}s" begin="-{random.uniform(0, d):.1f}s" repeatCount="indefinite"/>'
        stars.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr:.1f}" fill="{col}">{tw}</circle>')
    s = "".join(stars)
    o(f'<g opacity="{op}"><g>{s}<g transform="translate({W},0)">{s}</g>'
      f'<animateTransform attributeName="transform" type="translate" from="0,0" to="-{W},0" dur="{speed}s" repeatCount="indefinite"/></g></g>')

# drifting asteroids
for img, x0, y0, x1, y1, d, rd, sc in [(ast_m, 1080, 40, -80, 120, 22, 9, 0.9), (ast_n, 1060, 300, -90, 210, 28, -12, 0.7),
                                       (ast_m, 1100, 190, -100, 300, 35, 15, 0.5), (fuel, -60, 320, 1060, 250, 30, 20, 0.8)]:
    o(f'<g><g transform="scale({sc})"><g><image href="{img[0]}" x="-32" y="-32" width="64" height="64"/>'
      f'<animateTransform attributeName="transform" type="rotate" from="0" to="{360 if rd > 0 else -360}" dur="{abs(rd)}s" repeatCount="indefinite"/></g></g>'
      f'<animateTransform attributeName="transform" type="translate" from="{x0},{y0}" to="{x1},{y1}" dur="{d}s" begin="-{random.uniform(0, d):.1f}s" repeatCount="indefinite"/></g>')

# title
o(f'<text x="44" y="78" font-family="Segoe UI,Helvetica Neue,Arial,sans-serif" font-size="46" font-weight="800" fill="#fff" letter-spacing="3" filter="url(#glow)">{TITLE}</text>')
o(f'<text x="47" y="108" font-family="Segoe UI,Helvetica Neue,Arial,sans-serif" font-size="17" fill="#c9c2ff" letter-spacing="1.5">{SUB}</text>')

# black hole bottom-right with crate spiralling in
bx, by = 880, 255
o(f'<g transform="translate({bx},{by})">'
  f'<g><image href="{spiral[0]}" x="-95" y="-95" width="190" height="190" opacity=".9"/>'
  f'<animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="6s" repeatCount="indefinite"/></g>'
  f'<image href="{hole[0]}" x="-75" y="-75" width="150" height="150"/></g>')
# spiral path for crate
spts = []
for i in range(60):
    k = i / 59
    rr = 150 * (1 - k) + 4
    a = -2.6 * math.pi * k + 2.2
    spts.append(f"{bx + rr * math.cos(a):.1f},{by + rr * 0.8 * math.sin(a):.1f}")
o(f'<g><image href="{crate[0]}" x="-20" y="-20" width="40" height="40">'
  f'<animateTransform attributeName="transform" type="rotate" from="0" to="-720" dur="8s" repeatCount="indefinite"/></image>'
  f'<animateMotion dur="8s" repeatCount="indefinite" path="M{" L".join(spts)}"/>'
  f'<animateTransform attributeName="transform" type="scale" values="1;1;0.1" keyTimes="0;.7;1" dur="8s" additive="sum" repeatCount="indefinite"/>'
  f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.08;.92;1" dur="8s" repeatCount="indefinite"/></g>')

# astronauts placed near the path; rescued by green tractor beam
SPEC = [(0.30, 0, 95), (0.47, 1, 95), (0.63, 2, -95)]
cap = 0.055  # beam window before pickup
for tc, idx, off in SPEC:
    sx, sy = path(tc)
    ax, ay = sx + 30, min(max(sy + off, 60), 295)
    t0, t1 = tc - cap, tc
    # astronaut: floats in place, then gets pulled to the shuttle and vanishes
    kts = "0;" + f"{t0:.4f};{t1:.4f};1"
    o(f'<g opacity="1"><g>'
      f'<g><image href="{astros[idx][0]}" x="-30" y="-35" width="60" height="70"/>'
      f'<animateTransform attributeName="transform" type="rotate" values="-18;18;-18" dur="{5 + idx}s" repeatCount="indefinite"/></g>'
      f'<animateTransform attributeName="transform" type="translate" values="0,-6;0,6;0,-6" dur="3.{idx}s" repeatCount="indefinite"/></g>'
      f'<animateTransform attributeName="transform" type="translate" values="{ax:.0f},{ay:.0f};{ax:.0f},{ay:.0f};{sx:.0f},{sy:.0f};{sx:.0f},{sy:.0f}" keyTimes="{kts}" dur="{DUR}s" repeatCount="indefinite"/>'
      f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{t0 + cap * 0.6:.4f};{t1:.4f};1" dur="{DUR}s" repeatCount="indefinite"/></g>')
    # beam: line from shuttle (moving) to astronaut (moving)
    seg = [t for t in times if t0 - 0.02 <= t <= t1 + 0.02]
    bvals1, bvals2 = [], []
    for t in times:
        x, y = path(t)
        bvals1.append((x, y))
        if t <= t0:
            bvals2.append((ax, ay))
        elif t >= t1:
            bvals2.append((x, y))
        else:
            k = (t - t0) / cap
            k = k * k
            bvals2.append((ax + (x - ax) * k, ay + (y - ay) * k))
    vis = ";".join("1" if t0 <= t <= t1 else "0" for t in times)
    o(f'<line stroke="#4dff7a" stroke-width="4" stroke-dasharray="3 7" stroke-linecap="round" filter="url(#glow)" opacity="0">'
      f'<animate attributeName="x1" values="{";".join(f"{p[0]:.1f}" for p in bvals1)}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/>'
      f'<animate attributeName="y1" values="{";".join(f"{p[1]:.1f}" for p in bvals1)}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/>'
      f'<animate attributeName="x2" values="{";".join(f"{p[0]:.1f}" for p in bvals2)}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/>'
      f'<animate attributeName="y2" values="{";".join(f"{p[1]:.1f}" for p in bvals2)}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/>'
      f'<animate attributeName="opacity" values="{vis}" keyTimes="{kt}" calcMode="discrete" dur="{DUR}s" repeatCount="indefinite"/>'
      f'<animate attributeName="stroke-dashoffset" from="0" to="-20" dur=".4s" repeatCount="indefinite"/></line>')
    # pickup flash + "+1"
    o(f'<g transform="translate({sx:.0f},{sy:.0f})" opacity="0"><circle r="40" fill="url(#flash)"/>'
      f'<text y="-50" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-weight="800" font-size="22" fill="#7dff9a" filter="url(#glow)">+1'
      f'<animate attributeName="y" values="-40;-40;-80;-80" keyTimes="0;{t1:.4f};{min(t1 + 0.08, .999):.4f};1" dur="{DUR}s" repeatCount="indefinite"/></text>'
      f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{t1 - 0.001:.4f};{t1 + 0.005:.4f};{t1 + 0.08:.4f};1" dur="{DUR}s" repeatCount="indefinite"/></g>')

# exhaust trail: puffs lagging behind shuttle
for i, lag in enumerate([0.012, 0.022, 0.032, 0.044, 0.056]):
    o(f'<g opacity="{0.55 - i * 0.09:.2f}"><circle r="{9 + i * 3}" fill="#d9d4ff" filter="url(#blur)"/>'
      f'<animateTransform attributeName="transform" type="translate" values="{fmt_tr(lag)}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/></g>')

# homing rocket chasing the shuttle
o(f'<g><g><image href="{rocket[0]}" x="-27" y="-27" width="54" height="54"/>'
  f'<animateTransform attributeName="transform" type="rotate" values="{fmt_rot(0.09)}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/></g>'
  f'<animateTransform attributeName="transform" type="translate" values="{fmt_tr(0.09)}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/></g>')

# shuttle with flame and shield
w, h = bsz
o('<g><g>'
  f'<g transform="translate(-{w * 0.36:.0f},0)"><ellipse rx="22" ry="9" fill="url(#flame)">'
  '<animate attributeName="rx" values="16;26;19;24;16" dur=".35s" repeatCount="indefinite"/></ellipse></g>'
  f'<image href="{buran}" x="-{w / 2:.0f}" y="-{h / 2:.0f}" width="{w}" height="{h}"/>'
  '<circle r="58" fill="url(#shield)"><animate attributeName="r" values="55;60;55" dur="1.6s" repeatCount="indefinite"/>'
  '<animate attributeName="opacity" values=".55;.9;.55" dur="1.6s" repeatCount="indefinite"/></circle>'
  f'<animateTransform attributeName="transform" type="rotate" values="{fmt_rot()}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/></g>'
  f'<animateTransform attributeName="transform" type="translate" values="{fmt_tr()}" keyTimes="{kt}" dur="{DUR}s" repeatCount="indefinite"/></g>')

o("</g>")
o('<rect x=".5" y=".5" width="999" height="339" rx="18" fill="none" stroke="#6a5cff" stroke-opacity=".35"/>')
o("</svg>")
open(OUT, "w").write("\n".join(out))
print(OUT, sum(len(x) for x in out) // 1024, "KB")
