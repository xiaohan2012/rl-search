import pickle
import uuid
from collections import defaultdict
from types import IntType, StringType, DictType

from scinet3.model import Document, Keyword
from scinet3.redis_util import (isnumber, dict2right_type)

class RecommendationSessionHandler(object):
    @property
    def doc_ids(self):
        raise NotImplemented        

    @doc_ids.setter
    def doc_ids(self, doc_ids):
        raise NotImplemented        

    @property
    def kw_ids(self):
        raise NotImplemented        

    @kw_ids.setter
    def kw_ids(self, kw_ids):
        raise NotImplemented        

    @property
    def kw_feedbacks(self):
        raise NotImplemented        

    @kw_feedbacks.setter
    def kw_feedbacks(self, value):
        raise NotImplemented

    @property
    def doc_feedbacks(self):
        raise NotImplemented

    @doc_feedbacks.setter
    def doc_feedbacks(self, value):
        raise NotImplemented
    
class RedisRecommendationSessionHandler(RecommendationSessionHandler):
    def __init__(self, conn, session_id):
        """
        if session_id is not given or empty string, generate a new session id
        """
        self.redis = conn;
        if not session_id or len(session_id) == 0:
            print 'session_id is None'
            self.session_id = self.generate_session_id()
        else:
            self.session_id = session_id
        
    def generate_session_id(self):
        return str(uuid.uuid1())
    
    @property
    def data(self):
        return {
            'kw_score_hist': self.kw_score_hist,
            'kw_explr_score_hist': self.kw_explr_score_hist,
            'kw_explt_score_hist': self.kw_explt_score_hist,
            'kw_fb_hist': self.kw_fb_hist,
            'doc_score_hist': self.doc_score_hist,
            'doc_explr_score_hist': self.doc_explr_score_hist,
            'doc_explt_score_hist': self.doc_explt_score_hist,
            'doc_fb_hist': self.doc_fb_hist
        }
        
    @classmethod
    def get_session(cls, conn, session_id=None):
        #factory method, return the session
        return cls(conn, session_id)    
        
    ###################################
    #The following long list of function
    #tracks the exploration/exploitation 
    #history involved for the entire session
    ###################################
    @property
    def kw_score_hist(self):
        return self._dict_list_getter('kw_score_hist')

    @kw_score_hist.setter
    def kw_score_hist(self, val):
        self._dict_list_setter('kw_score_hist', val)

    @property
    def kw_explt_score_hist(self):
        return self._dict_list_getter('kw_explt_score_hist')

    @kw_explt_score_hist.setter
    def kw_explt_score_hist(self, val):
        self._dict_list_setter('kw_explt_score_hist', val)

    @property
    def kw_explr_score_hist(self):
        return self._dict_list_getter('kw_explr_score_hist')

    @kw_explr_score_hist.setter
    def kw_explr_score_hist(self, val):
        self._dict_list_setter('kw_explr_score_hist', val)

    @property
    def doc_score_hist(self):
        return self._dict_list_getter('doc_score_hist')

    @doc_score_hist.setter
    def doc_score_hist(self, val):
        self._dict_list_setter('doc_score_hist', val)

    @property
    def doc_explt_score_hist(self):
        return self._dict_list_getter('doc_explt_score_hist')

    @doc_explt_score_hist.setter
    def doc_explt_score_hist(self, val):
        self._dict_list_setter('doc_explt_score_hist', val)

    @property
    def doc_explr_score_hist(self):
        return self._dict_list_getter('doc_explr_score_hist')

    @doc_explr_score_hist.setter
    def doc_explr_score_hist(self, val):
        self._dict_list_setter('doc_explr_score_hist', val)

    ###############################
    #docs/kws that are involve in the LinRel computation
    ###############################
    @property
    def doc_ids(self):
        val = self.redis.get('session:%s:doc_ids' %self.session_id)
        if val is None:
            return []
        else:
            return pickle.loads(val)

    @doc_ids.setter
    def doc_ids(self, doc_ids):
        new_ids = set(self.doc_ids) | set([doc_id for doc_id in doc_ids])
        self.redis.set('session:%s:doc_ids' %self.session_id, pickle.dumps(new_ids))

    @property
    def kw_ids(self):
        val = self.redis.get('session:%s:kw_ids' %self.session_id)
        if val is None:
            return []
        else:
            return pickle.loads(val)

    @kw_ids.setter
    def kw_ids(self, kw_ids):
        new_ids = set(self.kw_ids) | set(kw_ids)
        self.redis.set('session:%s:kw_ids' %self.session_id, pickle.dumps(new_ids))

    ############################
    #Generic method to manipulates over:
    # - list
    # - dict(key->list) 
    ############################
    def _list_getter(self, key):
        res = self.redis.get('session:%s:%s' %(self.session_id, key))
        if not res:
            return []
        else:
            return pickle.loads(res)

    def _list_setter(self, key, val):
        current_value = getattr(self, key)
        current_value.append(val)
        self.redis.set('session:%s:%s' %(self.session_id, key), pickle.dumps(current_value))
            
    def _dict_list_getter(self, key):
        val = self.redis.get('session:%s:%s' %(self.session_id, key))
        if val is None:
            return defaultdict(list)
        else:
            return pickle.loads(val)

    def _dict_list_setter(self, key, data):
        """
        generic setter for {key: list, ...} data structure
        
        `key`: the redis key
        data: dictionary data to be incorporated into
        """
        hist = getattr(self, key)
        for kw, val in data.items():
            hist[kw].append(val)
        return self.redis.set('session:%s:%s' %(self.session_id, key), pickle.dumps(hist))

    ###############################
    #get the doc/kw feedback history
    ###############################
    @property
    def kw_fb_hist(self):
        """keyword feedback history"""
        return self._list_getter('kw_fb_hist')

    @kw_fb_hist.setter
    def kw_fb_hist(self, val):
        """keyword feedback history"""
        self._list_setter('kw_fb_hist', val)

    @property
    def doc_fb_hist(self):
        """document feedback history"""
        return self._list_getter('doc_fb_hist')

    @doc_fb_hist.setter
    def doc_fb_hist(self, val):
        """document feedback history"""
        self._list_setter('doc_fb_hist', val)

    ####################################
    #kw/doc feedback getter/updater
    ####################################
    @property
    def kw_feedbacks(self):
        """keyword feedback"""
        return dict([(Keyword.get(_id), fb)
                     for _id, fb in self.get("kw_feedbacks", {}).items()])
            

    @property
    def doc_feedbacks(self):
        """document feedback"""
        return dict([(Document.get(_id), fb)
                     for _id, fb in self.get("doc_feedbacks", {}).items()])


    def update_kw_feedback(self, kw, fb):
        """update keyword feedback"""
        self.hmset("kw_feedbacks", {kw.id: fb})

    def update_doc_feedback(self, doc, fb):
        """update document feedback"""
        self.hmset("doc_feedbacks", {doc.id: fb})


    ####################################
    #by use of **feedback propagator**
    #to track the docs and kws whose feedback
    #shall be updated
    ####################################
    @property
    def affected_docs(self):
        return [Document.get(doc_id) 
                for doc_id in self.get("affected_docs", set())]

    @property
    def affected_kws(self):
        return [Keyword.get(kw_id)
                for kw_id in self.get("affected_kws", set())]
        
    def add_affected_docs(self, *docs):
        doc_ids = [doc.id for doc in docs]
        self.sadd("affected_docs", *doc_ids)

    def add_affected_kws(self, *kws):
        kw_ids = [kw.id for kw in kws]
        self.sadd("affected_kws", *kw_ids)
        
    def clean_affected_objects(self):
        self.delete("affected_kws")
        self.delete("affected_docs")
                

    ########################
    #
    # Tracing/logging the history of document/keyword recommendation
    #
    # The internal data structure that tracks the recommendation history is like:
    #
    # Iter   Data
    # 1      [[some_doc_ids, ...],
    # ...    ....,
    # n      [some_doc_ids, ...]]
    ########################
    def add_doc_recom_list(self, docs):
        doc_ids = [doc.id for doc in docs]
        
        prev_doc_ids = self.get("recommended_docs", []) #list of list of integers
        prev_doc_ids.append(doc_ids)
        
        self.set("recommended_docs", prev_doc_ids)
    
    def add_kw_recom_list(self, kws):
        kw_ids = [kw.id for kw in kws]
        
        prev_kw_ids = self.get("recommended_kws", []) #list of list of integers
        prev_kw_ids.append(kw_ids)
        
        self.set("recommended_kws", prev_kw_ids)

    @property
    def recom_docs(self):
        return [Document.get_many(id_list)
                for id_list in  self.get("recommended_docs", [])]
        
    @property
    def recom_kws(self):
        return [Keyword.get_many(id_list)
                for id_list in  self.get("recommended_kws", [])]

    @property
    def last_recom_docs(self):
        """
        the most recent recommended documents 
        """
        try:
            return self.recom_docs[-1]
        except IndexError:
            raise Exception("No recent recommended documents available.")

    #############################
    #generic wrapper functions
    #############################
    
    def set(self, key, value):
        self.redis.set('session:%s:%s' %(self.session_id, key),  pickle.dumps(value))

    def get(self, key, default=None):
        data = self.redis.get('session:%s:%s' %(self.session_id, key))
        if not data:
            return default
        return  pickle.loads(data)
        
    def hmset(self, key, value):
        """
        set value for hash map
        key: string
        value: dict
        """
        assert type(value) is DictType, "value must be dict, but is %r" %value
        
        d = self.get(key, {})

        assert type(d) is DictType, "`d` must be dict, but is %r" %d
        
        d.update(value)
        
        self.set(key,  d)

    def hget(self, key, key2):
        """
        get the dict specified by key
        """
        
        data = self.get(key)
        assert type(data) is DictType, "data must be dict, but is %r" %data
        return data[key2]

    def hgetall(self, key):
        """
        get the dict specified by key
        """
        data = self.get(key, {})
        assert type(data) is DictType, "data must be dict, but is %r" %data
        return data

    def sadd(self, key, *values):
        """
        add values to set specified by key
        """
        s = self.get(key, set())

        assert isinstance(s, set), "`d` must be set, but is %r" %d
        
        s |= set(values)
        
        self.set(key,  s)

    def sget(self, key):
        """
        get the set specified by key
        """
        
        data = self.get(key, set())
        assert isinstance(data, set) , "data must be set, but is %r" %data
        return data
        
    def delete(self, key):
        self.redis.delete('session:%s:%s' %(self.session_id, key))

