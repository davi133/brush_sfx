
import os
import sqlite3
from typing import List
import json
import shutil

from PyQt5.Qt import *

from .constants import plugin_version, db_version, dir_path, BAKING_DEFAULTS_MODE,config_version

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
    
    def get_preset_by_file_list(self, filename_list: List[str])-> dict: # {"filename": id}
        #sql="select * from sqlitetable where rowid in ({seq})".format(seq=','.join(['?']*len(args)))
        sql ="SELECT id, filename FROM resources WHERE filename IN ({seq})".format(seq=','.join(['?']*len(filename_list)))
        self.cur.execute(sql, filename_list)
        presets =  {preset[1]: preset[0] for preset in self.cur.fetchall()}
        return presets

    def get_preset_by_key(self, key_list, use_id = True)-> dict:
        #sql="select * from sqlitetable where rowid in ({seq})".format(seq=','.join(['?']*len(args))

        sql ="SELECT id, name, filename FROM resources WHERE " 
        if use_id:
            sql+= "id IN ({seq})".format(seq=','.join(['?']*len(key_list)))
        else:
            sql+= "filename IN ({seq})".format(seq=','.join(['?']*len(key_list)))
        self.cur.execute(sql, key_list)
        rows = self.cur.fetchall()
        if use_id:
            presets =  {preset[0]: preset[1] for preset in rows}
        else:
            presets =  {preset[2]: preset[1] for preset in rows}
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

    def __repr__(self):
        return f"{self.sfx_id}, {self.use_eraser}, {self.eraser_sfx_id}, {self.volume}"

class BrushSfxResourceFile:
    def __init__(self):
        self.file_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'brushsfxresources.bsfx')
        file_exists = os.path.isfile(self.file_path)
        self.data = None
        if not file_exists:
            self.__init_file()
        
        with open(self.file_path, "r+") as file:
            self.data = file.readlines()
        self.data = [line.strip() for line in self.data]

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

bsfxFile = BrushSfxResourceFile()



class BrushSfxResourceRepository:
    def __init__(self):
        self.db_path =os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 'brushsfxresources.sqlite')
        self.default_db_path =f"{dir_path}/assets/default.sqlite"
        self.__baking_defaults_mode = BAKING_DEFAULTS_MODE

        self.con = None
        self.cur = None

        if self.__baking_defaults_mode:
            self.db_path = self.default_db_path
            print("[BrushSfx] Setting defaults mode")
        db_exists = os.path.isfile(self.db_path)
        self.__connect()
        if not db_exists:
            self.__create_db()
            self.__load_default_db()
        #self.con.set_trace_callback(print)
        
    def __migrate(self):
        pass


    def __connect(self):
        print(f"[BrushSfx] Connecting to sqlite:{self.db_path}")
        self.con = sqlite3.connect(self.db_path)
        self.cur = self.con.cursor()
    def __disconnect(self):
        self.con.close()
        self.con = None
        self.cur = None

    def __load_default_db(self):
        if self.__baking_defaults_mode:
            return
        with sqlite3.connect(f"file:{self.default_db_path}?mode=ro", uri=True) as con_default:
            cur_default = con_default.cursor()
            
            #copying sfx_options
            cur_default.execute("SELECT id, name FROM sfx_option")
            for row in cur_default.fetchall():
                self.add_sfx(row[0], row[1])

            #loading defaults (with wrong ids)
            cur_default.execute("SELECT preset_id, sfx_id, use_eraser, eraser_sfx_id, volume, preset_filename FROM rel_preset_sfx")
            all_rel_preset_sfx = cur_default.fetchall()
            filenames = [row[5] for row in all_rel_preset_sfx]

            #get correct ids from filenames
            filename_ids = kraResourceReader.get_preset_by_file_list(filenames)

            #create new objects with correct
            new_rel = {filename_ids[row[5]]: bsfxConfig(row[1],row[2],row[3], row[4])
            for row in all_rel_preset_sfx if filename_ids.get(row[5], None) is not None} 

            #insert with correct ids
            for key in new_rel:
                self.link_preset_sfx(key, new_rel[key])

        print("[BrushSfx] Loaded default sfx configuration")


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
                ),
                "preset_filename": preset_filename
            }
            return preset_sfx
        else:
            return None
        
    
    def link_preset_sfx(self, preset_id: int, sfx_config: bsfxConfig, preset_filename:str = ""):
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

def migrate_to_file():
    use_id = True
    db_path = f"{dir_path}/assets/default.sqlite"
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute("SELECT preset_id, preset_filename, sfx_id, use_eraser,eraser_sfx_id, volume FROM rel_preset_sfx")
        all_configs = cur.fetchall()
        use_id = all_configs[0][0] <= 1000000

        configs_dict = {(row[0] if use_id else row[1]):bsfxConfig(row[2],row[3],row[4],row[5])for row in all_configs}
        print(len(configs_dict), "len(configs_dict)")
        keys = [key for key in configs_dict]
        print(len(keys), "len(keys)")
        print("keys", keys)
        kraResources = kraResourceReader.get_preset_by_key(keys, use_id)

        for key in kraResources:
            name = kraResources[key]
            config = configs_dict[key]
            bsfxFile.save_sfx(name, config)


        
migrate_to_file()
    #get all brush names

