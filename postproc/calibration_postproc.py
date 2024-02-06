#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import json
from SensorInfo import SensorInfo
import shutil
import subprocess

# --- ILT Calibration script ---
# calibration_postproc <folder> <param.json>

# constant
CALIB_SCRIPT = '/home/magikeye/bin/calib.sh'
MAKEMFW_PROGRAM = './makemfwpackage.py'
UPLOAD_PROGRAM = './uploadmfwpackage.py'



def usage():
    print("calibration_postproc.py <calib data folder> <parameter.json>")
    exit(1)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()

    # print(sys.argv)

    # load parameter
    foldername = sys.argv[1]
    with open(sys.argv[2]) as f:
        j = json.load(f)
    param = j.get("parameter", {})

    # print(foldername, param)

    sensorInfo = SensorInfo()
    sensorInfo.clear()
    sensorInfo.load_from_file(foldername + "/sensorinfo.json")
    # print(sensorInfo)

    outpath = param.get("outpath", os.path.dirname(foldername))
    print(outpath)
    newpathname = outpath + "/" + sensorInfo.labelid + "_" + os.path.split(foldername)[1]
    print("newname", newpathname)

    # move calib folder to output folder
    shutil.move(foldername, newpathname)

    # copy macro file
    macrofile = param.get("macrofile", "")
    print(f"macro:${macrofile}")
    if len(macrofile) > 0:
        shutil.copy(macrofile, newpathname + "/")

    # print(foldername, param)
    # calibration
    sensortype = param.get("sensortype", "vcsel")
    sensorname = sensorInfo.labelid

    print(CALIB_SCRIPT + " " + sensortype + " " + sensorname + " " + newpathname)
    retcode = subprocess.call(CALIB_SCRIPT + " -m " + os.path.basename(macrofile) + " " + sensortype + " " + sensorname + " " + newpathname, shell=True)
    print(f"returncode {retcode}")

    # make mfw package
    configfile = param.get("configfile", "")
    version = param.get("version", "")
    # print(f"configfile:{configfile}, version:{version}")
    if len(configfile) > 0 and len(version) > 0:
        # print(MAKEMFW_PROGRAM +" "+ newpathname + " " + configfile)
        retcode = subprocess.call(MAKEMFW_PROGRAM +" "+ newpathname + " " + configfile + " " + version, shell=True)
        print(f"returncode {retcode}")

    # upload package
    if param.get("upload", False):
        retcode = subprocess.call(UPLOAD_PROGRAM +" "+ newpathname, shell=True)
        print(f"returncode {retcode}")

