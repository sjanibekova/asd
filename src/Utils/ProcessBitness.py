import pywinauto #Is needed to detect OS bitness
import struct # Need to detect Current process bitness
import subprocess #Need to create subprocess
import os # Is needed to check file/folder path
import shutil #os operations
import pdb
############################################
####Module, which control the Bitness between 32 and 64 python (needed for pywinauto framework to work correctly)
############################################
global mSettingsDict
mSettingsDict = {
    "BitnessProcessCurrent": "64", # "64" or "32"
    "BitnessOS": "64", # "64" or "32"
    "Python32FullPath": None, #Set from user: "..\\Resources\\WPy32-3720\\python-3.7.2\\PythonRPARobotGUIx32.exe"
    "Python64FullPath": None, #Set from user
    "Python32ProcessName": "PythonRPAUIDesktopX32.exe", #Config set once
    "Python64ProcessName": "PythonRPAUIDesktopX64.exe", #Config set once
    "Python32Process":None,
    "Python64Process":None,
    "PythonArgs":["-m","pyPythonRPA.Robot"] #Start other bitness openRPA process with PIPE channel
}
#Init the global configuration
def SettingsInit(inSettingsDict):
    if inSettingsDict:
        global mSettingsDict
        #Update values in settings from input
        mSettingsDict.update(inSettingsDict)
        #mSettingsDict = inSettingsDict
        ####################
        #Detect OS bitness
        ####BitnessOS#######
        lBitnessOS="32";
        if pywinauto.sysinfo.is_x64_OS():
            lBitnessOS="64";
        inSettingsDict["BitnessOS"]=lBitnessOS
        ####################
        #Detect current process bitness
        ####BitnessProcessCurrent#######
        lBitnessProcessCurrent = str(struct.calcsize("P") * 8)
        inSettingsDict["BitnessProcessCurrent"]=lBitnessProcessCurrent
        #####################################
        #Create the other bitness process if OS is 64 and we have another Python path
        ##########################################################################
        #Check if OS is x64, else no 64 is applicable
        if mSettingsDict["BitnessOS"]=="64":
            #Check if current bitness is 64
            if mSettingsDict["BitnessProcessCurrent"]=="64":
                #create x32 if Python 32 path is exists
                if mSettingsDict["Python32FullPath"] and mSettingsDict["Python32ProcessName"]:
                    #Calculate python.exe folder path
                    lPython32FolderPath= "\\".join(mSettingsDict["Python32FullPath"].split("\\")[:-1])
                    lPython32NewNamePath = f"{lPython32FolderPath}\\{mSettingsDict['Python32ProcessName']}"
                    if not os.path.isfile(lPython32NewNamePath):
                        shutil.copyfile(mSettingsDict["Python32FullPath"],lPython32NewNamePath)
                    #pdb.set_trace()
                    mSettingsDict["Python32Process"] = subprocess.Popen([lPython32NewNamePath] + mSettingsDict["PythonArgs"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            else:
                #bitness current process is 32
                #return x64 if it is exists
                if mSettingsDict["Python64Process"]:
                    #Calculate python.exe folder path
                    lPython64FolderPath= "\\".join(mSettingsDict["Python64FullPath"].split("\\")[:-1])
                    lPython64NewNamePath = f"{lPython64FolderPath}\\{mSettingsDict['Python64ProcessName']}"
                    if not os.path.isfile(lPython64NewNamePath):
                        shutil.copyfile(mSettingsDict["Python64FullPath"],lPython64NewNamePath)
                    mSettingsDict["Python64Process"] = subprocess.Popen([lPython64NewNamePath] + mSettingsDict["PythonArgs"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
#Return the other module bitnes
def OtherProcessGet():
    #Result template
    lResult = None
    global mSettingsDict
    #Check if OS is x64, else no 64 is applicable
    if mSettingsDict["BitnessOS"]=="64":
        #Check if current bitness is 64
        if mSettingsDict["BitnessProcessCurrent"]=="64":
            #return x32 if it is exists
            if mSettingsDict["Python32Process"]:
                lResult = mSettingsDict["Python32Process"]
        else:
            #bitness current process is 32
            #return x64 if it is exists
            if mSettingsDict["Python64Process"]:
                lResult = mSettingsDict["Python64Process"]
    #Exit
    return lResult