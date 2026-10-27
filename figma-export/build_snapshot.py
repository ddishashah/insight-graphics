"""Build a static 1440px snapshot of index.html for Figma's HTML import.

Figma's importer runs no JS and can't read CSS masks, so: scripts are dropped,
animated states are frozen, and mask-drawn icons are swapped for <img> tags.
Run from insight-graphics/: python3 figma-export/build_snapshot.py
"""
import re, base64

s = open('index.html').read()
s = re.sub(r'<script>.*?</script>', '', s, flags=re.S)
s = re.sub(r'<link[^>]+fonts\.g[^>]+>\n?', '', s)


def b64(path, mime):
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def svg(name, fill='white'):
    t = open(f'assets/icons/{name}.svg').read()
    t = t.replace('preserveAspectRatio="none" overflow="visible" style="display: block;" ', '')
    t = t.replace('fill="white"', f'fill="{fill}"')
    return 'data:image/svg+xml;base64,' + base64.b64encode(t.encode()).decode()


ind = {n: b64(f'assets/icons/industries/{n}.png', 'image/png')
       for n in ['food', 'pharma', 'tea', 'personal-care', 'lubricants', 'building', 'home-care', 'spirits']}


def tile(m):
    cls, style = m.group(1), m.group(2) or ''
    mm = re.search(r'--ic-([a-z-]+)', style)
    src = ind[mm.group(1)] if mm else svg(cls.split('t-')[1])
    return f'<span class="tile {cls}" aria-hidden="true"><img class="ic-img" src="{src}" alt=""></span>'


s = re.sub(r'<span class="tile ([^"]+)"(?: style="([^"]*)")? aria-hidden="true"><i class="ic"></i></span>', tile, s)
s = re.sub(r'<div class="icon" style="--ic:var\(--ic-([a-z]+)\)"></div>',
           lambda m: f'<div class="icon icon-img"><img src="{svg(m.group(1), "#14121a")}" alt=""></div>', s)
s = s.replace(' loading="lazy"', '')

s = s.replace('</style>', '''
/* ---- static snapshot for Figma import ---- */
html,body{width:1440px;min-width:1440px}
.blob::before{animation:none}
.notes-toggle{display:none}
.reveal{color:var(--fg)}
.hero-slides .ph{opacity:0}.hero-slides .ph:first-child{opacity:1;transform:none}
.hero-progress button:first-child i{width:45%}
#offerPrev{opacity:.35}
.tile .ic-img{position:relative;z-index:1;width:48px;height:48px;mix-blend-mode:overlay}
.svc-card .icon-img{display:grid;place-items:center}.svc-card .icon-img::after{display:none}.svc-card .icon-img img{width:24px;height:24px}
</style>''', 1)

open('figma-export/insight-home-1440.html', 'w').write(s)
print(len(s) // 1024, 'KB')
