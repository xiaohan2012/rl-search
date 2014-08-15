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
    """
    There is no point in testing randomness.

    So we test the object length only
    """
    def setUp(self):
        self.r = RandomRecommender(2,2,True)
        
    def test_recom_doc(self):
        docs = self.r.recommend_documents(4)
        self.assertEqual(4, 
                         len(docs))

    def test_recom_kw_assoc(self):
        """keywords are associated with docs"""
        kws = self.r.recommend_keywords(4, Document.get_many([1,2]))
        self.assertEqual(4, 
                         len(kws))

    def test_recom_kw(self):
        kws = self.r.recommend_keywords(4, False)
        self.assertEqual(4, 
                         len(kws))

    def test_together(self):
        docs, kws = self.r.recommend(4,4,False)
        
        self.assertEqual(4, 
                         len(kws))
        self.assertEqual(4, 
                         len(docs))

    def test_together_assoc(self):
        """keywords are associated with docs"""
        docs, kws = self.r.recommend(4,4,True)
        self.assertEqual(4, 
                         len(docs))
        self.assertEqual(4, 
                         len(kws))

    def test_together_using_default_params(self):
        docs, kws = self.r.recommend()
        self.assertEqual(2, 
                         len(docs))
        self.assertEqual(2, 
                         len(kws))
        
