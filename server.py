#!/usr/bin/env python3
"""Luck Printer HTTP Server"""

import argparse
import asyncio
import base64
import io
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

import io
from printer import BluetoothDevice, SerialPortDevice, LuckPrinter
from render import render


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


class PrintRequestHandler(BaseHTTPRequestHandler):
    printer = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            if parsed.path == "/print/text":
                self.handle_print_text(body)
            elif parsed.path == "/print/image":
                self.handle_print_image(body)
            elif parsed.path == "/render":
                self.handle_render(body)
            elif parsed.path == "/print/layout":
                self.handle_print_layout(body)
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            self.send_error(500, str(e))

    def handle_print_text(self, body):
        data = json.loads(body)
        text = data.get("text", "")
        font = data.get("font", "zpix.ttf")
        font_size = data.get("font_size", 20)

        loop.run_until_complete(self.printer.initialize())
        loop.run_until_complete(self.printer.print_text(text, font=font, font_size=font_size))
        loop.run_until_complete(self.printer.print_end())
        loop.run_until_complete(self.printer.close())

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "text": text}).encode())

    def handle_print_image(self, body):
        data = json.loads(body)
        image_data = data.get("image", "")
        if image_data:
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = body

        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))

        loop.run_until_complete(self.printer.initialize())
        loop.run_until_complete(self.printer.print_image(img))
        loop.run_until_complete(self.printer.print_end())
        loop.run_until_complete(self.printer.close())

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def handle_render(self, body):
        layout_xml = body.decode("utf-8")
        img = render(layout_xml)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.end_headers()
        self.wfile.write(buf.getvalue())

    def handle_print_layout(self, body):
        layout_xml = body.decode("utf-8")
        img = render(layout_xml)

        loop.run_until_complete(self.printer.initialize())
        loop.run_until_complete(self.printer.print_image(img))
        loop.run_until_complete(self.printer.print_end())
        loop.run_until_complete(self.printer.close())

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode())

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")


def run_server(port: int, device_type: str, device_address: str):
    if device_type == "ble":
        device = BluetoothDevice(device_address)
    else:
        device = SerialPortDevice(device_address)

    printer = LuckPrinter(device)
    PrintRequestHandler.printer = printer

    server_address = ("", port)
    httpd = HTTPServer(server_address, PrintRequestHandler)
    print(f"Server started on http://localhost:{port}")
    print(f"Device: {device_type} {device_address}")
    print(f"Endpoints:")
    print(f"  GET  /health")
    print(f"  POST /render")
    print(f"  POST /print/text")
    print(f"  POST /print/image")
    print(f"  POST /print/layout")
    print(f"\nExample:")
    print(f'  curl -X POST http://localhost:{port}/render -d @receipt.xml > receipt.png')
    print(f'  curl -X POST http://localhost:{port}/print/layout -d @receipt.xml')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        loop.run_until_complete(printer.close())
        httpd.shutdown()
    finally:
        loop.close()


def main():
    parser = argparse.ArgumentParser(description="Luck Printer Server")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Server port")
    parser.add_argument("-d", "--device", type=str, default="ble",
                      choices=["ble", "serial"], help="Device type")
    parser.add_argument("-a", "--address", type=str,
                      default="D3808B0D-2DDF-2E33-B434-8FC9576A2BBE",
                      help="BLE address or serial port")
    args = parser.parse_args()

    run_server(args.port, args.device, args.address)


if __name__ == "__main__":
    main()