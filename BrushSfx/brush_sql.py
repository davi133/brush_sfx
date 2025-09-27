
import os
import sqlite3
from typing import List

from PyQt5.Qt import *

from .constants import plugin_version, db_version


db_path =os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'brushsfxcache.sqlite')
db_exists = os.path.isfile(db_path)

if not db_exists:
    create_db()

bsfx_con = sqlite3.connect(db_path)
bsfx_cur = bsfx_con.cursor()


class KritaResourcesHelper:
    def __init__(self):
        pass
    
    def get_preset_id(self, preset_name)->int:
        pass
    
    def get_tags(self)-> List[dict]:
        pass
    
    def get_presets_in_tag(self, tag_id)->List[dict]:
        pass

kraResourceHelper = KritaResourcesHelper()

class BrushSfxResourceHelper:
    def __init__(self):
        db_path =os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'brushsfxcache.sqlite')
        db_exists = os.path.isfile(db_path)
        
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()
        
        if not db_exists:
            self.__create_db()


    def __create_db(self):
        stmt_version = "CREATE TABLE IF NOT EXISTS bsfx_version (\
                            version TEXT PRIMARY KEY \
                        );"
        stmt_sfx_option = "CREATE TABLE IF NOT EXISTS sfx_option (\
                            id TEXT  PRIMARY KEY, \
                            nane TEXT  NOT NULL\
                        );"
        stmt_preset_sfx = "CREATE TABLE IF NOT EXISTS rel_preset_sfx (\
                            id INTEGER  PRIMARY KEY, \
                            preset_id INTEGER  NOT NULL,\
                            sfx_id TEXT NOT NULL,\
                            options_json TEXT,\
                            FOREIGN KEY(sfx_id) REFERENCES sfx_option(id)\
                        );"
        try:
            self.cur.execute(stmt_version)
            self.cur.execute(f"INSERT INTO bsfx_version(version) VALUES (\'{db_version}\')")
            self.cur.execute(stmt_sfx_option)
            self.cur.execute(stmt_preset_sfx)
            self.con.commit()
            print("[BrushSfx] brushsfxcache.sqlite created")
        except Exception as e:
            print("[BrushSfx] An error ocurred while creating the sqlite database")
            print(e)
            raise e

    def add_sfx(self, object_yet_to_define):
        pass
    
    def link_preset_sfx(self, preset_id: int, sfx_id: str, options: dict):
        pass
    
    def link_all_presets_in_tag(self, tag_id: int, sfx_id: str, options: dict):
        pass

bsfxResourceHelper = BrushSfxResourceHelper()