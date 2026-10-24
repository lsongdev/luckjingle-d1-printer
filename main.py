import asyncio
import argparse
from pathlib import Path

from PIL import Image
from render import render
from printer import BluetoothDevice, LuckPrinter


def parse_args():
    parser = argparse.ArgumentParser(description="Print text, an image, or an XML layout.")
    parser.add_argument(
        "--device", default="02:34:6B:35:A0:E3",
        help="Bluetooth printer address (default: %(default)s)",
    )
    commands = parser.add_subparsers(dest="command")

    text_cmd = commands.add_parser("text", help="Print text")
    text_cmd.add_argument("--device", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    text_cmd.add_argument("content", help="Text to print; use quotes for spaces or newlines")
    text_cmd.add_argument("--font-size", type=int, default=20)

    image_cmd = commands.add_parser("image", help="Print an image file")
    image_cmd.add_argument("--device", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    image_cmd.add_argument("file", type=Path)

    xml_cmd = commands.add_parser("xml", help="Render and print an XML layout")
    xml_cmd.add_argument("--device", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    xml_cmd.add_argument("file", type=Path, nargs="?", default=Path("receipt.xml"))

    args = parser.parse_args()
    if args.command is None:
        args.command = "xml"
        args.file = Path("receipt.xml")
    return args


async def main(args):
    device = BluetoothDevice(args.device)
    printer = LuckPrinter(device)

    try:
        await printer.initialize()
        if args.command == "text":
            await printer.print_text(args.content, font_size=args.font_size)
        elif args.command == "image":
            with Image.open(args.file) as img:
                await printer.print_image(img)
        else:
            layout_xml = args.file.read_text(encoding="utf-8")
            await printer.print_image(render(layout_xml))
        await printer.print_end()
    finally:
        await printer.close()


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
