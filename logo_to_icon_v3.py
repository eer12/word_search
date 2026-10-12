# -*- coding: utf-8 -*-
"""商标抠图 v3: u2net + alpha matting + 边缘收缩 + 阈值清理"""
import os
from PIL import Image, ImageFilter, ImageChops
from rembg import remove

SRC = r"d:\Desktop\文档存储检索工具商标名推荐 (4).png"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_ICO = os.path.join(ROOT, "app_icon.ico")
PREVIEW_DARK = os.path.join(ROOT, "icon_preview_dark.png")
PREVIEW_LIGHT = os.path.join(ROOT, "icon_preview_light.png")
CUTOUT_PNG = os.path.join(ROOT, "logo_cutout.png")

img = Image.open(SRC).convert("RGBA")
W, H = img.size
print(f"原图: {W}x{H}")

# 裁掉下方文字，只保留上方环形图形
img = img.crop((0, 0, W, int(H * 0.56)))

# u2net + alpha matting 精细边缘
img = remove(
    img,
    alpha_matting=True,
    alpha_matting_foreground_threshold=240,
    alpha_matting_background_threshold=10,
    alpha_matting_erode_size=10,
)

# 收紧到内容
bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)
print(f"抠图后: {img.size}")

# ---- 边缘清理：去除灰蒙蒙半透明残留 ----
a = img.getchannel("A")
# 低透明度直接砍掉（<35 设 0），减少灰边
a = a.point(lambda v: 0 if v < 35 else v)
img.putalpha(a)

# 轻微收缩 1px，去掉残余白边
eroded = a.filter(ImageFilter.MinFilter(3))
img.putalpha(eroded)

# 再轻微高斯羽化 0.5px，让边界自然
a2 = img.getchannel("A").filter(ImageFilter.GaussianBlur(0.5))
img.putalpha(a2)

img.save(CUTOUT_PNG)

# 加 4% 透明边距居中
w, h = img.size
m = int(max(w, h) * 0.04)
side = max(w, h) + m * 2
canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)

# 多尺寸 ICO
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
canvas.save(OUT_ICO, format="ICO", sizes=sizes)
print(f"ICO 已保存: {OUT_ICO} ({os.path.getsize(OUT_ICO)//1024} KB)")

# 深色底 / 浅色底 128px 预览，方便检验白边
for bg_color, path in [((24, 32, 48, 255), PREVIEW_DARK), ((255, 255, 255, 255), PREVIEW_LIGHT)]:
    bg = Image.new("RGBA", (160, 160), bg_color)
    small = canvas.resize((128, 128), Image.LANCZOS)
    bg.paste(small, (16, 16), small)
    bg.convert("RGB").save(path)
    print(f"预览: {path}")
