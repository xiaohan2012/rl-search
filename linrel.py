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
    
    explt_scores = a_t * y_t
    explr_scores = np.sqrt(np.array(a_t_2powered.sum(1))) * c / 2
    
    if hasattr(explt_scores, 'todense'): #if sparse, then to dense
        explt_scores = explt_scores.todense()
        
    scores = explt_scores + explr_scores
    return scores, explt_scores, explr_scores

if __name__ == "__main__":
    D = csr_matrix(np.array([[1, 0, 0, 0, 1, 1],
                             [0, 1, 1, 0, 0, 0], 
                             [1, 0, 0, 1, 0, 0],#we favor this one
                             [1, 0, 0, 0, 1, 1],
                             [1, 1, 0, 1, 0, 0],#this is good
                             [0, 1, 1, 0, 0, 0],
                             [1, 1, 1, 0, 0, 0],#this is surprise
                         ]))
    D_t = D[0:3,:]
    mu = 1
    c = .2
    y_t = csr_matrix([[.3], [.3], [.7]])

    scores, explr_scores, explt_scores = linrel(y_t, D_t, D, mu, c)
    
    print scores
    print '='
    print explr_scores
    print '+'
    print explt_scores
