import sys
import os
os.environ["SD_ENABLE_ASIO"] = "1"
from .dependencies import *

print("[BrushSfx] Checking for dependencies")
pipInstallPath()
enable_pip()

numpy_version = "2.2.6"
if sys.version_info[1] >= 12:
    numpy_version = "2.4.0"

checkPipLib([
                {"numpy": numpy_version},
                {"sounddevice": "0.5.2"}
            ])



from .brush_sfx import *
from .constants import plugin_version

__version__ = plugin_version

print("[BrushSfx] Module initialized without erros")