import sys

import pywintypes

import string
import traceback
import winreg as win

ERROR_LEVEL = 0

readAccess = win.KEY_READ | win.KEY_ENUMERATE_SUB_KEYS | win.KEY_QUERY_VALUE
writeAccess = win.KEY_READ | win.KEY_ENUMERATE_SUB_KEYS | win.KEY_QUERY_VALUE | win.KEY_WRITE

def getHive(name):
    if name == "HKEY_CLASSES_ROOT":
        return win.HKEY_CLASSES_ROOT
    elif name == "HKEY_CURRENT_USER":
        return win.HKEY_CURRENT_USER
    elif name == "HKEY_LOCAL_MACHINE":
        return win.HKEY_LOCAL_MACHINE
    elif name == "HKEY_USERS":
        return win.HKEY_USERS

class Value():
    def __init__(self, name, data, type, regkey, index):
        self.name = name
        self.data = data
        self.type = type
        self.regkey = regkey
        self.index = index

    def setData(self, input):
        self.regkey.edit()
        win.SetValueEx(self.regkey.hkey, self.name, 0, self.type, input)
        self.data = input

class RegKey():
    def __init__(self, hkey, name, directory):
        self.hkey = hkey
        self.name = name
        self.directory = directory

#    def __del__(self):
#        if self.hkey:
#            win.CloseKey(self.hkey)

    def openSubKey(self, index):
        subKeyName = win.EnumKey(self.hkey, index)
        try:
            subKeyHandle = win.OpenKeyEx(self.hkey, subKeyName, 0, readAccess)
            if self.directory == "":
                return RegKey(subKeyHandle, subKeyName, self.name)
            else:
                return RegKey(subKeyHandle, subKeyName, self.directory + "\\" + self.name)
        except:
            if ERROR_LEVEL > 0:
                print ("failed to open key", self.directory, "\\", subKeyName)
            if ERROR_LEVEL > 1:
                traceback.print_exc(file=sys.stdout)

    def getTotalSubKeys(self):
        return win.QueryInfoKey(self.hkey)[0]

    def getTotalValues(self):
        return win.QueryInfoKey(self.hkey)[1]

    def getValue(self, index):
        value = win.EnumValue(self.hkey, index)
        value = Value(value[0], value[1], value[2], self, index)
        return value

    def getHiveAndPath(self):
        path = ""
        hive = self.directory
        index = self.directory.find("\\")
        if index > -1:
            path = self.directory[index + 1:] + "\\"
            hive = (self.directory[:index])
        path += self.name
        return [hive, path]

    def edit(self):
        hive, path = self.getHiveAndPath()
        hive = getHive(hive)
        try:
            self.hkey = win.OpenKey(hive, path, 0, win.KEY_ALL_ACCESS)
        except:
            if ERROR_LEVEL > 0:
                print ("failed to open key for editing", self.directory, "\\", subKeyName)
            if ERROR_LEVEL > 1:
                traceback.print_exc(file=sys.stdout)
                return -1



