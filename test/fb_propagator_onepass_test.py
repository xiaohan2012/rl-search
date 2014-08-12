###############################
# Testing the onepass feedback propagator
###############################
import unittest
from util import (config_doc_kw_model, get_session)

#config model, 
#only done once
config_doc_kw_model()

from scinet3.model import (Document, Keyword)
from scinet3.fb_propagator import OnePassPropagator as ppgt

class OnePassPropagatorTest(unittest.TestCase):
    def setUp(self):
        self.session = get_session()
        
    def test_fb_from_doc(self):
        doc = Document.get(1)
        ppgt.fb_from_doc(doc, 0.5, self.session)        
        ppgt.done(self.session)
        
        # assertions
        self.assertAlmostEqual(.5 * .7, doc.fb(self.session))

        self.assertAlmostEqual(0.164710003739, Keyword.get("a").fb(self.session))
        self.assertAlmostEqual(0.166666666667, Keyword.get("redis").fb(self.session))
        self.assertAlmostEqual(0.0791425072939, Keyword.get("database").fb(self.session))

    def test_fb_from_kw(self):
        kw = Keyword.get("redis")
        
        recom_docs = [Document.get(_id) for _id in [1,2,3]]
        self.session.add_doc_recom_list(recom_docs)
        
        ppgt.fb_from_kw(kw, 0.5, self.session)        
        ppgt.done(self.session)
        
        # assertions
        self.assertAlmostEqual(.5 * .7, kw.fb(self.session))
        
        self.assertAlmostEqual(0.183701573217, recom_docs[0].fb(self.session))
        self.assertAlmostEqual(0.191506501383, recom_docs[1].fb(self.session))
        self.assertAlmostEqual(0, recom_docs[2].fb(self.session))

    def test_fb_from_dockw(self):
        kw = Keyword.get("redis")
        doc = Document.get(1)
        
        ppgt.fb_from_dockw(kw, doc, .5, self.session)
        ppgt.done(self.session)
        
        self.assertAlmostEqual(0.183701573217, doc.fb(self.session))
        self.assertAlmostEqual(0.166666666667, kw.fb(self.session))

    def test_all_together(self):
        """
        All three types of feedbacks are involved
        """
        doc = Document.get(1)
        kw = Keyword.get("redis")
        recom_docs = [Document.get(_id) for _id in [1,2,3]]
        self.session.add_doc_recom_list(recom_docs)

        ppgt.fb_from_doc(doc, 0.5, self.session)
        ppgt.fb_from_dockw(kw, doc, .5, self.session)
        ppgt.fb_from_kw(kw, 0.5, self.session)

        ppgt.done(self.session)

        self.assertAlmostEqual(0.164710003739, Keyword.get("a").fb(self.session))
        self.assertAlmostEqual(0.166666666667 * .3 + .5 * .7, Keyword.get("redis").fb(self.session))
        self.assertAlmostEqual(0.0791425072939, Keyword.get("database").fb(self.session))
        
        self.assertAlmostEqual(0.183701573217 * .3  + .7 * .5, recom_docs[0].fb(self.session))
        self.assertAlmostEqual(0.191506501383, recom_docs[1].fb(self.session))
        self.assertAlmostEqual(0, recom_docs[2].fb(self.session))



