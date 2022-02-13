import asyncio
from bleak import BleakScanner
from enum import Enum
import sys

# usage:
# python3 findTiles.py [search time] [address]
# 
# This script discovers and prints all nearby Tile Devices.

known_devices = {
    "Spare key":            "E6:9E:55:1A:91:28",
    "Wallet":               "DF:30:61:4F:AB:DA",
    "Backpack":             "E1:5B:A3:01:A0:F1",
    "Toy":                  "D1:7F:8E:E6:9E:B1",
    "madelines_earbud1":    "12:34:56:00:33:E1", 
    "madelines_earbud2":    "12:34:56:00:37:1D"
}

found_addr_list = []
search_addr = None
tileUUID = "0000feed-0000-1000-8000-00805f9b34fb"
tiles_found = 0

# Label things true or false depending on what information you want to see:
class Display_Attributes(Enum):
    DEVICE_NUM = True
    NAME = True
    ADDRESS = True
    METADATA = False # a lot of redundant information
    RSSI = True
    INTERPRET_RSSI = True # - displays connection strength - RSSI must be on to work
    UUIDS = False
    ADVERTISEMENT_DATA = False

class Pad_Lengths(Enum):
    DEVICE_NUM = 4
    NAME = 20
    RSSI = 3
    INTERPRET_RSSI = 17

# function to return key for any value
def get_key(val, dict) -> str:
    for key, value in dict.items():
        if val == value:
            return key
    return "no key found"

def pad(string, pad_length):
    padded_string = string
    while len(padded_string) < pad_length :
        padded_string += " "
    return padded_string

def print_header():
    head = "\u001b[7m"
    if Display_Attributes.DEVICE_NUM.value == True:
        head += pad("#", Pad_Lengths.DEVICE_NUM.value)
    if Display_Attributes.NAME.value == True:
        head += pad("Name", Pad_Lengths.NAME.value)
    if Display_Attributes.ADDRESS.value == True:
        head += pad("Address", 19)
    if Display_Attributes.INTERPRET_RSSI.value == True and Display_Attributes.RSSI.value == True:
        head += pad("Signal Strength", Pad_Lengths.INTERPRET_RSSI.value)
    elif Display_Attributes.RSSI.value == True:
        head += pad("RSSI:", Pad_Lengths.RSSI.value)
    if Display_Attributes.METADATA.value == True:
        head += "Metadata:" + (" " * 20)
    if Display_Attributes.UUIDS.value == True:
        head += "UUID(s):" + (" " * 20)
    if Display_Attributes.ADVERTISEMENT_DATA.value == True:
        head += "Advertisement Data:" + (" " * 20)
    print(head + "\u001b[0m")

def get_device_data(device, advertisement_data) -> str:
    info = ""
    if Display_Attributes.DEVICE_NUM.value == True:
        info += pad(str(tiles_found), Pad_Lengths.DEVICE_NUM.value)
    if Display_Attributes.NAME.value == True:
        info += pad(device.name, Pad_Lengths.NAME.value)
    if Display_Attributes.ADDRESS.value == True:
        info += device.address + "  "
    if Display_Attributes.RSSI.value == True:
        info += str(device.rssi) + " "
        if Display_Attributes.INTERPRET_RSSI.value == True:
            if int(device.rssi) > -50:
                info += pad("\u001b[32mStrong           \u001b[0m", Pad_Lengths.INTERPRET_RSSI.value - 3)
            elif int(device.rssi) > -70:
                info += pad("\u001b[33mModerate         \u001b[0m", Pad_Lengths.INTERPRET_RSSI.value - 3)
            elif int(device.rssi) < -69:
                info += pad("\u001b[31mWeak             \u001b[0m", Pad_Lengths.INTERPRET_RSSI.value - 3)
    # fix null metadata on Linux machines...
    if device.metadata:
        if Display_Attributes.METADATA.value == True:
            info += str(device.metadata) + "  "
        if Display_Attributes.UUIDS.value == True:
            info += str(device.metadata["uuids"]) + "  "
    if Display_Attributes.ADVERTISEMENT_DATA.value == True:
        info += (str(advertisement_data))
    return info

def detection_callback(device, advertisement_data):
    # Whenever a device is found...
    global search_addr
    global found_addr_list
    global tileUUID
    global known_devices
    global tiles_found
    if tileUUID in device.metadata["uuids"]:
        # we found a tile
        if search_addr == None:
            # if not searching for any particular tile:
            # exclude devices we don't want to appear
            if device.address not in found_addr_list:
                # document only unique instances
                tiles_found += 1
                found_addr_list.append(device.address)
                # if device is known, give it a meaningful name
                if device.address in known_devices.values():
                    device.name = get_key(device.address, known_devices)
                    print(get_device_data(device, advertisement_data))
                # otherwise just print
                else:
                    device.name = "Unknown Tile"
                    print(get_device_data(device, advertisement_data))
        elif device.address == search_addr:
            print("\u001b[1m----- Tile of interest found! -----\n", get_device_data(device, advertisement_data))
            # since we found what we're looking for, exit
            sys.exit(0)

async def main(addr = None, time = 60.0):
    args = sys.argv[1:]
    global search_addr
    global tiles_found
    if len(args) == 0:
        print("\u001b[1mSearching for all Tile devices for", time, "seconds...\u001b[0m")
    elif len(args) == 1:
        time = float(args[0])
        print("\u001b[1mSearching for all Tile devices for", time, "seconds...\u001b[0m")
    elif len(args) == 2:
        time = float(args[0])
        addr = str(args[1])
        search_addr = addr
        print("\u001b[1mSearching for Tile w/ address", search_addr, "for", time, "seconds...\u001b[0m")
    print_header()    
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
    await scanner.start()
    await asyncio.sleep(time)
    await scanner.stop()
    print("\nTiles found:", str(tiles_found))

# Run the program, catching any ^Cs
try: 
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nTiles found:", str(tiles_found), "(scanner terminated early)")
    sys.exit(0)