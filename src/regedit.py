import sys
#import pywintypes
#import string
import traceback
try:
    import winreg as win
except ImportError:
    import _winreg as win
import logging
import time


logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',)
ERROR_LEVEL = 0

readAccess = win.KEY_READ | win.KEY_ENUMERATE_SUB_KEYS | win.KEY_QUERY_VALUE
writeAccess = win.KEY_READ | win.KEY_ENUMERATE_SUB_KEYS | win.KEY_QUERY_VALUE | win.KEY_SET_VALUE | win.KEY_WRITE
allAccess = win.KEY_ALL_ACCESS

def getHive(name):
    if name == "HKEY_CLASSES_ROOT":
        return win.HKEY_CLASSES_ROOT
    elif name == "HKEY_CURRENT_USER":
        return win.HKEY_CURRENT_USER
    elif name == "HKEY_LOCAL_MACHINE":
        return win.HKEY_LOCAL_MACHINE
    elif name == "HKEY_USERS":
        return win.HKEY_USERS


###############################################################################
#   RegValue
###############################################################################

class RegValue():
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

    def setName(self, name):
        self.regkey.edit()
        win.DeleteValue(self.regkey.hkey, self.name)
        self.name = name
        win.SetValueEx(self.regkey.hkey, self.name, 0, self.type, input)



###############################################################################
#   RegKey
###############################################################################

class RegKey():
    def __init__(self, hkey, name, directory):
        self.hkey = hkey
        self.name = name
        self.directory = directory
        
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
                logging.debug ("failed to open key", self.directory, "\\", subKeyName)
            if ERROR_LEVEL > 1:
                traceback.logging.debug_exc(file=sys.stdout)

    def getTotalSubKeys(self):
        return win.QueryInfoKey(self.hkey)[0]

    def getTotalValues(self):
        return win.QueryInfoKey(self.hkey)[1]

    def getValue(self, index):
        value = win.EnumValue(self.hkey, index)
        value = RegValue(value[0], value[1], value[2], self, index)
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
        win.CloseKey(self.hkey)
        hive, path = self.getHiveAndPath()
        hive = getHive(hive)
        try:
            self.hkey = win.OpenKey(hive, path, 0, allAccess)
        except:
            if ERROR_LEVEL > 0:
                logging.debug ("failed to open key for editing", self.directory, "\\", subKeyName)
            if ERROR_LEVEL > 1:
                traceback.logging.debug_exc(file=sys.stdout)
                return -1

def getRegKey(name):
    if name == "HKEY_CLASSES_ROOT":
        return RegKey(win.HKEY_CLASSES_ROOT, "HKEY_CLASSES_ROOT", "HKEY_CLASSES_ROOT")
    elif name == "HKEY_CURRENT_USER":
        return RegKey(win.HKEY_CURRENT_USER, "HKEY_CURRENT_USER", "HKEY_CURRENT_USER")
    elif name == "HKEY_LOCAL_MACHINE":
        return RegKey(win.HKEY_LOCAL_MACHINE, "HKEY_LOCAL_MACHINE", "HKEY_LOCAL_MACHINE")
    elif name == "HKEY_USERS":
        return RegKey(win.HKEY_USERS, "HKEY_USERS", "HKEY_USERS")
    else:
        logging.debug("Couldn't find registry hive named " + name + ".")


###############################################################################
#   RegEdit
###############################################################################

