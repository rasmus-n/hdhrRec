#! /usr/bin/python
# -*- coding: latin-1 -*-

import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

import hdhr
import sqlite3 as sql
from datetime import datetime, timedelta

video_root = "/home/rn/tv/"

def dict_factory(cursor, row):
  d = {}
  for idx, col in enumerate(cursor.description):
    if row[idx] != None:
      d[col[0]] = row[idx]
  return d

db = sql.connect('tv.sqlite')
db.row_factory = dict_factory

db.execute('UPDATE rec SET rid=NULL')
db.execute('DELETE FROM rec WHERE (et < ?)', (datetime.now(),))
db.commit()

def my_callback():
  now = datetime.now()
  start = now + timedelta(minutes=2)
  stop = now - timedelta(minutes=5)
  r = db.execute('SELECT rec.rowid,* FROM rec,streams WHERE (rec.ch_tag=streams.ch_tag) AND (st < ?) AND (et > ?) AND (rid ISNULL)', (start,stop))
  for p in r:
    print "Start recording: %s" % p['title']
    file_path = "%s%s.ts" % (video_root,p['title'])
    rid = hdhr.record(p['ch_nr'], p['vid'], p['aid'], p['sid'], p['pid'], file_path.encode(code))
    db.execute('UPDATE rec SET rid=? WHERE rowid=?', (rid,p['rowid']))
    db.commit()

  r = db.execute('SELECT rowid,rid,title FROM rec WHERE (et < ?) AND (rid NOTNULL)', (stop,))
  for p in r:
    print "End recording: %s" % (p['title'])
    hdhr.stop(p['rid'])
    
  db.execute('DELETE FROM rec WHERE (et < ?)', (stop,))
  db.commit()
    

hdhr.install_tuner(0x122004D5, 0)
hdhr.install_tuner(0x122004D5, 1)

hdhr.set_callback(my_callback)

hdhr.run()
