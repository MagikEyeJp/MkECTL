#!/usr/bin/env python3
# coding: utf-8

import configparser
import os
import datetime

def loadIni(dirname):
    config = configparser.ConfigParser()
    config.read(dirname + '/Log.ini')

    sectionNum = len(config.sections())

    scriptPath = config.get('script' + str(sectionNum), 'scriptpath')

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

def updateIni_start(scriptParams):
    if os.path.exists(scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/Log.ini'):
        config = configparser.ConfigParser()
        config.read(scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/Log.ini')

        newSectionNum = len(config.sections()) + 1
        newSection = 'script' + str(newSectionNum)
        config.add_section(newSection)
        config.set(newSection, 'section_no', str(newSectionNum))
        config.set(newSection, 'scriptpath', scriptParams.scriptName[scriptParams.currentScript - 1])

        lastExecutedScript = config.get('script' + str(newSectionNum - 1),
                                        'scriptpath')

        dt_start = datetime.datetime.now()
        config.set(newSection, 'ir_on_multiplier', str(scriptParams.IRonMultiplier))
        config.set(newSection, 'ir_off_multiplier', str(scriptParams.IRoffMultiplier))
        config.set(newSection, 'iso_value', str(scriptParams.isoValue))
        config.set(newSection, 'start_time', str(dt_start))

        if scriptParams.isContinue and lastExecutedScript == scriptParams.scriptName[scriptParams.currentScript - 1]:
            pass
        else:
            with open(scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/Log.ini', 'w') as configfile:
                config.write(configfile)

    else:
        config = configparser.RawConfigParser()

        section1 = 'script1'
        config.add_section(section1)
        config.set(section1, 'section_no', '1')
        config.set(section1, 'scriptpath', scriptParams.scriptName[scriptParams.currentScript - 1])

        dt_start = datetime.datetime.now()
        config.set(section1, 'ir_on_multiplier', str(scriptParams.IRonMultiplier))
        config.set(section1, 'ir_off_multiplier', str(scriptParams.IRoffMultiplier))
        config.set(section1, 'iso_value', str(scriptParams.isoValue))
        config.set(section1, 'start_time', str(dt_start))

        with open(scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/Log.ini', 'w') as configfile:
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

def getPreviousScriptPath(iniFile):
    config = configparser.ConfigParser()
    config.read(iniFile)
    scriptPath = config.get('previous_script', 'scriptpath')

    return scriptPath

def updatePreviousScriptPath(iniFile, scriptName):
    # update/generate previousScript.ini
    config_ps = configparser.RawConfigParser()

    section = 'previous_script'
    config_ps.add_section(section)
    config_ps.set(section, 'scriptpath', scriptName)

    with open(iniFile, 'w') as configfile:
        config_ps.write(configfile)

def getPreviousMachineFile(iniFile):
    config = configparser.ConfigParser()
    config.read(iniFile)
    machineFilePath = config.get('previous_machine', 'machine_file')

    return machineFilePath

def getPreviousIPAddress(iniFile) -> "data/previousIPAddress.ini":
    # if not exist IPadr iniFile, return default IPadr
    try:
        config = configparser.ConfigParser()
        config.read(iniFile)
        IPAddress = config.get('previous_IPadr', 'IP_Address')
    except:
        IPAddress = "127.0.0.1" # default
    return IPAddress

def getPreviousPostProcFile(iniFile):
    config = configparser.ConfigParser()
    config.read(iniFile)
    machineFilePath = config.get('previous_postproc', 'postproc_file')

    return machineFilePath

def updatePreviousMachineFile(iniFile, machineFile):
    # update/generate previousMachine.ini
    config_ps = configparser.RawConfigParser()

    section = 'previous_machine'
    config_ps.add_section(section)
    config_ps.set(section, 'machine_file', machineFile)

    with open(iniFile, 'w') as configfile:
        config_ps.write(configfile)

def updatePreviousPostProcFile(iniFile, postprocFile):
    # update/generate previousMachine.ini
    config_ps = configparser.RawConfigParser()

    section = 'previous_postproc'
    config_ps.add_section(section)
    config_ps.set(section, 'postproc_file', postprocFile)

    with open(iniFile, 'w') as configfile:
        config_ps.write(configfile)

def updatePreviousIPAddressFile(iniFile, IPadr):
    config_ps = configparser.RawConfigParser()

    section = 'previous_IPadr'
    config_ps.add_section(section)
    config_ps.set(section, "IP_address", IPadr)

    with open(iniFile, 'w') as configfile:
        config_ps.write(configfile)

if __name__ == '__main__':
    generateIni('.', 'script/sampleScript1.txt')
    loadIni('.')
