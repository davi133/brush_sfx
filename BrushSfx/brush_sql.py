
import os
import sqlite3
from typing import List
import json

from PyQt5.Qt import *

from .constants import plugin_version, db_version


db_path =os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'brushsfxcache.sqlite')
db_exists = os.path.isfile(db_path)

#bsfx_con = sqlite3.connect(db_path)
#bsfx_cur = bsfx_con.cursor()


class KritaResourcesHelper:
    def __init__(self):
        db_path =os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'resourcecache.sqlite')
        self.con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.cur = self.con.cursor()
    
    def get_all_tags(self)-> List[dict]: # {"id":"id, "name":"name"}
        self.cur.execute("SELECT id, name FROM tags ORDER BY name")
        tags = [{"id":tag[0], "name": tag[1]} for tag in self.cur.fetchall()]
        return tags
    
    def get_presets_with_tag(self, tag_id: int)->List[dict]: # {name:"name", filename:"filename"}
        self.cur.execute("SELECT name, filename FROM resources WHERE resource_type_id = 5 AND id IN (SELECT resource_id FROM resource_tags rt WHERE tag_id = ?)", (tag_id,))
        presets = [{"name":preset[0], "filename":preset[1]} for preset in self.cur.fetchall()]
        return presets
    
    def __del__(self):
        self.con.close()

kraResourceHelper = KritaResourcesHelper()


class SoundEffectOption:
    def __init__(self, sfx_id: str, name: str):
        self.id = sfx_id
        self.name = name


class BrushSfxResourceHelper:
    def __init__(self):
        db_path =os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'brushsfxcache.sqlite')
        db_exists = os.path.isfile(db_path)
        
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()
        
        #self.con.set_trace_callback(print)
        
        if not db_exists:
            self.__create_db()


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
                            options_json TEXT,\
                            FOREIGN KEY(sfx_id) REFERENCES sfx_option(id)\
                        );"
        try:
            self.cur.execute(stmt_version)
            self.cur.execute("PRAGMA foreign_keys = ON;")
            self.cur.execute(f"INSERT INTO bsfx_version(version) VALUES (\'{db_version}\')")
            self.cur.execute(stmt_sfx_option)
            self.cur.execute(stmt_preset_sfx)
            self.con.commit()
            print("[BrushSfx] brushsfxcache.sqlite created")
        except Exception as e:
            print("[BrushSfx] An error ocurred while creating the sqlite database")
            print(e)
            raise e

    def add_sfx(self, sound_effect: SoundEffectOption):
        params = (sound_effect.sfx_id, sound_effect.name)
        self.cur.execute("INSERT OR REPLACE INTO sfx_option VALUES (?, ?)", params)
        self.con.commit()
        
    
    def get_preset_sfx(self, preset_filename: str) -> dict:
        #1)_Realistic_Standard_Ballpoint_EXPER_PressureB.kpp
        self.cur.execute("SELECT preset_filename, sfx_id, options_json FROM rel_preset_sfx WHERE preset_filename = ? ", (preset_filename, ))
        rel_preset_sfx = self.cur.fetchall()
        if len(rel_preset_sfx) > 0:
            return {
                "preset_filename": rel_preset_sfx[0][0],
                "sfx_id": rel_preset_sfx[0][1],
                "options": rel_preset_sfx[0][2],
            }
        else:
            return None

    def link_preset_sfx(self, preset_filename: str, sfx_id: str, options: dict):
        params = [(preset_filename, sfx_id, json.dumps(options))]
        self.cur.executemany("INSERT OR REPLACE INTO rel_preset_sfx VALUES ( ? , ?, ? )", params)
        self.con.commit()
    
    def link_all_presets_in_tag(self, tag_id: int, sfx_id: str, options: dict):
        presets = kraResourceHelper.get_presets_with_tag(tag_id)
        params = [ (preset["filename"], sfx_id, json.dumps(options)) for preset in presets ]
        self.cur.executemany("INSERT OR REPLACE INTO rel_preset_sfx VALUES (?, ?, ?)", params)
        self.con.commit()

    def unlink_preset_sfx(self, preset_filename:str):
        self.cur.execute("DELETE FROM rel_preset_sfx WHERE preset_filename = ?", (preset_filename, ))
        self.con.commit()
    
    def __del__(self):
        self.con.close()

bsfxResourceHelper = BrushSfxResourceHelper()