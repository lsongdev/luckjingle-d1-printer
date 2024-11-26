import asyncio
from dither import applyDither
from PIL import Image, ImageFont, ImageDraw

CHARACTERISTIC_1 = "0000ff01-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_2 = "0000ff02-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_3 = "0000ff03-0000-1000-8000-00805f9b34fb"

class BluetoothDevice:
    def __init__(self, address: str):
        import bleak
        self.client = bleak.BleakClient(address)

    async def open(self):
        await self.client.connect()
        await self.client.start_notify(CHARACTERISTIC_1, self._notification_handler)
        await self.client.start_notify(CHARACTERISTIC_3, self._notification_handler)

    async def close(self):
        await self.client.disconnect()

    async def write(self, data):
        await self.client.write_gatt_char(CHARACTERISTIC_2, data)

    def _notification_handler(self, sender, data):
        """处理BLE通知"""
        print(f"BLE通知 - 发送者: {sender}, 数据: {data}")
        if data == b"\xaa":
            print("接收到终止信号")

class SerialPortDevice:
    def __init__(self, path):
        self.path = path
        self.device = None
    async def open(self):
      from serial import Serial
      self.device = Serial(self.path)
    async def close(self):
        self.device.close()
    async def write(self, data):
        self.device.write(data)


class LuckPrinter:
    def __init__(self, device):
        self.device = device
        self.width = 384
        self.brightness = 0.35
        self.contrast = 1.45
        self.density = 1

    async def initialize(self):
        await self.open()
        await self.enable()
        await self.disable_shutdown()

    async def open(self):
        await self.device.open()
    async def close(self):
        await self.device.close()

    async def enable(self):
        await self.device.write(bytes.fromhex("10FF40"))
        await self.device.write(bytes.fromhex("10FFF103"))

    async def print_end(self):
        await self.device.write(bytes.fromhex("1B4A64".rjust(256, "0")))
        await self.device.write(bytes.fromhex("10FFF145"))

    async def disable_shutdown(self):
        await self.device.write(bytes.fromhex("10FF120000"))

    async def print_text(self, text, font="zpix.ttf", font_size=20):
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
        await self.print_image(img)

    def print_image_file(self, path):
        img = Image.open(path)
        self.print_image(img)

    async def print_image(self, img):
        img = img.convert("RGB")
        img = img.resize(
            (self.width, int(img.height * self.width / img.width)), Image.LANCZOS
        )
        imgHexStr = applyDither(
            img.size, img.load(), self.brightness, contrast=self.contrast**2
        )
        # set density (0000 for low, 0100 for normal, 0200 for high)
        await self.device.write(bytes.fromhex(("10FF1000" + "0200").ljust(256, "0")))
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
        await self.device.write(
            bytes.fromhex(
                ("1D7630003000" + fronthex + endhex).ljust(32, "0") + imgHexStr[0:224]
            )
        )
        # send the image data in chunks
        for i in range(32 * 7, len(imgHexStr), 256):
            str = imgHexStr[i : i + 256]
            if len(str) < 256:
                str = str.ljust(256, "0")
            await self.device.write(bytes.fromhex(str))


async def main():
    # BLE示例 // run scan.py to get address
    # device = BluetoothDevice("028EBD80-9CCC-AD10-E727-8715AF47A664")
    device = BluetoothDevice("60:6E:41:62:DC:F4")

    # 串口示例
    # device = SerialPortDevice("/dev/rfcomm1")
    printer = LuckPrinter(device)

    try:
        await printer.initialize()
        await printer.print_text("Hello, World!")
        await printer.print_end()
    finally:
        await printer.close()


if __name__ == "__main__":
    asyncio.run(main())
