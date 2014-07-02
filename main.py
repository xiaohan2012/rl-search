#!/usr/bin/env python
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import torndb, redis
from tornado.options import define, options

import pickle

from session import RedisRecommendationSessionHandler
from engine import LinRelRecommender, QueryBasedRecommender

from base_handlers import BaseHandler
from data import kw2doc_matrix, KwDocData
from util import get_weights, iter_summary
from document import Document 

define("port", default=8000, help="run on the given port", type=int)
define("mysql_port", default=3306, help="db's port", type=int)
define("mysql_host", default="193.167.138.8", help="db database host")
define("mysql_user", default="hxiao", help="db database user")
define("mysql_password", default="xh24206688", help="db database password")
define("mysql_database", default="scinet3", help="db database name")
define("redis_port", default=6379, help="redis' port", type=int)
define("redis_host", default="ugluk", help="key-value cache host")
define("redis_db", default="scinet3", help="key-value db")

define("table", default='john', help="db table to be used")
define("refresh_pickle", default=False, help="refresh pickle or not")

define("recom_kw_num", default=5, help="recommended keyword number at each iter")
define("recom_doc_num", default=10, help="recommended document number at each iter")
define("samp_kw_num", default=5, help="sampled keyword number from documents")
define("samp_doc_num", default=5, help="extra document number apart from the recommended ones")

define("random_kw", default=True, help="Random keyword intialization or not")
define("random_doc", default=True, help="Random document intialization or not")

define("linrel_kw_mu", default=1, help="Value for \mu in the linrel algorithm for keyword")
define("linrel_kw_c", default=0.2, help="Value for c in the linrel algorithm for keyword")
define("linrel_doc_mu", default=1, help="Value for \mu in the linrel algorithm for document")
define("linrel_doc_c", default=0.2, help="Value for c in the linrel algorithm for document")

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
        self.kwdoc_data = kw2doc_matrix(table=options.table, keyword_field_name = 'keywords', refresh = options.refresh_pickle) 
    
class RecommandHandler(BaseHandler):        
    def _fill_kw_weight(self, kws, docs):
        """fill in documents' weight for each keyword"""        
        kw_idx = [self.kwdoc_data._kw_ind[kw['id']] for kw in kws] 
        doc_idx = [self.kwdoc_data._doc_ind[doc['id']] for doc in docs] 
        
        weights = get_weights(self.kwdoc_data._kw2doc_m, kw_idx, 
                              self.kwdoc_data._doc_ind_r, self.kwdoc_data._kw_ind_r, 
                              col_idx = doc_idx)        
        for kw in kws:
            kw_id = kw['id']
            kw['docs'] = weights[kw_id]
        
    def _fill_doc_weight(self, docs):
        """fill in keywords' weight for each document"""        
        doc_idx = [self.kwdoc_data._doc_ind[doc['id']] for doc in docs] 
        
        weights = get_weights(self.kwdoc_data._doc2kw_m, doc_idx, 
                              self.kwdoc_data._kw_ind_r, self.kwdoc_data._doc_ind_r, 
                              col_idx = None)#no keyword are passed
        
        for doc in docs:
            doc_id = doc['id']
            doc['kws'] = weights[doc_id]        

    def _get_doc(self, doc_id):
        sql_temp = 'SELECT id, title, keywords FROM %s WHERE id=%%s' %options.table
        row = self.db.get(sql_temp, doc_id)
        row['keywords'] = tornado.escape.json_decode(row['keywords'])
        return row

    def _get_docs(self, doc_ids):
        return [self._get_doc(doc_id) 
                for doc_id in doc_ids]

    def _get_kws(self, kw_ids):
        return [{'id': kw} 
                for kw in kw_ids]
        
    def post(self):
        try:
            data = tornado.escape.json_decode(self.request.body) 
        except:
            data = {}
        
        self.session_id = data.get('session_id', '')
        query = data.get('query', '')
        kw_fb = dict([(fb['id'], fb['score']) for fb in data.get('kw_fb', [])])
        doc_fb = dict([(fb['id'], fb['score']) for fb in data.get('doc_fb', [])])

        session = RedisRecommendationSessionHandler.get_session(self.redis, self.session_id)
        
        if not self.session_id:  #if no session id, start a new one
            print 'start a session..', session.session_id
            print 'Query: ', query
            engine = QueryBasedRecommender(self.db, options.table, 
                                           self.kwdoc_data._kw_ind, self.kwdoc_data._doc_ind, 
                                           self.kwdoc_data._kw2doc_m, self.kwdoc_data._doc2kw_m) 
            
            rec_docs = engine.recommend_documents(query, options.recom_doc_num)
            
            rec_kws = engine.recommend_keywords(rec_docs, options.recom_kw_num, options.samp_kw_num)

            extra_docs = engine.associated_documents_by_keywords([kw #only those extra keywords
                                                                   for kw in rec_kws 
                                                                   if not kw['recommended']], 
                                                                  options.samp_doc_num)
            rec_docs = rec_docs + extra_docs
            
        else:#else we are in a session
            print 'continue the session..', session.session_id
            if not kw_fb or not doc_fb:
                self.json_fail(ERR_INVALID_POST_DATA, 'Since you are in a session, please give the feedbacks for both keywords and documents')

            engine = LinRelRecommender(session, self.db, options.table,
                                       self.kwdoc_data._kw_ind, self.kwdoc_data._doc_ind, 
                                       self.kwdoc_data._kw2doc_m, self.kwdoc_data._doc2kw_m)
            
            rec_kws = engine.recommend_keywords(options.recom_kw_num, 
                                                   options.linrel_kw_mu, options.linrel_kw_c, 
                                                   feedbacks = kw_fb)
            
            rec_docs = engine.recommend_documents(options.recom_doc_num, 
                                                     options.linrel_doc_mu, options.linrel_doc_c, 
                                                     feedbacks = doc_fb)                

        #add the scores for kws
        print rec_kws
        for rec_kw in rec_kws: #they are displayed
            rec_kw['display'] = True

        #fill in the weights for both kws and docs
        self._fill_doc_weight(rec_docs)
        self._fill_kw_weight(rec_kws, rec_docs)
        
        #get associated keywords
        rec_kw_ids = [kw['id'] for kw in rec_kws]
        extra_kw_ids = set([kw_id
                        for doc in rec_docs
                        for kw_id in doc['keywords']
                        if kw_id not in rec_kw_ids])
        
        extra_kws = self._get_kws(extra_kw_ids)
        
        for kw in extra_kws:
            kw['display'] = False
            kw['score'] = 0
            
        self._fill_kw_weight(extra_kws, rec_docs)
        
        kw_dict = dict([(kw, kw) for kw in self.kwdoc_data._kw_ind.keys()])
        doc_dict = dict([(doc_id, Document(self._get_doc(doc_id))) for doc_id in self.kwdoc_data._doc_ind.keys()])

        #print the summary
        iter_summary(kw_dict = kw_dict,
                     doc_dict = doc_dict,
                     **session.data)
        
        print "Recommended documents:"
        for doc in rec_docs:
            print doc

        print "Recommended keywords:"
        for kw in rec_kw_ids:
            print kw,
        print 

        print 'extra_kw_ids:', extra_kw_ids
        self.json_ok({'session_id': session.session_id,
                      'kws': (rec_kws + extra_kws),
                      'docs': rec_docs})
                                
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
