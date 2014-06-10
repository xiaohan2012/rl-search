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
import pickle


import numpy as np
from numpy import matrix,eye

from base_handlers import BaseHandler
from data import kw2doc_matrix, test_matrix

define("port", default=8000, help="run on the given port", type=int)
define("mysql_port", default=3306, help="db's port", type=int)
define("mysql_host", default="193.167.138.8", help="db database host")
define("mysql_user", default="hxiao", help="db database user")
define("mysql_password", default="xh24206688", help="db database password")
define("mysql_database", default="scinet3", help="db database name")
define("redis_port", default=6379, help="redis' port", type=int)
define("redis_host", default="127.0.0.1", help="key-value cache host")
define("redis_db", default="scinet3", help="key-value db")

ERR_INVALID_POST_DATA = 1001

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
            xsrf_cookies = False,
            debug = True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = torndb.Connection("%s:%s" % (options.mysql_host, options.mysql_port), options.mysql_database, options.mysql_user, options.mysql_password)
        self.redis = redis.StrictRedis(host=options.redis_host, port=options.redis_port, db=options.redis_db)
        self.linrel_dict = test_matrix() #kw2doc_matrix()
    
class RecommandHandler(BaseHandler):
    
    def generate_session_id(self):
        return str(uuid.uuid1())
        
    @property
    def session_doc_ids(self):
        return pickle.loads(self.redis.get('session:%s:doc_ids' %self.session_id))

    @session_doc_ids.setter
    def session_doc_ids(self, doc_ids):
        self.redis.set('session:%s:doc_ids' %self.session_id, pickle.dumps(doc_ids))

    @property
    def session_kw_ids(self):
        return pickle.loads(self.redis.get('session:%s:kw_ids' %self.session_id))

    @session_kw_ids.setter
    def session_kw_ids(self, kw_ids):
        self.redis.set('session:%s:kw_ids' %self.session_id, pickle.dumps(kw_ids))

    @property
    def kw_fb_hist(self):
        """keyword feedback history"""
        #we use pickle to avoid the int-string problem
        #descriped in http://stackoverflow.com/questions/1450957/pythons-json-module-converts-int-dictionary-keys-to-strings
        res = self.redis.get('session:%s:kw_fb_hist' %self.session_id)
        if not res:
            return {}
        else:
            return pickle.loads(res)

    @kw_fb_hist.setter
    def kw_fb_hist(self, value):
        """keyword feedback history"""
        self.redis.set('session:%s:kw_fb_hist' %self.session_id, pickle.dumps(value))

    @property
    def doc_fb_hist(self):
        """document feedback history"""
        res = self.redis.get('session:%s:doc_fb_hist' %self.session_id)
        if not res:
            return {}
        else:
            return pickle.loads(res)

    @doc_fb_hist.setter
    def doc_fb_hist(self, value):
        """document feedback history"""
        self.redis.set('session:%s:doc_fb_hist' %self.session_id, pickle.dumps(value))

    @property
    def kw2doc_m(self):
        return self.application.linrel_dict['kw2doc_m']

    @property
    def doc2kw_m(self):
        return self.application.linrel_dict['doc2kw_m']

    @property
    def kw_ind(self):
        return self.application.linrel_dict['kw_ind']

    @property
    def kw_ind_r(self):        
        return dict([(ind, kw ) for kw, ind in self.application.linrel_dict['kw_ind'].items()])

    @property
    def doc_ind_r(self):
        return dict([(ind, doc_id ) for doc_id, ind in self.application.linrel_dict['doc_ind'].items()])

        
    @property
    def doc_ind(self):
        return self.application.linrel_dict['doc_ind']
        
    def get_init_kws(self, **kwargs):
        """
        generate some initial keywords 
        """
        return [{'id': 'python'}, 
                {'id': 'database'}]

    def get_init_docs(self, **kwargs):
        """
        generate some initial documents 
        """
        return [{'id': 1, 'title': 'key-value storage database', 'author': 'unknown', 'keywords': ['database', 'key-value', 'in-memory']},
                {'id': 2, 'title': 'Asynchronous Python Web framework', 'author': 'unknown', 'keywords': ['python', 'web', 'framework']}]

    def post(self):
        try:
            data = tornado.escape.json_decode(self.request.body) 
        except:
            data = {}
        
        self.session_id = data.get('session_id', '')
        kw_fb = dict([(fb['id'], fb['score']) for fb in data.get('kw_fb', [])])
        doc_fb = dict([(fb['id'], fb['score']) for fb in data.get('doc_fb', [])])

        if not self.session_id:         #if no session id, render index page
            print 'start a session..'
            self.session_id = self.generate_session_id()

            #generate some kws and documents
            keywords = self.get_init_kws()
            documents = self.get_init_docs()

            #save it to database
            self.session_doc_ids =  [doc['id'] for doc in documents]
            self.session_kw_ids = [kw['id'] for kw in keywords]

            self.json_ok({'session_id': self.session_id,
                          'keywords': keywords, 
                          'documents': documents})

        else:#else we are in a session
            #continue a session
            #try to get the feedbacks
            print self.kw_ind
            if not kw_fb or not doc_fb:
                self.json_fail(ERR_INVALID_POST_DATA, 'Since you are in a session, please the feedbacks for both keywords and documents')
            else:
                #get the K_t(kw2doc) and D_t(doc2kw) matrix
                kw_idx_in_K = [self.kw_ind[kw_id] for kw_id in self.session_kw_ids]
                K_t = self.kw2doc_m[kw_idx_in_K, :]
                doc_idx_in_K = [self.doc_ind[doc_id] for doc_id in self.session_doc_ids]
                D_t = self.doc2kw_m[doc_idx_in_K, :] 
                
                #relevance feedback for kw and doc
                #and incrementally save the feedback back to db
                kw_fb_hist = self.kw_fb_hist
                kw_fb_hist.update(kw_fb)
                self.kw_fb_hist = kw_fb_hist
                
                y_kt = matrix([self.kw_fb_hist[kw_id] for kw_id in self.session_kw_ids]).T

                doc_fb_hist = self.doc_fb_hist
                doc_fb_hist.update(doc_fb)
                self.doc_fb_hist = doc_fb_hist
                y_dt = matrix([self.doc_fb_hist[doc_id] for doc_id in self.session_doc_ids]).T

                print "kw ids: %s" %(repr(self.session_kw_ids))
                print "doc ids: %s" %(repr(self.session_doc_ids))

                print "K_t: %s" %(repr(K_t))
                print "D_t: %s" %(repr(D_t))
                
                print "y_kt: %s" %(repr(y_kt))
                print "y_dt: %s" %(repr(y_dt))
                
                kw_n, doc_n = self.kw2doc_m.shape
                mu = 1; c = 0.2
                KW_RECOMMEND_N = 2; DOC_RECOMMEND_N = 4
                
                #for each keyword i, do a_i = k_i*(K' * K + \mu * I)^{-1} * K'
                a_kt = self.kw2doc_m * (K_t.T * K_t + mu * eye(doc_n, doc_n)).I * K_t.T
                
                kw_scores = a_kt * y_kt + np.sqrt(np.sum(np.power(a_kt, 2), 1)) * c / 2
                kw_scores = sorted(enumerate(np.array(kw_scores.T).tolist()[0]), key = lambda (kw_id, score): score, reverse = True)
                
                print "kw_scores: %s"  %repr([(self.kw_ind_r[ind], score) for ind,score in kw_scores])
                
                #for each document i, do a_i = d_i * (D' * D + \mu * I)^{-1} * D'
                a_dt = self.doc2kw_m * (D_t.T * D_t + mu * eye(kw_n, kw_n)).I * D_t.T
                
                doc_scores = a_dt * y_dt + np.sqrt(np.sum(np.power(a_dt, 2), 1)) * c / 2
                doc_scores = sorted(enumerate(np.array(doc_scores.T).tolist()[0]), key = lambda (doc_id, score): score, reverse = True)
                
                print "doc_scores: %s"  %repr([(self.doc_ind_r[ind], score) for ind,score in doc_scores])
                
                #do the linrel to get the recommandations,
                #select the top n for keywords and documents respectively                
                self.json_ok({'session_id': self.session_id,
                              'kw_ids': [{'id': self.kw_ind_r[ind], 'score': score} for ind, score in  kw_scores[:KW_RECOMMEND_N]],
                              'doc_ids': [{'id': self.doc_ind_r[ind], 'score': score} for ind, score in  doc_scores[:DOC_RECOMMEND_N]]})
                
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
