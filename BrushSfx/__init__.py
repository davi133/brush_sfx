import sys
import os
os.environ["SD_ENABLE_ASIO"] = "1"
from .dependencies import *

print("[BrushSfx] Checking for dependencies")
pipInstallPath()
enable_pip()
checkPipLib([
                {"numpy": "2.2.6"},
                {"sounddevice": "0.5.2"}
            ])



from .brush_sfx import *
from .constants import plugin_version

__version__ = plugin_version

print("[BrushSfx] Module initialized without erros")