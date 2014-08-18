####################
# Testing Modellist
####################
import unittest

from scinet3.model import Document, Keyword
from scinet3.modellist import (DocumentList, KeywordList)
from scinet3.numerical_util import matrix2array

from util import (config_doc_kw_model, get_session, NumericTestCase)

config_doc_kw_model()

class HashableTest(unittest.TestCase):
    def test_ids_str(self):
        kwlist = Keyword.get_many(["redis", "a", "the"])
        self.assertEqual("a,redis,the", kwlist.ids_str)
        
        doclist = Document.get_many([2, 1, 3])
        self.assertEqual("1,2,3", doclist.ids_str)
        
    def test_equality_same_type(self):
        kwlist1 = Keyword.get_many(["redis", "a", "the"])
        kwlist2 = Keyword.get_many(["a", "the", "redis"])
        kwlist3 = Keyword.get_many(["a", "the", "python"])

        self.assertEqual(kwlist1, kwlist2)
        self.assertNotEqual(kwlist3, kwlist2)

        doclist1 = Document.get_many([1,2,3])
        doclist2 = Document.get_many([2,3,1])
        doclist3 = Document.get_many([4,5,6])

        self.assertEqual(doclist1, doclist2)
        self.assertNotEqual(doclist3, doclist2)
        
    def test_equality_different_type(self):
        kwlist = Keyword.get_many(["redis", "a", "the"])
        doclist = Document.get_many([2, 1, 3])
        
        self.assertNotEqual(kwlist, doclist)
        
    def test_kw_hashable(self):
        d = {}
        kwlist1 = Keyword.get_many(["redis", "a", "the"])
        kwlist2 = Keyword.get_many(["a", "the", "redis"])
        kwlist3 = Keyword.get_many(["redis", "a", "python"])

        d[kwlist1] = 1
        d[kwlist2] = 2 #override
        d[kwlist3] = 3 

        self.assertEqual({kwlist1:2, kwlist3: 3}, d)

    def test_doc_hashable(self):
        d = {}
        doclist1 = Document.get_many([1,2,3])
        doclist2 = Document.get_many([2,1,3])
        doclist3 = Document.get_many([4,5,6])

        d[doclist1] = 1
        d[doclist2] = 2 #override
        d[doclist3] = 3 

        self.assertEqual({doclist1:2, doclist3: 3}, d)
        
        
class SimilarityTest(NumericTestCase):
    def setUp(self):
        #load all first
        self.docs = Document.load_all_from_db()


    def test_keyword_centroid(self):
        kw = Keyword.get("a")
        kwlist1 = KeywordList([kw])
        
        self.assertArrayAlmostEqual(matrix2array(kwlist1.centroid), kw.vec.toarray()[0])

        kw1 = Keyword.get("a")
        kw2 = Keyword.get("the")
        
        kwlist2 = Keyword.get_many(["a", "the"])
        
        self.assertArrayAlmostEqual(matrix2array(kwlist2.centroid), 
                                    (kw1.vec.toarray()[0] + kw2.vec.toarray()[0]) / 2)

    def test_document_centroid(self):
        doc = Document.get(1)
        doclist1 = DocumentList([doc])
        
        self.assertArrayAlmostEqual(matrix2array(doclist1.centroid), doc.vec.toarray()[0])

        doc1 = Document.get(1)
        doc2 = Document.get(2)
        
        doclist2 = Document.get_many([1, 2])
        
        self.assertArrayAlmostEqual(matrix2array(doclist2.centroid), 
                                    (doc1.vec.toarray()[0] + doc2.vec.toarray()[0]) / 2)        

    def test_model2modellist_similarity(self):
        #for keywords
        kw = Keyword.get("redis")
        kwlist = Keyword.get_many(["database", "mysql"])

        self.assertAlmostEqual(0.3754029265429976, kw.similarity_to(kwlist))
        
        #for documents
        doc = Document.get(6)
        doclist = Document.get_many([1, 2])
        
        self.assertAlmostEqual(0.7382455893131392, doc.similarity_to(doclist))
        
    def test_modellist2model_similarity(self):
        #for keywords
        kw = Keyword.get("redis")
        kwlist = Keyword.get_many(["database", "mysql"])

        self.assertAlmostEqual(0.3754029265429976, kwlist.similarity_to(kw))
        self.assertAlmostEqual(kw.similarity_to(kwlist), kwlist.similarity_to(kw))

        #for documents
        doc = Document.get(6)
        doclist = Document.get_many([1, 2])
        
        self.assertAlmostEqual(0.7382455893131392, doclist.similarity_to(doc))
        self.assertAlmostEqual(doc.similarity_to(doclist), doclist.similarity_to(doc))

    def test_modellist2modellist_similarity(self):
        #for keywords
        kwlist1 = Keyword.get_many(["redis", "a"])
        kwlist2 = Keyword.get_many(["database", "the"])

        self.assertAlmostEqual(0.42205423035497763, kwlist1.similarity_to(kwlist2))
        
        #for documents
        doclist1 = Document.get_many([3,5])
        doclist2 = Document.get_many([4,6])
        
        self.assertAlmostEqual(0.6990609119502719, doclist1.similarity_to(doclist2))
        
    def test_type_mismatch(self):
        kw = Keyword.get("redis")
        kwlist = Keyword.get_many(["database", "mysql"])

        doc = Document.get(6)
        doclist = Document.get_many([1, 2])
        
        #doc to kw
        self.assertRaises(AssertionError, kw.similarity_to, doc)
        
        #kw to doc
        self.assertRaises(AssertionError, doc.similarity_to, kw)

        #kw to doclist
        self.assertRaises(AssertionError, kw.similarity_to, doclist)
        
        #doclist to kw
        self.assertRaises(AssertionError, doclist.similarity_to, kw)

        #doc to kwlist
        self.assertRaises(AssertionError, doc.similarity_to, kwlist)
                
        #kwlist to doc
        self.assertRaises(AssertionError, kwlist.similarity_to, doc)
