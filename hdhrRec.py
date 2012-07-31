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

db.execute('UPDATE recordings SET id=NULL')
db.execute('DELETE FROM recordings WHERE (program_end < ?)', (datetime.now(),))
db.commit()

def my_callback():
  now = datetime.now()
  table_update_times = db.execute('SELECT * FROM table_update_times').fetchone()
  update_rec = False
  
  if table_update_times['programs'] < str(now - timedelta(hours=12)):
    print "Updating program table..."
    
  if table_update_times['programs'] > table_update_times['recordings']:
    print "Program table updated"
    update_rec = True 
    
  if table_update_times['rules'] > table_update_times['recordings']:
    print "Rule table updated"
    update_rec = True

  if update_rec:
    print "Updating recording table",
    db.execute('UPDATE table_update_times SET recordings=?', (now,))
    db.commit()
    
  start = now + timedelta(minutes=2)
  stop = now - timedelta(minutes=5)
  r = db.execute('SELECT recordings.rowid,* FROM recordings,channels WHERE (recordings.channel_name=channels.name) AND (program_start < ?) AND (program_end > ?) AND (id ISNULL)', (start,stop))
  for p in r:
    print "Start recording: %s" % p['program_title']
    file_path = "%s%s (%s).ts" % (video_root,p['program_title'],now.strftime("%Y-%m-%d %H%M"))
    record_id = hdhr.record(p['mux'], p['video'], p['audio'], p['subtitles'], p['pid'], file_path.encode(code))
    db.execute('UPDATE recordings SET id=? WHERE rowid=?', (record_id,p['rowid']))
    db.commit()

  r = db.execute('SELECT rowid,id,program_title FROM recordings WHERE (program_end < ?) AND (id NOTNULL)', (stop,))
  for p in r:
    print "End recording: %s" % (p['program_title'])
    hdhr.stop(p['id'])
    
  db.execute('DELETE FROM recordings WHERE (program_end < ?)', (stop,))
  db.commit()
    

hdhr.install_tuner(0x122004D5, 0)
hdhr.install_tuner(0x122004D5, 1)

hdhr.set_callback(my_callback)

hdhr.run()
#~ my_callback()
