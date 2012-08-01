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

rule_form = form.Form (
  form.Textbox('name', description='Name'),
  form.Textbox('channel_name', description='Channel'),
  form.Textbox('program_title', description='Title'),
  form.Textbox('program_description', description='Description'),
  form.Textbox('weight', description='Weight'),
  form.Textbox('profile_name', description='Profile'),
)

profile_form = form.Form (
  form.Textbox('name', description='Name'),
  form.Textbox('format', description='Format'),
  form.Textbox('pre_record', description='Pre rec.'),
  form.Textbox('post_record', description='Post rec.'),
)

urls = (
  '/'                     , 'start',
  '/streams'              , 'streams',
  '/rules'                , 'rules',
  '/rules/add'            , 'rule_add',
  '/rules/edit/([0-9]+)'  , 'rule_edit',
  '/rec'                  , 'rec',
  '/profiles'             , 'profiles',
  '/profiles/add'         , 'profile_add',
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
    f = rule_form()
    return render.rule_add(f)
    
  def POST(self):
    f = rule_form()
    if f.validates():
      db.insert('rules', **f.d)
      db.update('table_update_times', where='rowid=1', rules=datetime.now())
      raise web.seeother('/rules')
    else:
      return render.rule_add(f)

class rule_edit:
  def GET(self, rule_nr):
    f = rule_form()
    d = dict(id = rule_nr);
    rule = db.select('rules', d, where='rowid = $id', what='rowid,*')
    f.fill(rule[0])
    return render.rule_edit(f)
    
  def POST(self, rule_nr):
    f = rule_form()
    if f.validates():
      d = dict(id = rule_nr)
      db.update('rules', 'rowid=$id', d, **f.d)
      db.update('table_update_times', where='rowid=1', rules=datetime.now())
      raise web.seeother('/rules')
    else:
      return render.rule_edit(f)

class profiles:
  def GET(self):
    profiles = db.select('profiles', what='rowid,*')
    return render.profiles(profiles)

class profile_add:
  def GET(self):
    f = profile_form()
    return render.profile_add(f)
    
  def POST(self):
    f = profile_form()
    if f.validates():
      db.insert('profiles', **f.d)
      raise web.seeother('/profiles')
    else:
      return render.profile_add(f)

class rec:
  def GET(self):
    rec = db.select('recordings', what='rowid,*', order='program_start')
    return render.rec(rec)

app = web.application(urls, globals())

if __name__ == "__main__":
  app.run() 
else:
  application = app.wsgifunc()
