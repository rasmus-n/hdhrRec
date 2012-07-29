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
  form.Textbox('subtitle', description='Subtitle'),
  form.Textbox('description', description='Description'),
)

urls = (
  '/'           , 'start',
  '/streams'    , 'streams',
  '/rules'      , 'rules',
  '/rules/add'  , 'add_rule',
  '/rec'        , 'rec',
)

class start:
  def GET(self):
    now = datetime.now()
    plan = {}
    ch_tags = db.select('streams', what='ch_tag')
    for tag in ch_tags:
      d=dict(ch=tag['ch_tag'], t=now)
      plan[tag.ch_tag] = db.select("plan", d, where='(ch = $ch) AND (et > $t)')
    print plan
    return render.index(plan)

class streams:
  def GET(self):
    streams = db.select('streams', what='rowid,*')
    return render.streams(streams)
    
class rules:
  def GET(self):
    rules = db.select('rules', what='rowid,*')
    return render.rules(rules)

class add_rule:
  def GET(self):
    f = add_rule_form()
    return render.add_rule(f)
    
  def POST(self):
    d = {}
    f = add_rule_form()
    if f.validates():
      db.insert('rules', **f.d)
      raise web.seeother('/rules')
    else:
      return render.add_rule(f)

class rec:
  def GET(self):
    rec = db.select('rec', what='rowid,*', order='st')
    return render.rec(rec)

app = web.application(urls, globals())

if __name__ == "__main__":
  app.run() 
else:
  application = app.wsgifunc()
