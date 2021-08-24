import json

def loadJson(jsonFile):
    json_open = open(jsonFile, 'r')
    json_load = json.load(json_open)

    return json_load    # dictionary

def writeJson(dict, jsonFile):
    with open(jsonFile, 'w') as f:
        json.dump(dict, f, indent=4)
