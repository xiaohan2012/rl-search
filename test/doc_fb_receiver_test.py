##############################
# Test for document feedback receiver
##############################

import unittest

import torndb
import redis

from scinet3.model import Document, Keyword

from util import (config_doc_kw_model, get_session)

#config model, 
#only done once
config_doc_kw_model()
docs = Document.load_all_from_db()

class DocumentFeedbackTest(unittest.TestCase):
    def setUp(self):
        #session
        self.session = get_session()

    def test_rec__from_doc(self):
        """
        getter/setting for receiving feedback from document
        """
        doc = Document.get(1)
        
        doc.rec_fb_from_doc(doc, 1, self.session)        
        self.assertEqual(1, doc.fb_from_doc(self.session))

        doc.rec_fb_from_doc(doc, .5, self.session)        
        self.assertEqual(.5, doc.fb_from_doc(self.session))

        #is not the right document
        self.assertRaises(AssertionError, doc.rec_fb_from_doc, Document.get(2), 1, self.session) 
        
    def test_rec_fb_from_dockw(self):
        """
        getter/setting for receiving feedback from in-document keyword
        """
        doc = Document.get(1)

        doc.rec_fb_from_dockw(Keyword.get("redis"), doc, 1, self.session)
        doc.rec_fb_from_dockw(Keyword.get("database"), doc, .5, self.session)
        
        self.assertEqual(doc.fb_from_kw(self.session), {Keyword.get("redis"): 1, Keyword.get("database"): .5})

        #not the right document
        self.assertRaises(AssertionError, doc.rec_fb_from_dockw, Document.get(2), Keyword.get("redis"), 1, self.session)

        #python is not a keyword for document#1, error should be raised
        self.assertRaises(AssertionError, doc.rec_fb_from_dockw, doc, Keyword.get("python"), 1, self.session)

    def test_rec_fb_from_kw(self):
        """
        getter/setting for receiving feedback from keyword
        """
        doc = Document.get(1)

        doc.rec_fb_from_kw(Keyword.get("redis"), 1, self.session)
        doc.rec_fb_from_kw(Keyword.get("database"), .5, self.session)
        
        self.assertEqual(doc.fb_from_kw(self.session), {Keyword.get("redis"): 1, Keyword.get("database"): .5})

        #does not contain redis, error should be raised
        self.assertRaises(AssertionError, doc.rec_fb_from_kw, Keyword.get("python"), 1, self.session)
                

    def test_fb_weighted_sum(self):
        """
        test if the weighted sum is correct
        """
        doc = Document.get(1)

        
        doc.rec_fb_from_dockw(Keyword.get("redis"), doc, 1, self.session)
        doc.rec_fb_from_kw(Keyword.get("database"), .5, self.session)

        doc.rec_fb_from_doc(doc, .5, self.session)
        
        redis = Keyword.get("redis")
        db = Keyword.get("database")
        weights = {redis: 0.62981539329519109, 
                   db: 0.45460437826405437, 
                   Keyword.get("a"): 0.62981539329519109
        }
        
        self.assertAlmostEqual(.7 * .5 + .3 * (weights[redis] * 1 + weights[db] * .5) / sum(weights.values()),
                         doc.fb_weighted_sum(self.session))
        
    def test_loop_done(self):
        """
        test if things are cleaned when the loop is done
        """
        doc = Document.get(1)

        doc.rec_fb_from_dockw(Keyword.get("redis"), doc, 1, self.session)
        doc.rec_fb_from_kw(Keyword.get("database"), .5, self.session)

        doc.rec_fb_from_doc(doc, .5, self.session)

        # terminate the loop
        # everything feedback stuff cleaned
        doc.loop_done(self.session)

        self.assertEqual(doc.fb_weighted_sum(self.session), 0)
