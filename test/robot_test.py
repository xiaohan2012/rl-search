#################
# Test for the automatic interacting robot
#################

import unittest
from util import (config_doc_kw_model, get_session)

from scinet3.robot import NearSightedRobot
from scinet3.model import Document, Keyword

config_doc_kw_model()
Document.load_all_from_db()

class NearSightedRobotTest(unittest.TestCase):
    def setUp(self):
        self.r = NearSightedRobot()
        self.kwgoal = Keyword.get_many(["python", "redis", "database"])
        
        self.r.setGoal(Document.get_many([6]), self.kwgoal)
        
    def test_give_feedback(self):
        docs = Document.get_many([1, 3])
        kws = Keyword.get_many(["redis", "database", "a", "tornado", "web", "python"])

        # Iter 1
        fb = self.r.give_feedback(docs, kws)        
        expected = {"docs": [[1, 1]],
                    "kws": [["database", 1]]}
        
        self.assertEqual(expected, fb)

        # Iter 2
        # what is selected in iter 1 
        # should not be selected any more
        fb = self.r.give_feedback(docs, kws)        
        expected = {"docs": [[3, 1]],
                    "kws": [["redis", 1]]}
        
        self.assertEqual(expected, fb)

        
