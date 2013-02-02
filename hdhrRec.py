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
from logging import info, warning, error
from os import fork, chdir, setsid, umask, getpid, close, open as os_open, dup2, O_RDWR

update_program = True

def dict_factory(cursor, row):
  d = {}
  for idx, col in enumerate(cursor.description):
    if row[idx] != None:
      d[col[0]] = row[idx]
  return d


def my_callback():
  now = datetime.now()
  now_str = str(now)[:19]
  global update_program

  table_update_times = db.execute('SELECT * FROM table_update_times').fetchone()
  update_rec = False
  
  if update_program and (table_update_times['programs'] < str(now - timedelta(hours=6))):
    print "Updating program table..."
    update_program = False
    Popen([tvdb_script, db_path])
    
  if table_update_times['programs'] > table_update_times['recordings']:
    print "Program table updated"
    update_rec = True
    update_program = True
    
  if table_update_times['rules'] > table_update_times['recordings']:
    print "Rule table updated"
    update_rec = True

  if update_rec:
    print "Updating recording table"
    Popen([recdb_script, db_path])
   
  r = []
  try:
    r = db.execute('SELECT id,program_title FROM recordings WHERE (program_end < ?) AND (id NOTNULL)', (now_str,))
    for p in r:
      print "End recording: %s" % (p['program_title']).encode(code)
      hdhr.stop(p['id'])
      db.execute('DELETE FROM recordings WHERE (id=?)', (p['id'],))
    db.commit()
  except Exception:
    print "Error A: %s" % (now_str)
    print traceback.format_exc()

  r = []
  try:
    r = db.execute('SELECT recordings.rowid,* FROM recordings,channels,profiles WHERE (recordings.channel_name=channels.name) AND (recordings.profile_name = profiles.name) AND (program_start < ?) AND (program_end > ?) AND (id ISNULL)', (now_str, now_str))
    for p in r:
      print "Start recording: %s" % p['program_title'].encode(code)
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


if __name__ == "__main__":
  try:
    cp = ConfigParser()
    cp.read("/usr/local/etc/hdhrRec.ini")
    video_root    =  cp.get("recorder" , "path")
    ip            =  cp.get("recorder" , "ip")
    tuners_raw    =  cp.get("tuner"    , "id").split()
    db_path       =  cp.get("scheduler", "db")
    tvdb_script   =  cp.get("scheduler", "tv")
    recdb_script  =  cp.get("scheduler", "rec")
    pid_file      =  cp.get("scheduler", "pid")
    
    tuners=[]
    for tuner in tuners_raw:
      tuners.append(int(tuner, 16))
      
    del cp
    del tuners_raw

  except:
    print traceback.format_exc()
    exit(-1)

  db = sql.connect(db_path)
  db.row_factory = dict_factory

  db.execute('UPDATE recordings SET id=NULL')
  db.execute('DELETE FROM recordings WHERE (program_end < ?)', (datetime.now(),))
  db.commit()

  hdhr.set_recorder_ip(ip)
  for tuner_id in tuners:
    hdhr.install_tuner(tuner_id, 0)
    hdhr.install_tuner(tuner_id, 1)

  hdhr.set_callback(my_callback)
  
  if (True):
    try:
      pid = fork()
      if pid > 0:
        exit(0)
    except OSError, e:
      exit(1)
      
    chdir("/")
    setsid()
    umask(0)
    
    try:
      pid = fork()
      if pid > 0:
        exit(0)
    except OSError, e:
      exit(1)
    
    close(0)
    close(1)
    close(2)
    
    os_open("/dev/null", O_RDWR)
    dup2(0,1)
    dup2(0,2)
    
  pf = open(pid_file, 'w')
  pf.write(str(getpid()))
  pf.close()
  del pf
  
  hdhr.run()
#~ my_callback()
