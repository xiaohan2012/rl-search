import numpy as np
import json
import torndb
import random
from numpy import matrix

from util import iter_summary
from model import Document, Keyword, config as config_model

from linrel import linrel
from data import KwDocData

from pprint import pprint

random.seed(123456)

class Recommender(object):
    """
    Recommendation engine that handles the recommending stuff
    """
    @classmethod
    def init(cls, conn, table, **kwargs):
        config_model(conn, table, kwargs)        

        for k, v in kwargs.items():
            setattr(cls, k, v)
        print "loading docs from db..."
        Document.load_all_from_db()
        
    def recommend_keywords(self, *args, **kwargs):
        raise NotImplementedError

    def recommend_documents(self, *args, **kwargs):
        raise NotImplementedError

class QueryBasedRecommender(Recommender):
    """
    query-based IR system 
    """
    def _word_vec(self, words):
        """
        given the word strings return the word binary vector
        """
        kw_total_num = len(self.kw_ind.keys())
        word_vec = np.zeros((kw_total_num, 1))
        for word in words:
            word_vec[self.kw_ind[word], 0] = 1
        return matrix(word_vec)

    def associated_documents_by_keywords(self, keywords, n):
         """
         sample n documents from all documents that contain any of the keywords
         """
         #get all doc ids of which the document contains any of the keywords
         kw_ids = [kw['id'] for kw in keywords]
         word_vec = self._word_vec(kw_ids)
         row_idx, _ = np.nonzero(self.doc2kw_m * word_vec)
         doc_ids= [self.doc_ind_r[row_id] 
                   for row_id in row_idx.tolist()[0]]

         #sample it
         return [Document.get(doc_id)
                 for doc_id in random.sample(doc_ids, n)]
         
    def recommend_keywords(self, rec_docs, kw_num, kw_num_from_docs):
        """
        Given the recommended documents, rec_docs, as well as the number of keywords, kw_num_from_docs to be sampled from the documents, 
        return the sampled keywords from recommended documents and sampled keywords from documents associated with the recommended documents by keywords(sounds complicated..)

        Param:
        rec_docs: the recommended documents
        kw_num: the number of keywords to be recommended
        kw_num_from_docs: number of keywords to be sampled from the docs
        weighted: using TfIdf weight for the above sampling or not(**NOT IMPLEMENTED BY NOW**))

        Return:
        keywords from docs, associated keywords
        """
        if kw_num_from_docs > kw_num:
            raise ValueError('kw_num_from_docs should be less or equal to kw_num')
            
        #sample kw_num_from_docs from the keywords in the documents, 
        all_kws_from_docs = set([kw 
                                 for doc in rec_docs 
                                 for kw in doc['keywords']])
        
        if len(all_kws_from_docs) <= kw_num_from_docs:
            kws_from_docs = list(all_kws_from_docs)
        else:
            kws_from_docs = random.sample(list(all_kws_from_docs), kw_num_from_docs)

        #get all the documents that have keywords in common with the documents being recommended
        word_vec = self._word_vec([kw.id for kw in kws_from_docs])
        row_idx, _ = np.nonzero(self.doc2kw_m * word_vec)

        assoc_docs = [Document.get(self.doc_ind_r[idx])
                      for idx in row_idx.tolist()[0]]
                
        keywords = set([kw for doc in assoc_docs for kw in doc['keywords']])
        remaining_keywords = keywords - set(kws_from_docs)
        
        #sample kw_num - kw_num_from_docs keywords from the above document set
        if len(remaining_keywords) <= kw_num - kw_num_from_docs: #not enough population to sample from..
            print 'Not enouth remaining keywords.. use them all'
            extra_keywords = list(remaining_keywords)
        else:
            extra_keywords = random.sample(list(remaining_keywords), kw_num - kw_num_from_docs)
        
        #return the joined set of keywordsn
        kws = []
        for kw in kws_from_docs:
            kw['recommended'] = True
            kws.append(kw)

        for kw in extra_keywords:
            kw['recommended'] = False
            kws.append(kw)            

        return kws
        
    def recommend_documents(self, query, top_n):
        """
        Given the query, 
        Return the top_n related documents as well as the scores
        """
        query_words = query.strip().split()
        #prepare the query word binary column vector        
        word_vec = self._word_vec(query_words)
        
        #get the scores for documents and scort it
        scores = self.doc2kw_m * word_vec
        sorted_scores = sorted(enumerate(np.array(scores.T).tolist()[0]), key = lambda (id, score): score, reverse = True)
        
        #get the top_n documents 
        docs = []
        for ind, score in sorted_scores[:top_n]:
            doc_id = self.doc_ind_r[ind]
            doc = Document.get(doc_id)
            doc['score'] = score
            docs.append(doc)

        return docs
        

