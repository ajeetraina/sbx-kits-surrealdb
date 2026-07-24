#!/usr/bin/env python3
"""Generate SurrealDB-kit architecture diagrams as SVG + PNG, for both embedder tags.

Two variants, built from one model:

  openai : embeddings are produced by OpenAI's text-embedding-3-small, so the
           outbound arrow is SOLID -- that call DOES cross to an external system,
           while the SurrealKV vector store stays on-disk locally.
  dmr    : the embedder runs on the host via Docker Model Runner, so the outbound
           arrow is DOTTED and faded -- the whole memory loop stays on the host.
"""
import os, math, html
from PIL import Image, ImageDraw, ImageFont

W, H = 2040, 900
SS = 2  # supersample factor for crisp PNG

# ---- palette ----
BLUE      = (37, 99, 235)     # #2563EB accent / arrows
BLUE_DK   = (29, 78, 216)     # #1D4ED8
NAVY      = (18, 40, 75)      # heading text
GRAY_TXT  = (90, 100, 115)
GRAY_FADE = (150, 160, 172)   # faded/optional elements
HOST_FILL = (228, 239, 252)   # #E4EFFC
HOST_STK  = (47, 107, 235)
BAR_FILL  = (223, 235, 251)   # inner DMR bars
WHITE     = (255, 255, 255)
BOX_STK   = (201, 211, 223)   # #C9D3DF
SAND_STK  = (150, 163, 181)

FONT_DIR = os.path.join(os.path.dirname(__import__('matplotlib').__file__), 'mpl-data/fonts/ttf')
REG = os.path.join(FONT_DIR, 'DejaVuSans.ttf')
BLD = os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf')

# ---- model containers (reset per variant) ----
boxes, arrows, texts = [], [], []
def box(x, y, w, h, r=16, lines=None, fill=WHITE, stroke=BOX_STK, sw=2,
        dashed=False, shadow=True, label_top=None):
    boxes.append(dict(x=x, y=y, w=w, h=h, r=r, lines=lines or [], fill=fill,
                      stroke=stroke, sw=sw, dashed=dashed, shadow=shadow, label_top=label_top))
def arrow(x1, y1, x2, y2, color=BLUE, sw=4, dashed=False, label=None, lx=None, ly=None):
    arrows.append(dict(x1=x1, y1=y1, x2=x2, y2=y2, color=color, sw=sw,
                       dashed=dashed, label=label, lx=lx, ly=ly))
def text(x, y, s, bold=False, size=24, color=NAVY, anchor='lm'):
    texts.append(dict(x=x, y=y, s=s, bold=bold, size=size, color=color, anchor=anchor))


