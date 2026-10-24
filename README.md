# LuckJingle Printer

<img width="300" src="https://ae01.alicdn.com/kf/Se12173c0674d4859a9c613cb259ff593k/LUCK-JINGLE-Sticker-Printer-Machine-Mini-Bluetooth-Inkless-Thermal-Photo-Printer-Compatible-with-Android-IOS.jpg" />

[[🛒 Buy now]](https://mobile.yangkeduo.com/goods2.html?goods_id=215919711645)

## Setup

```shell
~$ pip install -r requirements.txt
~$ python3 printer.py
```

## Command-line printing

```shell
# Print text
python3 main.py text "Hello, World!"

# Print an image
python3 main.py image output.png

# Render and print an XML layout (defaults to receipt.xml)
python3 main.py xml receipt.xml
python3 main.py
```

The printer address defaults to `02:34:6B:35:A0:E3`. Override it with `--device`,
either before or after the command. Text size defaults to 20 pixels:

```shell
python3 main.py --device AA:BB:CC:DD:EE:FF text "Hello" --font-size 24
python3 main.py image output.png --device AA:BB:CC:DD:EE:FF
```

## Example

```python
import asyncio
from luck_printer import LuckPrinter, BluetoothDevice

async def main():
  # BLE示例 // run scan.py to get address
  device = BluetoothDevice("028EBD80-9CCC-AD10-E727-8715AF47A664")
  await device.open()

  # 串口示例
  # from serial import Serial
  # device = Serial("/dev/rfcomm1")

  printer = LuckPrinter(device)

  try:
    await printer.initialize()
    await printer.print_text("Hello, World!")
    await printer.print_end()
  finally:
    await printer.close()

if __name__ == "__main__":
  asyncio.run(main())
```

## `rfcomm`

```shell
~$ bluetoothctl
[bluetoothctl]# agent on
[bluetoothctl]# discoverable on
[bluetoothctl]# scan on
[bluetoothctl]# trust <address>
[bluetoothctl]# pair <address>

~$ sudo rfcomm connect 1 <address>
```

## Credits

+ <https://github.com/LynMoe/DingdangD1-PoC>
+ <https://github.com/Lakr233/GGLyn>
+ <https://github.com/SolidZORO/zpix-pixel-font>
+ <https://github.com/yihong0618/blue>
