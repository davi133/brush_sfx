
import os
import sqlite3
from typing import List
import json
import shutil

from PyQt5.Qt import *

from .constants import plugin_version, db_version, dir_path, setting_defaults_mode

class KritaResourceReader:
    def __init__(self):
        db_path =os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'resourcecache.sqlite')
        self.con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.cur = self.con.cursor()
        #self.con.set_trace_callback(print)

    def get_preset_id_by_filename(self, preset_filename: str)-> int:
        self.cur.execute("SELECT id, filename FROM resources WHERE filename = ?", (preset_filename,))
        result = self.cur.fetchall()
        preset_id = result[0][0]
        return preset_id
    
    def get_preset_by_file_list(self, filename_list: List[str])-> dict: # {id:"filename"}
        #sql="select * from sqlitetable where rowid in ({seq})".format(seq=','.join(['?']*len(args)))
        sql ="SELECT id, filename FROM resources WHERE filename IN ({seq})".format(seq=','.join(['?']*len(filename_list)))
        self.cur.execute(sql, filename_list)
        presets =  {preset[1]: preset[0] for preset in self.cur.fetchall()}
        return presets
    
    def __del__(self):
        self.con.close()

kraResourceReader = KritaResourceReader()

class bsfxConfig:
    def __init__(self,sfx_id: str, use_eraser: bool = False, eraser_sfx_id: str = "", volume: float = 1.0, 
    preset_filename: str = ""):
        self.sfx_id = sfx_id
        self.use_eraser = use_eraser
        self.eraser_sfx_id = eraser_sfx_id
        self.volume = volume

    def __str__(self):
        return f"{self.sfx_id}, {self.use_eraser}, {self.eraser_sfx_id}, {self.volume}"

class BrushSfxResourceRepository:
    def __init__(self):
        self.db_path =os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'brushsfxresources.sqlite')
        self.default_db_path =f"{dir_path}/assets/default.sqlite"
        self.__setting_defaults_mode = setting_defaults_mode

        self.con = None
        self.cur = None

        if self.__setting_defaults_mode:
            self.db_path = self.default_db_path
            print("[BrushSfx] Setting defaults mode")
        db_exists = os.path.isfile(self.db_path)
        self.__connect()
        if not db_exists:
            self.__create_db()
            self.__load_default_db()

        #self.con.set_trace_callback(print)
        

    def __connect(self):
        print(f"[BrushSfx] Connecting to sqlite:{self.db_path}")
        self.con = sqlite3.connect(self.db_path)
        self.cur = self.con.cursor()
    def __disconnect(self):
        self.con.close()
        self.con = None
        self.cur = None

    def __load_default_db(self):
        if self.__setting_defaults_mode:
            return
        print("[BrushSfx] Loaded default sfx list")
        con_default = sqlite3.connect(f"file:{self.default_db_path}?mode=ro", uri=True)
        cur_default = con_default.cursor()
        #get ids from filenames on default


        #create new objects


        #insert with correct ids


        con_default.close()


    def __create_db(self):
        stmt_version = "CREATE TABLE IF NOT EXISTS bsfx_version (\
                            version TEXT PRIMARY KEY \
                        );"
        stmt_sfx_option = "CREATE TABLE IF NOT EXISTS sfx_option (\
                            id TEXT  PRIMARY KEY, \
                            name TEXT  NOT NULL\
                        );"
        stmt_preset_sfx = "CREATE TABLE IF NOT EXISTS rel_preset_sfx (\
                            preset_id INTEGER PRIMARY KEY, \
                            sfx_id TEXT NOT NULL,\
                            use_eraser INTEGER DEFAULT 0, \
                            eraser_sfx_id TEXT, \
                            volume REAL,\
                            preset_filename TEXT,\
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
        
    
    def get_preset_sfx(self, preset_id: int) -> dict:
        self.cur.execute("SELECT preset_id, sfx_id, use_eraser, eraser_sfx_id, volume FROM rel_preset_sfx WHERE preset_id = ?", (preset_id,))
        rel_preset_sfx = self.cur.fetchall()
        if len(rel_preset_sfx) > 0:
            preset_sfx =  {
                "preset_id": rel_preset_sfx[0][0],
                "sfx_config": bsfxConfig(
                    rel_preset_sfx[0][1],
                    rel_preset_sfx[0][2],
                    rel_preset_sfx[0][3],
                    rel_preset_sfx[0][4],
                )
            }
            return preset_sfx
        else:
            return None
    
    def get_preset_sfx_by_filename(self, preset_filename:str) -> dict:
        print("get_preset_sfx_by_filename", preset_filename)
        self.cur.execute("SELECT preset_id, sfx_id, use_eraser, eraser_sfx_id, volume FROM rel_preset_sfx WHERE preset_filename = ?", (preset_filename,))
        rel_preset_sfx = self.cur.fetchall()
        if len(rel_preset_sfx) > 0:
            preset_sfx =  {
                "preset_id": rel_preset_sfx[0][0],
                "sfx_config": bsfxConfig(
                    rel_preset_sfx[0][1],
                    rel_preset_sfx[0][2],
                    rel_preset_sfx[0][3],
                    rel_preset_sfx[0][4],
                    preset_filename
                )
            }
            return preset_sfx
        else:
            return None
        
    
    def link_preset_sfx(self, preset_id: int, sfx_config: bsfxConfig, preset_filename:str = ""):
        if self.__setting_defaults_mode:
            preset_id +=1000000
        params = [(preset_id, sfx_config.sfx_id, sfx_config.use_eraser, sfx_config.eraser_sfx_id, sfx_config.volume, preset_filename)]
        self.cur.executemany("INSERT OR REPLACE INTO rel_preset_sfx VALUES (?, ?, ?, ?, ?, ?)", params)
        self.con.commit()
    

    def unlink_preset_sfx(self, preset_id: int):
        self.cur.execute("DELETE FROM rel_preset_sfx WHERE preset_id = ?", (preset_id, ))
        self.con.commit()

    def unlink_preset_sfx_by_filename(self, preset_filename: int):
        self.cur.execute("DELETE FROM rel_preset_sfx WHERE preset_filename = ?", (preset_filename, ))
        self.con.commit()
    
    def __del__(self):
        self.con.close()

bsfxResourceRepository = BrushSfxResourceRepository()