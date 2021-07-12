#!/usr/bin/env python3
from SensorInfo import SensorInfo
import sys
import os


def usage():
    print("usge: makesensorinfo.py <foldername>")
    exit(1)

def foldername_to_labelid(folder):
    name = os.path.basename(os.path.splitdrive(folder)[1])
    print(name)
    t = name.partition("_")
    if len(t) == 3 and t[1] == "_":
        moduleType = t[0]
        labelnumber = t[2].partition("_")[0]
        return moduleType + "_" + labelnumber
    else:
        return ""


if __name__ == '__main__':
    if len(sys.argv) != 2:
        usage()
    folderName = sys.argv[1]
    if os.path.isdir(folderName) and \
       os.path.isdir(folderName + "/ccalib") and \
       os.path.isdir(folderName + "/pattern1"):
        labelid = foldername_to_labelid(folderName)
        if len(labelid) > 0:
            s = SensorInfo()
            s.labelid = labelid
            s.smid_from_labelid()
            s.save_to_file(folderName + "/sensorinfo.json")
    else:
        print("not folder")
