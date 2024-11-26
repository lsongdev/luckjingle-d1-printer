import serial
from PIL import Image, ImageFont, ImageDraw
from dither import Dither

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
        
    def print_text(self, text, font, font_size = 20):
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
        d = Dither(img.size, img.load())
        d.apply(self.brightnes, contrast=self.contrast**2)
        # set density (0000 for low, 0100 for normal, 0200 for high)
        self.device.write(bytes.fromhex("10FF10000200".ljust(256, "0")))
        imgHexStr = d.to_hex_str()
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
    