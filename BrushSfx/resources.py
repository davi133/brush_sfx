
import os
import sqlite3
from typing import List
import json
import shutil

from PyQt5.Qt import *

from .constants import plugin_version, db_version, dir_path


class bsfxConfig:
    def __init__(self,sfx_id: str, use_eraser: bool = False, eraser_sfx_id: str = "", options:dict = {}):
        self.sfx_id = sfx_id
        self.use_eraser = use_eraser
        self.eraser_sfx_id = eraser_sfx_id
        self.options = options


class bsfxConfig:
    def __init__(self,sfx_id: str, use_eraser: bool = False, eraser_sfx_id: str = "", options:dict = {}):
        self.sfx_id = sfx_id
        self.use_eraser = use_eraser
        self.eraser_sfx_id = eraser_sfx_id
        self.options = options

    def __str__(self):
        return f"{self.sfx_id}, {self.use_eraser}, {self.eraser_sfx_id}, {self.options}"

class BrushSfxResourceRepository:
    def __init__(self):
        self.db_path =os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'brushsfxresources.sqlite')
        db_exists = os.path.isfile(self.db_path)

        if not db_exists:
            self.__load_default_db()
        
        self.con = sqlite3.connect(self.db_path)
        self.cur = self.con.cursor()
        
       
    def __load_default_db(self):
        print("[BrushSfx] Loaded default sfx list")
        shutil.copy(f"{dir_path}/assets/default.sqlite", self.db_path)

    def __create_db(self):
        stmt_version = "CREATE TABLE IF NOT EXISTS bsfx_version (\
                            version TEXT PRIMARY KEY \
                        );"
        stmt_sfx_option = "CREATE TABLE IF NOT EXISTS sfx_option (\
                            id TEXT  PRIMARY KEY, \
                            name TEXT  NOT NULL\
                        );"
        stmt_preset_sfx = "CREATE TABLE IF NOT EXISTS rel_preset_sfx (\
                            preset_filename TEXT PRIMARY KEY,\
                            sfx_id TEXT NOT NULL,\
                            use_eraser INTEGER DEFAULT 0, \
                            eraser_sfx_id TEXT, \
                            options_json TEXT,\
                            FOREIGN KEY(sfx_id) REFERENCES sfx_option(id),\
                            FOREIGN KEY(eraser_sfx_id) REFERENCES sfx_option(id)\
                        );"
        try:
            self.cur.execute(stmt_version)
            self.cur.execute("PRAGMA foreign_keys = ON;")
            self.cur.execute(f"INSERT INTO bsfx_version(version) VALUES (\'{db_version}\')")
            self.cur.execute(stmt_sfx_option)
            self.cur.execute(stmt_preset_sfx)
            self.con.commit()
            print("[BrushSfx] brushsfxresources.sqlite created")
        except Exception as e:
            print("[BrushSfx] An error ocurred while creating the sqlite database")
            print(e)
            raise e

    def add_sfx(self, sfx_id: str, name: str):
        params = (sfx_id, name)
        self.cur.execute("INSERT OR REPLACE INTO sfx_option VALUES (?, ?)", params)
        self.con.commit()
        
    
    def get_preset_sfx(self, preset_filename: str) -> dict:
        #1)_Realistic_Standard_Ballpoint_EXPER_PressureB.kpp
        self.cur.execute("SELECT \
                        preset_filename,\
                        sfx_id, \
                        use_eraser,\
                        eraser_sfx_id,\
                        options_json \
                        FROM rel_preset_sfx \
                        WHERE preset_filename = ? ", (preset_filename, ))
        rel_preset_sfx = self.cur.fetchall()
        if len(rel_preset_sfx) > 0:
            preset_sfx =  {
                "preset_filename": rel_preset_sfx[0][0],
                "sfx_config": bsfxConfig(
                    rel_preset_sfx[0][1],
                    rel_preset_sfx[0][2],
                    rel_preset_sfx[0][3],
                    {}
                )
            }
            try:
                preset_sfx["sfx_config"].options = json.loads(rel_preset_sfx[0][4])
            except:
                preset_sfx["sfx_config"].options = {}
            return preset_sfx
        else:
            return None
    
    def link_preset_sfx(self, preset_filename: str, sfx_config: bsfxConfig):
        params = [(preset_filename, sfx_config.sfx_id, sfx_config.use_eraser, sfx_config.eraser_sfx_id, json.dumps(sfx_config.options))]
        self.cur.executemany("INSERT OR REPLACE INTO rel_preset_sfx VALUES (?, ?, ?, ?, ?)", params)
        self.con.commit()
    
    def link_all_presets_in_tag(self, tag_id: int, sfx_id: str, options: dict):
        presets = kraResourceHelper.get_presets_with_tag(tag_id)
        params = [ (preset["filename"], sfx_id, json.dumps(options)) for preset in presets ]
        self.cur.executemany("INSERT OR REPLACE INTO rel_preset_sfx VALUES  (?, ?, ?, ?, ?)", params)
        self.con.commit()

    def unlink_preset_sfx(self, preset_filename:str):
        self.cur.execute("DELETE FROM rel_preset_sfx WHERE preset_filename = ?", (preset_filename, ))
        self.con.commit()
    
    def __del__(self):
        self.con.close()

bsfxResourceRepository = BrushSfxResourceRepository()