def build(variant):
    boxes.clear(); arrows.clear(); texts.clear()

    # ===== HOST =====
    box(40, 55, 1250, 800, r=42, fill=HOST_FILL, stroke=HOST_STK, sw=4, shadow=False)
    text(105, 812, "Host machine", bold=True, size=32, color=BLUE)

    # ===== Workspace directories =====
    box(85, 205, 250, 118, r=18, lines=[("Workspace", True, 26, NAVY), ("directories", True, 26, NAVY)])

    # ===== microVM sandbox + container =====
    box(450, 135, 445, 448, r=24, stroke=SAND_STK, sw=3, label_top=("microVM-based sandbox", 25, NAVY))
    box(470, 205, 405, 258, r=14, fill=WHITE, stroke=BLUE, sw=2.5, dashed=True, shadow=False,
        label_top=("container", 20, GRAY_TXT))
    box(548, 230, 245, 74, r=16, lines=[("Agent / Claude", True, 25, NAVY)])
    box(518, 330, 300, 92, r=16, lines=[("Memory layer", True, 24, NAVY),
                                         ("surrealdb Python SDK", False, 20, GRAY_TXT)])
    box(492, 483, 255, 84, r=16, lines=[("SurrealDB (embedded)", True, 23, NAVY),
                                         ("SurrealKV · on-disk", False, 20, GRAY_TXT)])

    # ===== Network policies / Secrets / Network Policy =====
    box(940, 200, 148, 102, r=18, lines=[("Network", True, 23, NAVY), ("policies", True, 23, NAVY)])
    secret_sub = "(openai key)" if variant == "openai" else "(none needed)"
    box(1108, 200, 148, 102, r=18, lines=[("Secrets", True, 23, NAVY), (secret_sub, False, 20, GRAY_TXT)])
    box(950, 385, 290, 118, r=20, lines=[("Network Policy", True, 25, NAVY),
                                          ("/ sbx proxy", False, 21, GRAY_TXT)])

    # ===== common arrows =====
    arrow(335, 264, 545, 264)                                            # Workspace -> Agent
    arrow(670, 304, 670, 328)                                            # Agent -> Memory
    arrow(600, 422, 600, 481, label="store / query", lx=612, ly=452)     # Memory -> SurrealDB
    arrow(1014, 302, 1014, 383)                                          # Net policies -> NP
    arrow(1182, 302, 1120, 383)                                          # Secrets -> NP

    if variant == "openai":
        # External OpenAI + SOLID outbound (embeddings DO cross)
        box(1410, 300, 300, 132, r=20, lines=[("External: OpenAI API", True, 24, NAVY),
                                               ("text-embedding-3-small", False, 20, GRAY_TXT),
                                               ("api.openai.com", False, 19, GRAY_TXT)])
        arrow(818, 372, 947, 430, label="embed text", lx=812, ly=352)    # Memory -> NP
        arrow(1240, 428, 1410, 372, sw=5, label="HTTPS", lx=1300, ly=381)  # NP -> External (SOLID)
        text(1410, 500, "SurrealDB data stays on-disk", bold=True, size=24, color=BLUE)
        text(1410, 528, "locally at ~/.surrealdb/data", bold=False, size=20, color=NAVY)
        text(1410, 578, "Embeddings DO cross to OpenAI", bold=True, size=24, color=BLUE)
        text(1410, 606, "via the sbx proxy (key injected)", bold=False, size=20, color=NAVY)
    else:  # dmr
        # Docker Model Runner on the host (embedder is local)
        box(468, 615, 440, 165, r=20, stroke=SAND_STK, sw=2.5,
            label_top=("Docker Model Runner (on host)", 22, NAVY))
        box(490, 663, 396, 44, r=10, fill=BAR_FILL, stroke=BAR_FILL, sw=1, shadow=False,
            lines=[("ai/gemma3 (LLM)", True, 20, NAVY)])
        box(490, 718, 396, 44, r=10, fill=BAR_FILL, stroke=BAR_FILL, sw=1, shadow=False,
            lines=[("ai/mxbai-embed-large (embedder)", True, 20, NAVY)])
        arrow(800, 422, 800, 611, label="embed", lx=812, ly=505)         # Memory -> DMR (down)
        # faded External + DOTTED outbound (nothing crosses)
        box(1410, 300, 300, 118, r=20, stroke=GRAY_FADE, sw=2, shadow=False,
            lines=[("External Systems", True, 24, GRAY_FADE),
                   ("(not reached)", False, 20, GRAY_FADE)])
        arrow(1240, 430, 1408, 372, color=GRAY_FADE, sw=4, dashed=True,
              label="nothing crosses", lx=1258, ly=475)
        text(1410, 520, "The memory loop stays on the host", bold=True, size=24, color=BLUE)
        text(1410, 548, "Nothing crosses to external systems", bold=False, size=20, color=NAVY)


# =========================================================================
# RENDERING
# =========================================================================
_font_cache = {}
def _font(size, bold):
    k = (size, bold)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(BLD if bold else REG, size*SS)
    return _font_cache[k]

