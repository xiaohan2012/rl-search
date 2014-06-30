import pickle
import uuid
from collections import defaultdict

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

    @classmethod
    def get_session(cls, conn, session_id=None):
        #factory method, return the session
        return cls(conn, session_id)    

    def _dict_list_getter(self, key):
        val = self.redis.get('session:%s:%s' %(self.session_id, key))
        if val is None:
            return defaultdict(list)
        else:
            return pickle.loads(val)

    def _dict_list_setter(self, key, data):
        """
        `key`: the redis key
        data: dictionary data to be incorporated into
        generic setter for {key: list, ...} data structure
        """
        hist = getattr(self, key)
        for kw, val in data.items():
            hist[kw].append(val)
        return self.redis.set('session:%s:%s' %(self.session_id, key), pickle.dumps(hist))

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

    @property
    def kw_feedbacks(self):
        """keyword feedback history"""
        #we use pickle to avoid the int-string problem
        #descriped in http://stackoverflow.com/questions/1450957/pythons-json-module-converts-int-dictionary-keys-to-strings
        res = self.redis.get('session:%s:kw_feedbacks' %self.session_id)
        if not res:
            return {}
        else:
            return pickle.loads(res)

    @kw_feedbacks.setter
    def kw_feedbacks(self, kw_fb):
        """keyword feedback history"""
        kw_feedbacks = self.kw_feedbacks
        kw_feedbacks.update(kw_fb)
        self.redis.set('session:%s:kw_feedbacks' %self.session_id, pickle.dumps(kw_feedbacks))

    @property
    def doc_feedbacks(self):
        """document feedback history"""
        res = self.redis.get('session:%s:doc_feedbacks' %self.session_id)
        if not res:
            return {}
        else:
            return pickle.loads(res)

    @doc_feedbacks.setter
    def doc_feedbacks(self, doc_fb):
        """document feedback history"""
        doc_feedbacks = self.doc_feedbacks
        doc_feedbacks.update(doc_fb)
        self.redis.set('session:%s:doc_feedbacks' %self.session_id, pickle.dumps(doc_feedbacks))                

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
