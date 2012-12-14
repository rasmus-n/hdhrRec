#! /usr/bin/python

import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

import web
from web import form
from datetime import datetime
from ConfigParser import SafeConfigParser as ConfigParser
from os import fork, chdir, setsid, umask, getpid, close, dup2, O_RDWR
from os import open as os_open

cp = ConfigParser()
cp.read("/home/rn/src/hdhrRec/hdhrRec.ini")
db_path   =  cp.get("scheduler" , "db")
templates =  cp.get("http"      , "templates")
pid_file  =  cp.get("http"      , "pid")
del cp

render = web.template.render(templates, base='layout')
db = web.database(dbn='sqlite', db=db_path)

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

stream_form = form.Form (
  form.Textbox('name'     , description='Name'),
  form.Textbox('mux'      , description='Channel'),
  form.Textbox('pid'      , description='PID'),  
  form.Textbox('video'    , description='VID'),
  form.Textbox('audio'    , description='AID'),
  form.Textbox('subtitles', description='SID'),
)

urls = (
  '/'                       , 'start',
  '/streams'                , 'streams',
  '/streams/add'            , 'stream_add',
  '/streams/edit/([0-9]+)'  , 'stream_edit',
  '/streams/delete/([0-9]+)', 'stream_delete',
  '/rules'                  , 'rules',
  '/rules/add'              , 'rule_add',
  '/rules/edit/([0-9]+)'    , 'rule_edit',
  '/rules/delete/([0-9]+)'  , 'rule_delete',
  '/rec'                    , 'rec',
  '/rec/edit/([0-9]+)'      , 'rec_edit',
  '/profiles'               , 'profiles',
  '/profiles/add'           , 'profile_add',
  '/profiles/edit/([0-9]+)' , 'profile_edit',
  '/profiles/delete/([0-9]+)' , 'profile_delete',
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

class stream_add:
  def GET(self):
    f = stream_form()
    return render.stream_add(f)
    
  def POST(self):
    f = stream_form()
    if f.validates():
      db.insert('channels', **f.d)
      raise web.seeother('/streams')
    else:
      return render.stream_add(f)

class stream_edit:
  def GET(self, stream_nr):
    f = stream_form()
    d = dict(id = stream_nr);
    stream = db.select('channels', d, where='rowid = $id', what='rowid,*')
    f.fill(stream[0])
    return render.stream_edit(f, stream_nr)
    
  def POST(self, stream_nr):
    f = stream_form()
    if f.validates():
      d = dict(id = stream_nr)
      db.update('channels', 'rowid=$id', d, **f.d)
      raise web.seeother('/streams')
    else:
      return render.stream_edit(f)

class stream_delete:
  def POST(self, stream_nr):
    f = stream_form()
    if f.validates():
      d = dict(id = stream_nr)
      db.delete('channels', 'rowid=$id', vars=d)
      raise web.seeother('/streams')
    else:
      return render.stream_edit(f)

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
    return render.rule_edit(f, rule_nr)
    
  def POST(self, rule_nr):
    f = rule_form()
    if f.validates():
      d = dict(id = rule_nr)
      db.update('rules', 'rowid=$id', d, **f.d)
      db.update('table_update_times', where='rowid=1', rules=datetime.now())
      raise web.seeother('/rules')
    else:
      return render.rule_edit(f)

class rule_delete:
  def POST(self, rule_nr):
    f = rule_form()
    if f.validates():
      d = dict(id = rule_nr)
      db.delete('rules', 'rowid=$id', vars=d)
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

class profile_edit:
  def GET(self, profile_nr):
    f = profile_form()
    d = dict(id = profile_nr);
    profile = db.select('profiles', d, where='rowid = $id', what='rowid,*')
    f.fill(profile[0])
    return render.profile_edit(f, profile_nr)
    
  def POST(self, profile_nr):
    f = profile_form()
    if f.validates():
      d = dict(id = profile_nr)
      db.update('profiles', 'rowid=$id', d, **f.d)
      raise web.seeother('/profiles')
    else:
      return render.profile_edit(f)

class profile_delete:
  def POST(self, profile_nr):
    f = profile_form()
    if f.validates():
      d = dict(id = profile_nr)
      db.delete('profiles', 'rowid=$id', vars=d)
      raise web.seeother('/profiles')
    else:
      return render.profile_edit(f)

class rec:
  def GET(self):
    rec = db.select('recordings', what='rowid,*', order='program_start')
    return render.rec(rec)

class rec_edit:
  def GET(self, rec_nr):
    raise web.seeother('/rec')
    
app = web.application(urls, globals())

if __name__ == "__main__":
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
    
  pf = open(pid_file, "w")
  pf.write(str(getpid()))
  pf.close()
  del pf
  app.run() 
else:
  application = app.wsgifunc()
