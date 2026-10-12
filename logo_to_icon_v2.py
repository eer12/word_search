"""用 rembg 专业抠图：将商标 PNG 转为干净的桌面图标"""
from rembg import remove
from PIL import Image

SRC = r"d:\Desktop\文档存储检索工具商标名推荐 (4).png"
OUT = r"c:\Users\ADMIN\Documents\trae_projects\word_wearch\app_icon.ico"
PREVIEW = r"c:\Users\ADMIN\Documents\trae_projects\word_wearch\icon_preview.png"

img = Image.open(SRC).convert("RGBA")
W, H = img.size
print(f"原图: {W}x{H}")

# 先裁掉下方文字区域（只保留环形图形，约占顶部 56%）
img = img.crop((0, 0, W, int(H * 0.56)))

# rembg 抠图（AI 模型，边缘干净）
img = remove(img)

# 按非透明像素的实际边界收紧
bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)

# 四周加少量透明边距（约 6%），视觉居中
w, h = img.size
side = max(w, h)
margin = int(side * 0.06)
canvas = Image.new("RGBA", (side + margin * 2, side + margin * 2), (0, 0, 0, 0))
canvas.paste(img, ((canvas.width - w) // 2, (canvas.height - h) // 2), img)
img = canvas

# 生成多尺寸 ICO
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save(OUT, format="ICO", sizes=sizes)
print(f"OK: {OUT}")

# 预览
img.resize((128, 128), Image.LANCZOS).save(PREVIEW)
print(f"PREVIEW: {PREVIEW}")
