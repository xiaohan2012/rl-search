###############################
# Testing the Query based Recommender
###############################
import unittest
from util import (config_doc_kw_model, get_session)

#config model, 
#only done once
config_doc_kw_model()

from scinet3.model import (Document, Keyword)

class QueryRecommenderTest(unittest.TestCase):
    pass
