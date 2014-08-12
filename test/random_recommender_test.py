###############################
# Testing the Random recommender
###############################
import unittest
import random

from scinet3.model import (Document, Keyword)

from scinet3.rec_engine.random_rec import RandomRecommender

from util import config_doc_kw_model

config_doc_kw_model()

class RadnomRecommenderTest(unittest.TestCase):
    def setUp(self):
        self.r = RandomRecommender()
        random.seed(123456)
        
    def test_recom_doc(self):
        docs = self.r.recommend_documents(4)
        self.assertEqual(Document.get_many([9,8,1,2]), 
                         docs)

    def test_recom_kw_assoc(self):
        """keywords are associated with docs"""
        kws = self.r.recommend_keywords(4, Document.get_many([1,2]))
        self.assertEqual(Keyword.get_many(["database", "redis" , "a", "the"]), 
                         kws)

    def test_recom_kw(self):
        kws = self.r.recommend_keywords(4, False)
        self.assertEqual(Keyword.get_many(["mysql", "python", "a", "the"]), 
                         kws)

    def test_together(self):
        docs, kws = self.r.recommend(4,4,False)
        
        self.assertEqual(Keyword.get_many(["a", "redis", "the", "web"]), 
                         kws)
        self.assertEqual(Document.get_many([9,8,1,2]), 
                         docs)

    def test_together_assoc(self):
        """keywords are associated with docs"""
        docs, kws = self.r.recommend(4,4,True)
        self.assertEqual(Document.get_many([9,8,1,2]), 
                         docs)
        self.assertEqual(Keyword.get_many(["python", "the", "database", "redis"]), 
                         kws)
