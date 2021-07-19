import json
import csv


# SensorInfo Class
class SensorInfo:
    def __init__(self):
        self._smidDic = None
        self.clear()

    def __del__(self):
        pass

    def clear(self):
        self.cameraType = ""
        self.serialNumber = ""
        self.moduleType = ""
        self.labelNumber = ""

    @property
    def smid(self):
        return self.cameraType + ":" + self.serialNumber if len(self.cameraType) > 0 or len(self.serialNumber) > 0 else ""
    
    @smid.setter
    def smid(self, value):
        if type(value) is str:
            t = value.strip().partition(":")
            if len(t) == 3 and t[1] == ":":
                self.cameraType = t[0]
                self.serialNumber = t[2]

    @property
    def labelid(self):
        return self.moduleType + "_" + self.labelNumber if len(self.moduleType) > 0 or len(self.labelNumber) > 0 else ""

    @labelid.setter
    def labelid(self, value):
        if type(value) is str:
            t = value.strip().partition("_")
            if len(t) == 3 and t[1] == "_":
                self.moduleType = t[0]
                self.labelNumber = t[2]

    @property
    def smiddic(self):
        if type(self._smidDic) != dict or len(self._smidDic) == 0:
            dicfile = "smid_dictionary.csv"
            # read smid dictionary
            self._smidDic = {}
            with open(dicfile, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._smidDic[row['smid']] = row['lblid']
        return self._smidDic

    def to_dic(self):
        dic = {"cameraType": self.cameraType, "serialNumber": self.serialNumber, "moduleType": self.moduleType,
               "labelNumber": self.labelNumber}
        return dic

    def from_dic(self, dic):
        if type(dic) is dict:
            self.cameraType = dic.get("cameraType", "")
            self.serialNumber = dic.get("serialNumber", "")
            self.moduleType = dic.get("moduleType", "")
            self.labelNumber = dic.get("labelNumber", "")

    def load_from_file(self, filename):
        with open(filename) as f:
            dic = json.load(f)
            self.from_dic(dic)

    def save_to_file(self, filename):
        dic = self.to_dic()
        with open(filename, 'w') as f:
            json.dump(dic, f, indent=4)

    def smid_from_labelid(self):
        if self.labelid in self.smiddic.values():
            keys = [k for k, v in self.smiddic.items() if v == self.labelid]
            if keys:
                self.smid = keys[0]

    def labelid_from_smid(self):
        if self.smid in self.smiddic:
            self.labelid = self.smiddic.get(self.smid)


if __name__ == '__main__':
    # pass
    s = SensorInfo()
    s.smid = "MKEPI:012345678"
    s.labelid = "ILT001_0001"
    s.save_to_file("test.json")
    print(vars(s))
    s.load_from_file("test2.json")
    print(vars(s))
    print(s.labelid, s.smid)

    s.labelid = "ILT001_0023"
    s.smid_from_labelid()
    print(s.labelid, s.smid)
    print(vars(s))

    s.smid = "MKEPI:0123c019ebb4c647ee"
    s.labelid_from_smid()
    print(s.smid, s.labelid)
    print(vars(s))
