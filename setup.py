# Place this .git repo in a directory child to your pykrita folder like this:
# /pykrita
#     ╚brush_sfx (this repo)
#         ╚.git
#         ╚brush_sfx.desktop
#         ╚setup.py (this file)
#     ╚other_krita_plugin
#     ╚other_krita_plugin.desktop
#
# It's required to have python (preferably 3.10) installed on your machine to run this script.
#
# To use this script run the following command on your terminal after every change:
# $py setup.py
#
# Depending on your python installation you may have to use 'python3' instead of 'py' e.g
# $python3 setup.py
#
# This script copies the contents from this repo that, will be used by the plugin, to the pykrita directory where krita can find it.
# By doing that you can work with more than one git repository inside your pykrita directory


import pathlib
import shutil

repo_dir = pathlib.Path(__file__).parent
pykrita_dir = repo_dir.parent
resources_dir = pykrita_dir.parent

if repo_dir.name == "pykrita":
    print("No setup is needed, the plugin should already run")
if pykrita_dir.name != "pykrita":
    print("This setup should be used when the repo is inside the pykrita directory")
else:
    shutil.copy(repo_dir / "brush_sfx.desktop", pykrita_dir)
    shutil.copytree(repo_dir/"BrushSfx"/"actions", resources_dir/ "actions",  dirs_exist_ok=True)
    shutil.copytree(repo_dir/"BrushSfx", pykrita_dir/"BrushSfx", dirs_exist_ok=True)
    print("Setup successful")
