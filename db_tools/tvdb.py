#! /usr/bin/python
# -*- coding: latin-1 -*-

import simplejson as json
import urllib
import sqlite3 as sql
from datetime import datetime, timedelta
from time import sleep

db = sql.connect('tv.sqlite')

channelMap = {
'DR1'       : ('DR1',"dr.dk/mas/whatson/channel/"),
'DR2'       : ('DR2',"dr.dk/mas/whatson/channel/"),
'TV2'       : ('td2',"dr.dk/external/ritzau/channel/"),
'TV3'       : ('dk3',"dr.dk/external/ritzau/channel/"),
'Kanal5'    : ('999',"dr.dk/external/ritzau/channel/"),
'DRK'       : ('TVK',"dr.dk/mas/whatson/channel/"),
'Ramasjang' : ('TVR',"dr.dk/mas/whatson/channel/"),
'DRHD'      : ('TVH',"dr.dk/mas/whatson/channel/"),
'NRK1'      : ('nk1',"dr.dk/external/ritzau/channel/"),
'SVT1'      : ('sv1',"dr.dk/external/ritzau/channel/"),
'SVT2'      : ('sv2',"dr.dk/external/ritzau/channel/"),
'STV4'      : ('tv4',"dr.dk/external/ritzau/channel/"),
}

dateFormatDR = "%Y-%m-%dT%H:%M:%S"

#db.execute("CREATE TABLE plan (ch text, st datetime, et datetime, title text, subtitle text, description text)")

#channels = channelMap.keys()
channels = ('DR1','DR2','DRK','Ramasjang','DRHD')
numberOfDays = 1

now = datetime.now()

for channel in channels:
  if not channel in channelMap:
      stderr.write("Unknown channel: %s\n" % channel)
      continue
      
  source = channelMap[channel][1] + channelMap[channel][0]
  for day in range(numberOfDays):
    date=(datetime.now()+timedelta(days=day)).strftime("%Y-%m-%d")
    request = "http://www.dr.dk/tjenester/programoversigt/DBService.ashx/getSchedule?channel_source_url=%s&broadcastDate=%s" % (source, date)
    data = json.loads(urllib.urlopen(request).read())

    if 'result' in data and data['result'] != []:
      programs = data['result']
    else:
      stderr.write("No info: %s %s\n" % (channel, date))
      programs = {}
      continue
    
    dbdata = []
    ts = datetime.now()
    for program in programs:
      d=[]
      d.append(channel)
      d.append(program['pro_title'])
      d.append(datetime.strptime(program['pg_start'][:18], dateFormatDR))
      d.append(datetime.strptime(program['pg_stop'][:18], dateFormatDR))
      des = None
      if program.has_key('ppu_punchline'):
        des = program['ppu_punchline']
        if program.has_key('ppu_description'):
          des = "%s\n%s" % (des, program['ppu_description'])
      elif program.has_key('ppu_description'):
        des = program['ppu_description']
        
      d.append(des)
      if d[3] > now: # 3 = end
        dbdata.append(d)
    
    db.execute('DELETE FROM programs WHERE channel_name=?', (channel,))
#    s = "INSERT INTO programs(channel_name, title, start, end, description"
    db.executemany('INSERT INTO programs(channel_name, title, start, end, description) VALUES (?, ?, ?, ?, ?)', dbdata)
    db.commit()
    
now = datetime.now()
db.execute('UPDATE table_update_times SET programs=?', (now,))
db.commit()
