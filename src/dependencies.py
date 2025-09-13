# https://krita-artists.org/t/use-of-external-pip-libraries-in-python-plugins/21739

from PyQt5.Qt import *

from .constants import plugin_root_path

import sys
import os
import runpy
import re

import importlib.util


def pipInstallPath():
    """Return pip lib path
    
    Eventually:
    - create directory if not exist
    - add it to sys.path
    """
    returned=os.path.join(plugin_root_path, "dependencies")
    
    if not os.path.isdir(returned):
        os.makedirs(returned)

    if not returned in sys.path:
        sys.path.append(returned)
        
    return returned


def pip(param):
    """Execute pip 
    
    Given `param` is a list of pip command line parameters 
    
    
    Example:
        To execute:
            "python -m pip install numpy"
        
        Call function:
            pip(["install", "numpy"])
    """
    def exitFct(exitCode):
        return exitCode
    
    pipLibPath=pipInstallPath()

    # keep pointer to original values
    sysArgv=sys.argv
    sysExit=sys.exit

    # replace exit function to be sure that pip won't stop script
    sys.exit=exitFct

    # prepare arguments for pip module
    sys.argv=["pip"] + param
    sys.argv.append(f'--target={pipLibPath}')
    
    #print("pip command:", sys.argv)
    runpy.run_module("pip", run_name='__main__')
    
    sys.exit=sysExit
    sys.argv=sysArgv


def checkPipLib(libNames):
    """Import a library installed from pip (example: numpy)
    
    If library doesn't exists, do pip installation
    """
    pipLibPath=pipInstallPath()
    
    if isinstance(libNames, list) or isinstance(libNames, tuple):
        installList=[]
        for libName in libNames:
            if isinstance(libName, dict):
                libNameCheck=list(libName.keys())[0]
                libInstall=libName[libNameCheck]
            elif isinstance(libName, str):
                libNameCheck=libName
                libInstall=libName
                
            try:
                # try to import module
                print("Try to load", libNameCheck)
                __import__(libNameCheck)
                print("Ok!")
            except Exception as e:
                print("Failed", str(e))
                installList.append(libInstall)

        if len(libInstall)>0:
            pip(["install"]+installList)
    elif isinstance(libNames, str):
        checkPipLib([libNames])


def loadNumpy():
    print("importing from ", f"{pipInstallPath()}/numpy/__init__.py")
    previous_np = sys.modules.get("numpy")
    previous_fft = sys.modules.get("numpy.fft")
    numpy_spec = importlib.util.spec_from_file_location("numpy", f"{pipInstallPath()}/numpy/__init__.py")
    numpy_fft_spec = importlib.util.spec_from_file_location("numpy.fft", f"{pipInstallPath()}/numpy/fft/__init__.py")
    numpy_module = importlib.util.module_from_spec(numpy_spec)
    numpy_fft_module = importlib.util.module_from_spec(numpy_fft_spec)
    numpy_spec.loader.exec_module(numpy_module)
    numpy_fft_spec.loader.exec_module(numpy_fft_module)
    sys.modules["numpy"] = previous_np
    sys.modules["numpy.fft"] = previous_fft
    #foo.fft = fft
    
    return [numpy_module,numpy_fft_module]

def loadSoundDevice():
    print("importing from ", f"{pipInstallPath()}/sounddevice.py")
    spec = importlib.util.spec_from_file_location("sounddevice", f"{pipInstallPath()}/sounddevice.py")
    foo = importlib.util.module_from_spec(spec)
    #sys.modules["numpy_brush_sfx"] = foo
    spec.loader.exec_module(foo)
    return foo


numpy_modules = loadNumpy()
numpy = numpy_modules[0]
numpy_fft = numpy_modules[1]
sounddevice = loadSoundDevice()
#print('-------------------------------------------------------------------------')

#checkPipLib([
#            {"PIL": "Pillow"},       # module name (PIL) != pip installation name (Pillow)
#            "numpy"                # module name = pip installation name
#        ])

#try:
#    import numpy
#    print("Numpy version", numpy.version.version)
#except Exception as e:
#    print("Can't import numpy", str(e))
    

#try:
#    import PIL
#    print("PIL version", PIL.__version__)
#except Exception as e:
#    print("Can't import PIL", str(e))


#print('-------------------------------------------------------------------------')