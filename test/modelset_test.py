####################
# Testing ModelSet
####################
import unittest

from scinet3.model import Document, Keyword
from scinet3.modelset import (DocumentSet, KeywordSet)

from util import config_doc_kw_model, get_session

config_doc_kw_model()

class SimilarityTest(unittest.TestCase):
    def setUp(self):
        #load all first
        self.docs = Document.load_all_from_db()

    def test_model2modelset_similarity(self):
        #for keywords
        kw = Keyword.get("redis")
        kwset = Keyword.get_many(["database", "mysql"])

        self.assertAlmostEqual(.5, kw.similarity_to(kwset))
        
        #for documents
        doc = Document.get(6)
        docset = Document.get_many([1, 2])
        
        self.assertAlmostEqual(.5, doc.similarity_to(docset))
        
    def test_modelset2model_similarity(self):
        #for keywords
        kw = Keyword.get("redis")
        kwset = Keyword.get_many(["database", "mysql"])

        self.assertAlmostEqual(.5, kwset.similarity_to(kw))
        self.assertAlmostEqual(kw.similarity_to(kwset), kwset.similarity_to(kw))

        #for documents
        doc = Document.get(6)
        docset = Document.get_many([1, 2])
        
        self.assertAlmostEqual(.5, docset.similarity_to(doc))
        self.assertAlmostEqual(doc.similarity_to(docset), docset.similarity_to(doc))

    def test_modelset2modelset_similarity(self):
        #for keywords
        kwset1 = Keyword.get_many(["redis", "a"])
        kwset2 = Keyword.get_many(["database", "the"])

        self.assertAlmostEqual(.5, kwset1.similarity_to(kwset2))
        
        #for documents
        docset1 = Document.get_many([3,5])
        docset2 = Document.get_many([4,6])
        
        self.assertAlmostEqual(.5, docset1.similarity_to(docset2))
        
    def test_type_mismatch(self):
        kw = Keyword.get("redis")
        kwset = Keyword.get_many(["database", "mysql"])

        doc = Document.get(6)
        docset = Document.get_many([1, 2])
        
        #doc to kw
        self.assertRaises(TypeError, kw.similarity_to, doc)
        
        #kw to doc
        self.assertRaises(TypeError, doc.similarity_to, kw)

        #kw to docset
        self.assertRaises(TypeError, kw.similarity_to, docset)
        
        #docset to kw
        self.assertRaises(TypeError, docset.similarity_to, kw)

        #doc to kwset
        self.assertRaises(TypeError, doc.similarity_to, kwset)
                
        #kwset to doc
        self.assertRaises(TypeError, kwset.similarity_to, doc)



