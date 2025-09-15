# https://krita-artists.org/t/use-of-external-pip-libraries-in-python-plugins/21739

from PyQt5.Qt import *

import sys
import os
import runpy
import re
from pathlib import Path
import platform
from urllib import request
import json


def pipInstallPath():
    """Return pip lib path
    
    Eventually:
    - create directory if not exist
    - add it to sys.path
    """
    returned=os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'pykrita', 'piplib')
    
    if not os.path.isdir(returned):
        os.makedirs(returned)

    if not returned in sys.path:
        sys.path.append(returned)
        
    return returned


def enable_pip():
    # thanks to https://gitlab.com/mellotanica/sonic_visions/-/blob/main/sonicvisions/modules.py
    
    plugin_dir = Path(__file__).parent

    # search for an already downloaded pip wheel
    pip_path = None
    for file in plugin_dir.iterdir():
        if file.name.startswith("pip-") and file.suffix == ".whl":
            pip_path = file
            break

    # retrieve pip wheel from the internet
    if pip_path is None:
        ctx = None
        if platform.system() == "Darwin":
            pemfile = str(Path(Krita.instance().getAppDataLocation()) /"SystemRootCerts.pem")
            subprocess.run(["security", "export", "-t", "certs", "-f", "pemseq", "-k", "/System/Library/Keychains/SystemRootCertificates.keychain",  "-o", pemfile])
            ctx = ssl.create_default_context(cafile=str(pemfile))
        resp = request.urlopen("https://pypi.org/pypi/pip/json", context=ctx)
        jdata = json.loads(resp.read())
        for url in jdata["urls"]:
            if url["packagetype"] == "bdist_wheel":
                pipurl = url["url"]
                resp = request.urlopen(pipurl, context=ctx)
                pip_path = plugin_dir / Path(pipurl).name
                with open(pip_path, "wb") as pipwheel:
                    pipwheel.write(resp.read())
    
    # add pip wheel to the python path
    sys.path.append(str(pip_path))





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
    
    runpy.run_module("pip", run_name='__main__')
    
    sys.exit=sysExit
    sys.argv=sysArgv


def checkPipLib(libNames):
    """Import a library installed from pip
    
    If library doesn't exists, do pip installation with specific version
    
    usage example:
        checkPipLib("numpy")
        checkPipLib ([{
            "numpy":"2.2.6"
        }])
    
    """

    if isinstance(libNames, list) or isinstance(libNames, tuple):
        to_install=[]
        for libName in libNames:
            if isinstance(libName, dict):
                key = list(libName.keys())[0] 
                name=key
                name_version= list(libName.keys())[0] + "==" +libName[key]
            elif isinstance(libName, str):
                name=libName
                name_version=libName
            

            #continue
            try:
                # try to import module
                print("Try to load", name)
                __import__(name)
                print("Ok!")
            except Exception as e:
                print("Failed", str(e))
                to_install.append(name_version)

        if len(to_install)>0:
            pip(["install"]+to_install)
    elif isinstance(libNames, str):
        checkPipLib([libNames])


pipInstallPath()
enable_pip()