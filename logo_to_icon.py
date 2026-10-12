"""将商标 PNG 转为桌面图标：去白底、裁掉文字、生成多尺寸 ICO"""
from PIL import Image

SRC = r"d:\Desktop\文档存储检索工具商标名推荐 (4).png"
OUT = r"c:\Users\ADMIN\Documents\trae_projects\word_wearch\app_icon.ico"
PREVIEW = r"c:\Users\ADMIN\Documents\trae_projects\word_wearch\icon_preview.png"

img = Image.open(SRC).convert("RGBA")
W, H = img.size
print(f"原图: {W}x{H}")

# --- 1. 去白底：接近白色的像素设为透明 ---
px = img.load()
for y in range(H):
    for x in range(W):
        r, g, b, a = px[x, y]
        if r > 235 and g > 235 and b > 235:
            px[x, y] = (r, g, b, 0)

# --- 2. 裁剪：只保留上半部分的环形图形（去掉下方文字）---
# 环形图形大致在垂直方向 20%~55% 区间，先按 55% 高度裁剪再按内容收紧
img = img.crop((0, 0, W, int(H * 0.56)))

# 按非透明像素的实际边界收紧（裁掉四周留白）
bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)

# --- 3. 四周加少量透明边距（约 8%），让图标视觉居中 ---
w, h = img.size
side = max(w, h)
margin = int(side * 0.08)
canvas = Image.new("RGBA", (side + margin * 2, side + margin * 2), (0, 0, 0, 0))
canvas.paste(img, ((canvas.width - w) // 2, (canvas.height - h) // 2), img)
img = canvas

# --- 4. 生成多尺寸 ICO ---
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save(OUT, format="ICO", sizes=sizes)
print(f"OK: {OUT}")

# 预览
img.resize((128, 128), Image.LANCZOS).save(PREVIEW)
print(f"PREVIEW: {PREVIEW}")
