# Draws the Trichter (beer funnel) icon: brass funnel seen from slightly above, filled with beer and foam,
# with a long leather hose hanging from the spout. Painted look: dark outline, soft shading, highlights.
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import math, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
S = 4            # supersampling
W = 512 * S
OUTLINE = (52, 30, 16, 255)


def layer():
    return Image.new('RGBA', (W, W), (0, 0, 0, 0))


def bezier(p0, p1, p2, p3, n=200):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t*t*p2[0] + t**3*p3[0]
        y = (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t*t*p2[1] + t**3*p3[1]
        pts.append((x * S, y * S))
    return pts


def stroke(img, pts, width, color):
    d = ImageDraw.Draw(img)
    r = width * S / 2
    d.line(pts, fill=color, width=int(width * S), joint='curve')
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=color)


def shade(mask_img, light, dark, angle_dx=-0.6, angle_dy=-0.8):
    """Fill the alpha shape of mask_img with a diagonal gradient light -> dark."""
    g = Image.new('RGBA', (W, W))
    px = g.load()
    grad = Image.linear_gradient('L').resize((W, W)).rotate(35, resample=Image.BICUBIC)
    a = Image.merge('RGBA', [Image.eval(grad, lambda v, c=c0, e=c1: int(c + (e - c) * v / 255)) for c0, c1 in zip(light[:3], dark[:3])] + [mask_img.split()[3]])
    return a


img = layer()

# ---- hose: from the spout down, one loop, nozzle at the lower left -------------------------------------------
hose_pts = (bezier((256, 300), (262, 360), (420, 350), (400, 430))
            + bezier((400, 430), (385, 492), (210, 500), (170, 440))
            + bezier((170, 440), (150, 405), (170, 372), (120, 372)))
ol = layer(); stroke(ol, hose_pts, 44, OUTLINE)
body = layer(); stroke(body, hose_pts, 32, (150, 92, 52, 255))
hi = layer(); stroke(hi, [(x - 5 * S, y - 6 * S) for x, y in hose_pts], 9, (214, 158, 104, 255))
hi = Image.composite(hi, layer(), body.split()[3])
lo = layer(); stroke(lo, [(x + 6 * S, y + 7 * S) for x, y in hose_pts], 9, (104, 58, 32, 255))
lo = Image.composite(lo, layer(), body.split()[3])
for l in (ol, body, lo.filter(ImageFilter.GaussianBlur(2 * S)), hi.filter(ImageFilter.GaussianBlur(2 * S))):
    img.alpha_composite(l)
# seams on the hose
d = ImageDraw.Draw(img)
for i in range(18, len(hose_pts) - 10, 22):
    (x0, y0), (x1, y1) = hose_pts[i - 2], hose_pts[i + 2]
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1
    nx, ny = -dy / n * 13 * S, dx / n * 13 * S
    x, y = hose_pts[i]
    d.line((x - nx, y - ny, x + nx, y + ny), fill=(96, 54, 30, 255), width=3 * S)
# mouthpiece
mx, my = hose_pts[-1]
d.ellipse((mx - 30 * S, my - 22 * S, mx + 14 * S, my + 22 * S), fill=OUTLINE)
d.ellipse((mx - 25 * S, my - 17 * S, mx + 9 * S, my + 17 * S), fill=(206, 164, 72, 255))
d.ellipse((mx - 20 * S, my - 10 * S, mx - 4 * S, my + 10 * S), fill=(70, 44, 22, 255))

# ---- funnel ----------------------------------------------------------------------------------------------------
cx, rim_y, rx, ry = 256, 120, 196, 62           # rim ellipse
neck_y, neck_r, spout_y, spout_r = 262, 30, 318, 20


def P(pts):
    return [(x * S, y * S) for x, y in pts]


cone = P([(cx - rx, rim_y), (cx - neck_r, neck_y), (cx - spout_r, spout_y), (cx + spout_r, spout_y), (cx + neck_r, neck_y), (cx + rx, rim_y)])
ol = layer(); d2 = ImageDraw.Draw(ol)
d2.polygon(cone, fill=OUTLINE)
d2.line(cone + [cone[0]], fill=OUTLINE, width=12 * S, joint='curve')
d2.ellipse(((cx - rx - 7) * S, (rim_y - ry - 7) * S, (cx + rx + 7) * S, (rim_y + ry + 7) * S), fill=OUTLINE)
img.alpha_composite(ol)

