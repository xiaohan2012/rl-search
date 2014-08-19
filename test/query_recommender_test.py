###############################
# Testing the Query based Recommender
###############################
import unittest
from util import (config_doc_kw_model, get_session, NumericTestCase)

#config model, 
#only done once
_, fmim = config_doc_kw_model()

from scinet3.model import (Document, Keyword)
from scinet3.modellist import KeywordList
from scinet3.rec_engine.query import QueryBasedRecommender
from scinet3.numerical_util import matrix2array

class QueryRecommenderTest(NumericTestCase):
    def setUp(self):
        self.r = QueryBasedRecommender(4, 2,
                                       4, 2,
                                       **fmim)
    
    def test_word_vec(self):
        words = ["web", "database"]
        
        expected = [0, 1, 0, 0, 0, 0, 0, 1]

        self.assertArrayAlmostEqual(expected, matrix2array(self.r._word_vec(words).T))

    def test_word_vec_non_existing_word(self):
        words = ["web", "database", 
                 "no exist, :)"]
        
        expected = [0, 1, 0, 0, 0, 0, 0, 1]

        self.assertArrayAlmostEqual(expected, matrix2array(self.r._word_vec(words).T))

        
    def test_recommend_documents_sensible_query(self):
        """
        query that has keywords existing in the documents' keyword list
        """
        query = "database, python, redis"
        matched_docs, query_keywords = self.r.recommend_documents(query, 4)
        
        self.assertEqual(Document.get_many([6,1,2,5]), matched_docs)
        self.assertEqual(Keyword.get_many(["database", "python", "redis"]), query_keywords)

    def test_recommend_documents_insane_query(self):
        """
        query that has keywords NOT existing in the documents' keyword list
        """
        query = "blah, blah, hahaha"
        matched_docs, query_keywords = self.r.recommend_documents(query, 10)

        self.assertTrue(len(matched_docs) == 0)
        self.assertTrue(len(query_keywords) == 0)

    def test_recommend_keywords(self):
        kws = self.r.recommend_keywords(Document.get_many([6, 1]), 5, 3, 
                                        query_keywords = Keyword.get_many(["python", "redis", 
                                                                           "non-existing"]))
        kw_from_recom_docs = kws[:3]
        kw_from_assoc_docs = kws[3:]
        
        self.assertEqual(5, len(kws))
        self.assertEqual(list(Keyword.get_many(["python", "redis"])), kw_from_recom_docs[:2]) #the first two should be python and redis
        
        for kw in kw_from_recom_docs:
            self.assertTrue(kw["recommended"])
        for kw in kw_from_assoc_docs:
            self.assertFalse(kw["recommended"])
            
        #no easy way to further test the elements of the kws
        pass
        
    def test_sample_documents_associated_with_keywords_empty_keywords_case(self):
        """
        in case keywords are empty 
        """
        docs = self.r.sample_documents_associated_with_keywords(KeywordList([]), 999)
        self.assertEqual(0, len(docs))

    def test_sample_documents_associated_with_keywords_sample_size_too_large(self):
        """
        in case the sample size is too large
        """
        docs = self.r.sample_documents_associated_with_keywords(Keyword.get_many(["python"]), 999)
        self.assertEqual(Document.get_many([3,4,5,6,8]), docs)

    def test_sample_documents_associated_with_keywords_not_existing_keywords_case(self):
        """
        in case keywords are non-existant in the corpus
        """
        docs = self.r.sample_documents_associated_with_keywords(Keyword.get_many(["foo", "bar", "baz"]), 999)
        self.assertEqual(0, len(docs))        

    def test_sample_documents_associated_with_keywords(self):
        """
        normal case
        """
        docs = self.r.sample_documents_associated_with_keywords(Keyword.get_many(["python", "redis"]), 2)

        self.assertEqual(2, len(docs))

        for doc in docs:
            self.assertTrue((Keyword.get("python") in doc.keywords) or \
                            (Keyword.get("redis") in doc.keywords))
            
    def test_query_that_produces_match(self):
        """
        Query that matches something in the corpus
        """
        query = "python, redis"
        docs, kws = self.r.recommend(query)
        
        self.assertEqual(Document.get(6), docs[0])
        self.assertEqual(4, len(docs))
        
        #kws should be superset of assoc_kws
        assoc_kws = set([kw 
                         for doc in docs
                         for kw in doc.keywords])
        self.assertTrue(assoc_kws.issubset(set(kws)))
        
        
    def test_query_that_produces_nothing(self):
        """
        Query that does not match keywords in the corpus
        """
        query = "blah, haha"
        docs, kws = self.r.recommend(query)

        self.assertEqual(0, len(docs))
        self.assertEqual(0, len(kws))

