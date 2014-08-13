#######################
# The model used in this app:
# 1. Document
# 2. Keyword
# in included here

#######################
__all__ = ["Document", "Keyword", "config_model"]

import json
import numpy as np
from pprint import pprint
from cPickle import load
from copy import copy

from scipy import linalg, mat, dot

from data import FeatureMatrixAndIndexMapping as fmim
from fb_receiver import KeywordFeedbackReceiver, DocumentFeedbackReceiver

class Document(DocumentFeedbackReceiver, dict):
    __all_docs_by_id = {}
    
    all_docs = []
    db_conn = None
    table = None
    
    #whether all documents are loaded or not
    all_docs_loaded = False
    
    @classmethod
    def config(cls, conn, table, **kwargs):
        """
        kwargs should be 
        """
        cls.db_conn = conn
        cls.table = table

        for key, value in kwargs.items():
            setattr(cls, key, value)
    
    @classmethod
    def __ensure_configured(cls):
        assert cls.db_conn is not None, "database connection should not None"
        assert cls.table is not None,  "table should not None"

        for field in fmim.DICT_FIELDS:
            assert getattr(cls, field) is not None, "%s should be not None" %field
        
    @classmethod
    def prepare_doc(cls, doc_dict):
        doc = Document(doc_dict)
        
        #if keywords are not parsed,  parse it
        if not isinstance(doc['keywords'], list):
            kw_strs = json.loads(doc['keywords'])
            kws = [Keyword.get(kw_str) for kw_str in kw_strs]
            doc['keywords'] = kws

        #mutual binding for keywords
        for kw in doc['keywords']: 
            if doc not in kw.docs:
                kw.add_assoc_doc(doc)

        #set dict keys as attributes
        for key, value in doc.items():
            setattr(doc, key, value)

        return doc
        
    @classmethod
    def load_all_from_db(cls):
        cls.__ensure_configured()
        
        rows = cls.db_conn.query("SELECT * from %s" %(cls.table))
        for row in rows:
            doc = cls.prepare_doc(row)
            #save it in the global dictionary
            cls.__all_docs_by_id[doc['id']] = doc
            cls.all_docs.append(doc)

        cls.all_docs_loaded = True

        return cls.__all_docs_by_id.values()
        
    @classmethod
    def get(cls, doc_id):
        if cls.__all_docs_by_id.has_key(doc_id):
            return cls.__all_docs_by_id[doc_id]
        else:
            cls.__ensure_configured()
            
            row = cls.db_conn.get("SELECT * from %s where id=%d" %(cls.table, doc_id))
            doc = cls.prepare_doc(row)
            cls.__all_docs_by_id[doc_id] = doc
            return doc

    @classmethod
    def get_many(cls, ids):
        """
        get multiple documents by id
        """
        return [cls.get(_id)
                for _id in ids]

    @property
    def vec(self):
        """ feature vector of the document """
        if not hasattr(self, "_vec"):
            cls = self.__class__
            self._vec = cls.doc2kw_m[cls.doc_ind[self.id],:]
        return self._vec

    def similarity_to(self, other, metric="cosine"):
        assert type(other) is Document, "`other` should be Document, but is %r" %(other)
        
        vec1, vec2 = mat(self.vec.todense()), mat(other.vec.todense())
        if metric == "cosine":
            return (dot(vec1,vec2.T)/linalg.norm(vec1)/linalg.norm(vec2)).tolist()[0][0]
        else:
            raise NotImplementedError("Only cosine distance metric is implemented for now")
    
    @property
    def _kw_weight(self):
        """
        return (Keyword -> weight) dictionary
        """
        self.__ensure_configured()
        
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
        """
        Feedback received along the way
        """
        return session.doc_feedbacks.get(self, 0)
        
    def fb_from_kws(self, session):
        """
        feedbacks from keywords
        return the weighted sum of keyword feedbacks
        """
        kw_w_dict = self._kw_weight
        weight_sum = sum(kw_w_dict.values())
        
        return sum([kw.fb(session) * kw_w_dict[kw] 
                    for kw in self.keywords]) \
                / weight_sum
    
    def __init__(self, *args, **kwargs):                
        self.__dict__ = self #propagate the json data to attributes

        self.__original_keys = self.keys() #original dictionary keys/data fields

        self.__kw_weight = None
    
        super(Document, self).__init__(*args, **kwargs)
    
    def __repr__(self):
        return '%d: (%s)' %(self['id'], 
                            ', '.join(["%s" %(kw.id) 
                                       for kw in self['keywords']]))

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return (self.id) == (other.id)

