"""Turn client logo sources into white-on-transparent PNGs.

Recolour only: every pixel keeps its shape; "ink" (anything not near-white)
becomes white, near-white (backgrounds and knockouts inside marks) becomes
transparent. Then trim and cap the size.
"""
import io, sys
import fitz
from PIL import Image, ImageChops

SRC = sys.argv[1]
OUT = sys.argv[2]

LOGOS = {
    # slug: (source file, invert_already_white)
    'adani-wilmar':     'deck-adani-wilmar.png',   # vector art from Insight's own deck, rendered at 1600dpi
    'emami':            'site-emamiagro.png',
    'godrej':           'commons-Godrej-Logo.svg',
    'tata-consumer':    'wiki-TATA-CONSUMER-PRODUCTS-BLUE-LOGO-Feb-13.png',
    'tata':             'wiki-Tata-logo.svg',
    'indian-oil':       'wiki-Indian-Oil-Logo.svg',
    'jsw-steel':        'site-jsw.svg',
    'aditya-birla':     'wiki-Aditya-Birla-Group-Logo.svg',
    'balmer-lawrie':    'site-balmer-full.png',
    'kitply':           'site-kitply.png',
    'bengal-chemicals': 'wiki-Bengal-Chemicals--Pharmaceuticals-Ltd.-logo.jpg',
    'boroline':         'site-boroline.png',
    'ifb-agro':         'site-ifb-agro.svg',
    'pernod-ricard':    'commons-Pernod-Ricard-logo-2019.svg',
    'strassenburg':     'site-strassenburg.png',
    'albert-david':     'site-albert-david.png',   # only a 144px file on albertdavidindia.com; replace with a better source when one turns up
}

MAX_W, MAX_H = 1400, 360


def load(path):
    if path.endswith('.svg'):
        doc = fitz.open(path)
        page = doc[0]
        zoom = max(1, 1600 / max(page.rect.width, page.rect.height))
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
        return Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGBA')
    return Image.open(path).convert('RGBA')


def whiten(im):
    r, g, b, a = im.split()
    darkest = ImageChops.darker(ImageChops.darker(r, g), b)   # min channel
    ink = darkest.point(lambda v: max(0, min(255, int((255 - v) * 1.7))))
    alpha = ImageChops.multiply(ink, a)
    white = Image.new('L', im.size, 255)
    return Image.merge('RGBA', (white, white, white, alpha))


for slug, f in LOGOS.items():
    im = whiten(load(f'{SRC}/{f}'))
    bbox = im.split()[3].point(lambda v: 255 if v > 12 else 0).getbbox()
    im = im.crop(bbox)
    im.thumbnail((MAX_W, MAX_H), Image.LANCZOS)
    im.save(f'{OUT}/{slug}.png', optimize=True)
    print(slug, im.size)
