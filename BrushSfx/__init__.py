import sys
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
os.environ["SD_ENABLE_ASIO"] = "1"
from .dependencies import checkPipLib

checkPipLib([
                {"numpy": "2.2.6"},
                {"sounddevice": "0.5.2"}
            ])


from .brush_sfx import *
print("hello krita again")