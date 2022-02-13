import asyncio
from bleak import BleakScanner
import sys
from manufacturers import MANUFACTURERS
from enum import Enum
from datetime import datetime
from datetime import date
import calendar

# usage:
# python3 discover.py [logfilename]
# 
# This script discovers and prints all nearby Bluetooth devices to a logfile.
# If no logfile is specified, it defaults to bluetooth.log.
# Author: Tim Dibert (dubbltninja)

devices_found = 0
addr_list = []
search_addr = None
delim = " ; " 
log = None

# Label things true or false depending on what information you want to see:
class Display_Attributes(Enum):
    TIME = True
    MILITARY_TIME = False
    NAME = True
    ADDRESS = True
    METADATA = False # a lot of redundant information
    RSSI = True
    INTERPRET_RSSI = True # - displays connection strength
    UUIDS = False
    ADVERTISEMENT_DATA = False
    PRETTY_PRINT = True

class Pad_Lengths(Enum):
    TIME = 26
    NAME = 23
    RSSI = 6
    INTERPRET_RSSI = 20

def pad(string, pad_length):
    padded_string = string
    if Display_Attributes.PRETTY_PRINT.value == True:
        while len(padded_string) < pad_length :
            padded_string += " "
    global delim
    return padded_string + delim

def get_date() -> str:
    # day of week, date, time (12 hour), AM/PM
    day_of_week = calendar.day_name[date.today().weekday()]
    date_time = ""
    am_pm = ""
    if Display_Attributes.MILITARY_TIME.value == True:
        date_time = str(datetime.now())[:19]
    else:
        date_time = str(datetime.now().strftime('%Y/%m/%d %I:%M:%S'))
        if int(str(datetime.now())[11:13]) < 12:
            am_pm = " AM"
        else:
            am_pm = " PM"
    return day_of_week + " " + date_time + am_pm

def print_device_data(device, advertisement_data):
    info = ""
    if Display_Attributes.TIME.value == True:
        info += pad(get_date(), Pad_Lengths.TIME.value)
    if Display_Attributes.NAME.value == True:
        #if no name, print manufacturer name
        if device.name == None or device.name[:2] == device.address[:2]:
            name = get_manufacturer_name(device)
            info += pad(name, Pad_Lengths.NAME.value)
        else:
            info += pad(device.name, Pad_Lengths.NAME.value)
    if Display_Attributes.ADDRESS.value == True:
        # explicitly append delimiter since we're not calling pad()
        info += device.address + delim
    if Display_Attributes.RSSI.value == True:
        info += str(device.rssi) + " "
        if Display_Attributes.INTERPRET_RSSI.value == True:
            if int(device.rssi) > -50:
                info += pad("Strong", Pad_Lengths.INTERPRET_RSSI.value)
            elif int(device.rssi) > -70:
                info += pad("Moderate", Pad_Lengths.INTERPRET_RSSI.value)
            elif int(device.rssi) < -69:
                info += pad("Weak", Pad_Lengths.INTERPRET_RSSI.value)
    if Display_Attributes.METADATA.value == True:
        info += str(device.metadata) + "  "
    if Display_Attributes.UUIDS.value == True:
        info += str(device.metadata["uuids"]) + "  "
    if Display_Attributes.ADVERTISEMENT_DATA.value == True:
        info += str(advertisement_data)
    global log
    log.write(info + "\n")

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
        log.write("Search Device Found!" + "\n")
        print_device_data(device, advertisement_data)
        log.write(advertisement_data + "\n")
        # since we found what we're looking for, exit
        sys.exit(0)
    else:
        # if we found a device, but it wasn't the one we are looking for
        # just to show the user that the script is working
        if device.address not in addr_list:
            addr_list.append(device.address)
            devices_found += 1
            log.write("Found a device (" + str(devices_found) + ")" + "\n")

async def main():
    global devices_found
    global log
    scan_time = 10
    log = open("bluetooth.log", "a")
    log.write("Searching for all BT devices for " + str(scan_time) + " seconds..." + "\n")
    # Start the scanner and listen for callbacks
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
    await scanner.start()
    await asyncio.sleep(float(scan_time))
    await scanner.stop()
    # give scan summary
    log.write(get_date() + " Total BT devices found: " + str(devices_found) + "\n")
    log.close()

# Scan for two minutes
asyncio.run(main())

