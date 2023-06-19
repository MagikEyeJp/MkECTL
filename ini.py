#!/usr/bin/env python3
# coding: utf-8

import configparser
import os
import datetime
class LogIni:

    def loadIni(self, dirname):
        config = configparser.ConfigParser()
        config.read(dirname + '/Log.ini')

        sectionNum = len(config.sections())

        scriptPath = config.get('script' + str(sectionNum), 'scriptpath')

        print('scriptpath: ' + scriptPath)

        return scriptPath

    def generateIni(self, dirname, scriptName):
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

    def updateIni_start(self, scriptParams):
        if os.path.exists(scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/Log.ini'):
            config = configparser.ConfigParser()
            config.read(scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/Log.ini')

            newSectionNum = len(config.sections()) + 1
            newSection = 'script' + str(newSectionNum)
            config.add_section(newSection)
            config.set(newSection, 'section_no', str(newSectionNum))
            config.set(newSection, 'scriptpath', scriptParams.scriptName)

            lastExecutedScript = config.get('script' + str(newSectionNum - 1),
                                            'scriptpath')

            dt_start = datetime.datetime.now()
            config.set(newSection, 'ir_on_multiplier', str(scriptParams.IRonMultiplier))
            config.set(newSection, 'ir_off_multiplier', str(scriptParams.IRoffMultiplier))
            config.set(newSection, 'iso_value', str(scriptParams.isoValue))
            config.set(newSection, 'start_time', str(dt_start))

            if scriptParams.isContinue and lastExecutedScript == scriptParams.scriptName:
                pass
            else:
                with open(scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/Log.ini', 'w') as configfile:
                    config.write(configfile)

        else:
            config = configparser.RawConfigParser()

            section1 = 'script1'
            config.add_section(section1)
            config.set(section1, 'section_no', '1')
            config.set(section1, 'scriptpath', scriptParams.scriptName)

            dt_start = datetime.datetime.now()
            config.set(section1, 'ir_on_multiplier', str(scriptParams.IRonMultiplier))
            config.set(section1, 'ir_off_multiplier', str(scriptParams.IRoffMultiplier))
            config.set(section1, 'iso_value', str(scriptParams.isoValue))
            config.set(section1, 'start_time', str(dt_start))

            with open(scriptParams.baseFolderName + '/' + scriptParams.subFolderName + '/Log.ini', 'w') as configfile:
                config.write(configfile)

    def updateIni_finish(self, dirname, scriptName):
        config = configparser.ConfigParser()
        config.read(dirname + '/Log.ini')

        sectionNum = len(config.sections())
        sectionName = 'script' + str(sectionNum)

        dt_finish = datetime.datetime.now()
        config.set(sectionName, 'finish_time', str(dt_finish))

        with open(dirname + '/Log.ini', 'w') as configfile:
            config.write(configfile)

class Ini:
    def __init__(self, config_file='data/MkECTL.ini'):
        self.config_file = config_file

    def getPreviousScriptPath(self):
        try: # check section & entries
            config = configparser.ConfigParser()
            config.read(self.config_file)
            scriptPath = config.get('MkECTL', 'script_file')
        except:
            scriptPath = None
        return scriptPath

    def updatePreviousScriptPath(self, scriptName):
        # update/generate previousScript.ini
        section = 'MkECTL'
        key = "script_file"
        self.updateIniFile(section, key, scriptName)
        

    def getPreviousMachineFile(self):
        try: # check section & entries
            config = configparser.ConfigParser()
            config.read(self.config_file)
            machineFilePath = config.get('MkECTL', 'machine_file')
        except:
            machineFilePath = None
        return machineFilePath

    def getPreviousIPAddress(self):
        try: # check section & entries
            config = configparser.ConfigParser()
            config.read(self.config_file)
            IPAddress = config.get('SENSOR', 'ip_address')
        except:
            IPAddress = None
        return IPAddress

    def getPreviousPostProcFile(self):
        try: # check section & entries
            config = configparser.ConfigParser()
            config.read(self.config_file)
            machineFilePath = config.get('MkECTL', 'postproc_file')
        except:
            machineFilePath = None
        return machineFilePath

    def updatePreviousMachineFile(self, machineFile):
        # update/generate previousMachine.ini
        section = 'MkECTL'
        key = "machine_file"
        self.updateIniFile(section, key, machineFile)

    def updatePreviousPostProcFile(self, postprocFile):
        # update/generate previousMachine.ini
        section = 'MkECTL'
        key = "postproc_file"
        self.updateIniFile(section, key, postprocFile)

    def updatePreviousIPAddressFile(self, IPAddr):
        section = 'SENSOR'
        key = "ip_address"
        self.updateIniFile(section, key, IPAddr)
    
    def updateIniFile(self, section, key, value):
        config_ps = configparser.ConfigParser()
        config_ps.read(self.config_file)
        # check section whether it has already existed
        if not section in config_ps.sections():
            config_ps.add_section(section)
        config_ps.set(section, key, value)
        with open(self.config_file, mode="w") as f:
            config_ps.write(f)
        

        
if __name__ == '__main__':
    logIni = LogIni()
    logIni.generateIni('.', 'script/sampleScript1.txt')
    logIni.loadIni('.')
