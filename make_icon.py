"""生成应用图标：文档+放大镜，紫蓝渐变圆角背景"""
from PIL import Image, ImageDraw
import math

def make_icon(size=256, out="app_icon.ico"):
    # 4x 超采样抗锯齿
    S = 4
    W = size * S
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # --- 圆角矩形背景，垂直渐变 #667eea -> #764ba2 ---
    c1 = (0x66, 0x7e, 0xea)
    c2 = (0x76, 0x4b, 0xa2)
    radius = int(W * 0.20)
    bg = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    bgd = ImageDraw.Draw(bg)
    bgd.rounded_rectangle([0, 0, W - 1, W - 1], radius=radius, fill=(255, 255, 255, 255))
    # 渐变
    grad = Image.new("RGB", (1, W))
    for y in range(W):
        t = y / (W - 1)
        grad.putpixel((0, y), tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))
    grad = grad.resize((W, W))
    mask = bg.split()[3]
    img.paste(grad, (0, 0), mask)

    cx = W / 2

    # --- 文档（白色圆角矩形，带折角） ---
    dw, dh = W * 0.44, W * 0.56
    dx, dy = cx - dw / 2, W * 0.22
    fold = dw * 0.22
    doc = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    dd = ImageDraw.Draw(doc)
    dd.rounded_rectangle([dx, dy, dx + dw, dy + dh], radius=int(W * 0.03),
                         fill=(255, 255, 255, 255))
    # 折角：右上的小三角（挖掉再画浅色三角）
    dd.polygon([(dx + dw - fold + 1, dy - 1), (dx + dw + 1, dy - 1),
                (dx + dw + 1, dy + fold - 1)], fill=(0, 0, 0, 0))
    dd.polygon([(dx + dw - fold + S, dy), (dx + dw, dy + fold - S),
                (dx + dw, dy)], fill=(219, 226, 250, 255))
    # 文档内的横线（浅紫）——画在文档图层上
    for i, yf in enumerate([0.36, 0.46, 0.56]):
        lw = dw * (0.58 if i < 2 else 0.36)
        dd.rounded_rectangle([dx + dw * 0.13, W * yf, dx + dw * 0.13 + lw, W * yf + W * 0.022],
                             radius=int(W * 0.011), fill=(176, 187, 232, 255))
    img = Image.alpha_composite(img, doc)
    d = ImageDraw.Draw(img)

    # --- 放大镜（右上叠放，白色描边+半透明镜片） ---
    mg_r = W * 0.155
    mg_cx, mg_cy = cx + W * 0.13, W * 0.60
    ring = int(W * 0.045)
    # 手柄
    hx1 = mg_cx + mg_r * math.cos(math.radians(45))
    hy1 = mg_cy + mg_r * math.sin(math.radians(45))
    hx2 = hx1 + W * 0.11
    hy2 = hy1 + W * 0.11
    d.line([(hx1, hy1), (hx2, hy2)], fill=(255, 255, 255, 255), width=ring)
    d.ellipse([hx2 - ring * 0.62, hy2 - ring * 0.62,
               hx2 + ring * 0.62, hy2 + ring * 0.62], fill=(255, 255, 255, 255))
    # 镜片：白圈 + 半透明浅蓝镜片
    d.ellipse([mg_cx - mg_r, mg_cy - mg_r, mg_cx + mg_r, mg_cy + mg_r],
              fill=(232, 241, 251, 235), outline=(255, 255, 255, 255), width=ring)
    # 镜片高光
    d.arc([mg_cx - mg_r * 0.6, mg_cy - mg_r * 0.6,
           mg_cx + mg_r * 0.2, mg_cy + mg_r * 0.2],
          start=110, end=220, fill=(255, 255, 255, 160), width=int(S * 3))

    # 缩小到目标尺寸（LANCZOS 抗锯齿）
    img = img.resize((size, size), Image.LANCZOS)

    # 生成 ico（内嵌多尺寸）
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(out, format="ICO", sizes=sizes)
    print(f"OK: {out}")

if __name__ == "__main__":
    make_icon()
