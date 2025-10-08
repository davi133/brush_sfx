
import os
import sqlite3
from typing import List
import json
import shutil

from PyQt5.Qt import *

from .constants import plugin_version, db_version, dir_path

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

    #TODO delete later
    def get_preset_by_file_list(self, filename_list: List[str])-> List[dict]: # {id: 0, filename: "filename"}
        #sql="select * from sqlitetable where rowid in ({seq})".format(seq=','.join(['?']*len(args)))
        sql ="SELECT id, filename FROM resources WHERE filename IN ({seq})".format(seq=','.join(['?']*len(filename_list)))
        self.cur.execute(sql, filename_list)
        presets =  {preset[1]: preset[0] for preset in self.cur.fetchall()}
        return presets
    
    def __del__(self):
        self.con.close()

kraResourceReader = KritaResourceReader()

class bsfxConfig:
    def __init__(self,sfx_id: str, use_eraser: bool = False, eraser_sfx_id: str = "", volume: float = 1.0):
        self.sfx_id = sfx_id
        self.use_eraser = use_eraser
        self.eraser_sfx_id = eraser_sfx_id
        self.volume = volume

    def __str__(self):
        return f"{self.sfx_id}, {self.use_eraser}, {self.eraser_sfx_id}, {self.volume}"

class BrushSfxResourceRepository:
    def __init__(self):
        self.db_path =os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'brushsfxresources.sqlite')
        db_exists = os.path.isfile(self.db_path)

        if not db_exists:
            self.__load_default_db()
        
        self.con = sqlite3.connect(self.db_path)
        self.cur = self.con.cursor()
        #self.con.set_trace_callback(print)
        
    def update_db_hoje(self):
        return
        # GET OBJECTS
        self.cur.execute("SELECT preset_filename, sfx_id, use_eraser, eraser_sfx_id, options_json FROM rel_preset_sfx")
        all_rel_preset_sfx = self.cur.fetchall()
        filenames = [row[0] for row in all_rel_preset_sfx]
        #print(filenames)

        #GET IDS FOR FILENAMES
        resources_dict = kraResourceReader.get_preset_by_file_list(filenames)
        print(resources_dict)


        #discard filenames not found
        #all_rel_preset_sfx = []

        #NEW OBJECTS
        new_rel = {resources_dict[row[0]]: bsfxConfig2(row[1],row[2],row[3], json.loads(row[4])["volume"])
        for row in all_rel_preset_sfx if resources_dict.get(row[0], None) is not None} 

        print(new_rel)
        
        # CREATE NEW TABLE
        stmt_preset_sfx = "CREATE TABLE rel_preset_sfx_aux (\
                            preset_id INTEGER PRIMARY KEY, \
                            sfx_id TEXT NOT NULL,\
                            use_eraser INTEGER DEFAULT 0, \
                            eraser_sfx_id TEXT, \
                            volume REAL,\
                            FOREIGN KEY(sfx_id) REFERENCES sfx_option(id),\
                            FOREIGN KEY(eraser_sfx_id) REFERENCES sfx_option(id)\
                        );"
        self.cur.execute(stmt_preset_sfx)
        self.con.commit()

        #TRANSFER OLDER TABLE TO NEW TABLE
        for key in new_rel:
            self.link_preset_sfx(key, new_rel[key])
        self.con.commit()

        # DELETE OLD TABLE

        stmt_delete = "DROP TABLE rel_preset_sfx"
        self.cur.execute(stmt_delete)
        self.con.commit()

        # RENAME NEW TABLE
        stmt_rename = "ALTER TABLE rel_preset_sfx_aux RENAME TO rel_preset_sfx;"
        self.cur.execute(stmt_rename)
        self.con.commit()




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
                            preset_id INTEGER PRIMARY KEY, \
                            sfx_id TEXT NOT NULL,\
                            use_eraser INTEGER DEFAULT 0, \
                            eraser_sfx_id TEXT, \
                            volume REAL,\
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
        self.cur.execute( "SELECT preset_id, sfx_id, use_eraser, eraser_sfx_id, volume FROM rel_preset_sfx WHERE preset_id = ?", (preset_id,))
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
    
    def link_preset_sfx(self, preset_id: int, sfx_config: bsfxConfig):
        params = [(preset_id, sfx_config.sfx_id, sfx_config.use_eraser, sfx_config.eraser_sfx_id, sfx_config.volume)]
        self.cur.executemany("INSERT OR REPLACE INTO rel_preset_sfx VALUES (?, ?, ?, ?, ?)", params)
        self.con.commit()
    

    def unlink_preset_sfx(self, preset_id: int):
        self.cur.execute("DELETE FROM rel_preset_sfx WHERE preset_id = ?", (preset_id, ))
        self.con.commit()
    
    def __del__(self):
        self.con.close()

bsfxResourceRepository = BrushSfxResourceRepository()