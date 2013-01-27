#! /usr/bin/python
# -*- coding: latin-1 -*-

import simplejson as json
import urllib
import sqlite3 as sql
from datetime import datetime, timedelta
from time import sleep
from sys import stderr, argv

db = sql.connect(argv[1])

channelMap = {
'DR1'       : ('DR1',"w_"),
'DR2'       : ('DR2',"w_"),
'TV2'       : ('td2',"r_"),
'TV2News'   : ('tws',"r_"),
'TV2Zulu'   : ('t2z',"r_"),
'TV3'       : ('dk3',"r_"),
'TV3Plus'   : ('r382',"r_"),
'Kanal5'    : ('999',"r_"),
'6eren'     : ('snt',"r_"),
'BBCE'      : ('bbp',"r_"),
}

dateFormatDR = "%Y-%m-%dT%H:%M:%S"

#db.execute("CREATE TABLE plan (ch text, st datetime, et datetime, title text, subtitle text, description text)")

channels = channelMap.keys()
#channels = ('DR1','DR2','DRK','Ramasjang','DRHD','TV2OJ')
numberOfDays = 2

now = datetime.now()

db.execute('DELETE FROM programs WHERE (end < ?)', (now,))
db.commit()

for channel in channels:
  if not channel in channelMap:
      stderr.write("Unknown channel: %s\n" % channel)
      continue
      
  source = channelMap[channel][1] + channelMap[channel][0]
  for day in range(numberOfDays):
    date=(datetime.now()+timedelta(days=day)).strftime("%Y-%m-%d")
#    request = "http://www.dr.dk/tjenester/programoversigt/DBService.ashx/getSchedule?channel_source_url=%s&broadcastDate=%s" % (source, date)
    request = "http://www.dr.dk/tv/oversigt/json/guide/schedule?startTimesectionId=0&days=%d&channelid=%s" % (day,source)
    try:
      data = json.loads(urllib.urlopen(request).read())
    except:
      continue

#    if 'result' in data and data['result'] != []:
#      programs = data['result']
#    else:
#      stderr.write("No info: %s %s\n" % (channel, date))
#      programs = {}
#      continue
    
    TimeSections = data['TimeSection']
    dbdata = []
    dbdata_start = []
    dbdata_end = []
    
    for TimeSection in TimeSections:
      programs = TimeSection['Programs']

      ts = datetime.now()
      for program in programs:
        d=[]
        d.append(channel)
        d.append(program['Title'])
        d.append(datetime.fromtimestamp(int(program['StartDateTime'][6:-5]))) #'/Date(1352224200000)/'
        d.append(datetime.fromtimestamp(int(program['EndDateTime'][6:-5])))
#        des = None
#        if program.has_key('ppu_punchline'):
#          des = program['ppu_punchline']
#          if program.has_key('ppu_description'):
#            des = "%s\n%s" % (des, program['ppu_description'])
#        elif program.has_key('ppu_description'):
#          des = program['ppu_description']
          
        d.append(program['Punchline'])
        if d[3] > now: # 3 = end
          dbdata.append(d)
          dbdata_start.append([d[0], d[2], d[2]])
          dbdata_end.append([d[0], d[3], d[3]])
#          db.execute('DELETE FROM programs WHERE (channel_name=?) AND (start < ?) AND (end > ?)', (channel,d[2],d[2]))
#          db.execute('DELETE FROM programs WHERE (channel_name=?) AND (start < ?) AND (end > ?)', (channel,d[3],d[3]))
#          db.execute('INSERT INTO programs(channel_name, title, start, end, description) VALUES (?, ?, ?, ?, ?)', d)
#          db.commit()
      
#    db.execute('DELETE FROM programs WHERE (channel_name=?) AND (start > ?)', (channel,now))
#    s = "INSERT INTO programs(channel_name, title, start, end, description"
    db.executemany('DELETE FROM programs WHERE (channel_name=?) AND (start <= ?) AND (end >= ?)', dbdata_start)
    db.executemany('DELETE FROM programs WHERE (channel_name=?) AND (start <= ?) AND (end >= ?)', dbdata_end)
    db.executemany('INSERT INTO programs(channel_name, title, start, end, description) VALUES (?, ?, ?, ?, ?)', dbdata)
    db.commit()
    
now = datetime.now()
db.execute('UPDATE table_update_times SET programs=?', (now,))
db.commit()
