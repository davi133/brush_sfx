import sys
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f"{dir_path}\\dependencies")
os.environ["SD_ENABLE_ASIO"] = "1"
from .src.brush_sfx import *



print("hello krita again")
