# Draws the Schlauch (hose) icon in the same style as the Trichter icon: a coil of leather hose seen from
# slightly above, with seams, and a free end with a brass mouthpiece.
from PIL import Image, ImageDraw, ImageFilter
import math, os
HERE = os.path.dirname(os.path.abspath(__file__))
S = 4
W = 512 * S
OUTLINE = (52, 30, 16, 255)
BODY, LIGHT, DARK, SEAM = (150, 92, 52, 255), (214, 158, 104, 255), (104, 58, 32, 255), (96, 54, 30, 255)


def layer():
    return Image.new('RGBA', (W, W), (0, 0, 0, 0))


def stroke(img, pts, width, color, caps=True):
    d = ImageDraw.Draw(img)
    r = width * S / 2
    d.line(pts, fill=color, width=int(width * S), joint='curve')
    if caps:
        for x, y in (pts[0], pts[-1]):
            d.ellipse((x - r, y - r, x + r, y + r), fill=color)


def hose(img, pts, width=40, seams=True, caps=True):
    ol = layer(); stroke(ol, pts, width + 12, OUTLINE, caps)
    body = layer(); stroke(body, pts, width, BODY, caps)
    hi = layer(); stroke(hi, [(x - 6 * S, y - 8 * S) for x, y in pts], width * 0.28, LIGHT, caps)
    lo = layer(); stroke(lo, [(x + 7 * S, y + 9 * S) for x, y in pts], width * 0.3, DARK, caps)
    hi = Image.composite(hi, layer(), body.split()[3]).filter(ImageFilter.GaussianBlur(2 * S))
    lo = Image.composite(lo, layer(), body.split()[3]).filter(ImageFilter.GaussianBlur(2 * S))
    for l in (ol, body, lo, hi):
        img.alpha_composite(l)
    if seams:
        d = ImageDraw.Draw(img)
        step = 26
        for i in range(step, len(pts) - step // 2, step):
            (x0, y0), (x1, y1) = pts[i - 2], pts[i + 2]
            dx, dy = x1 - x0, y1 - y0
            n = math.hypot(dx, dy) or 1
            nx, ny = -dy / n * width * 0.42 * S, dx / n * width * 0.42 * S
            x, y = pts[i]
            d.line((x - nx, y - ny, x + nx, y + ny), fill=SEAM, width=3 * S)


def ellipse_pts(cx, cy, rx, ry, a0, a1, n=260):
    return [((cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n))) * S,
             (cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) * S) for i in range(n + 1)]


def bezier(p0, p1, p2, p3, n=160):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t*t*p2[0] + t**3*p3[0]
        y = (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t*t*p2[1] + t**3*p3[1]
        pts.append((x * S, y * S))
    return pts


img = layer()
cx, cy, rx, ry = 262, 300, 176, 88

# back halves of the rings (far side), drawn first, top ring last
rings = [(cy + 60, 1.00), (cy + 12, 0.97), (cy - 36, 0.93)]
for y, k in rings:
    hose(img, ellipse_pts(cx, y, rx * k, ry * k, 176, 364), caps=False)
# front halves, bottom ring first so upper rings overlap lower ones
for y, k in rings:
    hose(img, ellipse_pts(cx, y, rx * k, ry * k, -4, 184), caps=False)

# free end: leaves the top ring at the right, arcs up and over to the left, ends in a mouthpiece
end = bezier((cx + rx * 0.93 - 6, cy - 40), (cx + 190, cy - 190), (cx + 20, cy - 250), (cx - 96, cy - 196))
hose(img, end)
d = ImageDraw.Draw(img)
mx, my = end[-1]
d.ellipse((mx - 40 * S, my - 30 * S, mx + 14 * S, my + 30 * S), fill=OUTLINE)
d.ellipse((mx - 34 * S, my - 24 * S, mx + 8 * S, my + 24 * S), fill=(206, 164, 72, 255))
d.ellipse((mx - 34 * S, my - 24 * S, mx - 6 * S, my + 2 * S), fill=(240, 208, 120, 255))
d.ellipse((mx - 28 * S, my - 14 * S, mx - 6 * S, my + 14 * S), fill=(70, 44, 22, 255))
# brass ferrule where the hose meets the mouthpiece
fx, fy = end[-14]
d.ellipse((fx - 16 * S, fy - 27 * S, fx + 16 * S, fy + 27 * S), fill=OUTLINE)
d.ellipse((fx - 11 * S, fy - 22 * S, fx + 11 * S, fy + 22 * S), fill=(206, 164, 72, 255))

out = img.resize((512, 512), Image.LANCZOS)
out.save(os.path.join(HERE, 'schlauch.png'))
t = Image.open(os.path.join(HERE, 'trichter.png'))
prev = Image.new('RGBA', (1024 + 120, 512), (58, 52, 46, 255))
prev.alpha_composite(t, (0, 0)); prev.alpha_composite(out, (512, 0))
for i, im in enumerate((t, out)):
    prev.alpha_composite(im.resize((96, 96), Image.LANCZOS), (1036, 20 + i * 110))
    prev.alpha_composite(im.resize((48, 48), Image.LANCZOS), (1060, 260 + i * 60))
prev.save(os.path.join(HERE, 'preview.png'))
print('ok')
