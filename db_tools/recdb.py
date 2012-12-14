#! /usr/bin/python
# -*- coding: latin-1 -*-

import sqlite3 as sql
from datetime import datetime, timedelta
from sys import argv

def dict_factory(cursor, row):
  d = {}
  for idx, col in enumerate(cursor.description):
    if row[idx] != '':
      d[col[0]] = row[idx]
  return d

db = sql.connect(argv[1])
db.row_factory = dict_factory

now = datetime.now()

db.execute('DELETE FROM programs WHERE end < ?', (now,))
db.execute('DELETE FROM recordings WHERE (program_end < ?) AND (id ISNULL)', (now,))
db.commit()

m = db.execute('SELECT programs.rowid,* from programs,rules WHERE ((rules.channel_name = "" OR programs.channel_name LIKE rules.channel_name) AND (rules.program_title = "" OR programs.title LIKE rules.program_title) AND (rules.program_description = "" OR programs.description LIKE rules.program_description))')

p = {}
for r in m:
  if r['rowid'] in p:
    p[r['rowid']]['weight'] += r['weight']
    if r['weight'] > p[r['rowid']]['rule_weight']:
      p[r['rowid']]['profile_name'] = r['profile_name']

  else:
    p[r['rowid']] = r
    p[r['rowid']]['rule_weight'] = r['weight']

db.execute('DELETE FROM recordings WHERE (id ISNULL) AND (program_start > ?)', (now,))  
for r in p:
  d = p[r]
  if d['weight'] > 0:
    profile = db.execute('SELECT * FROM profiles WHERE name = ?', (d['profile_name'],)).fetchone()
    d['start'] = datetime.strptime(d['start'], "%Y-%m-%d %H:%M:%S") - timedelta(minutes=profile['pre_record'])
    d['end'] = datetime.strptime(d['end'], "%Y-%m-%d %H:%M:%S") + timedelta(minutes=profile['post_record'])

    l = len(db.execute('SELECT * FROM recordings WHERE (channel_name = :channel_name AND program_start = :start)', d).fetchall())
    #TODO: Support update
    if l == 0:
      db.execute('INSERT INTO recordings(channel_name,program_title,profile_name,program_start,program_end) VALUES (:channel_name, :title, :profile_name, :start, :end)', d)
    elif l > 1:
      print 'Error!'

db.commit()


#~ p[r['rowid']]['start'] = datetime.strptime(r['start'], "%Y-%m-%d %H:%M:%S") - timedelta(minutes=r['pre_record'])
#~ p[r['rowid']]['end'] = datetime.strptime(r['end'], "%Y-%m-%d %H:%M:%S") + timedelta(minutes=r['post_record'])
