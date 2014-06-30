"""
the linrel algorithm
"""
import numpy as np
from scipy.sparse import eye, csr_matrix
from scipy.sparse.linalg import inv

def linrel(y_t, D_t, D, mu, c):
    """
    Parameter:
    y_t: the feedbacks so far
    D_t: the feature matrix for objects given feedback so far(one row per object)
    D: the feature matrix for the whole object set
    mu: parameter \mu
    c: paramter c

    Return:
    scores: csr sparse column vector containing the scores
    exploration_scores: as the name implies
    exploitation_scores: as the name implies 
    """
    feature_n = D_t.shape[1] #the feature number
    a_t = D * inv(D_t.T * D_t + mu * eye(feature_n, feature_n)) * D_t.T
    
    #tricky way to do the power 2 operation
    #http://stackoverflow.com/questions/6431557/element-wise-power-of-scipy-sparse-matrix
    a_t_2powered = a_t.copy()

    a_t_2powered.data **= 2
    print 'after'
    print np.sqrt(np.array(a_t_2powered.sum(1)))
    
    exploration_scores = np.sqrt(np.array(a_t_2powered.sum(1))) * c / 2
    print '**a_t**'
    print type(a_t), a_t
    print '**y_t**'
    print type(y_t), y_t, y_t.shape
    exploitation_scores = np.array(a_t * y_t)
    scores = exploration_scores + exploitation_scores

    print 'explr scores'
    print exploration_scores
    print 'explt scores'
    print exploitation_scores

    return scores, exploration_scores, exploitation_scores
