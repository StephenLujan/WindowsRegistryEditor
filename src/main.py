from _winreg import *

import os
import string
import sys
sys.setdefaultencoding('utf-8')



#
#temp_dir = win32api.GetTempPath()
#fname = win32api.GetTempFileName(temp_dir, 'rsk')[0]
#print(fname)
### file can't exist
#os.remove(fname)
#
### enable backup and restore privs
#required_privs = ((win32security.LookupPrivilegeValue('', ntsecuritycon.SE_BACKUP_NAME), win32con.SE_PRIVILEGE_ENABLED),
#                  (win32security.LookupPrivilegeValue('', ntsecuritycon.SE_RESTORE_NAME), win32con.SE_PRIVILEGE_ENABLED)
#                  )
#ph = win32api.GetCurrentProcess()
#th = win32security.OpenProcessToken(ph, win32con.TOKEN_READ | win32con.TOKEN_ADJUST_PRIVILEGES)
#adjusted_privs = win32security.AdjustTokenPrivileges(th, 0, required_privs)
#
#try:
#    sa = win32security.SECURITY_ATTRIBUTES()
#    my_sid = win32security.GetTokenInformation(th, ntsecuritycon.TokenUser)[0]
#    sa.SECURITY_DESCRIPTOR.SetSecurityDescriptorOwner(my_sid, 0)
#
#    key, disp = win32api.RegCreateKeyEx(win32con.HKEY_CURRENT_USER, 'Python test key', SecurityAttributes=sa,
#                                        samDesired=win32con.KEY_ALL_ACCESS, Class='some class', Options=0)
#    win32api.RegSetValue(key, None, win32con.REG_SZ, 'Default value for python test key')
#
#    subkey, disp = win32api.RegCreateKeyEx(key, 'python test subkey', SecurityAttributes=sa,
#                                           samDesired=win32con.KEY_ALL_ACCESS, Class='some other class', Options=0)
#    win32api.RegSetValue(subkey, None, win32con.REG_SZ, 'Default value for subkey')
#
#    win32api.RegSaveKeyEx(key, fname, Flags=winnt.REG_STANDARD_FORMAT, SecurityAttributes=sa)
#
#    restored_key, disp = win32api.RegCreateKeyEx(win32con.HKEY_CURRENT_USER, 'Python test key(restored)', SecurityAttributes=sa,
#                                                 samDesired=win32con.KEY_ALL_ACCESS, Class='restored class', Options=0)
#    win32api.RegRestoreKey(restored_key, fname)
#finally:
#    win32security.AdjustTokenPrivileges(th, 0, adjusted_privs)


class RegKey():
    def __init__(self, hkey, name, directory):
        self.hkey = hkey
        self.name = name
        self.directory = directory

    def openSubKey(self, index, access):
        subKeyName = EnumKey(self.hkey, index)
        try:
            subKeyHandle = OpenKeyEx(self.hkey, subKeyName, 0, access)
            return RegKey(subKeyHandle, subKeyName, self.directory +"->"+ self.name)
        except:
            print "failed to open key", self.directory, "->", subKeyName

    def getTotalSubKeys(self):
        return QueryInfoKey(self.hkey)[0]

    def getTotalValues(self):
        return QueryInfoKey(self.hkey)[1]

    def getValue(self, index):
        value = EnumValue(self.hkey, index)
        value.append(self)
        return value

class RegEdit():
    def __init__(self):
        self.access = KEY_READ | KEY_ENUMERATE_SUB_KEYS | KEY_QUERY_VALUE
        self.found = 0
        self.regkey = None
        self.value = None
        self.directory = None
        self.searchKeyName = True
        self.searchValueData = True
        self.searchValueName = True
        self.searchString = None
        self.searchCaseSensitive = False

    def addSearchResult(self, result):
        print result
        self.found.append(result)

    def iterateKeys(self, regkey, func, params=None):

        subKeyName = None
        subKeyHandle = None

        # process this key and return the results
        self.regkey = regkey
        self.directory = regkey.directory
        if params:
            result = func(regkey, * params)
        else:
            result = func(regkey)
        if result:
            return result

        for x in range(0, regkey.getTotalSubKeys()):
            subkey = regkey.openSubKey(x, self.access)
            if subkey:
                result = self.iterateKeys(subkey, func, params)
                if result:
                    return result

        #print ("finished with ", directory)
        return result

    def findInKey(self, regkey):
        if self.searchKeyName:
            name = regkey.name
            if not self.searchCaseSensitive:
                name = name.lower()
            index = name.find(self.searchString)
            if index > -1:
                self.addSearchResult(["key",regkey])
        if self.searchValueData or self.searchValueName:
            self.iterateValues(regkey, self.findInValue)


    def iterateValues(self, regkey, func, params=None):
        num = regkey.getTotalValues()
        #print (num, " values found.")
        for index in range (0, num):
            self.value = regkey.getValue(index)
            if params:
                result = func(self.value, * params)
            else:
                result = func(self.value)
            if result:
                return result
        return False

    def p(self, value):
        print (value)

    def findInValue(self, value):
        data = value[1]
        name = value[0]
        if not self.searchCaseSensitive:
            data = data.lower()
            name = name.lower()
        #print (data)
        if (self.searchValueData):
            index = data.find(self.searchString)
            if index > -1:
                #print ("found!")
                self.addSearchResult(self.directory + '->>' + name + "->>" + data)
        if (self.searchValueName):
            index = name.find(self.searchString)
            if index > -1:
                #print ("found!")
                self.addSearchResult(self.directory + '->>' + name)
        return False

    def replaceAll(self, value, oldstring, newstring, searchKeyName=True, searchValueData=True, searchValueName=True, caseSensitive=False):
        findAll(oldstring, searchKeyName, searchValueData, searchValueName, caseSensitive)
        for x in self.found:
            print x


    def findAll(self, searchString, searchKeyName=True, searchValueData=True, searchValueName=True, caseSensitive=False):
        print("Finding all instances of \"" + searchString + "\"")
        self.found = []
        self.searchKeyName = searchKeyName
        self.searchValueData = searchValueData
        self.searchValueName = searchValueName
        self.searchCaseSensitive = caseSensitive
        if caseSensitive:
            self.searchString = searchString
        else:
            self.searchString = searchString.lower()
        #self.iterateKeys (RegKey(HKEY_CLASSES_ROOT, "HKEY_CLASSES_ROOT", "HKEY_CLASSES_ROOT"), self.findInKey)
        self.iterateKeys (RegKey(HKEY_CURRENT_USER, "HKEY_CURRENT_USER", "HKEY_CURRENT_USER"), self.findInKey)
        #self.iterateKeys (RegKey(HKEY_LOCAL_MACHINE, "HKEY_LOCAL_MACHINE", "HKEY_LOCAL_MACHINE"), self.findInKey)
        #self.iterateKeys (RegKey(HKEY_USERS, "HKEY_USERS", "HKEY_USERS"), self.findInKey)
        


r = RegEdit()

r.findAll("python test")
