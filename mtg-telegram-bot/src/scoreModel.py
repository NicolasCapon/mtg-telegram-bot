import datetime
import logging
import botutils as bu
import sqlite3

class ScoreModel:
    """Class to keep track of game scores"""
    
    def __init__(self):
        """ScoreModel constructor"""
       self.database = ""
       self.create_DB() # A mettre dans une command init du bot
       
    def add_score(self, winner_deck_id, loosers_deck_ids ,format_id, time, comment):
        
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        
        # Insert new game
        try:                                                                         
            c.execute("""INSERT INTO game(format_id, date, time, comment) 
               VALUES (?,?,?,?);""", (format_id, datetime.datetime.now(), time, comment))
            game_id = c.lastrowid
        except sqlite3.Error as e:
            logging.info("An SQL error [{}] occurred while inserting game".format(e))
            conn.close()
            return False
        
        # Insert winner deck and result
        try:
            c.execute("""INSERT INTO player(deck_id, game_id, is_winner) 
               VALUES (?,?,?);""", (winner_deck_id, game_id, 1))
        except sqlite3.Error as e:
            logging.info("An SQL error [{}] occurred while inserting winner_deck_id {}".format(e, winner_deck_id))
            conn.close()
            return False
        
        # Insert loosers deck and result
        for looser_deck_id in loosers_deck_ids:
            try:
                c.execute("""INSERT INTO player(deck_id, game_id, is_winner) 
                   VALUES (?,?,?);""", (looser_deck_id, game_id, 0))
            except sqlite3.Error as e:
                logging.info("An SQL error [{}] occurred while inserting looser_deck_id {}".format(e, looser_deck_id))
                conn.close()
                return False
        
        conn.commit()
        conn.close()
        return True
        
    def get_user_decks(self, user):
        """Return all decks from database for a specified user"""
        conn = sqlite3.connect(self.database)
        conn.row_factory = self.dict_factory
        c = conn.cursor()
        
        decks = c.execute("SELECT * from deck WHERE personn_id=?", (user["id"],)).fetchall()
        conn.close()
        
        return decks
        
    def update_DB(self):
        # TODO : update values (is_active and names...) not just inserting
        conn = sqlite3.connect(self.database)
        c = conn.cursor()
        
        # get all users and insert via id
        members = bu.load_members()
        db_member_ids = c.execute("SELECT id FROM person").fetchall()
        for member in members:
            if not member["id"] in db_member_ids:
                try:
                    c.execute("""INSERT INTO person(id, first_name, GD_dir_id) 
                       VALUES (?,?,?);""", (member["id"], member["first_name"], member["GD_dir_id"]))
                except sqlite3.Error as e:
                    logging.info("An SQL error [{}] occurred while inserting person {}.".format(e, member))
        # Update is_active status for old members
        # TODO : get all members id and change status of every other person to is_active=0
        
        # get all formats from local file and try to insert
        formats = self.load_formats()
        db_format_ids = c.execute("SELECT id FROM format").fetchall()
        for format in formats:
            if not format["id"] in db_format_ids:
                try:
                    c.execute("""INSERT INTO format(id, name, GD_banlist_file_id) 
                       VALUES (?,?,?);""", (format["id"], format["name"], format["GD_banlist_file_id"]))
                except sqlite3.Error as e:
                    logging.info("An SQL error [{}] occurred while inserting format {}.".format(e, format))
        
        # get all decks from Google Drive and insert via file_id
        db_gd_deck_ids = c.execute("SELECT GD_file_id FROM deck").fetchall()
        for member in members:
            decks = [] # TODO: Load list of file for each deck in member GD directory
            for deck in decks:
                if not deck["id"] in db_gd_deck_ids:
                    try:
                        c.execute("""INSERT INTO deck(personn_id, name, GD_file_id) 
                           VALUES (?,?,?);""", (member["id"], deck["title"], deck["id"]))
                    except sqlite3.Error as e:
                        logging.info("An SQL error [{}] occurred while inserting format {}.".format(e, format))
            # Update is_active status for old decks
            # TODO : get all current decks id and change status of every other decks to is_active=0
        
        conn.commit()   
        conn.close()
        return True
        
    def create_DB(self):
    
        # https://www.pythoncentral.io/advanced-sqlite-usage-in-python/
        conn = sqlite3.connect(self.database)
        c = conn.cursor()

        req = "CREATE TABLE IF NOT EXISTS game (id integer PRIMARY KEY AUTOINCREMENT,\
                                                format_id integer NOT NULL,\
                                                date timestamp NOT NULL,\
                                                time integer,\
                                                comment text,\
                                                FOREIGN KEY(format_id) REFERENCES format(id))"
        c.execute(req)
        req = "CREATE TABLE IF NOT EXISTS player (deck_id integer NOT NULL,\
                                                  game_id integer NOT NULL,\
                                                  is_winner integer NOT NULL\
                                                  PRIMARY KEY(deck_id, game_id),\
                                                  FOREIGN KEY(deck_id) REFERENCES deck(id),\
                                                  FOREIGN KEY(game_id) REFERENCES game(id))"
        c.execute(req)
        req = "CREATE TABLE IF NOT EXISTS deck (id integer PRIMARY KEY AUTOINCREMENT,\
                                                personn_id integer NOT NULL,\
                                                name text,\
                                                GD_file_id text,\
                                                is_active integer NOT NULL,\
                                                FOREIGN KEY(personn_id) REFERENCES person(id))"
        c.execute(req)
        req = "CREATE TABLE IF NOT EXISTS format (id integer PRIMARY KEY AUTOINCREMENT,\
                                                  name text,\
                                                  GD_banlist_file_id text,\
                                                  is_active integer NOT NULL)"
        c.execute(req)
        req = "CREATE TABLE IF NOT EXISTS person (id integer PRIMARY KEY AUTOINCREMENT,\
                                                  first_name text,\
                                                  GD_dir_id text,\
                                                  is_active integer NOT NULL)"
        c.execute(req)
        conn.commit()  
        conn.close()
        return True
        
    def dict_factory(self, cursor, row):
        """Return rows as dict"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d