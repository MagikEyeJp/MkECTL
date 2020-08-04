#!/usr/bin/env python3
# coding: utf-8

import configparser
import os

def loadIni(dirname):
    config = configparser.ConfigParser()
    config.read(dirname + '/Log.ini')
    scriptPath = config.get('general', 'scriptpath')

    print('scriptpath: ' + scriptPath)

    return scriptPath

def generateIni(dirname, scriptName):
    config = configparser.RawConfigParser()

    section1 = 'general'
    config.add_section(section1)
    # config.set(section1, 'env', os.environ.get('ENV'))
    # config.set(section1, 'name', 'myname')
    # config.set(section1, 'base_dir', '/home/myhome/exp')
    # config.set(section1, 'exe_dir', '%(base_dir)s/bin')
    # config.set(section1, 'hostname', '%(env).hostname')
    config.set(section1, 'scriptpath', scriptName)

    with open(dirname + '/Log.ini', 'w') as configfile:
        config.write(configfile)

if __name__ == '__main__':
    generateIni('.')
    loadIni('.')
