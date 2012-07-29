#! /usr/bin/python
# -*- coding: latin-1 -*-

import sqlite3 as sql

db = sql.connect('tv.sqlite')

db.execute('DROP TABLE IF EXISTS plan')
db.execute('CREATE TABLE plan (ch text, st datetime, et datetime, title text, subtitle text, description text)')

db.execute('DROP TABLE IF EXISTS rules')
db.execute('CREATE TABLE rules (ch text, title text, subtitle text, description text)')
db.execute('INSERT INTO rules(title) VALUES ("The Daily Show")')
db.execute('INSERT INTO rules(title) VALUES ("Deadline")')
db.execute('INSERT INTO rules(title) VALUES ("Storrygeren%")')
db.execute('INSERT INTO rules(title) VALUES ("Jimmys madfabrik%")')
db.execute('INSERT INTO rules(subtitle) VALUES ("%thriller%")')
db.execute('INSERT INTO rules(subtitle) VALUES ("%krimi%")')


db.execute('DROP TABLE IF EXISTS rec')
db.execute('CREATE TABLE rec (ch_tag text, st datetime, et datetime, title text, rid number)')

db.execute('DROP TABLE IF EXISTS streams')
db.execute('CREATE TABLE streams (ch_tag text, ch_nr number , pid number , vid number, aid number, sid number)')
db.execute('INSERT INTO streams VALUES ("DR1", 26,  101,  111,  121,  135)')
db.execute('INSERT INTO streams VALUES ("DR2", 26,  102,  211,  221,  235)')
db.execute('INSERT INTO streams VALUES ("DRK", 44, 2100, 2111, 2121, 2135)')
db.execute('INSERT INTO streams VALUES ("Ramasjang", 44, 2050, 2061, 2071, 2085)')
db.execute('INSERT INTO streams VALUES ("DRHD", 44, 2300, 2311, 2321, 2335)')

db.commit()
