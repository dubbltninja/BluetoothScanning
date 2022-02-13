import asyncio
from bleak import BleakScanner
import sys
from manufacturers import MANUFACTURERS
from enum import Enum

# usage:
# python3 discover.py [search time] [address]
# 
# This script discovers and prints all nearby Bluetooth devices.

devices_found = 0
addr_list = []
search_addr = None
print_string_append = ""

# Label things true or false depending on what information you want to see:
class Display_Attributes(Enum):
    DEVICE_NUM = True
    NAME = True
    ADDRESS = True
    METADATA = False # a lot of redundant information
    RSSI = True
    INTERPRET_RSSI = True # - displays connection strength
    UUIDS = False
    ADVERTISEMENT_DATA = False

class Pad_Lengths(Enum):
    DEVICE_NUM = 4
    NAME = 23
    RSSI = 6
    INTERPRET_RSSI = 16

def pad(string, pad_length):
    padded_string = string
    # handle strings that are a bit too long
    # also, yes technically the line below can cause collisions with other pad lengths if there were more
    # but we only want to have the IF continue if we are dealing with a name
    if len(padded_string) > pad_length and pad_length == Pad_Lengths.NAME.value:
        str1 = padded_string[:pad_length - 2] + "- "
        str2 = ""
        dev_pad = 0
        # handle extra padding in case of device number being printed
        if Display_Attributes.DEVICE_NUM.value == True:
            dev_pad = Pad_Lengths.DEVICE_NUM.value
            str2 += str(" " * dev_pad)
        str2 += padded_string[pad_length - 2:]
        while len(str2) < (pad_length + dev_pad) :
            str2 += " "
        padded_string = str1
        # extra name line should be printed on separate line
        global print_string_append
        print_string_append = "\n" + str2
    else:
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
    if Display_Attributes.INTERPRET_RSSI.value == True:
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

def print_device_data(device, advertisement_data):
    info = ""
    global devices_found
    if Display_Attributes.DEVICE_NUM.value == True:
        info += pad(str(devices_found), Pad_Lengths.DEVICE_NUM.value)
    if Display_Attributes.NAME.value == True:
        #if no name, print manufacturer name
        if device.name == None or device.name[:2] == device.address[:2]:
            name = get_manufacturer_name(device)
            info += pad(name, Pad_Lengths.NAME.value)
        else:
            info += pad(device.name, Pad_Lengths.NAME.value)
    if Display_Attributes.ADDRESS.value == True:
        info += device.address + "  "
    if Display_Attributes.RSSI.value == True:
        info += str(device.rssi) + " "
        if Display_Attributes.INTERPRET_RSSI.value == True:
            if int(device.rssi) > -50:
                info += pad("\u001b[32mStrong\u001b[0m", Pad_Lengths.INTERPRET_RSSI.value - 3)
            elif int(device.rssi) > -70:
                info += pad("\u001b[33mModerate\u001b[0m", Pad_Lengths.INTERPRET_RSSI.value - 3)
            elif int(device.rssi) < -69:
                info += pad("\u001b[31mWeak\u001b[0m", Pad_Lengths.INTERPRET_RSSI.value - 3)
    if Display_Attributes.METADATA.value == True:
        info += str(device.metadata) + "  "
    if Display_Attributes.UUIDS.value == True:
        info += str(device.metadata["uuids"]) + "  "
    if Display_Attributes.ADVERTISEMENT_DATA.value == True:
        info += str(advertisement_data)
    # print a new header every 30 lines
    if devices_found % 30 == 0:
        print_header()
    global print_string_append
    print(info + print_string_append)
    print_string_append = ""

# I pretty much just stole this method from bleak:
# https://bleak.readthedocs.io/en/latest/_modules/bleak/backends/device.html
def get_manufacturer_name(device) -> str:
    if not device.name:
        if "manufacturer_data" in device.metadata:
            ks = list(device.metadata["manufacturer_data"].keys())
            if len(ks):
                return str(MANUFACTURERS.get(ks[0], MANUFACTURERS.get(0xFFFF)))
    # test if tile enabled
    elif device.metadata :
        if "0000feed-0000-1000-8000-00805f9b34fb" in device.metadata["uuids"] :
            return "Tile Enabled Device"
    return "Unknown Manufacturer"

def detection_callback(device, advertisement_data):
    # Whenever a device is found...
    global search_addr
    global addr_list
    global devices_found
    if search_addr == None:
        # if not searching for particular address
        if device.address not in addr_list:
            # find and document only unique instances
            devices_found += 1
            addr_list.append(device.address)
            print_device_data(device, advertisement_data)
    elif device.address == search_addr:
        # if we found the device we're looking for
        print("Search Device Found!")
        print_device_data(device, advertisement_data)
        print(advertisement_data)
        # since we found what we're looking for, exit
        sys.exit(0)
    else:
        # if we found a device, but it wasn't the one we are looking for
        # just to show the user that the script is working
        if device.address not in addr_list:
            addr_list.append(device.address)
            devices_found += 1
            print("Found a device (" + str(devices_found) + ")")

async def main(time = 60.0, addr = None):
    global devices_found
    args = sys.argv[1:]
    if len(args) == 0:
        print("\u001b[1mSearching for all BT devices for", time, "seconds...\u001b[0m")
    elif len(args) == 1:
        time = float(args[0])
        print("\u001b[1mSearching for all BT devices for", time, "seconds...\u001b[0m")
    elif len(args) == 2:
        time = float(args[0])
        addr = str(args[1])
        global search_addr
        search_addr = addr
        print("\u001b[1mSearching for address", search_addr, "for", time, "seconds...\u001b[0m")
    print_header()
    # Start the scanner and listen for callbacks
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
    await scanner.start()
    await asyncio.sleep(time)
    await scanner.stop()
    print("\nTotal BT devices found:", str(devices_found))

# Run the program, catching any ^Cs
try: 
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nTotal BT devices found:", str(devices_found), "(scanner terminated early)")
    sys.exit(0)