def test_query(query):
    from data import kw2doc_matrix    
    table = 'test'
    d_ = kw2doc_matrix(table)
    
    db = torndb.Connection("%s:%s" % ('ugluk', 3306), 'scinet3', 'hxiao', 'xh24206688')
    
    r = QueryBasedRecommender(db, table, **d_)
    docs = r.recommend_documents(query, 2)
    
    pprint(docs)

    kws = r.recommend_keywords(docs, 4, 2)
    pprint(kws)
    

class LinRelRecommender(Recommender): 
    def __init__(self, session, *args, **kwargs):
        """
        session: the session object used to retrieve session data
        args: the matrix and index mapping stuff
        """

        self._session = session
        
        super(LinRelRecommender, self).__init__(*args, **kwargs)
        
    def generic_recommend(self, K, fb, id2ind_map,
                          mu, c):
        """
        Parameter:
        K: the whole data matrix
        fb: feedbacks, dict
        id2ind_map: mapping from object id to matrix indices
        
        Return:
        the matrix row indices as well as the scores(in descending order)
        and the sorted decomposition of the scores
        """
        ids = fb.keys()
        def submatrix():
            idx_in_K = [id2ind_map[id] for id in ids]
            K_sub = K[idx_in_K, :]
            return K_sub
        
        def fb_vec():
            y_t = matrix([fb.get(id, 0) for id in ids]).T
            return y_t
        
        #prepare the matrices
        K_t = submatrix()
        y_t = fb_vec()

        scores, exploitation_scores, exploration_scores  = linrel(y_t, K_t, K, mu, c) #do the linrel
        
        def add_index_and_sort(matrix):
            """add the row index information and sort """
            return sorted(enumerate(np.array(matrix.T).tolist()[0]), key = lambda (id, score): score, reverse = True)

        sorted_scores =  add_index_and_sort(scores)
        sorted_exploitation_scores =  add_index_and_sort(exploitation_scores)
        sorted_exploration_scores =  add_index_and_sort(exploration_scores)
        
        
        return sorted_scores, sorted_exploitation_scores, sorted_exploration_scores
    
    def _filter_objs(self, objs, filters):
        """
        we shall do some filtering here:
        select only the objects which passes at least one of the filters

        return:
        the filtered list of objects
        """
        sel_objs = set()
        for filter_func in filters:
            sel_objs |= set(filter_func(objs))
            
        return list(sel_objs)
        
    def _submatrix_and_indexing(self, objs, obj_feature_matrix, obj2ind_map):
        """
        given the objects, the whole datamatrix and the original obj2ind mapping
        return:
        - the feature matrix concerning only the objects
        - the object to matrix index mapping
        - the inverse index to object mapping
        """
        obj_indx = [obj2ind_map[obj] for obj in objs]
        
        #get the sub matrix
        submatrix = obj_feature_matrix[obj_indx, :]
        obj2ind_submap = dict([(obj, ind) for obj, ind in zip(objs, xrange(len(objs)))])
        ind2obj_submap = dict([(ind, obj) for obj, ind in zip(objs, xrange(len(objs)))])

        return submatrix, obj2ind_submap, ind2obj_submap
            
    def recommend_keywords(self, top_n, mu, c, filters, sampler=None, feedbacks = None):
        """
        filters: a list of filtering function applied to the keywords before doing the LinRel computation, a keyword satisfying any of the filters will be considered candidate.
        
        return a list of keyword ids as well as their scores
        """
        if feedbacks:#if given, update
            self._session.kw_feedbacks = feedbacks
            self._session.kw_fb_hist = feedbacks
        else:
            self._session.kw_fb_hist = {}        
        
        #do some filtering and form the corresponding sub matrix
        filtered_kws = self._filter_objs(Keyword.all_kws, filters); filtered_kw_ids = [kw.id for kw in filtered_kws]
        
        kw2doc_submat, kw_ind_map, kw_ind_map_r = self._submatrix_and_indexing(filtered_kw_ids, self.kw2doc_m, self.kw_ind)
        fbs = dict([(kw.id, kw.fb(self._session)) for kw in filtered_kws])
        
        if sampler:
            pass#do some sampling here

        print "kw2doc_submat=:\n", kw2doc_submat
        print "kw_ind_map=:\n", kw_ind_map
        
        ind_with_scores, ind_with_explt_scores, ind_with_explr_scores = self.generic_recommend(kw2doc_submat, fbs, kw_ind_map,
                                                                                               mu, c)
        
        id_with_scores = [(kw_ind_map_r[ind], score) for ind,score in ind_with_scores]
        id_with_explr_scores = [(kw_ind_map_r[ind], score) for ind,score in ind_with_explr_scores]
        id_with_explt_scores = [(kw_ind_map_r[ind], score) for ind,score in ind_with_explt_scores]
                
        # save them to history
        self._session.kw_score_hist = dict(id_with_scores)
        self._session.kw_explr_score_hist = dict(id_with_explr_scores)
        self._session.kw_explt_score_hist = dict(id_with_explt_scores) 
        
        #prepare the documents
        top_ids_with_scores = [(kw_ind_map_r[ind], score) for ind,score in ind_with_scores[:top_n]]
        
        kws = []
        for kw_id, score in top_ids_with_scores:
            kw = Keyword.get(kw_id)
            kw['score'] = score
            kws.append(kw)
            
        return kws
        
    def recommend_documents(self, top_n, mu, c, filters, sampler = None, feedbacks = None):
        """
        return a list of document ids as well as the scores
        """
        if feedbacks:#if given, update
            self._session.doc_feedbacks = feedbacks
            self._session.doc_fb_hist = feedbacks
        else:
            self._session.doc_fb_hist = {}

        #do some filtering and form the corresponding sub matrix
        filtered_docs = self._filter_objs(Document.all_docs, filters); filtered_doc_ids = [doc.id for doc in filtered_docs]
        
        doc2kw_submat, doc_ind_map, doc_ind_map_r = self._submatrix_and_indexing(filtered_doc_ids, self.doc2kw_m, self.doc_ind)
        fbs = dict([(doc.id, doc.fb(self._session)) for doc in filtered_docs])

        if sampler:
            pass#do some sampling here

        ind_with_scores, ind_with_explt_scores, ind_with_explr_scores = self.generic_recommend(doc2kw_submat, fbs, doc_ind_map,
                                                                                               mu, c)        
        # the history also
        id_with_scores = [(doc_ind_map_r[ind], score) for ind,score in ind_with_scores]
        id_with_explr_scores = [(doc_ind_map_r[ind], score) for ind,score in ind_with_explr_scores]
        id_with_explt_scores = [(doc_ind_map_r[ind], score) for ind,score in ind_with_explt_scores]
        
        self._session.doc_score_hist = dict(id_with_scores)
        self._session.doc_explr_score_hist = dict(id_with_explr_scores)
        self._session.doc_explt_score_hist = dict(id_with_explt_scores) 
        
        top_ids_with_scores = [(doc_ind_map_r[ind], score) for ind, score in ind_with_scores[:top_n]]

        docs = []
        for doc_id, score in top_ids_with_scores:
            doc = Document.get(doc_id)
            doc['score'] = score

            docs.append(doc)

        return docs
            
