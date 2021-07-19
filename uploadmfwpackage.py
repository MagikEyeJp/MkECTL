#!/usr/bin/env python3
import sys
import os
from SensorInfo import SensorInfo
from docopt import docopt
import subprocess
import json


def execCmdline():
    """
    usage: uploadmfwpackage.py [options] <folder>

        <folder>  path to folder includes mfw package file

    options:
        -h --help         show usage
        -v --version      show version
    """
    args = (docopt(execCmdline.__doc__, version="1.0.0"))
    folder = os.path.normpath(args["<folder>"])
    # print("folder:" + folder)

    infofile = folder + "/sensorinfo.json"
    if not os.path.exists(infofile):
        print("not exist sensor info.")
        exit(1)
    s = SensorInfo()
    s.load_from_file(infofile)

    packagefile = folder + "/calib_" + s.serialNumber + ".mfw"
    if not os.path.exists(packagefile):
        print("not exist package file")
        exit(1)
    # get version of package
    cmd = f"pymkefw_package -e -p {packagefile}"
    j = subprocess.check_output(cmd, shell=True).decode('utf-8')
    m = json.loads(j)
    version = m.get("version", "")

    # upload
    manifest = {"camera_type": s.cameraType, "serial_number": s.serialNumber, "module_type": s.moduleType, "version": version}
    cmd = f"pymkess_storage -d add_package -i {packagefile} -m '{json.dumps(manifest)}'"
    print(cmd, subprocess.call(cmd, shell=True))


if __name__ == '__main__':
    execCmdline()
