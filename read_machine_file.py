import json

def loadJson(jsonFile):
    json_open = open(jsonFile, 'r')
    json_load = json.load(json_open)

    return json_load

