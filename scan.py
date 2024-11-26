import asyncio
from bleak import BleakScanner

async def scan():
    devices = await BleakScanner.discover()
    
    for device in devices:
        print(f"Name: {device.name}, Addr: {device.address}")
    

async def main():
    await scan()

if __name__ == "__main__":
    asyncio.run(main())