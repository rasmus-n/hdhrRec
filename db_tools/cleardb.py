#! /usr/bin/python
# -*- coding: latin-1 -*-

import sqlite3 as sql

db = sql.connect('tv.sqlite')

#~ db.execute('DROP TABLE IF EXISTS programs')
#~ db.execute('CREATE TABLE programs (channel_name text, title text, start datetime, end datetime, description text)')
#~ 
#~ db.execute('DROP TABLE IF EXISTS rules')
#~ db.execute('CREATE TABLE rules (name text, weight number, profile_name text, channel_name text, program_title text, program_description text)')
#~ db.execute('INSERT INTO rules(program_title) VALUES ("The Daily Show")')
#~ db.execute('INSERT INTO rules(program_title) VALUES ("Deadline")')
#~ db.execute('INSERT INTO rules(program_title) VALUES ("Storrygeren%")')
#~ db.execute('INSERT INTO rules(program_title) VALUES ("Jimmys madfabrik%")')
#~ db.execute('INSERT INTO rules(program_description) VALUES ("%thriller%")')
#~ db.execute('INSERT INTO rules(program_description) VALUES ("%krimi%")')
#~ 
#~ db.execute('DROP TABLE IF EXISTS profiles')
#~ db.execute('CREATE TABLE profiles (name text, format text, pre_record number, post_record number)')
#~ 
#~ db.execute('DROP TABLE IF EXISTS recordings')
#~ db.execute('CREATE TABLE recordings (id number, channel_name text, program_title text, profile_name text, program_start datetime, program_end datetime)')
#~ 
#~ db.execute('DROP TABLE IF EXISTS channels')
#~ db.execute('CREATE TABLE channels (name text, mux number , pid number , video number, audio number, subtitles number)')
#~ db.execute('INSERT INTO channels VALUES ("DR1", 26,  101,  111,  121,  135)')
#~ db.execute('INSERT INTO channels VALUES ("DR2", 26,  102,  211,  221,  235)')
#~ db.execute('INSERT INTO channels VALUES ("DRK", 44, 2100, 2111, 2121, 2135)')
#~ db.execute('INSERT INTO channels VALUES ("Ramasjang", 44, 2050, 2061, 2071, 2085)')
#~ db.execute('INSERT INTO channels VALUES ("DRHD", 44, 2300, 2311, 2321, 2335)')
#~ 
#~ db.execute('DROP TABLE IF EXISTS table_update_times')
#~ db.execute('CREATE TABLE table_update_times (programs datetime, rules datetime, recordings datetime)')
#~ db.execute('INSERT INTO table_update_times VALUES (0, 0, 0)')

db.commit()