def test():
    import  redis
    conn = redis.StrictRedis(host='ugluk', port='6379', db='test')
    s = RedisRecommendationSessionHandler.get_session(conn)
    s.kw_ids = ['kw1', 'kw2']
    print s.kw_ids
    s.kw_ids = ['kw2', 'kw3']
    print s.kw_ids

    s.doc_ids = [1, 2]
    print s.doc_ids
    s.doc_ids = [3, 2]
    print s.doc_ids
    

    s.kw_feedbacks = {'kw1': .7, 'kw2': .5}
    print s.kw_feedbacks
    s.kw_feedbacks = {'kw3': .9, 'kw2': .6}
    print s.kw_feedbacks
    
    s.kw_score_hist = {'kw1': 0.5, 'kw2': 0.4}
    print s.kw_score_hist
    s.kw_score_hist = {'kw1': 0.7, 'kw2': 0.3}
    print s.kw_score_hist

    s.kw_explr_score_hist = {'kw1': 0.3, 'kw2': 0.2}
    print s.kw_explr_score_hist
    s.kw_explr_score_hist = {'kw1': 0.4, 'kw2': 0.1}
    print s.kw_explr_score_hist

    s.kw_explt_score_hist = {'kw1': 0.2, 'kw2': 0.2}
    print s.kw_explt_score_hist
    s.kw_explt_score_hist = {'kw1': 0.3, 'kw2': 0.2}
    print s.kw_explt_score_hist
if __name__ == "__main__":
    test()
