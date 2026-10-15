#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from PIL import Image, ImageDraw


def create_default_png(dest: Path, size: int = 512):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Тёмно-графитовый скруглённый квадрат (в стиле macOS Big Sur+)
    pad = int(size * 0.06)
    radius = int(size * 0.22)
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius,
        fill=(30, 34, 42, 255),
        outline=(65, 160, 195, 255),
        width=max(2, int(size * 0.015)),
    )

    # Бирюзовый параллелограмм Bandcamp в верхней части
    para_top = int(size * 0.22)
    para_bottom = int(size * 0.54)
    slant = int(size * 0.10)
    left_x = int(size * 0.22)
    right_x = int(size * 0.78)

    parallelogram = [
        (left_x + slant, para_top),
        (right_x, para_top),
        (right_x - slant, para_bottom),
        (left_x, para_bottom),
    ]
    draw.polygon(parallelogram, fill=(29, 160, 195, 255))

    # Белая стрелка скачивания и нижняя планка
    cx = size // 2
    shaft_w = int(size * 0.08)
    shaft_top = int(size * 0.44)
    shaft_bottom = int(size * 0.66)
    head_w = int(size * 0.22)
    head_tip = int(size * 0.77)

    # Стержень и остриё стрелки
    draw.rectangle(
        [cx - shaft_w // 2, shaft_top, cx + shaft_w // 2, shaft_bottom],
        fill=(255, 255, 255, 255),
    )
    draw.polygon(
        [
            (cx - head_w // 2, shaft_bottom - 2),
            (cx + head_w // 2, shaft_bottom - 2),
            (cx, head_tip),
        ],
        fill=(255, 255, 255, 255),
    )

    # Нижняя полоска-лоток
    tray_y = int(size * 0.81)
    tray_h = int(size * 0.035)
    tray_w = int(size * 0.36)
    draw.rounded_rectangle(
        [cx - tray_w // 2, tray_y, cx + tray_w // 2, tray_y + tray_h],
        radius=tray_h // 2,
        fill=(29, 160, 195, 255),
    )

    img.save(dest, format="PNG")


def main():
    base = Path(__file__).resolve().parent
    png_path = base / "icon.png"
    ico_path = base / "icon.ico"
    icns_path = base / "icon.icns"

    if not png_path.exists():
        print("[*] Custom icon.png not found — start generate default icon...")
        create_default_png(png_path)
        print(f"[+] {png_path.name} done")
    else:
        print("[*] Use exist icon.png...")

    img = Image.open(png_path).convert("RGBA")

    img.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"[+] {ico_path.name} done")

    img.save(icns_path, format="ICNS")
    print(f"[+] {icns_path.name} done")


if __name__ == "__main__":
    main()
