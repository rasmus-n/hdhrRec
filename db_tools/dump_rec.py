#! /usr/bin/python
# -*- coding: latin-1 -*-

import sqlite3 as sql

db = sql.connect('tv.sqlite')

for line in db.iterdump():
  if "INSERT INTO \"recordings\"" in line:
    print line[31:]
