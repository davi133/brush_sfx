
import os
import sqlite3
from typing import List
import json
import shutil

from PyQt5.Qt import *

from .constants import dir_path, config_version

class bsfxConfig:
    def __init__(self,sfx_id: str, use_eraser: bool = False, eraser_sfx_id: str = "", volume: float = 1.0):
        self.sfx_id = sfx_id
        self.use_eraser = use_eraser
        self.eraser_sfx_id = eraser_sfx_id
        self.volume = volume

    def __str__(self):
        return f"{self.sfx_id}, {self.use_eraser}, {self.eraser_sfx_id}, {self.volume}"

    def __repr__(self):
        return f"{self.sfx_id}, {self.use_eraser}, {self.eraser_sfx_id}, {self.volume}"

class BrushSfxResourceRepository:
    def __init__(self):
        self.file_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'brushsfxresources.bsfx')
        self.default_file_path =f"{dir_path}/assets/default.bsfx"
        
        file_exists = os.path.isfile(self.file_path)
        self.data = None
        if not file_exists:
            self.__load_default()
        
        with open(self.file_path, "r+") as file:
            self.data = file.readlines()
        self.data = [line.strip() for line in self.data]

    def __load_default(self):
        print("[BrushSfx] Loaded default sfx list")
        shutil.copy(self.default_file_path, self.file_path)

    def __init_file(self):
        with open(self.file_path, "w") as file:
            file.writelines([config_version])

    def __save_all_data(self):
        string_data = "\n".join(self.data)
        with open(self.file_path, "w+") as file:
            file.write(string_data)

    def save_sfx(self, preset_name: str, sfx_config: bsfxConfig):
        new_config =f"{preset_name.strip()};;"
        new_config+=f"{sfx_config.sfx_id};;"
        new_config+=f"{('1' if sfx_config.use_eraser else '0')};;"
        new_config+=f"{sfx_config.eraser_sfx_id};;"
        new_config+=f"{float(sfx_config.volume)}"

        i = 0
        config_index = -1
        for line in self.data[1:]:
            i+=1 #first line is version anyway
            config = line.split(";;")
            if config[0].strip() == preset_name.strip():
                config_index = i
                break
        
        if config_index != -1:
            self.data[config_index] = new_config 
        else:
            self.data+=[new_config]
        self.__save_all_data()


    
    def get_sfx(self, preset_name: str):
        for line in self.data[1:]:
            config = line.split(";;")
            if config[0].strip() == preset_name.strip():
                volume_string = config[4].strip()
                try:
                    volume =float(volume_string)
                except ValueError:
                    volume=1.0
                preset_sfx =  {
                "name": config[0],
                "sfx_config": bsfxConfig(
                    config[1],
                    config[2].strip() != "0",
                    config[3],
                    volume
                )}
                return preset_sfx
        return None

    def remove_sfx(self, preset_name: str):
        i = 0
        config_index = -1
        for line in self.data[1:]:
            i+=1 #first line is version anyway
            config = line.split(";;")
            if config[0].strip() == preset_name.strip():
                config_index = i
                break
        if config_index != -1:
            self.data.pop(config_index)

        self.__save_all_data()

bsfxResourceRepository = BrushSfxResourceRepository()

