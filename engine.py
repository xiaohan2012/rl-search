class Recommender(object):
    """
    Recommendation engine that handles the recommending stuff
    """
    def recommend_keywords(self, *args, **kwargs):
        raise NotImplementedError

    def recommend_documents(self, *args, **kwargs):
        raise NotImplementedError

class QueryBasedRecommender(Recommender):
    def recommend_keywords(self, **kwargs):
        """
        """
        
    def recommend_documents(self, **kwargs):
        """
        """
        
class LinRelRecommender(Recommender): 
    @property
    def _kw2doc_m(self):
        return self.linrel_dict['kw2doc_m']

    @property
    def _doc2kw_m(self):
        return self.linrel_dict['doc2kw_m']

    @property
    def _kw_ind(self):
        return self.linrel_dict['kw_ind']

    @property
    def _kw_ind_r(self):                
        if self.__kw_ind_r is None:#cache it if not exist
            self.__kw_ind_r = dict([(ind, kw ) for kw, ind in self.linrel_dict['kw_ind'].items()])
        return self.__kw_ind_r

    @property
    def _doc_ind_r(self):
        if self.__doc_ind_r is None:#cache it if not exist
            self.__doc_ind_r = dict([(ind, doc_id ) for doc_id, ind in self.linrel_dict['doc_ind'].items()])
        return self.__doc_ind_r

    @property
    def _doc_ind(self):
        return self.linrel_dict['doc_ind']

    def __init__(self, session):
        self.__kw_ind_r = None
        self.__doc_ind_r = None
        self._session = session
        self.linrel_dict = {}
    
    def generic_recommend(self, K, fb, ids, id2ind_map,
                          mu, c):
        """
        Parameter:
        K: the whole data matrix
        fb: feedbacks, dict
        ids: object ids to be considered
        id2ind_map: mapping from object id to matrix indices
        
        Return:
        the matrix row indices as well as the scores(in descending order)
        """
        def submatrix():
            idx_in_K = [id2ind_map[id] for id in ids]
            K_sub = K[idx_in_K, :]
            return K_sub
        
        def fb_vec():
            y_kt = matrix([fb.get(id, 0) for id in ids]).T
        
        #prepare the matrices
        K_t = submatrix()
        y_t = fb_vec()
        
        scores = linrel(y_t, K_t, K, mu, c) #do the linrel
        
        sorted_scores = sorted(enumerate(np.array(scores.T).tolist()[0]), key = lambda (id, score): score, reverse = True) #sort it
        return sorted_scores    
        
    def recommend_keywords(self, top_n, mu, c, feedbacks = None ):
        """
        return a list of keyword ids
        """
        if feedbacks:#if given, update
            self._session.kw_feedback = feedbacks
        
        kw_scores = self.generic_recommend(self._kw2doc_m, self.kw_fb_hist, self._session.kw_ids, self.kw_ind,
                                           mu, c)
        
        top_kw_ids = [self.kw_ind_r[ind] for ind,_ in kw_scores[:top_n]]
        
        self._session.kw_ids = top_kw_ids #**UPDATE** feedback in session
        return top_kw_ids
        
    def recommend_documents(self):
        """
        return a list of document ids
        """
        if feedbacks:#if given, update
            self._session.doc_feedback = feedbacks
        
        doc_scores = self.generic_recommend(self._doc2kw_m, self.doc_fb_hist, self._session.doc_ids, self.doc_ind,
                                            mu, c)
        
        top_doc_ids = [self.doc_ind_r[ind] for ind,_ in doc_scores[:top_n]]
        
        self._session.doc_ids = top_doc_ids #**UPDATE** feedback in session
        return top_doc_ids
    
