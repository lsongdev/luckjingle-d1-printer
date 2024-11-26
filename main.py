import asyncio
from render import render
from printer import BluetoothDevice, LuckPrinter


async def main():
    with open("receipt.xml", "r", encoding="utf-8") as f:
        layout_xml = f.read()

    # BLE示例 // run scan.py to get address
    # device = BluetoothDevice("028EBD80-9CCC-AD10-E727-8715AF47A664")
    device = BluetoothDevice("D3808B0D-2DDF-2E33-B434-8FC9576A2BBE")
    # device = BluetoothDevice("60:6E:41:62:DC:F4")

    # 串口示例
    # from printer import SerialPortDevice
    # device = SerialPortDevice("/dev/rfcomm1")

    printer = LuckPrinter(device)

    try:
        await printer.initialize()
        img = render(layout_xml)
        await printer.print_image(img)
        await printer.print_end()
    finally:
        await printer.close()


if __name__ == "__main__":
    asyncio.run(main())
