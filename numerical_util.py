import numpy as np
from scipy import (linalg, mat, dot)
from scipy.sparse import isspmatrix

def cosine_similarity(vec1, vec2):
    """
    Calculate the cosine similarity between vec1 and vec2
    
    vec1, vec2: list, np.array, scipy.mat or scipy.sparse.csr_matrix|csc_matrix...
    
    Return:
    float
    """    
    
    if isspmatrix(vec1):
        vec1 = vec1.todense()
        
    if isspmatrix(vec2):
        vec2 = vec2.todense()

    vec1, vec2 = mat(vec1), mat(vec2)    

    return (dot(vec1,vec2.T)/linalg.norm(vec1)/linalg.norm(vec2)).tolist()[0][0]


def matrix2array(M):
    """
    1xN matrix to array. 
    
    In other words:
    
    [[1,2,3]] => [1,2,3]
    """
    if isspmatrix(M):
        M = M.todense()
    return np.squeeze(np.asarray(M))
    
