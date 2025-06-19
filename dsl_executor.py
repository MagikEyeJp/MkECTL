import os
from typing import Any, List

from PySide6 import QtWidgets

from dsl_parser import parse_script, ScriptEnvironment
import execute_script


def execute_script_lark(scriptParams, devices, mainWindow, isdemo=False):
    env = ScriptEnvironment()
    with open(scriptParams.scriptName) as f:
        code = f.read()
    ast = parse_script(code, env)

    command_names = [n[1] for n in ast if n and n[0] == 'command']

    execute_script.systate.seqn = 0
    execute_script.isDemo = isdemo
    execute_script.systate.past_parameters.reset()
    execute_script.systate.offset = [0] * len(devices['robot'].motorSet)
    execute_script.systate.scale = [1.0] * len(devices['robot'].motorSet)

    if isdemo:
        execute_script.commands['mov'][1] = False
    else:
        execute_script.commands['mov'][1] = True

    execute_script.warm_lasers(scriptParams, devices, mainWindow)

    if not isdemo:
        execute_script.logIni.updateIni_start(scriptParams)

    if 'snap' in command_names or 'contsnap' in command_names:
        if not devices['3Dsensors'].connected:
            QtWidgets.QMessageBox.critical(
                mainWindow,
                'Sensor connection error',
                'Please connect to the sensor before executing script.'
            )
            return True

    mainWindow.stopClicked = False
    mainWindow.total = len(ast)
    if not scriptParams.isContinue:
        mainWindow.done = 0
    mainWindow.updateScriptProgress()

    range_obj = range(scriptParams.start_command_num, len(ast)) if isdemo else range(len(ast))

    for i in range_obj:
        if execute_script.isAborted(scriptParams, mainWindow):
            return mainWindow.stopClicked
        node = ast[i]
        if mainWindow.stopClicked:
            return True
        if node is None:
            continue
        isStop = False
        typ = node[0]
        if typ == 'set':
            args = [node[1], node[2]]
            execute_script.systate.args = args
            isStop = execute_script.set_filename(args, scriptParams, devices, mainWindow)
        elif typ == 'assign':
            env[node[1]] = node[2]
            isStop = False
        elif typ == 'command':
            cmd = node[1]
            args = node[2]
            mainWindow.ui.commandLabel.setText(cmd)
            execute_script.systate.args = args
            handler = execute_script.commands.get(cmd)
            if handler is None:
                QtWidgets.QMessageBox.critical(mainWindow, 'script syntax error',
                                                f'illegal command "{cmd}" at step {i}')
                return True
            func = getattr(execute_script, handler[0])
            execute_script.systate.skip = handler[1]
            try:
                isStop = func(args, scriptParams, devices, mainWindow)
            except execute_script.TimeoutError:
                execute_script.timeoutCallback(mainWindow)
                return True
        else:
            continue
        if isStop:
            execute_script.timeoutCallback(mainWindow)
            return True
        mainWindow.done = i + 1
        mainWindow.updateScriptProgress()

    execute_script.resume_state(scriptParams, devices, mainWindow)
    if not isdemo:
        execute_script.logIni.updateIni_finish(scriptParams.baseFolderName + '/' + scriptParams.subFolderName,
                                               scriptParams.scriptName)
    return False

def count_commands_lark(scriptParams):
    if not os.path.isfile(scriptParams.scriptName):
        return 0
    with open(scriptParams.scriptName) as f:
        code = f.read()
    ast = parse_script(code)
    return len([n for n in ast if n])
