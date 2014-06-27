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
from data import kw2doc_matrix, test_matrix

random.seed(123456)

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
        self.linrel_dict = kw2doc_matrix(table=options.table, keyword_field_name = 'keywords', refresh = options.refresh_pickle) 
    
class RecommandHandler(BaseHandler):
        
    def _get_weights(self, M, row_idx, col_ind2id_map, row_ind2id_map, col_idx = None):
        """
        Generic function that gets the weights for docs/kws associated with kws/docs
        
        Params:
        M: data matrix, each row for each object
        row_idx: the matrix row indices to be considered
        col_ind2id_map: map from matrix **column** index to object id
        row_ind2id_map: map from matrix **row** index to object id
        col_idx(optional): the matrix column indices(features) to be considered

        Return:
        {'row_obj_id': [{'id': 'col_obj_id', 'w': 'weight value in M'}, ...], ...}
        """
        if col_idx is None:
            submatrix = M[row_idx, :]
        else:
            submatrix = M[row_idx, col_idx]
            
        data = {}
        for i, row_ind in enumerate(row_idx):
            row = submatrix[i, :]
            if col_idx is None:
                _, nonzero_col_idx = np.nonzero(row[0,:])
                
            else:
                _, nonzero_col_idx = np.nonzero(row[0,col_idx]) #nonzero_col_idx in col_idx 
                nonzero_col_idx = np.array(col_idx)[nonzero_col_idx]#make it an array for faster and more convenient slicing
            
            weights = row[0, nonzero_col_idx]
            
            #map index to col object id
            col_ids = [col_ind2id_map[col_ind] for col_ind in nonzero_col_idx]
            
            #get the matrix value
            value = [{'id': col_id, 'w': weight} 
                     for col_id, weight in zip(col_ids, weights)]
                        
            data[row_ind2id_map[row_ind]] = value
        return data

    def _fill_kw_weight(self, kws, docs):
        """fill in documents' weight for each keyword"""
        kw_idx = [self.kw_ind[kw['id']] for kw in kws] 
        doc_idx = [self.doc_ind[doc['id']] for doc in docs] 
        
        weights = self._get_weights(self.kw2doc_m, kw_idx, self.doc_ind_r, self.kw_ind_r, 
                                   col_idx = doc_idx)        
        for kw in kws:
            kw_id = kw['id']
            kws['docs'] = weights[kw_id]
        
    def _fill_doc_weight(self, docs):
        doc_idx = [self.doc_ind[doc['id']] for doc in docs] 
        
        weights = self._get_weights(self.doc2kw_m, doc_idx, self.kw_ind_r, self.doc_ind_r, 
                                   col_idx = None)#no keyword are passed
        
        for doc in docs:
            doc_id = doc['id']
            docs['kws'] = weights[doc_id]        

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
        query = data.get('feedback', '')
        kw_fb = dict([(fb['id'], fb['score']) for fb in data.get('kw_fb', [])])
        doc_fb = dict([(fb['id'], fb['score']) for fb in data.get('doc_fb', [])])

        session = RedisRecommendationSessionHandler.get_session(self.redis, self.session_id)
        
        if not self.session_id:  #if no session id, start a new one
            print 'start a session..'
            
            engine = QueryBasedRecommender()    
            
            rec_doc_ids = engine.recommend_documents(query)
            
            rec_kw_ids = engine.recommend_keywords(rec_docs)
            
        else:#else we are in a session
            if not kw_fb or not doc_fb:
                self.json_fail(ERR_INVALID_POST_DATA, 'Since you are in a session, please give the feedbacks for both keywords and documents')

            engine = LinRelRecommender(session)
            rec_kw_ids = engine.recommend_keywords(options.recom_kw_num, 
                                                   options.linrel_kw_mu, options.linrel_kw_c, 
                                                   feedbacks = kw_fb)
            rec_doc_ids = engine.recommend_documents(options.recom_doc_num, 
                                                     options.linrel_doc_mu, options.linrel_doc_c, 
                                                     feedbacks = doc_fb)
                
        #start get the actual content for both keywords and documents
        rec_docs = self._get_docs(rec_doc_ids)
        self._fill_doc_weight(doc_kws)
                                
        rec_kws = self._get_kws(rec_kw_ids)
        
        for rec_kw in rec_kws: #they are displayed
            rec_kw['display'] = True
                
        self._fill_kw_weight(rec_kws, rec_docs)
            
        #for keywords associated with documents
        assoc_kw_ids = [kw_id
                        for doc in rec_docs 
                        for  kw_id in doc['keywords'] 
                        if kw_id not in rec_kw_ids]
        
        assoc_kws = [{'id': kw} 
                     for kw in assoc_kw_ids]
        
        self._fill_kw_weight(assoc_kws)
        
        #update the session       
        #we need to do it manually
        #as QueryBasedRecommender does not provide it
        session.kw_ids = (rec_kw_ids + assoc_kw_ids) #update session 
        session.doc_ids = (rec_doc_ids) #update session 
    
        self.json_ok({'session_id': self.session_id,
                      'kws': rec_kws + assoc_kws, 
                      'docs': docs})
                                
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