def render(out_base):
    img = Image.new("RGB", (W*SS, H*SS), WHITE)
    d = ImageDraw.Draw(img)
    def S(v): return int(round(v*SS))
    def dt(cx, cy, s, bold, size, color, anchor='mm'):
        d.text((S(cx), S(cy)), s, font=_font(size, bold), fill=color, anchor=anchor)

    def dashed_round_rect(x, y, w, h, r, color, sw, dash=9, gap=7):
        def seg(x1, y1, x2, y2):
            L = math.hypot(x2-x1, y2-y1); ux, uy = (x2-x1)/L, (y2-y1)/L
            p = 0.0
            while p < L:
                a, b = p, min(p+dash, L)
                d.line([(S(x1+ux*a), S(y1+uy*a)), (S(x1+ux*b), S(y1+uy*b))], fill=color, width=int(sw*SS))
                p += dash+gap
        seg(x+r, y, x+w-r, y); seg(x+r, y+h, x+w-r, y+h)
        seg(x, y+r, x, y+h-r); seg(x+w, y+r, x+w, y+h-r)

    for b in boxes:
        x, y, w, h, r = b['x'], b['y'], b['w'], b['h'], b['r']
        if b['shadow']:
            d.rounded_rectangle([S(x-1), S(y+3), S(x+w+2), S(y+h+5)], radius=S(r), fill=(223, 229, 237))
        if b['dashed']:
            d.rounded_rectangle([S(x), S(y), S(x+w), S(y+h)], radius=S(r), fill=b['fill'])
            dashed_round_rect(x, y, w, h, r, b['stroke'], b['sw'])
        else:
            d.rounded_rectangle([S(x), S(y), S(x+w), S(y+h)], radius=S(r),
                                fill=b['fill'], outline=b['stroke'], width=int(b['sw']*SS))
        if b['label_top']:
            t, sz, col = b['label_top']; dt(x+22, y+22, t, False, sz, col, anchor='lm')
        if b['lines']:
            total = sum(sz for _, _, sz, _ in b['lines']) + (len(b['lines'])-1)*6
            cy = y + h/2 - total/2
            for t, bold, sz, col in b['lines']:
                dt(x+w/2, cy+sz/2, t, bold, sz, col, anchor='mm'); cy += sz + 6

    def arrowhead(x1, y1, x2, y2, color, sw):
        ang = math.atan2(y2-y1, x2-x1); size = 11 + sw*1.4
        p1 = (x2 + size*math.cos(ang+math.radians(150)), y2 + size*math.sin(ang+math.radians(150)))
        p2 = (x2 + size*math.cos(ang-math.radians(150)), y2 + size*math.sin(ang-math.radians(150)))
        d.polygon([(S(x2), S(y2)), (S(p1[0]), S(p1[1])), (S(p2[0]), S(p2[1]))], fill=color)

    for a in arrows:
        x1, y1, x2, y2 = a['x1'], a['y1'], a['x2'], a['y2']
        L = math.hypot(x2-x1, y2-y1); ux, uy = (x2-x1)/L, (y2-y1)/L
        if a['dashed']:
            p = 0
            while p < L-10:
                b = min(p+12, L-10)
                d.line([(S(x1+ux*p), S(y1+uy*p)), (S(x1+ux*b), S(y1+uy*b))], fill=a['color'], width=int(a['sw']*SS))
                p += 20
        else:
            d.line([(S(x1), S(y1)), (S(x2-ux*10), S(y2-uy*10))], fill=a['color'], width=int(a['sw']*SS))
        arrowhead(x1, y1, x2, y2, a['color'], a['sw'])
        if a['label']:
            dt(a['lx'], a['ly'], a['label'], False, 19, BLUE_DK, anchor='lm')

    for t in texts:
        dt(t['x'], t['y'], t['s'], t['bold'], t['size'], t['color'], anchor=t['anchor'])

    img.resize((W, H), Image.LANCZOS).save(out_base + ".png")
    print("wrote", out_base + ".png")

    # ---- SVG ----
    def rgb(c): return f"rgb({c[0]},{c[1]},{c[2]})"
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           '<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="140%">'
           '<feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#0b1f3a" flood-opacity="0.12"/></filter></defs>']
    for b in boxes:
        x, y, w, h, r = b['x'], b['y'], b['w'], b['h'], b['r']
        dash = ' stroke-dasharray="9 7"' if b['dashed'] else ''
        filt = '' if (b['dashed'] or not b['shadow']) else ' filter="url(#sh)"'
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{rgb(b["fill"])}" '
                   f'stroke="{rgb(b["stroke"])}" stroke-width="{b["sw"]}"{dash}{filt}/>')
        if b['label_top']:
            t, sz, col = b['label_top']
            svg.append(f'<text x="{x+22}" y="{y+28}" font-size="{sz}" fill="{rgb(col)}">{html.escape(t)}</text>')
        if b['lines']:
            total = sum(sz for _, _, sz, _ in b['lines']) + (len(b['lines'])-1)*6
            cy = y + h/2 - total/2
            for t, bold, sz, col in b['lines']:
                fw = ' font-weight="bold"' if bold else ''
                svg.append(f'<text x="{x+w/2}" y="{cy+sz*0.72}" font-size="{sz}" fill="{rgb(col)}" '
                           f'text-anchor="middle"{fw}>{html.escape(t)}</text>'); cy += sz + 6
    for i, a in enumerate(arrows):
        mid = f"m{i}"
        svg.append(f'<defs><marker id="{mid}" markerWidth="12" markerHeight="12" refX="9" refY="5" '
                   f'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{rgb(a["color"])}"/></marker></defs>')
        dash = ' stroke-dasharray="4 8"' if a['dashed'] else ''
        svg.append(f'<line x1="{a["x1"]}" y1="{a["y1"]}" x2="{a["x2"]}" y2="{a["y2"]}" '
                   f'stroke="{rgb(a["color"])}" stroke-width="{a["sw"]}"{dash} marker-end="url(#{mid})"/>')
        if a['label']:
            svg.append(f'<text x="{a["lx"]}" y="{a["ly"]+5}" font-size="19" fill="{rgb(BLUE_DK)}">{html.escape(a["label"])}</text>')
    for t in texts:
        anchor = 'start' if t['anchor'] == 'lm' else 'middle'
        fw = ' font-weight="bold"' if t['bold'] else ''
        svg.append(f'<text x="{t["x"]}" y="{t["y"]+t["size"]*0.34}" font-size="{t["size"]}" '
                   f'fill="{rgb(t["color"])}" text-anchor="{anchor}"{fw}>{html.escape(t["s"])}</text>')
    svg.append('</svg>')
    open(out_base + ".svg", 'w').write('\n'.join(svg))
    print("wrote", out_base + ".svg")


here = os.path.dirname(__file__)
build("openai"); render(os.path.join(here, "surrealdb_architecture"))
build("dmr");    render(os.path.join(here, "surrealdb_architecture_dmr"))
