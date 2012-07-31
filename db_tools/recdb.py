#! /usr/bin/python
# -*- coding: latin-1 -*-

import sqlite3 as sql
from datetime import datetime, timedelta

def dict_factory(cursor, row):
  d = {}
  for idx, col in enumerate(cursor.description):
    if row[idx] != None:
      d[col[0]] = row[idx]
  return d

db = sql.connect('tv.sqlite')
db.row_factory = dict_factory

now = datetime.now()

db.execute('DELETE FROM programs WHERE end < ?', (now,))
db.execute('DELETE FROM recordings WHERE program_end < ?', (now,))
db.commit()

rules = db.execute('SELECT * FROM rules')

for rule in rules:
  keys = ""
  for key in rule.keys():
    if "program_" in key:
      programs_key = key[8:]
      if keys:
        keys = keys + "AND "
      keys = keys + "%s LIKE :%s " % (programs_key, key)
  query = 'SELECT * FROM programs WHERE %s' % (keys)
  programs = db.execute(query, rule)

  for program in programs:
    l = len(db.execute('SELECT * FROM recordings WHERE (channel_name = :channel_name AND program_start = :start)', program).fetchall())
    if l == 0:
      db.execute('INSERT INTO recordings(channel_name,program_title,program_start,program_end) VALUES (:channel_name, :title, :start, :end)', program)
    elif l > 1:
      print 'Error!'

db.commit()

for r in db.execute('SELECT * FROM recordings'):
  print r
