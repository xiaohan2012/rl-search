####################
# Testing ModelSet
####################
import unittest

from scinet3.model import Document, Keyword
from scinet3.modelset import (DocumentSet, KeywordSet)
from scinet3.numerical_util import matrix2array

from util import (config_doc_kw_model, get_session, NumericTestCase)

config_doc_kw_model()

class HashableTest(unittest.TestCase):
    def test_ids_str(self):
        kwset = Keyword.get_many(["redis", "a", "the"])
        self.assertEqual("a,redis,the", kwset.ids_str)
        
        docset = Document.get_many([2, 1, 3])
        self.assertEqual("1,2,3", docset.ids_str)
        
    def test_equality_same_type(self):
        kwset1 = Keyword.get_many(["redis", "a", "the"])
        kwset2 = Keyword.get_many(["a", "the", "redis"])
        kwset3 = Keyword.get_many(["a", "the", "python"])

        self.assertEqual(kwset1, kwset2)
        self.assertNotEqual(kwset3, kwset2)
        
    def test_equality_different_type(self):
        kwset = Keyword.get_many(["redis", "a", "the"])
        docset = Document.get_many([2, 1, 3])
        
        self.assertNotEqual(kwset, docset)
        
    def test_kw_hashable(self):
        d = {}
        kwset1 = Keyword.get_many(["redis", "a", "the"])
        kwset2 = Keyword.get_many(["redis", "a", "the"])
        kwset3 = Keyword.get_many(["redis", "a", "python"])

        d[kwset1] = 1
        d[kwset2] = 2 #overides it
        d[kwset3] = 3 

        self.assertEqual({kwset1:2, kwset3: 3}, d)

    def test_doc_hashable(self):
        d = {}
        docset1 = Document.get_many([1,2,3])
        docset2 = Document.get_many([2,1,3])
        docset3 = Document.get_many([4,5,6])

        d[docset1] = 1
        d[docset2] = 2 #overides it
        d[docset3] = 3 

        self.assertEqual({docset1:2, docset3: 3}, d)
        
        
class SimilarityTest(NumericTestCase):
    def setUp(self):
        #load all first
        self.docs = Document.load_all_from_db()


    def test_keyword_centroid(self):
        kw = Keyword.get("a")
        kwset1 = KeywordSet([kw])
        
        self.assertArrayAlmostEqual(matrix2array(kwset1.centroid), kw.vec.toarray()[0])

        kw1 = Keyword.get("a")
        kw2 = Keyword.get("the")
        
        kwset2 = Keyword.get_many(["a", "the"])
        
        self.assertArrayAlmostEqual(matrix2array(kwset2.centroid), 
                                    (kw1.vec.toarray()[0] + kw2.vec.toarray()[0]) / 2)

    def test_document_centroid(self):
        doc = Document.get(1)
        docset1 = DocumentSet([doc])
        
        self.assertArrayAlmostEqual(matrix2array(docset1.centroid), doc.vec.toarray()[0])

        doc1 = Document.get(1)
        doc2 = Document.get(2)
        
        docset2 = Document.get_many([1, 2])
        
        self.assertArrayAlmostEqual(matrix2array(docset2.centroid), 
                                    (doc1.vec.toarray()[0] + doc2.vec.toarray()[0]) / 2)        

    def test_model2modelset_similarity(self):
        #for keywords
        kw = Keyword.get("redis")
        kwset = Keyword.get_many(["database", "mysql"])

        self.assertAlmostEqual(0.3754029265429976, kw.similarity_to(kwset))
        
        #for documents
        doc = Document.get(6)
        docset = Document.get_many([1, 2])
        
        self.assertAlmostEqual(0.7382455893131392, doc.similarity_to(docset))
        
    def test_modelset2model_similarity(self):
        #for keywords
        kw = Keyword.get("redis")
        kwset = Keyword.get_many(["database", "mysql"])

        self.assertAlmostEqual(0.3754029265429976, kwset.similarity_to(kw))
        self.assertAlmostEqual(kw.similarity_to(kwset), kwset.similarity_to(kw))

        #for documents
        doc = Document.get(6)
        docset = Document.get_many([1, 2])
        
        self.assertAlmostEqual(0.7382455893131392, docset.similarity_to(doc))
        self.assertAlmostEqual(doc.similarity_to(docset), docset.similarity_to(doc))

    def test_modelset2modelset_similarity(self):
        #for keywords
        kwset1 = Keyword.get_many(["redis", "a"])
        kwset2 = Keyword.get_many(["database", "the"])

        self.assertAlmostEqual(0.42205423035497763, kwset1.similarity_to(kwset2))
        
        #for documents
        docset1 = Document.get_many([3,5])
        docset2 = Document.get_many([4,6])
        
        self.assertAlmostEqual(0.6990609119502719, docset1.similarity_to(docset2))
        
    def test_type_mismatch(self):
        kw = Keyword.get("redis")
        kwset = Keyword.get_many(["database", "mysql"])

        doc = Document.get(6)
        docset = Document.get_many([1, 2])
        
        #doc to kw
        self.assertRaises(AssertionError, kw.similarity_to, doc)
        
        #kw to doc
        self.assertRaises(AssertionError, doc.similarity_to, kw)

        #kw to docset
        self.assertRaises(AssertionError, kw.similarity_to, docset)
        
        #docset to kw
        self.assertRaises(AssertionError, docset.similarity_to, kw)

        #doc to kwset
        self.assertRaises(AssertionError, doc.similarity_to, kwset)
                
        #kwset to doc
        self.assertRaises(AssertionError, kwset.similarity_to, doc)



