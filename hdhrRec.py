#! /usr/bin/python
# -*- coding: latin-1 -*-

import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

import hdhr
import sqlite3 as sql
from datetime import datetime, timedelta
from subprocess import Popen
import traceback
from ConfigParser import SafeConfigParser as ConfigParser

try:
  cp = ConfigParser()
  cp.read("hdhrRec.ini")
  video_root =  cp.get("recorder" , "path")
  ip         =  cp.get("recorder" , "ip")
  tuners_raw =  cp.get("tuner"    , "id").split()
  
  tuners=[]
  for tuner in tuners_raw:
    tuners.append(int(tuner, 16))
    
  del cp
  del tuners_raw
    
except:
  print traceback.format_exc()
  exit(-1)


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
  now_str = str(now)[:19]

  table_update_times = db.execute('SELECT * FROM table_update_times').fetchone()
  update_rec = False
  
  if table_update_times['programs'] < str(now - timedelta(hours=12)):
    print "Updating program table..."
    Popen('./db_tools/tvdb.py')
    
  if table_update_times['programs'] > table_update_times['recordings']:
    print "Program table updated"
    update_rec = True 
    
  if table_update_times['rules'] > table_update_times['recordings']:
    print "Rule table updated"
    update_rec = True

  if update_rec:
    print "Updating recording table"
    Popen('./db_tools/recdb.py')
    db.execute('UPDATE table_update_times SET recordings=?', (now_str,))
    db.commit()
   
  r = []
  try:
    r = db.execute('SELECT id,program_title FROM recordings WHERE (program_end < ?) AND (id NOTNULL)', (now_str,))
    for p in r:
      print "End recording: %s" % (p['program_title'])
      hdhr.stop(p['id'])
      db.execute('DELETE FROM recordings WHERE (id=?)', (p['id'],))
      db.commit()
  except Exception:
    print "Error A: %s" % (now_str)
    print traceback.format_exc()

  r = []
  try:
    r = db.execute('SELECT recordings.rowid,* FROM recordings,channels,profiles WHERE (recordings.channel_name=channels.name) AND (recordings.profile_name = profiles.name) AND (program_start < ?) AND (program_end > ?) AND (id ISNULL)', (now_str,now_str))
    for p in r:
      print "Start recording: %s" % p['program_title']
      file_path = "%s/%s" % (video_root, p['format'])
      file_path = file_path.replace('\\title', p['program_title'])
      file_path = file_path.replace('\date', now.strftime("%Y-%m-%d"))
      file_path = file_path.replace('\\time', now.strftime("%H%M"))

      record_id = hdhr.record(p['mux'], p['video'], p['audio'], p['subtitles'], p['pid'], file_path.encode(code))
      db.execute('UPDATE recordings SET id=? WHERE rowid=?', (record_id,p['rowid']))
      db.commit()
      
  except Exception:
    print "Error B: %s" % (now_str)
    print traceback.format_exc()
    Popen('./db_tools/dump_rec.py')
    
      
hdhr.set_recorder_ip(ip)
for tuner_id in tuners:
  hdhr.install_tuner(tuner_id, 0)
  hdhr.install_tuner(tuner_id, 1)

hdhr.set_callback(my_callback)

hdhr.run()
#~ my_callback()
