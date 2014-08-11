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
        
        self.assertEqual(set(doc.keywords), set([Keyword.get(kw_str) 
                                                 for kw_str in kw_strs]))

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
        self.assertEqual(set(kw.docs), set([Document.get(doc_id) 
                                            for doc_id in doc_ids]))
        
        #that is as far as we can test
        #no numerical testing
        self.assertTrue(type(kw._doc_weight) is DictType)
