import unittest

import redis
from scinet3.model import Document, Keyword


from util import (config_doc_kw_model, get_session)

config_doc_kw_model()

class RedisWrapperTest(unittest.TestCase):
    """
    Test on the wrapper methods on redis native methods
    """
    def setUp(self):
        self.session = get_session()

    def test_hashmap(self):
        """
        test operations on hashmap
        """
        key = "test_key"
        self.session.hmset(key, {"hmkey1": 1.2, "hmkey2": "value", 1: 1.2})
        self.session.hmset(key, {"hmkey3": "value"})
        self.assertEqual(self.session.hgetall(key), {"hmkey1": 1.2, "hmkey2": "value", 1: 1.2, "hmkey3": "value"})

        self.assertEqual(self.session.hget(key, "hmkey1"), 1.2)
        self.assertEqual(self.session.hget(key, "hmkey2"), "value")
        self.assertEqual(self.session.hget(key, 1), 1.2)
        
        self.session.delete(key)
        self.assertEqual(self.session.hgetall(key), {})
        
    def test_set(self):
        """
        test operations on set
        """
        key = "sets"
        
        self.session.sadd(key, 1,2,3, "asdf")
        self.assertEqual({1,2,3,"asdf"}, 
                         self.session.get(key))

        self.session.sadd(key, "asdf")
        self.assertEqual({1,2,3,"asdf"}, 
                         self.session.get(key))

        self.session.sadd(key, 4)
        self.assertEqual({1,2,3,4,"asdf"}, 
                         self.session.get(key))

    def test_get_and_set(self):
        """
        test on `get` and `set` methods
        """
        self.session.set("numer_value", 1)
        self.assertEqual(self.session.get("numer_value"), 1)
        
        self.session.set("str_value", "abc")
        self.assertEqual(self.session.get("str_value"), "abc")
        


class RedisSessionTest(unittest.TestCase):
    """
    Test on the session-related methods
    """
    def setUp(self):
        self.session = get_session()

    def test_affected_docs(self):
        docs = [Document.get(1), Document.get(2)]
        
        self.session.add_affected_docs(*docs)
        self.assertEqual(docs, self.session.affected_docs)

        doc3 = Document.get(3)
        docs.append(doc3)
        self.session.add_affected_docs(doc3)
        self.assertEqual(set(docs), 
                         set(self.session.affected_docs))

    def test_affected_kws(self):
        kws = [Keyword.get("python"), Keyword.get("redis")]
        
        self.session.add_affected_kws(*kws)
        self.assertEqual(kws, self.session.affected_kws)

        kw3 = Keyword.get("a")
        kws.append(kw3)
        self.session.add_affected_kws(kw3)
        self.assertEqual(set(kws), 
                         set(self.session.affected_kws))

    def test_clean_affected_objects(self):        
        self.session.clean_affected_objects()
        
        empty_list = []
        self.assertEqual(empty_list, self.session.affected_docs)
        self.assertEqual(empty_list, self.session.affected_kws)

        
    def test_update_kw_fb(self):
        """update keyword feedback"""
        kw = Keyword.get('redis')
        self.session.update_kw_feedback(kw, 1)
        
        self.assertEqual(self.session.kw_feedbacks, {kw: 1})
        
        self.assertEqual(kw.fb(self.session), 1)

    def test_update_doc_fb(self):
        """update document feedback"""
        doc = Document.get(1)
        self.session.update_doc_feedback(doc, 1)
        
        self.assertEqual(self.session.doc_feedbacks, {doc: 1})
        
        self.assertEqual(doc.fb(self.session), 1)

class RecommendationTrackingTest(unittest.TestCase):
    def setUp(self):
        self.session = get_session()
        self.maxDiff = None

    def test_add_kws(self):
        iter1 = Keyword.get_many(["redis", "database", "mysql"])
        iter2 = Keyword.get_many(["redis", "database", "python"])
        
        self.session.add_kw_recom_list(iter1)        
        self.assertEqual([iter1], self.session.recom_kws)

        self.session.add_kw_recom_list(iter2)        
        self.assertEqual([iter1, iter2], self.session.recom_kws)

    def test_add_docs(self):
        """
        as well as last_recom_docs
        """
        iter1 = Document.get_many([1, 2, 3])
        iter2 = Document.get_many([2, 3, 4])
        
        self.session.add_doc_recom_list(iter1)        
        
        self.assertEqual([iter1], self.session.recom_docs)

        self.session.add_doc_recom_list(iter2)        
        self.assertEqual([iter1, iter2], self.session.recom_docs)

        self.assertEqual(iter2, self.session.last_recom_docs)
        