m = layer(); ImageDraw.Draw(m).polygon(cone, fill=(255, 255, 255, 255))
body = Image.new('RGBA', (W, W))
# horizontal brass gradient: bright band left of centre, dark right edge
band = Image.new('RGBA', (W, 1))
bp = band.load()
for x in range(W):
    t = x / S
    u = (t - (cx - rx)) / (2 * rx)
    u = min(1, max(0, u))
    k = math.exp(-((u - 0.28) / 0.16) ** 2)           # highlight
    sh = max(0, (u - 0.55) / 0.45)                      # shadow towards the right
    r = 190 + 60 * k - 80 * sh; g = 142 + 70 * k - 72 * sh; b = 52 + 90 * k - 34 * sh
    bp[x, 0] = (int(max(0, min(255, r))), int(max(0, min(255, g))), int(max(0, min(255, b))), 255)
body = band.resize((W, W))
img.alpha_composite(Image.composite(body, layer(), m.split()[3]))
# ring at the neck
d = ImageDraw.Draw(img)
d.line(P([(cx - neck_r - 2, neck_y), (cx + neck_r + 2, neck_y)]), fill=OUTLINE, width=5 * S)
# rim ellipse: brass edge, then the opening with beer
d.ellipse(((cx - rx) * S, (rim_y - ry) * S, (cx + rx) * S, (rim_y + ry) * S), fill=(236, 196, 96, 255))
ix, iy = rx - 16, ry - 12
d.ellipse(((cx - ix - 4) * S, (rim_y - iy - 4) * S, (cx + ix + 4) * S, (rim_y + iy + 4) * S), fill=OUTLINE)
d.ellipse(((cx - ix) * S, (rim_y - iy) * S, (cx + ix) * S, (rim_y + iy) * S), fill=(224, 150, 34, 255))   # beer
d.ellipse(((cx - ix + 26) * S, (rim_y - iy + 14) * S, (cx + ix - 40) * S, (rim_y + iy - 8) * S), fill=(240, 176, 54, 255))
# rim highlight
d.arc(((cx - rx + 5) * S, (rim_y - ry + 4) * S, (cx + rx - 5) * S, (rim_y + ry - 4) * S), 185, 300, fill=(255, 240, 180, 255), width=5 * S)

# ---- foam: blobs spilling over the rim ------------------------------------------------------------------------
random.seed(7)
foam = layer(); fo = layer()
blobs = [(150, 108, 46), (205, 88, 54), (270, 82, 58), (330, 96, 50), (372, 118, 38), (118, 128, 34),
         (240, 118, 44), (300, 126, 40), (182, 132, 36), (392, 150, 26), (398, 186, 20), (106, 162, 22)]
for x, y, r in blobs:
    ImageDraw.Draw(fo).ellipse(((x - r - 5) * S, (y - r - 5) * S, (x + r + 5) * S, (y + r + 5) * S), fill=OUTLINE)
for x, y, r in blobs:
    ImageDraw.Draw(foam).ellipse(((x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S), fill=(252, 246, 228, 255))
img.alpha_composite(fo); img.alpha_composite(foam)
sh = layer()
for x, y, r in blobs:
    ImageDraw.Draw(sh).ellipse(((x - r * 0.5 + 8) * S, (y + r * 0.15) * S, (x + r * 0.8) * S, (y + r * 0.9) * S), fill=(222, 204, 170, 150))
sh = Image.composite(sh.filter(ImageFilter.GaussianBlur(3 * S)), layer(), foam.split()[3])
img.alpha_composite(sh)
for x, y, r in blobs[:6]:
    d.ellipse(((x - r * 0.45) * S, (y - r * 0.55) * S, (x - r * 0.05) * S, (y - r * 0.2) * S), fill=(255, 255, 255, 255))

out = img.resize((512, 512), Image.LANCZOS)
out.save(os.path.join(HERE, 'trichter.png'))
prev = Image.new('RGBA', (512 + 96 + 16, 512), (58, 52, 46, 255))
prev.alpha_composite(out, (0, 0))
prev.alpha_composite(out.resize((96, 96), Image.LANCZOS), (520, 20))
prev.alpha_composite(out.resize((48, 48), Image.LANCZOS), (544, 140))
prev.save(os.path.join(HERE, 'preview.png'))
print('ok')
