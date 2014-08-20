###############################
# Testing the command line app
###############################
import unittest, random

from util import (config_doc_kw_model, get_session)

_, fmim_dict = config_doc_kw_model()

from scinet3.cmdapp import CmdApp
from scinet3.model import (Document, Keyword)

from scinet3.fb_propagator import OnePassPropagator
from scinet3.fb_updater import OverrideUpdater

from scinet3.rec_engine.query import QueryBasedRecommender
from scinet3.rec_engine.linrel import LinRelRecommender

class CmdAppTest(unittest.TestCase):
    def setUp(self):
        init_recommender = QueryBasedRecommender(3, 2, 
                                                 3, 2, 
                                                 **fmim_dict)
        main_recommender = LinRelRecommender(3, 3, 
                                             1., .5, 
                                             1., .5, 
                                             None,None,
                                             None,None,
                                             **fmim_dict)

        self.app = CmdApp(OnePassPropagator, OverrideUpdater, 
                          init_recommender, main_recommender)        
        
        self.session = get_session()
        
        #add recommended list
        self.session.add_doc_recom_list(Document.get_many([1,2,3]))
        self.session.add_kw_recom_list(Keyword.get_many(["a", "redis", "database"]))
        
        self.fb = {
            "docs": [[1, .5]],
            "kws": [["redis", .5]],
            "dockws": [["redis", 1, .5]]
        }
        
        random.seed(123456)

    def test_receive_feedbacks(self):    
        self.app.receive_feedbacks(self.session, self.fb)
        
        docs = Document.get_many([1,2,3])
        self.assertAlmostEqual(0.183701573217 * .3  + .7 * .5, docs[0].fb(self.session))
        self.assertAlmostEqual(0.191506501383, docs[1].fb(self.session))
        self.assertAlmostEqual(0., docs[2].fb(self.session))

        kws = Keyword.get_many(["a", "redis", "database", "python"])
        self.assertAlmostEqual(0.56689342264886755 * .5 / (0.56689342264886755 + 0.49704058656839417), kws[0].fb(self.session))
        self.assertAlmostEqual(1 / 4. * .3 + .5 * .7, kws[1].fb(self.session))
        self.assertAlmostEqual(1 / 4., kws[2].fb(self.session))
        self.assertAlmostEqual(0., kws[3].fb(self.session))
        
    def test_recommend_initial(self):
        docs , kws = self.app.recommend(start = True, query = "python, redis")
        self.assertEqual(3, len(docs))
        self.assertTrue(len(kws) >= 3) 

    def test_recommend_main(self):
        #receive the feedback first
        self.app.receive_feedbacks(self.session, self.fb)
        
        docs , kws = self.app.recommend(start = False, session = self.session)
        self.assertEqual(Document.get_many([1,2,6]), 
                         docs)
        self.assertEqual(Keyword.get_many(["redis", "database", "a", "python", "the"]), 
                         kws)
        

    def test_recommend_together(self):
        #### Iter 1 ######
        docs , kws = self.app.recommend(start = True, query = "python, redis")
        self.assertEqual(3, len(docs))
        self.assertTrue(len(kws) >= 3)        

        #### Iter 2 ######
        # receive the feedback first
        self.app.receive_feedbacks(self.session, self.fb)
        
        docs , kws = self.app.recommend(start = False, session = self.session)
        self.assertEqual(Document.get_many([1,2,6]), 
                         docs)
        self.assertEqual(Keyword.get_many(["redis", "database", "a", "python", "the"]), 
                         kws)
        
    def test_interaction(self):
        docs = Document.get_many([1, 2, 3])
        kws = Keyword.get_many(["redis",  "database", "a", "the"])
        
        inputs = ["0 1", #docs
                  "0 1", #kws
                  "0 1", #kw in doc 1
                  "", #kw in doc 2, nothing
                  "2"    #kw in doc 3
        ]
        fb = self.app.interact_with_user(docs, kws, inputs)
        
        expected = {
            "docs": [[1L, 1], [2L, 1]],
            "kws": [[u"redis", 1], [u"database", 1]],
            "dockws": [[u"redis", 1L, 1], [u"database", 1L, 1], [u"python", 3L, 1]],
        }
        self.assertEqual(expected, fb)
