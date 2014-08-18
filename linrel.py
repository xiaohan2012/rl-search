"""
the linrel algorithm
"""
import numpy as np
from numpy.linalg import inv

from scipy.sparse import eye

def linrel(y_t, D_t, D, mu, c):
    """
    Parameter:
    y_t: the feedbacks so far
    D_t: the feature matrix for objects given feedback so far(one row per object)
    D: the feature matrix for the whole object set
    mu: parameter \mu
    c: paramter c

    Return:
    scores: dense matrix
    exploration_scores: as the name implies
    exploitation_scores: as the name implies 
    """
    print "doing linrel.."
    feature_n = D_t.shape[1] #the feature number
    
    inter_M = (D_t.T * D_t + mu * eye(feature_n, feature_n)).todense()
    a_t = D * inv(inter_M) * D_t.T 
    
    explt_scores = a_t * y_t
    explr_scores = np.sqrt(np.array(np.power(a_t, 2).sum(1))) * c / 2
    
    if hasattr(explt_scores, 'todense'): #if sparse, then to dense
        explt_scores = explt_scores.todense()
        
    scores = explt_scores + explr_scores
    return scores, explt_scores, explr_scores
