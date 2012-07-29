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

#db.execute('DELETE FROM rec')
now = datetime.now()

db.execute('DELETE FROM plan WHERE et < ?', (now,))
db.execute('DELETE FROM rec WHERE et < ?', (now,))
db.commit()

rules = db.execute('SELECT * FROM rules')

for rule in rules:
  keys = ""
  for key in rule.keys():
    if keys:
      keys = keys + "AND "
    keys = keys + "%s LIKE :%s " % (key, key)
  query = 'SELECT * FROM plan WHERE %s' % (keys)
  programs = db.execute(query, rule)

  for program in programs:
    l = len(db.execute('SELECT * FROM rec WHERE ch_tag = :ch AND st = :st', program).fetchall())
    if l == 0:
      db.execute('INSERT INTO rec(ch_tag,st,et,title) VALUES (:ch, :st, :et, :title)', program)
    elif l > 1:
      print 'Error!'

db.commit()

for r in db.execute('SELECT * FROM rec'):
  print r
