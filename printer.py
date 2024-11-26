import serial
from PIL import Image, ImageFont, ImageDraw

# credits to https://www.emexee.com/2022/01/thermal-printer-image-converter.html
# https://github.com/LynMoe/DingdangD1-PoC/blob/main/app.py#L12
# using floyd-steinberg dithering
def applyDither(size, pixels, brightness, contrast):
    def getValue(pixels, y, x):
        return int((pixels[x, y][0] + pixels[x, y][1] + pixels[x, y][2]) / 3)
    def setValue(pixels, y, x, v):
        pixels[x, y] = (v, v, v)
    def nudgeValue(pixels, y, x, v):
        v = int(v)
        pixels[x, y] = (pixels[x, y][0] + v, pixels[x, y][1] + v, pixels[x, y][2] + v)
    w, h = size
    for y in range(h):
        for x in range(w):
            for i in range(3):
                r, g, b = pixels[x, y]
                arr = [r, g, b]
                arr[i] += (brightness - 0.5) * 256
                arr[i] = (arr[i] - 128) * contrast + 128
                arr[i] = int(min(max(arr[i], 0), 255))
                pixels[x, y] = (arr[0], arr[1], arr[2])

    for y in range(h):
        BOTTOM_ROW = y == h - 1
        for x in range(w):
            LEFT_EDGE = x == 0
            RIGHT_EDGE = x == w - 1
            i = (y * w + x) * 4
            level = getValue(pixels, y, x)
            newLevel = (level < 128) * 0 + (level >= 128) * 255
            setValue(pixels, y, x, newLevel)
            error = level - newLevel
            if not RIGHT_EDGE:
                nudgeValue(pixels, y, x + 1, error * 7 / 16)
            if not BOTTOM_ROW and not LEFT_EDGE:
                nudgeValue(pixels, y + 1, x - 1, error * 3 / 16)
            if not BOTTOM_ROW:
                nudgeValue(pixels, y + 1, x, error * 5 / 16)
            if not BOTTOM_ROW and not RIGHT_EDGE:
                nudgeValue(pixels, y + 1, x + 1, error * 1 / 16)
    result = ""
    for y in range(size[1]):
        for x in range(size[0]):
            r, g, b = pixels[x, y]
            if r + g + b > 600:
                result += '0'
            else:
                result += '1'
    # start bits
    result = '1' + '0' * 318 + result
    # convert to hex
    return hex(int(result, 2))[2:]


class Printer:
    def __init__(self, path):
        self.width = 384
        self.brightnes = 0.35
        self.contrast = 1.45
        self.density = 1
        self.device = serial.Serial(path)
        self.enable()
        self.disable_shutdown()
        
    def enable(self):
        # enable the printer(for model D1)
        self.device.write(bytes.fromhex("10FF40"))
        self.device.write(bytes.fromhex("10FFF103"))
        
    def disable_shutdown(self):
        # disable shutdown
        self.device.write(bytes.fromhex("10FF120000"))
        
    def print_text(self, text, font="zpix.ttf", font_size = 20):
        font = ImageFont.truetype(font, font_size)
        content = ""
        line_length = 0
        for i, c in enumerate(text):
            if c == "\n":
                line_length = 0
                content += "\n"
                continue
            elif ord(c) <= 256:
                l = 0.5
            else:
                l = 1
            if line_length + l > self.width // font_size - 2:
                content += "\n"
                line_length = 0
            line_length += l
            content += c

        line_cnt = content.count("\n") + 1
        img = Image.new("RGB", (self.width, (font_size + 2) * line_cnt), "white")
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), str(content), fill="black", font=font)
        self.print_image(img)

    def print_image_file(self, path):
        img = Image.open(path)
        self.print_image(img)
        
    def print_image(self, img):
        img = img.convert("RGB")
        img = img.resize((self.width, int(img.height * self.width / img.width)), Image.LANCZOS)
        imgHexStr = applyDither(img.size, img.load(), self.brightnes, contrast=self.contrast**2)
        # set density (0000 for low, 0100 for normal, 0200 for high)
        self.device.write(bytes.fromhex(("10FF1000" + "0200").ljust(256, "0")))
        hexlen = hex(int(len(imgHexStr) / 96) + 3)[2:]
        # little-endian for the length of hex lines
        fronthex = hexlen
        endhex = "0"
        if len(hexlen) > 2:
            fronthex = hexlen[1:3]
            endhex += hexlen[0:1]
        else:
            endhex += "0"
        # start command with data length
        self.device.write(bytes.fromhex(("1D7630003000" + fronthex + endhex).ljust(32, "0") + imgHexStr[0:224]))
        # send the image data in chunks
        for i in range(32 * 7, len(imgHexStr), 256):
            str = imgHexStr[i : i + 256]
            if len(str) < 256:
                str = str.ljust(256, "0")
            self.device.write(bytes.fromhex(str))

if __name__ == "__main__":
    printer = Printer("/dev/rfcomm1")
    # printer.print_image_file("cat.jpg")
    printer.print_text("hello world\n\n\n")