class RegEdit():
    def __init__(self):
        self.reset()

        self.searchKeyName = True
        self.searchValueData = True
        self.searchValueName = True
        self.searchString = None
        self.searchCaseSensitive = False

    def reset(self):
        self.found = []
        self.readErrors = 0
        self.writeErrors = 0

    def addSearchResult(self, result):
        if result[0] == "Key Name":
            print("Key Name Match:")
            print("  key:", result[1].directory + "\\" + result[1].name)
        elif result[0] == "Value Name":
            print("Value Name Match:")
            print("  key:", result[1].regkey.directory + "\\" + result[1].regkey.name)
            print("  value index:", result[1].index)
            print("  value name:", result[1].name)
            print("  value data:", result[1].data)
        elif result[0] == "Value Data":
            print("Value Data Match:")
            print("  key:", result[1].regkey.directory + "\\" + result[1].regkey.name)
            print("  value index:", result[1].index)
            print("  value name:", result[1].name)
            print("  value data:", result[1].data)

        self.found.append(result)

    def iterateKeys(self, regkey, func, params=None):

        subKeyName = None
        subKeyHandle = None

        # process this key and return the results
        self.directory = regkey.directory
        if params:
            result = func(regkey, * params)
        else:
            result = func(regkey)
        if result:
            return result

        for x in range(0, regkey.getTotalSubKeys()):
            subkey = regkey.openSubKey(x)
            if subkey:
                result = self.iterateKeys(subkey, func, params)
            else:
                self.readErrors += 1
                if result:
                    return result

        return result

    def findInKey(self, regkey):
        if self.searchKeyName:
            name = regkey.name
            if not self.searchCaseSensitive:
                name = name.lower()
            index = name.find(self.searchString)
            if index > -1:
                self.addSearchResult(["Key Name", regkey])
        if self.searchValueData or self.searchValueName:
            self.iterateValues(regkey, self.findInValue)


    def iterateValues(self, regkey, func, params=None):
        num = regkey.getTotalValues()
        #print (num, " values found.")
        for index in range (0, num):
            value = regkey.getValue(index)
            if params:
                result = func(value, * params)
            else:
                result = func(value)
            if result:
                return result
        return False

    def p(self, value):
        print (value)

    def findInValue(self, value):
        data = str(value.data)
        name = str(value.name)
        if not self.searchCaseSensitive:
            data = data.lower()
            name = name.lower()
        #print (data)
        if (self.searchValueData):
            index = data.find(self.searchString)
            if index > -1:
                #print ("found!")
                self.addSearchResult(["Value Data", value])
        if (self.searchValueName):
            index = name.find(self.searchString)
            if index > -1:
                #print ("found!")
                self.addSearchResult(["Value Name", value])
        return False

    def replaceValueData(self, value, oldString, newString):
        print("replacing value data")
        data = str(value.data)
        oldStringLC = oldString.lower()
        newStringLC = newString.lower()
        dataLC = data.lower()
        index = dataLC.find(oldStringLC)
        while index > -1:
            print("found " + oldString + " in " + data + " at " + str(index))
            front = dataLC[:index]
            end = dataLC[index + len(oldStringLC):]
            dataLC = front + newStringLC + end

            front = data[:index]
            end = data[index + len(oldString):]
            data = front + newString + end

            index = dataLC.find(oldStringLC)
        value.setData(data)


    def replaceAll(self, oldstring, newstring, searchKeyName=True, searchValueData=True, searchValueName=True, caseSensitive=False):
        self.findAll(oldstring, searchKeyName, searchValueData, searchValueName, caseSensitive)
        for x in self.found:
            print (x)
            if x[0] == "Value Data":
                self.replaceValueData(x[1], oldstring, newstring)

    def findAll(self, searchString, searchKeyName=True, searchValueData=True, searchValueName=True, caseSensitive=False):
        print("Finding all instances of \"" + searchString + "\"")
        self.reset()
        self.searchKeyName = searchKeyName
        self.searchValueData = searchValueData
        self.searchValueName = searchValueName
        self.searchCaseSensitive = caseSensitive
        if caseSensitive:
            self.searchString = searchString
        else:
            self.searchString = searchString.lower()
        self.iterateKeys (RegKey(win.HKEY_CLASSES_ROOT, "HKEY_CLASSES_ROOT", "HKEY_CLASSES_ROOT"), self.findInKey)
        self.iterateKeys (RegKey(win.HKEY_CURRENT_USER, "HKEY_CURRENT_USER", ""), self.findInKey)
        self.iterateKeys (RegKey(win.HKEY_LOCAL_MACHINE, "HKEY_LOCAL_MACHINE", "HKEY_LOCAL_MACHINE"), self.findInKey)
        self.iterateKeys (RegKey(win.HKEY_USERS, "HKEY_USERS", "HKEY_USERS"), self.findInKey)
        print (len(self.found), " matches found.")
        print ("Read Errors: ", self.readErrors)
        print ("Write Errors: ", self.writeErrors)