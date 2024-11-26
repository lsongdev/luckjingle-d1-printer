from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as ET

try:
    import qrcode
except ImportError:
    qrcode = None

try:
    import barcode
    from barcode.writer import ImageWriter
except ImportError:
    barcode = None


def render(layout_xml, width=384):
    """将 XML 布局渲染为 PIL Image 对象"""
    img = Image.new("L", (width, 1200), color=255)
    draw = ImageDraw.Draw(img)
    root = ET.fromstring(layout_xml)
    current_y = 0

    def ensure_height(y):
        if y > img.height:
            new_img = Image.new("L", (width, y + 200), color=255)
            new_img.paste(img, (0, 0))
            return new_img, ImageDraw.Draw(new_img)
        return img, draw

    def measure_element(el):
        if el.tag == "text":
            font_name = el.get("font", "zpix.ttf")
            font_size = int(el.get("font_size", 18))
            font = ImageFont.truetype(font_name, font_size)
            text = el.text or ""
            tw, th = draw.textbbox((0, 0), text, font=font)[2:]
            return "text", {"font": font, "text": text, "el": el}, tw, th

        elif el.tag == "image":
            im = Image.open(el.get("src"))
            target_w = int(el.get("width", width))
            target_h = int(target_w / im.width * im.height)
            im = im.resize((target_w, target_h), resample=Image.Resampling.LANCZOS)
            return "image", {"img": im, "el": el}, target_w, target_h

        elif el.tag == "qrcode":
            if qrcode is None:
                raise RuntimeError("qrcode 库未安装，请运行: pip install 'qrcode[pil]'")
            size = int(el.get("size", 150))
            data = el.get("data", el.text or "")
            qr = qrcode.QRCode(version=1, box_size=3, border=2)
            qr.add_data(data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert("L")
            qr_img = qr_img.resize((size, size), resample=Image.Resampling.LANCZOS)
            if el.get("align") is None:
                el.set("align", "center")
            return "image", {"img": qr_img, "el": el}, size, size

        elif el.tag == "barcode":
            if barcode is None:
                raise RuntimeError("python-barcode 库未安装，请运行: pip install python-barcode")
            data = el.get("data", el.text or "")
            code_type = el.get("type", "code128")
            target_h = int(el.get("height", 60))
            writer = ImageWriter()
            writer.set_options({"module_height": 50, "quiet_zone": 2})
            CodeClass = barcode.get_barcode_class(code_type)
            code = CodeClass(data, writer=writer)
            buf = code.render()
            buf = buf.convert("L")
            import numpy as np
            arr = np.array(buf)
            white_gaps = []
            start = None
            for i in range(len(arr)):
                if arr[i].min() > 200:
                    if start is None:
                        start = i
                else:
                    if start is not None:
                        if i - start > 3:
                            white_gaps.append((start, i - 1))
                        start = None
            if start is not None and len(arr) - start > 3:
                white_gaps.append((start, len(arr) - 1))
            crop_y = len(arr)
            for s, e in white_gaps:
                if s > 50:
                    crop_y = s
                    break
            if crop_y < len(arr):
                buf = buf.crop((0, 0, buf.width, crop_y + 1))
            target_w = int(el.get("width", width))
            if target_h != buf.height or target_w != buf.width:
                buf = buf.resize((target_w, target_h), resample=Image.Resampling.LANCZOS)
            if el.get("align") is None:
                el.set("align", "center")
            return "image", {"img": buf, "el": el}, buf.width, buf.height

        elif el.tag == "hr":
            style = el.get("style", "solid")
            thickness = int(el.get("thickness", 1))
            margin = int(el.get("margin", 5))
            hr_w = int(el.get("width", width))
            h = thickness + margin * 2
            return "hr", {"style": style, "thickness": thickness, "margin": margin, "hr_w": hr_w, "el": el}, hr_w, h

        return None, None, 0, 0

    def render_element(info, x, y, container_w):
        nonlocal img, draw
        tag, data = info["tag"], info["data"]
        el = data["el"]
        align = el.get("align", "left")

        if tag == "text":
            tw, th = draw.textbbox((0, 0), data["text"], font=data["font"])[2:]
            if align == "left":
                tx = x
            elif align == "center":
                tx = x + (container_w - tw) // 2
            elif align == "right":
                tx = x + container_w - tw
            draw.text((tx, y), data["text"], font=data["font"], fill=0)

        elif tag == "image":
            im = data["img"]
            if align == "left":
                ix = x
            elif align == "center":
                ix = x + (container_w - im.width) // 2
            elif align == "right":
                ix = x + container_w - im.width
            img, draw = ensure_height(y + im.height)
            img.paste(im, (ix, y))

        elif tag == "hr":
            thickness = data["thickness"]
            margin = data["margin"]
            hr_w = data["hr_w"]
            style = data["style"]
            line_y = y + margin + thickness // 2
            if align == "center":
                hx = x + (container_w - hr_w) // 2
            elif align == "right":
                hx = x + container_w - hr_w
            else:
                hx = x

            if style == "solid":
                draw.line([(hx, line_y), (hx + hr_w, line_y)], fill=0, width=thickness)
            elif style == "dashed":
                dash_len = 8
                gap_len = 4
                cx = hx
                while cx < hx + hr_w:
                    end = min(cx + dash_len, hx + hr_w)
                    draw.line([(cx, line_y), (end, line_y)], fill=0, width=thickness)
                    cx += dash_len + gap_len
            elif style == "dotted":
                dot_gap = 4
                cx = hx
                while cx < hx + hr_w:
                    draw.ellipse([(cx, line_y - thickness//2), (cx + thickness, line_y + thickness//2)], fill=0)
                    cx += dot_gap + thickness

    for line in root.findall("line"):
        line_height = 30
        elements = list(line)
        measured = []
        for el in elements:
            tag, data, ew, eh = measure_element(el)
            if tag:
                measured.append({"tag": tag, "data": data, "w": ew, "h": eh})
                line_height = max(line_height, eh)

        if len(measured) > 1:
            # 多元素自动水平排列
            total_fixed = 0
            auto_cols = []
            for i, m in enumerate(measured):
                w_attr = m["data"]["el"].get("width")
                if w_attr:
                    m["w"] = int(w_attr)
                    total_fixed += m["w"]
                else:
                    auto_cols.append(i)

            if auto_cols:
                remaining = width - total_fixed
                per_auto = max(0, remaining // len(auto_cols))
                for idx in auto_cols:
                    measured[idx]["w"] = per_auto

            x_off = 0
            for m in measured:
                render_element(m, x_off, current_y, m["w"])
                x_off += m["w"]
        else:
            for m in measured:
                render_element(m, 0, current_y, width)

        current_y += line_height

    img = img.crop((0, 0, width, current_y))
    return img
