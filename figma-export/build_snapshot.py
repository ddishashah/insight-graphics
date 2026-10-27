"""Build static snapshots of index.html for Figma's HTML import.

Figma's importer runs no JS, can't read CSS masks, and renders at its own
viewport, so for each target width this script:
  - drops scripts and freezes animated states at their first frame,
  - swaps mask-drawn icons for <img> tags,
  - resolves every vw/vh unit to px for the target width,
  - for mobile, applies the max-width media queries unconditionally.

Run from insight-graphics/:  python3 figma-export/build_snapshot.py
Writes insight-home-1440.html and insight-home-390.html.
"""
import re, base64

TARGETS = {1440: 900, 390: 844}   # width: first-viewport height


def b64(path, mime):
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def svg(name, fill='white'):
    t = open(f'assets/icons/{name}.svg').read()
    t = t.replace('preserveAspectRatio="none" overflow="visible" style="display: block;" ', '')
    t = t.replace('fill="white"', f'fill="{fill}"')
    return 'data:image/svg+xml;base64,' + base64.b64encode(t.encode()).decode()


def uui(name, stroke):
    t = open(f'assets/icons/untitled-ui/{name}.svg').read()
    t = t.replace('preserveAspectRatio="none" overflow="visible" style="display: block;" ', '').replace('stroke="black"', f'stroke="{stroke}"')
    return 'data:image/svg+xml;base64,' + base64.b64encode(t.encode()).decode()


IND = ['food', 'pharma', 'tea', 'personal-care', 'lubricants', 'building', 'home-care', 'spirits']


def media_blocks(css, query):
    """Return (css_without_blocks, inner_rules) for every @media (query){...}."""
    out, inner, i = [], [], 0
    key = f'@media ({query})' + '{'
    while True:
        j = css.find(key, i)
        if j < 0:
            out.append(css[i:]); break
        out.append(css[i:j])
        k, depth = j + len(key), 1
        while depth:
            depth += {'{': 1, '}': -1}.get(css[k], 0); k += 1
        inner.append(css[j + len(key):k - 1]); i = k
    return ''.join(out), '\n'.join(inner)


def resolve_units(css, w, h):
    css = re.sub(r'(-?[\d.]+)vw', lambda m: f'{float(m.group(1)) * w / 100:.2f}px', css)
    css = re.sub(r'(-?[\d.]+)vh', lambda m: f'{float(m.group(1)) * h / 100:.2f}px', css)
    return css


def build(w, h):
    s = open('index.html', encoding='utf-8').read()
    s = re.sub(r'<script\b.*?</script>', '', s, flags=re.S)
    s = re.sub(r'<link[^>]+fonts\.g[^>]+>\n?', '', s)
    s = s.replace(' loading="lazy"', '')
    # Figma ignores the hidden attribute, so drop hidden elements outright
    s = re.sub(r'<!-- hidden for v1 launch[^>]*-->\n<section[^>]*\bhidden>.*?</section>\n', '', s, flags=re.S)
    s = re.sub(r'<p class="f-done" hidden>.*?</p>', '', s, flags=re.S)
    ind = {n: b64(f'assets/icons/industries/{n}.png', 'image/png') for n in IND}

    def tile(m):
        cls, style = m.group(1), m.group(2) or ''
        mm = re.search(r'--ic-([a-z-]+)', style)
        src = ind[mm.group(1)] if mm else svg(cls.split('t-')[1])
        return f'<span class="tile {cls}" aria-hidden="true"><img class="ic-img" src="{src}" alt=""></span>'

    s = re.sub(r'<span class="tile ([^"]+)"(?: style="([^"]*)")? aria-hidden="true"><i class="ic"></i></span>', tile, s)
    s = re.sub(r'<div class="icon" style="--ic:var\(--ic-([a-z]+)\)"></div>',
               lambda m: f'<div class="icon icon-img"><img src="{svg(m.group(1), "#14121a")}" alt=""></div>', s)
    # link arrows and the stat arrow are CSS masks: put real <img> icons in front of the text
    s = re.sub(r'(<a [^>]*class="link-arrow[^"]*"[^>]*>)', lambda m: m.group(1) + f'<img class="ic-la" src="{uui("corner-down-right", "#f4f4f5")}" alt="">', s)
    s = s.replace('<p class="num up">', f'<p class="num up"><img class="ic-up" src="{uui("arrow-up", "#f4f4f5")}" alt="">')

    head, rest = s.split('<style>', 1)
    css, tail = rest.split('</style>', 1)
    css, tablet = media_blocks(css, 'max-width:960px')
    css, phone = media_blocks(css, 'max-width:640px')
    if w <= 640:
        css += '\n/* phone media queries, applied unconditionally */\n' + tablet + '\n' + phone
    elif w <= 960:
        css += '\n' + tablet
    css = resolve_units(css, w, h)
    css += f'''
/* ---- static snapshot for Figma import ({w}px) ---- */
html,body{{width:{w}px;min-width:{w}px;max-width:{w}px;overflow:hidden}}
body{{position:relative}}
.blob::before{{animation:none}}
.notes-toggle,.whatsapp-modal{{display:none}}
.wa-float{{position:absolute;top:{h - 62}px;bottom:auto}}
.reveal{{color:var(--fg)}}
.hero-slides .ph{{opacity:0}}.hero-slides .ph:first-child{{opacity:1;transform:none}}
.hero-progress button:first-child i{{width:45%}}
.scroller-ctrls button:first-child{{opacity:.35}}
.marquee-track{{animation:none}}
.link-arrow::before,.stat .num.up::before{{display:none}}
.ic-la{{width:16px;height:16px;flex:none}}
.ic-up{{display:inline-block;width:.62em;height:.62em;margin-right:.18em;vertical-align:baseline}}
.tile .ic-img{{position:relative;z-index:1;width:48px;height:48px;mix-blend-mode:overlay}}
.svc-card .icon-img{{display:grid;place-items:center}}.svc-card .icon-img::after{{display:none}}.svc-card .icon-img img{{width:24px;height:24px}}
'''
    out = head + '<style>' + css + '</style>' + tail
    path = f'figma-export/insight-home-{w}.html'
    open(path, 'w', encoding='utf-8').write(out)
    print(path, len(out) // 1024, 'KB')


for w, h in TARGETS.items():
    build(w, h)
