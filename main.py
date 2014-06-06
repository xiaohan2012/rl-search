#!/usr/bin/env python
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import torndb, redis
from tornado.options import define, options

import uuid

from base_handlers import BaseHandler
from data import kw2doc_matrix

define("port", default=8000, help="run on the given port", type=int)
define("mysql_port", default=3306, help="db's port", type=int)
define("mysql_host", default="127.0.0.1", help="db database host")
define("mysql_user", default="hxiao", help="db database user")
define("mysql_password", default="xh24206688", help="db database password")
define("mysql_database", default="scinet3", help="db database name")
define("redis_port", default=6379, help="redis' port", type=int)
define("redis_host", default="127.0.0.1", help="key-value cache host")
define("redis_db", default="scinet3", help="key-value db")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/api/1.0/recommend",RecommandHandler)
        ]
        settings = dict(
            cookie_secret = "Put in your secret cookie here! (using the generator)",
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies = True,
            debug = True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = torndb.Connection("%s:%s" % (options.mysql_host, options.mysql_port), options.mysql_database, options.mysql_user, options.mysql_password)
        self.redis = redis.StrictRedis(host=options.redis_host, port=options.redis_port, db=options.redis_db)
        self.linrel_dict = kw2doc_matrix()
    
class RecommandHandler(BaseHandler):
    def get(self):
        session_id = self.get_argument('session_id', None)
        if not session_id:         #if no session id, render index page
            session_id = self.generate_session_id()
            keywords = [{'id': 1, 'name':'redis'}, 
                        {'id': 2, 'name':'tornado'}]
            documents = [{'id': 1, 'title': 'key-value storage database', 'author': 'unknown', 'keywords': ['database', 'key-value', 'in-memory']},
                         {'id': 2, 'title': 'Asynchronous Python Web framework', 'author': 'unknown', 'keywords': ['python', 'web', 'framework']}
                     ]
            self.redis.set('session:%s:doc_ids' %session_id, [doc['id'] for doc in documents])
            self.redis.set('session:%s:kw_ids' %session_id, [kw['id'] for kw in keywords])

            #save it to database
            self.json_ok({'session_id': session_id,
                          'keywords': keywords, 
                          'documents': documents})
        else:#else we are in a session            
            #get the user session data from redis
            doc_ids = self.redis.get('session:%s:doc_ids' %session_id)
            kw_ids = self.redis.get('session:%s:kw_ids' %session_id)
            
            #do the linrel to get the recommandations
            self.json_ok({'session_id': session_id,
                          'doc_ids': doc_ids, 
                          'kw_ids': kw_ids})

            

    def generate_session_id(self):
        return str(uuid.uuid1())

class MainHandler(BaseHandler):
    def get(self):
        self.render("index.html")
            

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.autoreload.add_reload_hook(main)
    tornado.autoreload.start()
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
