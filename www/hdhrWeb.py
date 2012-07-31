#! /usr/bin/python

import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

import web
from web import form
from datetime import datetime
import urllib

render = web.template.render('templates/', base='layout')
db = web.database(dbn='sqlite', db='../tv.sqlite')

add_rule_form = form.Form (
  form.Textbox('ch', description='Channel'),
  form.Textbox('title', description='Title'),
  form.Textbox('description', description='Description'),
)

urls = (
  '/'           , 'start',
  '/streams'    , 'streams',
  '/rules'      , 'rules',
  '/rules/add'  , 'rule_add',
  '/rec'        , 'rec',
)

class start:
  def GET(self):
    now = datetime.now()
    plan = {}
    channels = db.select('channels', what='name')
    for channel in channels:
      d=dict(channel=channel['name'], time=now)
      plan[channel['name']] = db.select("programs", d, where='(channel_name = $channel) AND (end > $time)')
    return render.index(plan)

class streams:
  def GET(self):
    streams = db.select('channels', what='rowid,*')
    return render.streams(streams)
    
class rules:
  def GET(self):
    rules = db.select('rules', what='rowid,*')
    return render.rules(rules)

class rule_add:
  def GET(self):
    f = add_rule_form()
    return render.add_rule(f)
    
  def POST(self):
    d = {}
    f = add_rule_form()
    if f.validates():
      db.insert('rules', **f.d)
      db.update('table_update_times', rules=datetime.now())
      raise web.seeother('/rules')
    else:
      return render.add_rule(f)

class rec:
  def GET(self):
    rec = db.select('recordings', what='rowid,*', order='program_start')
    return render.rec(rec)

app = web.application(urls, globals())

if __name__ == "__main__":
  app.run() 
else:
  application = app.wsgifunc()
