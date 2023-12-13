#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
import json
import subprocess
from glob import glob
import datetime

import SensorInfo
from natsort import natsorted

# --- ILT Report script ---
# iltreport_postproc <folder> <param.json>

# constant
ILTREPORT_SCRIPT = "/home/proj/EvalCalib/iltreport.py"


def usage():
    print("iltreport_postproc <folder> <param.json>")
    exit(1)

if __name__=="__main__":
    print(f"{sys.argv=}")
    if len(sys.argv) != 3:
        usage()

    foldername = sys.argv[1]
    pdfname = f"ILTReport_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    output = os.path.join(foldername, pdfname)
    with open(sys.argv[2]) as f:
        j = json.load(f)
    param = j.get("parameter", {})

    sensorInfo = SensorInfo()
    sensorInfo.load_from_file(foldername + "/sensorinfo.json")

    binDir = param.get("bindir")
    binfile = f"{binDir}/mkedet_{sensorInfo.moduleType}_{sensorInfo.labelNumber}.bin"
    if not os.path.exists(binfile):
        print("could not find such a binfile [{}]".format(binfile))
        exit(1)

    configfile = param.get("configfile", "") # 無かったら空文字列が返る
    # シーケンス順に取得
    imgs = natsorted(glob(f"{foldername}/laser/*.png"))
    # execute
    ret = subprocess.call(ILTREPORT_SCRIPT + f" {binfile} {configfile} --output {pdfname} {imgs}" )