class Keyword(KeywordFeedbackReceiver, dict):
    __all_kws_by_id = {}
    all_kws = []
    
    @classmethod
    def config(cls, **kwargs):
        for key, value in kwargs.items():
            setattr(cls, key, value)

    @classmethod
    def __ensure_configured(cls):
        for field in fmim.DICT_FIELDS:
            assert getattr(cls, field) is not None, "%s should be not None" %field
    
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

    @classmethod
    def get_many(cls, ids):
        """
        get multiple keywords by id
        """
        return [cls.get(_id)
                for _id in ids]

    @property
    def id(self):    
        return self['id']

    @property
    def _doc_weight(self):
        """
        return (doc -> weight) dictionary
        """
        self.__class__.__ensure_configured()

        if self.__doc_weight is None:
            
            cls = self.__class__
            
            feature_vec = cls.kw2doc_m[cls.kw_ind[self.id],:]
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

    @property
    def vec(self):
        """ feature vector of the keyword """
        if not hasattr(self, "_vec"):
            cls = self.__class__
            self._vec = cls.kw2doc_m[cls.kw_ind[self.id],:]
        return self._vec

    def similarity_to(self, other, metric="cosine"):
        assert type(other) is Keyword, "`other` should be Keyword, but is %r" %(other)
        
        vec1, vec2 = mat(self.vec.todense()), mat(other.vec.todense())
        if metric == "cosine":
            return (dot(vec1,vec2.T)/linalg.norm(vec1)/linalg.norm(vec2)).tolist()[0][0]
        else:
            raise NotImplementedError("Only cosine distance metric is implemented for now")

    def fb(self, session):
        """
        Feedback received along the way
        """
        return session.kw_feedbacks.get(self, 0)
        
    def add_assoc_doc(self, doc):
        self.docs.append(doc)
        
    def __init__(self, kw_str):
        self['id'] = kw_str
        
        self.docs = []

        self.__doc_weight = None
        
        super(Keyword, self).__init__()
        
    def __repr__(self):
        return self["id"]

    def __hash__(self):
        return hash(self['id'])

    def __eq__(self, other):
        return (self['id']) == (other['id'])

def config_model(conn, table, matrices_and_indices, doc_alpha, kw_alpha):
    """
    config
    1. the database connetion
    2. session 
    3. weight(\alpha) in feedback propagation 
    """
    print "configuring model..."
    Document.config(conn, table, **matrices_and_indices)
    Document.set_alpha(doc_alpha)
    
    Keyword.config(**matrices_and_indices)
    Keyword.set_alpha(kw_alpha)
    
def test():    
    # db = 'archive'
    # table = 'archive_500'
    
    # import torndb
    # conn = torndb.Connection("%s:%s" % ('ugluk', 3306), db, 'hxiao', 'xh24206688')

    # from data import kw2doc_matrix
    # matrices_and_indices = kw2doc_matrix(conn, table, keyword_field_name = 'keywords').__dict__

    # config(conn, table, matrices_and_indices, 0.7, 0.7)

    # #prepare the session
    # from session import RedisRecommendationSessionHandler
    # import redis
    # redis_db="archive"
    # redis_conn = redis.StrictRedis(host='ugluk', port=6379, db=redis_db)
    # session = RedisRecommendationSessionHandler.get_session(redis_conn)
    
    # #load the documents 
    # docs = Document.load_all_from_db()
    # session.doc_feedbacks = {1: .2}
    # session.kw_feedbacks = {'pebble game': .2, 'graphs': .5}
    
    # doc = Document.get(1)
    # print doc
    # print doc.fb(session)
    # print doc.fb_from_kws(session)
    
    # pprint(docs[0].keywords)
    # pprint(docs[0].keywords[0].docs)

    # kw = Keyword.get('algorithms')
    # print kw
    # print kw.docs
    # print kw.fb(session)
    # print kw.fb_from_docs(session)
    pass
    

    
if __name__ == "__main__":
    test()
