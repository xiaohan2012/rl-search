import json
import numpy as np
from pprint import pprint
from cPickle import load
from copy import copy

class Document(dict):
    __all_docs_by_id = {}
    all_docs = []

    db_conn = None
    table = None
            
    @classmethod
    def config(cls, conn, table, **kwargs):
        cls.db_conn = conn
        cls.table = table

        for key, value in kwargs.items():
            setattr(cls, key, value)
            
    @classmethod
    def prepare_doc(cls, doc_dict):
        doc = Document(doc_dict)
        
        #if keywords are not parsed,  parse it
        if not isinstance(doc['keywords'], list):
            kw_strs = json.loads(doc['keywords'])
            kws = [Keyword.get(kw_str) for kw_str in kw_strs]
            doc['keywords'] = kws

        #mutual binding
        for kw in doc['keywords']: kw.add_assoc_doc(doc)

        return doc
        
    @classmethod
    def load_all_from_db(cls):
        rows = cls.db_conn.query("SELECT * from %s" %(cls.table))
        for row in rows:
            doc = cls.prepare_doc(row)
            #save it in the global dictionary
            cls.__all_docs_by_id[doc['id']] = doc
            cls.all_docs.append(doc)

        return cls.__all_docs_by_id.values()
        
    @classmethod
    def get(cls, doc_id):
        if cls.__all_docs_by_id.has_key(doc_id):
            return cls.__all_docs_by_id[doc_id]
        else:
            row = cls.db_conn.get("SELECT * from %s where id=%d" %(cls.table, doc_id))
            doc = cls.prepare_doc(row)
            cls.__all_docs_by_id[doc_id] = doc
            return doc

    @property
    def _kw_weight(self):
        """
        return (keyword_str -> weight) dictionary
        """
        if self.__kw_weight is None:
            
            cls = self.__class__
            
            feature_vec = cls.doc2kw_m[cls.doc_ind[self.id],:]
            _, kw_idx = np.nonzero(feature_vec)
            
            kws = [cls.kw_ind_r[ind] for ind in kw_idx]
            
            weights = feature_vec[0, kw_idx].toarray().flatten()
            self.__kw_weight = dict([(Keyword.get(kw_str),weight) 
                                     for kw_str,weight in zip(kws, weights) ])

        return self.__kw_weight

    @property
    def dict(self):
        attrs = [a for a in self.keys() if not a.startswith('_')]
        return dict([(a, self[a]) for a in attrs])

    def fb(self, session):
        return session.doc_feedbacks.get(self.id, 0)
        
    def fb_from_kws(self, session):
        """
        feedbacks from keywords
        return the weighted sum of keyword feedbacks
        """
        kw_w_dict = self._kw_weight
        weight_sum = sum(kw_w_dict.values())
        return sum([kw.fb(session) * kw_w_dict[kw] for kw in self.keywords]) / weight_sum

    def __init__(self, *args, **kwargs):
        super(Document, self).__init__(*args, **kwargs)
        self.__dict__ = self #propagate the json data to attributes

        self.__original_keys = self.keys() #original dictionary keys/data fields

        self.__kw_weight = None
    
    def __repr__(self):
        return '%d. "%s" (%s)' %(self['id'], self['title'], 
                             ', '.join(["%d, %s" %(ind+1, repr(kw)) 
                                        for ind, kw in enumerate(self['keywords'])]))

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return (self.id) == (other.id)

class Keyword(dict):
    __all_kws_by_id = {}
    all_kws = []
    
    @classmethod
    def config(cls, **kwargs):
        for key, value in kwargs.items():
            setattr(cls, key, value)
    
    @classmethod
    def get(cls, kw_str):
        #if created, return
        #else, create it
        if cls.__all_kws_by_id.has_key(kw_str):
            return cls.__all_kws_by_id[kw_str]
        else:
            kw = Keyword(kw_str)
            cls.__all_kws_by_id[kw_str] = kw

            cls.all_kws.append(kw)

            return kw

    @property
    def id(self):
        return self.__str

    @property
    def _doc_weight(self):
        """
        return (doc -> weight) dictionary
        """
        if self.__doc_weight is None:
            
            cls = self.__class__
            
            feature_vec = cls.kw2doc_m[cls.kw_ind[self.__str],:]
            _, doc_idx = np.nonzero(feature_vec)

            doc_ids, weights = ([cls.doc_ind_r[ind] for ind in doc_idx], 
                                feature_vec[0, doc_idx].toarray().flatten())
            self.__doc_weight = dict([(Document.get(doc_id),weight) 
                                      for doc_id,weight in zip(doc_ids, weights) ])

        return self.__doc_weight

    @property
    def dict(self):
        attrs = [a for a in self.keys() if not a.startswith('_')]
        return dict([(a, self[a]) for a in attrs])
    
    def fb(self, session):
        return session.kw_feedbacks.get(self.id, 0)

    def fb_from_docs(self, session):
        doc_w_dict = self._doc_weight
        weight_sum = sum(doc_w_dict.values())
        return sum([doc.fb(session) * doc_w_dict[doc] for doc in self.docs]) / weight_sum


    def __init__(self, kw_str):
        super(Keyword, self).__init__()
        self['id'] = kw_str
        self.__str = kw_str
        
        self.docs = []

        self.__doc_weight = None
        
    def add_assoc_doc(self, doc):
        self.docs.append(doc)

    def __repr__(self):
        return "%s: %s" %(self.__class__.__name__, self.__str)

    def __hash__(self):
        return hash(self.__str)

    def __eq__(self, other):
        return (self.__str) == (other.__str)

def config(conn, table, matrices_and_indices):
    #config the database and session stuff
    Document.config(conn, table, **matrices_and_indices)
    Keyword.config(**matrices_and_indices)

def test():    
    db = 'archive'
    table = 'archive_500'
    
    import torndb
    conn = torndb.Connection("%s:%s" % ('ugluk', 3306), db, 'hxiao', 'xh24206688')

    from data import kw2doc_matrix
    matrices_and_indices = kw2doc_matrix(db, table, keyword_field_name = 'keywords').__dict__

    config(conn, table, matrices_and_indices)

    #prepare the session
    from session import RedisRecommendationSessionHandler
    import redis
    redis_db="archive"
    redis_conn = redis.StrictRedis(host='ugluk', port=6379, db=redis_db)
    session = RedisRecommendationSessionHandler.get_session(redis_conn)
    
    #load the documents 
    docs = Document.load_all_from_db()
    session.doc_feedbacks = {1: .2}
    session.kw_feedbacks = {'pebble game': .2, 'graphs': .5}
    
    doc = Document.get(1)
    print doc
    print doc.fb(session)
    print doc.fb_from_kws(session)
    
    pprint(docs[0].keywords)
    pprint(docs[0].keywords[0].docs)

    kw = Keyword.get('algorithms')
    print kw
    print kw.docs
    print kw.fb(session)
    print kw.fb_from_docs(session)
    

    
if __name__ == "__main__":
    test()
