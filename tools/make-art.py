#!/usr/bin/env python3
"""The pack icon and the recipe picture, drawn from vanilla textures.

    python3 tools/make-art.py <minecraft-client.jar>

Writes pack.png (128, the icon in the pack list), docs/icon.png (400, the CurseForge avatar) and docs/recipe.png
(the three recipes in crafting table screens). Block items are drawn as small isometric cubes like the inventory does.
"""
import io
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
VINE_TINT = (0x48, 0xB5, 0x18)  # items/vine.json: constant tint -12012264


def texture(jar: zipfile.ZipFile, name: str) -> Image.Image:
    return Image.open(io.BytesIO(jar.read('assets/minecraft/textures/%s.png' % name))).convert('RGBA')


def tinted(image: Image.Image, rgb) -> Image.Image:
    out = image.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            px[x, y] = (r * rgb[0] // 255, g * rgb[1] // 255, b * rgb[2] // 255, a)
    return out


def face(tex: Image.Image, size: int, origin, u, v, shade: float) -> Image.Image:
    """The texture mapped onto the parallelogram origin + s*u + t*v (s, t in 0..1), nearest neighbour."""
    big = tex.resize((tex.width * 16, tex.height * 16), Image.NEAREST)
    det = u[0] * v[1] - u[1] * v[0]
    # inverse of [u v]: (x, y) - origin -> (s, t), then scaled to texture pixels
    a, b = v[1] / det, -v[0] / det
    d, e = -u[1] / det, u[0] / det
    w, h = big.size
    data = (a * w, b * w, -(a * origin[0] + b * origin[1]) * w,
            d * h, e * h, -(d * origin[0] + e * origin[1]) * h)
    out = big.transform((size, size), Image.AFFINE, data, resample=Image.NEAREST)
    mask = Image.new('L', (size, size), 0)
    from PIL import ImageDraw
    corners = [origin, (origin[0] + u[0], origin[1] + u[1]),
               (origin[0] + u[0] + v[0], origin[1] + u[1] + v[1]), (origin[0] + v[0], origin[1] + v[1])]
    ImageDraw.Draw(mask).polygon(corners, fill=255)
    alpha = Image.composite(out.getchannel('A'), Image.new('L', (size, size), 0), mask)
    out = ImageEnhance.Brightness(out.convert('RGB')).enhance(shade).convert('RGBA')
    out.putalpha(alpha)
    return out


def cube(top: Image.Image, side: Image.Image, size: int) -> Image.Image:
    """An isometric block, size x size, top brightest, left and right side darker."""
    a = size / 2
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    for layer in (face(side, size, (0, a / 2), (a, a / 2), (0, a), 0.8),
                  face(side, size, (a, a), (a, -a / 2), (0, a), 0.6),
                  face(top, size, (0, a / 2), (a, -a / 2), (a, a / 2), 1.0)):
        out.alpha_composite(layer)
    return out


def flat(tex: Image.Image, size: int) -> Image.Image:
    return tex.resize((size, size), Image.NEAREST)


def crafting_screen(gui: Image.Image, scale: int, grid: dict, result: Image.Image) -> Image.Image:
    """The upper part of the crafting table screen with items in the grid (slot index -> picture) and the result."""
    screen = gui.crop((0, 0, 176, 80)).resize((176 * scale, 80 * scale), Image.NEAREST)
    for slot, item in grid.items():
        x, y = 30 + 18 * (slot % 3), 17 + 18 * (slot // 3)
        screen.alpha_composite(item, (x * scale, y * scale))
    screen.alpha_composite(result, (124 * scale, 35 * scale))
    return screen


def main() -> None:
    jar = zipfile.ZipFile(sys.argv[1])
    dirt = texture(jar, 'block/dirt')
    rooted = texture(jar, 'block/rooted_dirt')
    roots_side = texture(jar, 'block/mangrove_roots_side')
    roots_top = texture(jar, 'block/mangrove_roots_top')
    vine = tinted(texture(jar, 'block/vine'), VINE_TINT)
    hanging = texture(jar, 'block/hanging_roots')
    gui = texture(jar, 'gui/container/crafting_table')

    cube(rooted, rooted, 128).save(ROOT / 'pack.png')
    (ROOT / 'docs').mkdir(exist_ok=True)
    cube(rooted, rooted, 400).save(ROOT / 'docs/icon.png')

    scale = 3
    slot = 16 * scale
    ingredients = [flat(vine, slot), flat(hanging, slot), cube(roots_top, roots_side, slot)]
    screens = [crafting_screen(gui, scale, {3: cube(dirt, dirt, slot), 4: item}, cube(rooted, rooted, slot))
               for item in ingredients]
    gap = 8 * scale
    w, h = screens[0].size
    picture = Image.new('RGBA', (3 * w + 2 * gap, h), (0, 0, 0, 0))
    for i, screen in enumerate(screens):
        picture.alpha_composite(screen, (i * (w + gap), 0))
    picture.save(ROOT / 'docs/recipe.png')


if __name__ == '__main__':
    main()
