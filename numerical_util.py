from scipy import linalg, mat, dot

def cosine_similarity(vec1, vec2):
    """
    vec1, vec2: csr_matrix
    """    
    vec1, vec2 = mat(vec1.todense()), mat(vec2.todense())    
    return (dot(vec1,vec2.T)/linalg.norm(vec1)/linalg.norm(vec2)).tolist()[0][0]
