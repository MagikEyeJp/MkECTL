#!/usr/bin/env python3
# coding: utf-8

import configparser
import os
import datetime

def loadIni(dirname):
    config = configparser.ConfigParser()
    config.read(dirname + '/Log.ini')
    scriptPath = config.get('script', 'scriptpath')

    print('scriptpath: ' + scriptPath)

    return scriptPath

def generateIni(dirname, scriptName):
    config = configparser.RawConfigParser()

    section1 = 'script1'
    config.add_section(section1)
    # config.set(section1, 'env', os.environ.get('ENV'))
    # config.set(section1, 'name', 'myname')
    # config.set(section1, 'base_dir', '/home/myhome/exp')
    # config.set(section1, 'exe_dir', '%(base_dir)s/bin')
    # config.set(section1, 'hostname', '%(env).hostname')
    config.set(section1, 'section_no', '1')
    config.set(section1, 'scriptpath', scriptName)

    dt_start = datetime.datetime.now()
    config.set(section1, 'start_time', str(dt_start))

    with open(dirname + '/Log.ini', 'w') as configfile:
        config.write(configfile)

def updateIni_start(dirname, scriptName):
    if os.path.exists(dirname + '/Log.ini'):
        config = configparser.ConfigParser()
        config.read(dirname + '/Log.ini')

        newSectionNum = len(config.sections()) + 1
        newSection = 'script' + str(newSectionNum)
        config.add_section(newSection)
        config.set(newSection, 'section_no', str(newSectionNum))
        config.set(newSection, 'scriptpath', scriptName)

        dt_start = datetime.datetime.now()
        config.set(newSection, 'start_time', str(dt_start))

        with open(dirname + '/Log.ini', 'w') as configfile:
            config.write(configfile)

    else:
        config = configparser.RawConfigParser()

        section1 = 'script1'
        config.add_section(section1)
        config.set(section1, 'section_no', '1')
        config.set(section1, 'scriptpath', scriptName)

        dt_start = datetime.datetime.now()
        config.set(section1, 'start_time', str(dt_start))

        with open(dirname + '/Log.ini', 'w') as configfile:
            config.write(configfile)

def updateIni_finish(dirname, scriptName):
    config = configparser.ConfigParser()
    config.read(dirname + '/Log.ini')

    sectionNum = len(config.sections())
    sectionName = 'script' + str(sectionNum)

    dt_finish = datetime.datetime.now()
    config.set(sectionName, 'finish_time', str(dt_finish))

    with open(dirname + '/Log.ini', 'w') as configfile:
        config.write(configfile)



if __name__ == '__main__':
    generateIni('.')
    loadIni('.')
