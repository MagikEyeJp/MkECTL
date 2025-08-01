# -*- coding: utf-8 -*-

"""MagikEye devices discovery using the SSDP
"""
__author__ = "Jan Heller"
__copyright__ = "Copyright (c) 2021, Magik-Eye Inc."

# -----------------------------------------------------------------------------

from ssdpy import SSDPClient
import re
import os
import psutil
import concurrent.futures

MKE_DEVICE_URN = 'urn:schemas-upnp-org:device:Basic:1'
MKEAPIV1_TYPE = 'UPnP-MkE-'
LOCATION_RE = re.compile(
    r'^[^/]*//(([\d]{1,3})\.([\d]{1,3})\.([\d]{1,3})\.([\d]{1,3})).*$')


# -----------------------------------------------------------------------------


def parse_device_list(devices: list) -> dict:
    mke_sensors = {}

    for device in devices:
        if device['st'] == MKE_DEVICE_URN and MKEAPIV1_TYPE in device['usn']:
            m = LOCATION_RE.match(device['location'])
            if m:
                name = device['usn'].split(':')[1].replace(
                    MKEAPIV1_TYPE, '')
                mke_sensors[name] = m.group(1)
    # print(mke_sensors)
    return mke_sensors


# -----------------------------------------------------------------------------


def search_ssdp_devices(address, timeout) -> list:
    client = SSDPClient(address=address, timeout=timeout)
    devices = client.m_search("ssdp:all")
    return devices


# -----------------------------------------------------------------------------


def discover_devices(timeout=2) -> dict:
    # List all available IPv4 NICs
    nics = psutil.net_if_addrs()
    addrs = []

    for nic in nics.values():
        for addr in nic:
            if hasattr(addr, 'family') and addr.family == 2:
                addrs.append(addr.address)

    # SSDP M-SEARCH over all IPv4 interfaces
    # As this is an I/O bound task, we can use threads to paralelize the search
    devices = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for address in addrs:
            futures.append(executor.submit(search_ssdp_devices,
                                           address=address, timeout=timeout))

        for future in concurrent.futures.as_completed(futures):
            try:
                devices += future.result()
            except:
                pass
    return parse_device_list(devices)


if __name__ == "__main__":
    print(discover_devices())
