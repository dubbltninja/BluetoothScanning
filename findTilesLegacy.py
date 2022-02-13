import asyncio
from asyncio.windows_events import NULL
from bleak import BleakScanner

# Script by Madeline
async def main():
    #devices = await BleakScanner.discover()
    tileUUID = "0000feed-0000-1000-8000-00805f9b34fb"
    metadatatile = "{'uuids': ['0000feed-0000-1000-8000-00805f9b34fb']"
    async with BleakScanner() as scanner:
        await asyncio.sleep(45.0)
        #find each discoverable device
        for d in scanner.discovered_devices:
            #if it's a Tile based on the UUID then display it
            if tileUUID in d.metadata["uuids"]:
                print("NAME: ", d.name, " ADDRESS: ", d.address, " METADATA: ", d.metadata)

asyncio.run(main())