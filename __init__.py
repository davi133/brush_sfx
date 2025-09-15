import sys
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
#sys.path.append(f"{dir_path}\\dependencies")
os.environ["SD_ENABLE_ASIO"] = "1"

from .src.dependencies import checkPipLib


from pathlib import Path

checkPipLib([
                {"numpy": "2.2.6"},
                {"sounddevice": "0.5.2"}
            ])


from .src.brush_sfx import *



print("hello krita again")