def main():
    import  redis
    from session import RedisRecommendationSessionHandler
    from data import kw2doc_matrix
    top_n = 2
    mu = 1
    c = 1
    
    db = 'archive'
    table = 'archive'
    db = torndb.Connection("%s:%s" % ('ugluk', 3306), db, 'hxiao', 'xh24206688')    

    redis_conn = redis.StrictRedis(host='ugluk', port='6379', db=db)
    #init session
    s = RedisRecommendationSessionHandler.get_session(redis_conn)
    
    d_ = kw2doc_matrix(db, table)
    linrel_r = LinRelRecommender(s, db, table, d_.kw_ind, d_.doc_ind, d_.kw2doc_m, d_.doc2kw_m)
    query_r = QueryBasedRecommender(db, table, d_.kw_ind, d_.doc_ind, d_.kw2doc_m, d_.doc2kw_m)
    
    kw_dict = dict([(kw, kw) for kw in d_.kw_ind.keys()]) #kw_id -> kw
    doc_dict = dict([(doc_id, query_r._get_doc(doc_id)) for doc_id in d_.doc_ind.keys()]) #doc_id -> doc

    query = raw_input('Your query:')
    docs = query_r.recommend_documents(query, top_n)
    kws = query_r.recommend_keywords(docs, 4, 2)
    
    extra_docs = query_r.associated_documents_by_keywords([kw #only those extra keywords
                                                           for kw in kws 
                                                           if not kw['recommended']], 
                                                          top_n)
    print "Recommended documents:"
    for doc in docs:
        print doc

    print "Extra documents:"
    for doc in extra_docs:
        print doc
        
    print "Recommended keywords:"
    for kw in kws:
        print kw,
    print 
                
    while True:
        kws_str = raw_input('Type in the keywords you like, separated by comma\n')
        liked_kws = kws_str.split(',')
        
        docids_str = raw_input('Type in the document ids you like, separated by comma\n')
        liked_doc_ids = docids_str.split(',')
        
        kws = linrel_r.recommend_keywords(top_n, mu, c, kw_feedbacks)
        docs = linrel_r.recommend_documents(top_n, mu, c, doc_feedbacks)
        
        #print the summary
        iter_summary(kw_dict = kw_dict,
                     doc_dict = doc_dict,
                     **s.data)
        
        print "Recommended documents:"
        for doc in docs:
            print doc

        print "Recommended keywords:"
        for kw in kws:
            print kw,
        print 
    
if __name__ == "__main__":
    #test_query('python redis')
    # test_linrel()
    main()
