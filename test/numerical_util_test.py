#############################
# Numerical utility function testing
#############################
import unittest
import numpy as np
from scipy import (linalg, mat, dot)
from scipy.sparse import csr_matrix

from util import NumericTestCase
from scinet3.numerical_util import (cosine_similarity, matrix2array)


class ConsineSimilarityTest(unittest.TestCase):

    def setUp(self):
        self.row1 = [2, 1, 0, 2, 0, 1, 1, 1]
        self.row2 = [2, 1, 1, 1, 1, 0, 1, 1]

        self.expected = .8215838362577491
        
    def test_list(self):
        v1 = self.row1
        v2 = self.row2
        self.assertAlmostEqual(self.expected,
                               cosine_similarity(v1, v2))

    def test_array(self):
        v1 = np.array(self.row1)
        v2 = np.array(self.row2)
        
        self.assertAlmostEqual(self.expected,
                               cosine_similarity(v1, v2))
        
    def test_matrix(self):        
        v1 = mat([self.row1])
        v2 = mat([self.row2])
        
        self.assertAlmostEqual(self.expected,
                               cosine_similarity(v1, v2))
    
        
    def test_sparse_matrix(self):
        v1 = csr_matrix([self.row1])
        v2 = csr_matrix([self.row2])

        self.assertAlmostEqual(self.expected,
                               cosine_similarity(v1, v2))

class Matrix2arrayTest(NumericTestCase):
    def setUp(self):
        self.array = np.array([1,2,3])
        
    def test_matrix(self):
        a = matrix2array(mat(self.array))
        
        self.assertArrayAlmostEqual(self.array, a)

    def test_sparse_matrix(self):
        a = matrix2array(csr_matrix(self.array))

        self.assertArrayAlmostEqual(self.array, a)
