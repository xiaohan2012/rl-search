import unittest

import torndb
import redis

from scinet3.model import Document, Keyword

from util import (config_doc_kw_model, get_session)

#config model, 
#only done once
config_doc_kw_model()

class KeywordFeedbackTest(unittest.TestCase):
    def setUp(self):
        #session
        self.session = get_session()

    def test_rec_fb_from_doc(self):
        """
        getter/setting for receiving feedback from document
        """
        kw = Keyword.get("redis")
        
        kw.rec_fb_from_doc(Document.get(1), 1, self.session)
        kw.rec_fb_from_doc(Document.get(2), .5, self.session)
        
        self.assertEqual(kw.fb_from_doc(self.session), {Document.get(1): 1, Document.get(2): .5})        

        #does not contain redis, error should be raised
        self.assertRaises(AssertionError, kw.rec_fb_from_doc, Document.get(3), 1, self.session)
        
    def test_rec_fb_from_dockw(self):
        """
        getter/setting for receiving feedback from in-document keyword
        """
        kw = Keyword.get("redis")
        
        kw.rec_fb_from_dockw(kw, Document.get(2), .5, self.session)
        kw.rec_fb_from_dockw(kw, Document.get(1), 1, self.session)
        
        print kw.fb_from_doc(self.session)

        self.assertEqual(kw.fb_from_doc(self.session), {Document.get(1): 1, Document.get(2): .5})

        #is not the right keyword
        self.assertRaises(AssertionError, kw.rec_fb_from_dockw, Keyword.get("the"), Document.get(1), 1, self.session)

    def test_rec_fb_from_kw(self):
        """
        getter/setting for receiving feedback from keyword
        """
        kw = Keyword.get("redis")
        kw.rec_fb_from_kw(kw, 1, self.session)
        self.assertEqual(1, 
                         kw.fb_from_kw(self.session))
        
        kw.rec_fb_from_kw(kw, .5, self.session)
        self.assertEqual(.5, 
                         kw.fb_from_kw(self.session))

        #is not the right keyword
        self.assertRaises(AssertionError, kw.rec_fb_from_kw, Keyword.get("the"), 1, self.session)

    def test_fb_weighted_sum(self):
        """
        test if the weighted sum is correct
        """
        kw = Keyword.get("redis")
        
        kw.rec_fb_from_dockw(kw, Document.get(1), 1, self.session)
        kw.rec_fb_from_doc(Document.get(2), .5, self.session)

        kw.rec_fb_from_kw(kw, .5, self.session)

        self.assertEqual(.3 * (1 / 3. + 1 / 6.) + .7 * .5,
                         kw.fb_weighted_sum(self.session))
        

    def test_loop_done(self):
        """
        test if things are cleaned when the loop is done
        """
        kw = Keyword.get("redis")
        
        kw.rec_fb_from_dockw(kw, Document.get(1), 1, self.session)
        kw.rec_fb_from_doc(Document.get(2), .5, self.session)

        kw.rec_fb_from_kw(kw, .5, self.session)

        # terminate the loop
        # everything feedback stuff cleaned
        kw.loop_done(self.session)

        self.assertEqual(kw.fb_weighted_sum(self.session), 0)    
