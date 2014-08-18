###############################
# Testing the LinRel recommender
###############################
import unittest

import numpy as np
from scipy.sparse import csr_matrix

from util import (config_doc_kw_model, get_session, NumericTestCase)

from scinet3.model import (Document, Keyword)
from scinet3.linrel import linrel

#config model, 
#only done once
config_doc_kw_model()

class LinRelTest(NumericTestCase):
    
    def test_basic(self):
        D = csr_matrix(np.array([[1, 0, 0, 0, 1, 1],
                                 [0, 1, 1, 0, 0, 0], 
                                 [1, 0, 0, 1, 0, 0],#we favor this one
                                 [1, 0, 0, 0, 1, 1],
                                 [1, 1, 0, 1, 0, 0],#this is good
                                 [0, 1, 1, 0, 0, 0],
                                 [1, 1, 1, 0, 0, 0],
                             ]))
        D_t = D[0:3,:]
        mu = 1
        c = .2
        y_t = csr_matrix([[.3], [.3], [.7]])
        scores, explr_scores, explt_scores = linrel(y_t, D_t, D, mu, c)
        
        self.assertArrayAlmostEqual([0.35511143,0.26666667,0.53700971,0.35511143,0.6451382,0.26666667,0.51974334],
                         np.transpose(scores).tolist()[0])
        
