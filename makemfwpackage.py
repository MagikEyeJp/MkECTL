#!/usr/bin/env python3
import sys
import os
from SensorInfo import SensorInfo
from docopt import docopt
import subprocess

def execCmdline():
    """
    usage: makemfwpackage.py [options] <folder> <config> <version>

        <folder>  path to folder includes mkedet.bin
        <config>  path to config.json
        <version> version of mfw package

    options:
        -h --help         show usage
        -v --version      show version
    """
    args = (docopt(execCmdline.__doc__, version="1.0.0"))
    folder = os.path.normpath(args["<folder>"])
    # print("folder:" + folder)
    config = os.path.normpath(args["<config>"])
    # print("config:" + config)
    version = os.path.normpath(args["<version>"])
    # print("verson:" + version)

    infofile = folder + "/sensorinfo.json"
    binfile = folder + "/mkedet.bin"
    if not os.path.exists(infofile):
        print("not exist sensor info.")
        exit(1)

    if not os.path.exists(binfile):
        print("not exist mkedet.bin")
        exit(1)

    s = SensorInfo()
    s.load_from_file(infofile)
    packagefile = folder + "/calib_" + s.serialNumber + ".mfw"
    if os.path.exists(packagefile):
        bakfile = packagefile+".bak"
        if os.path.exists(bakfile):
            os.remove(bakfile)
        os.rename(packagefile, bakfile)
    cmd = f"pymkefw_package -p {packagefile} -v \"{version}\" {config} {folder}/mkedet.bin"
    print(cmd)

    print(subprocess.call(cmd, shell=True))

if __name__ == '__main__':
    execCmdline()
