#!/usr/bin/env python3
"""Render the KTS bracket/cursor mark into the desktop assets. Pillow required."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'kts/config.json').read_text())
ACCENT = '#' + CONFIG['accent']


def icon(size=1024, monochrome=False):
    image = Image.new('RGBA', (1024, 1024))
    d = ImageDraw.Draw(image)
    if not monochrome:
        d.rounded_rectangle((40, 40, 984, 984), radius=224, fill='#102F39')
    fg = '#000000' if monochrome else '#FFFFFF'
    teal = fg if monochrome else '#52D6CB'
    d.line([(368, 295), (240, 295), (240, 638), (368, 638)], fill=teal, width=52, joint='curve')
    d.line([(656, 295), (784, 295), (784, 638), (696, 638)], fill=teal, width=52, joint='curve')
    d.polygon([(440, 377), (440, 718), (527, 638), (603, 770), (663, 734), (586, 604), (701, 578)], fill=fg)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def font(size):
    for path in ['/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                 'C:/Windows/Fonts/arialbd.ttf']:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def main():
    assets = ROOT / 'flutter/assets'
    brand = ROOT / 'kts/branding'
    brand.mkdir(parents=True, exist_ok=True)
    image = icon()
    image.save(brand / 'icon.png')
    image.resize((256, 256), Image.Resampling.LANCZOS).save(assets / 'icon.png')
    image.save(ROOT / 'flutter/macos/Runner/AppIcon.icns', format='ICNS')
    ico_paths = ['flutter/windows/runner/resources/app_icon.ico', 'res/icon.ico',
                 'res/tray-icon.ico', 'flutter/assets/icon.ico']
    for path in ico_paths:
        image.save(ROOT / path, format='ICO', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    icon(44, monochrome=True).save(ROOT / 'res/mac-tray-dark-x2.png')
    for mode, fg in [('light', '#102F39'), ('dark', '#EDF9FA')]:
        logo = Image.new('RGBA', (1440, 288))
        logo.alpha_composite(image.resize((264, 264), Image.Resampling.LANCZOS), (0, 12))
        d = ImageDraw.Draw(logo)
        d.text((302, 38), CONFIG['app_name'], fill=fg, font=font(136))
        d.text((308, 196), 'REMOTE SUPPORT', fill=ACCENT, font=font(34))
        logo.save(assets / f'logo_{mode}.png')
        logo.save(brand / f'logo_{mode}.png')
        if mode == 'light':
            logo.save(assets / 'logo.png')
    print('Generated macOS, Windows, tray and Flutter branding assets')


if __name__ == '__main__':
    main()