class RegEdit():
    def __init__(self):
        self.reset()

        self.searchKeyName = True
        self.searchValueData = True
        self.searchValueName = True
        self.searchString = None
        self.searchCaseSensitive = False
        self.hives = dict()
        self.setHives(1,1,1,1)

    def setHives(self, HKEY_CLASSES_ROOT, HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, HKEY_USERS):
        self.hives["HKEY_CLASSES_ROOT"] = HKEY_CLASSES_ROOT
        self.hives["HKEY_CURRENT_USER"] = HKEY_CURRENT_USER
        self.hives["HKEY_LOCAL_MACHINE"] = HKEY_LOCAL_MACHINE
        self.hives["HKEY_USERS"] = HKEY_USERS


    def reset(self):
        self.found = []
        self.readErrors = 0
        self.writeErrors = 0


    def addSearchResult(self, result):
        if result[0] == "Key Name":
            logging.debug("Key Name Match:")
            logging.debug("  key: " + result[1].directory + "\\" + result[1].name)
        elif result[0] == "Value Name":
            logging.debug("Value Name Match:")
            logging.debug("  key:" + result[1].regkey.directory + "\\" + result[1].regkey.name)
            logging.debug("  value index: " + str(result[1].index))
            logging.debug("  value name: " + result[1].name)
            logging.debug("  value data: " + str(result[1].data))
        elif result[0] == "Value Data":
            logging.debug("Value Data Match:")
            logging.debug("  key:" + result[1].regkey.directory + "\\" + result[1].regkey.name)
            logging.debug("  value index: " + str(result[1].index))
            logging.debug("  value name: " + result[1].name)
            logging.debug("  value data: " + str(result[1].data))

        self.found.append(result)


    def iterateKeys(self, regkey, func, params=None):

        subKeyName = None
        subKeyHandle = None
        time.sleep(0)

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
        #logging.debug (num, " values found.")
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
        logging.debug (value)


    def findInValue(self, value):
        data = str(value.data)
        name = str(value.name)
        if not self.searchCaseSensitive:
            data = data.lower()
            name = name.lower()
        #logging.debug (data)
        if (self.searchValueData):
            index = data.find(self.searchString)
            if index > -1:
                #logging.debug ("found!")
                self.addSearchResult(["Value Data", value])
        if (self.searchValueName):
            index = name.find(self.searchString)
            if index > -1:
                #logging.debug ("found!")
                self.addSearchResult(["Value Name", value])
        return False


    def replaceInString(self, fullString, oldString, newString):
        oldStringLC = oldString.lower()
        newStringLC = newString.lower()
        fullStringLC = fullString.lower()
        index = fullStringLC.find(oldStringLC)
        while index > -1:
            logging.debug("found " + oldString + " in " + fullString + " at " + str(index))
            front = fullStringLC[:index]
            end = fullStringLC[index + len(oldStringLC):]
            fullStringLC = front + newStringLC + end

            front = fullString[:index]
            end = fullString[index + len(oldString):]
            fullString = front + newString + end

            index = fullStringLC.find(oldStringLC)
        return fullString


    def replaceValueData(self, value, oldString, newString):
        logging.debug("replacing value data")
        data = self.replaceInString(str(value.data), oldString, newString)
        value.setData(data)


    def replaceValueName(self, value, oldString, newString):
        logging.debug("replacing value name")
        name = self.replaceInString(str(value.name), oldString, newString)
        value.setName(name)


    def replaceAll(self, oldstring, newstring, searchKeyName=True, searchValueName=True, searchValueData=True, caseSensitive=False):
        self._findAll(oldstring, searchKeyName, searchValueName, searchValueData, caseSensitive)
        for x in self.found:
            logging.debug (x)
            if x[0] == "Value Data":
                self.replaceValueData(x[1], oldstring, newstring)
            if x[0] == "Value Name":
                self.replaceValueName(x[1], oldstring, newstring)
        self.doneOperations()

    def findAll(self, searchString, searchKeyName=True, searchValueName=True, searchValueData=True, caseSensitive=False):
        self._findAll(oldstring, searchKeyName, searchValueName, searchValueData, caseSensitive)
        self.doneOperations()

    def _findAll(self, searchString, searchKeyName=True, searchValueName=True, searchValueData=True, caseSensitive=False):
        if not (searchKeyName or searchValueName or searchValueData):
            logging.debug("Error: At least one category of data must be selected to search.")
            return

        logging.debug("Finding all instances of \"" + searchString + "\"")
        self.reset()
        self.searchKeyName = searchKeyName
        self.searchValueName = searchValueName
        self.searchValueData = searchValueData
        self.searchCaseSensitive = caseSensitive
        searching = "Searching:  "
        if self.searchKeyName:
            searching+= "key names, "
        if self.searchValueName:
            searching+= "value names, "
        if self.searchValueData:
            searching+= "value data, "
        logging.debug(searching)

        if caseSensitive:
            self.searchString = searchString
        else:
            self.searchString = searchString.lower()
        for hiveName, on in self.hives.items():
            if on:
                logging.debug ( "Searching hive "+ hiveName)
                self.iterateKeys (getRegKey(hiveName), self.findInKey)
        logging.debug (str(len(self.found)) + " matches found.")
        logging.debug ("Read Errors: " + str(self.readErrors))
        logging.debug ("Write Errors: " + str(self.writeErrors))

    def doneOperations(self):
        logging.debug (" --- Finished --- ")
