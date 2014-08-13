##############################
# Test the associations between Document and Keywords
##############################
import unittest
from types import DictType

from scinet3.model import Document, Keyword

from util import config_doc_kw_model, get_session

config_doc_kw_model()

class ModelTest(unittest.TestCase):
    def setUp(self):
        #load all first
        self.docs = Document.load_all_from_db()
        
    def test_document(self):
        """
        whether id, article, keywords are correct
        """
        kw_strs = ["redis", "database", "a"]
        doc = Document.get(1)
        
        self.assertEqual(doc.id, 1)
        
        self.assertEqual(doc.title, "redis: key-value-storage database (ONE)")
        
        self.assertEqual(set(doc.keywords), set(Keyword.get_many(kw_strs)))

        #that is as far as we can test
        #no numerical testing
        self.assertTrue(type(doc._kw_weight) is DictType)

                
    def test_keyword(self):
        """
        whether id, documents are correct
        """
        doc_ids = [1, 2, 6]
        kw = Keyword.get("redis")
        self.assertEqual(kw.id, "redis")
        self.assertEqual(set(kw.docs), set(Document.get_many(doc_ids)))
        
        #that is as far as we can test
        #no numerical testing
        self.assertTrue(type(kw._doc_weight) is DictType)


    def test_get_many(self):
        doc_ids = [1,2]
        kw_ids = ["a", "the"]
        
        self.assertEqual(Document.get_many([1,2]), 
                         Document.get_many(doc_ids))

        self.assertEqual(Keyword.get_many(["a", "the"]), 
                         Keyword.get_many(kw_ids))

    def test_similarity(self):
        # for doc
        doc1 = Document.get(1)
        doc2 = Document.get(2)
        doc3 = Document.get(3)
        
        self.assertAlmostEqual(0.6300877890447911, doc1.similarity_to(doc2))
        self.assertAlmostEqual(doc2.similarity_to(doc1), doc1.similarity_to(doc2))

        self.assertAlmostEqual(0.31713642199844894, doc1.similarity_to(doc3))
        
        self.assertRaises(NotImplementedError, doc1.similarity_to, doc3, "not implemented metric")
        
        # for kw
        kw1 = Keyword.get("redis")
        kw2 = Keyword.get("database")
        kw3 = Keyword.get("python")
        
        self.assertAlmostEqual(0.6698544675330306, kw1.similarity_to(kw2))
        self.assertAlmostEqual(kw2.similarity_to(kw1), kw1.similarity_to(kw2))

        self.assertAlmostEqual(0.2613424459663648, kw1.similarity_to(kw3))
        
        self.assertRaises(NotImplementedError, kw1.similarity_to, kw3, "not implemented metric")
