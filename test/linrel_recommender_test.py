###############################
# Testing the LinRel recommender
###############################
from util import (config_doc_kw_model, get_session, NumericTestCase)

from scinet3.model import (Document, Keyword)
from scinet3.rec_engine.linrel import LinRelRecommender
from scinet3.data import FeatureMatrixAndIndexMapping

_, fmim = config_doc_kw_model()

class LinRelUtilityTest(NumericTestCase):
    def setUp(self):
        self.r = LinRelRecommender(4, 4, 
                                   1., .5, 1., .5,
                                   None, None,
                                   **fmim.__dict__)

    def test_associated_keywords_from_documents(self):
        kws = self.r.associated_keywords_from_docs(Document.get_many([1,2]))
        self.assertEqual(set(Keyword.get_many(["a", "database", "redis", "the"])),
                         set(kws))
        
        exclude_kws = [Keyword.get("redis")]
        kws = self.r.associated_keywords_from_docs(Document.get_many([1,2]), exclude_kws)
        
        self.assertEqual(set(Keyword.get_many(["a", "database", "the"])), 
                         set(kws))

    def test_filter_objs(self):
        def has_redis_filter(objs = None):
            return filter(lambda obj: Keyword.get("redis") in obj.keywords,  objs)

        def has_database_filter(objs = None):
            return filter(lambda obj: Keyword.get("database") in obj.keywords,  objs)

        self.assertEqual(list(Document.get_many([1, 7])),
                         self.r._filter_objs([has_redis_filter, has_database_filter], 
                                             objs = Document.get_many([1, 7, 8])))

    def test_submatrix_and_indexing(self):
        docs = Document.get_many([1,2])
        kws = Keyword.get_many(["python", "redis"])
        
        feature_matrix = fmim.doc2kw_m
        doc2ind = fmim.doc_ind
        kw2ind = fmim.kw_ind
        
        submatrix, doc2ind_submap, ind2doc_submap = self.r._submatrix_and_indexing(docs, kws, feature_matrix, doc2ind, kw2ind)
        
        self.assertEqual((2,2), submatrix.shape)
        self.assertEqual({1: 0, 2: 1}, doc2ind_submap)
        self.assertEqual({0: 1, 1: 2}, ind2doc_submap)
        

    def test_generic_rank(self):
        K = fmim.doc2kw_m
        fb = {1: .7,
              2: .7, 
              8: .7}
        id2ind_map = fmim.doc_ind
        ind2id_map = fmim.doc_ind_r
        mu = 1.
        c = .5

        (total_scores, 
         explt_scores, 
         explr_scores) = self.r.generic_rank(K, fb, 
                                             id2ind_map, ind2id_map,
                                             mu, c)
        
        self.assertAlmostEqual(0.5130407362992312, total_scores[6])
        self.assertAlmostEqual(0.4217401124578374, explt_scores[6])
        self.assertAlmostEqual(0.09130062384139383, explr_scores[6])

class LinRelRecommenderWithoutFilterTest(NumericTestCase):
    """
    No filter is used
    """
    def setUp(self):
        self.r = LinRelRecommender(2, 2, 
                                   1., .1, 1., .1,
                                   None, None,
                                   **fmim.__dict__)
        
        
        
        self.session = get_session()

        #giving the feedbacks
        self.session.update_kw_feedback(Keyword.get("redis"), .7)
        self.session.update_kw_feedback(Keyword.get("database"), .6)
        
        self.session.update_doc_feedback(Document.get(1), .7)
        self.session.update_doc_feedback(Document.get(2), .7)
        self.session.update_doc_feedback(Document.get(8), .7)

    def test_recommend_keywords(self):
        kws = self.r.recommend_keywords(fmim, 
                                        self.session, 4, 1, .5)
        self.assertEqual(list(Keyword.get_many(["redis", "database", "the", "mysql"])), 
                         kws)

    def test_recommend_documents(self):
        docs = self.r.recommend_documents(fmim,
                                          self.session, 4, 1, .5)
        self.assertEqual(list(Document.get_many([1,8,2,6])), 
                         docs)

    def test_recommend(self):
        docs, kws = self.r.recommend(self.session, 
                                     4, 4, 
                                     1, .5,
                                     1., .5)

        self.assertEqual(Document.get_many([1,8,2,6]), docs)
        self.assertEqual(Keyword.get_many(["redis", "database", "the", "mysql", "a", "python"]), kws)

    def test_recommend_using_default(self):
        docs, kws = self.r.recommend(self.session)

        self.assertEqual(Document.get_many([1,8]), docs)
        self.assertEqual(Keyword.get_many(["redis", "database", "a", "python"]), kws)

class LinRelRecommenderWithFilterTest(NumericTestCase):
    """
    Filters is used
    """
    def setUp(self):
                #make the fmim
        kw_filters = [self.my_kw_filter]
        doc_filters = [self.kw_count_filter, self.has_database_filter]
        
        
        self.r = LinRelRecommender(2, 2, 
                                   1.0, 0.1, 1.0, 0.1,
                                   #the default configuration
                                   kw_filters = None, doc_filters = [self.kw_count_filter, self.has_database_filter],
                                   **fmim.__dict__)
        
        self.session = get_session()
        
        self.session.update_kw_feedback(Keyword.get("redis"), .7)
        self.session.update_kw_feedback(Keyword.get("database"), .6)
        
        self.session.update_doc_feedback(Document.get(1), .7)
        self.session.update_doc_feedback(Document.get(2), .7)
        self.session.update_doc_feedback(Document.get(8), .7)

        filtered_kws = self.r._filter_objs(kw_filters, kws = Keyword.all_kws)
        filtered_docs = self.r._filter_objs(doc_filters, docs = Document.all_docs)
        
        kw2doc_submat, kw_ind_map, kw_ind_map_r = self.r._submatrix_and_indexing(filtered_kws, filtered_docs, fmim.kw2doc_m, fmim.kw_ind, fmim.doc_ind)
        doc2kw_submat, doc_ind_map, doc_ind_map_r = self.r._submatrix_and_indexing(filtered_docs, filtered_kws, fmim.doc2kw_m, fmim.doc_ind, fmim.kw_ind)
        
        self.fmim = FeatureMatrixAndIndexMapping(kw_ind_map, doc_ind_map, kw2doc_submat, doc2kw_submat, kw_ind_map_r, doc_ind_map_r)

        
    ####################
    # Filters for testing purpose
    ####################
    def my_kw_filter(self, kws):
        """is not "a" nor "the" 
        and is associated with at least three docs"""
        return filter(lambda kw: kw not in Keyword.get_many(["a", "the"]) and \
                      len(kw.docs) >= 3,
                      kws)

    def kw_count_filter(self, docs):
        """At least three keywords"""
        return filter(lambda doc: len(doc.keywords) >= 3, docs)
        
    def has_database_filter(self, docs):
        """Contains database"""
        return filter(lambda doc: Keyword.get("database") in doc.keywords, docs)

    #######################
    # Testing begins
    #######################
    def test_recommend_keywords(self):
        kws = self.r.recommend_keywords(self.fmim, 
                                        self.session,
                                        8, 1, 0.5)
        self.assertEqual(list(Keyword.get_many(["redis", "database", "python", "mysql", "tornado", "web"])), 
                         kws)

    def test_recommend_documents(self):
        docs = self.r.recommend_documents(self.fmim, 
                                          self.session,
                                          8, 1, 0.5)
        self.assertEqual(list(Document.get_many([2,1,6,7,9,5,4,3])), 
                         docs)

    def test_recommend(self):
        docs, kws = self.r.recommend(self.session,
                                     4, 4, 
                                     1, .5,
                                     1., .5,
                                     kw_filters = [self.my_kw_filter],
                                     doc_filters = [self.kw_count_filter, self.has_database_filter])
        print self.fmim.doc2kw_m.shape
        self.assertEqual(Document.get_many([2,1,6,7]), docs)
        self.assertEqual(Keyword.get_many(["redis", "database", "python", "mysql", "a", "the"]), kws)        


    def test_recommend_using_default(self):
        docs, kws = self.r.recommend(self.session)

        self.assertEqual(Document.get_many([1,2]), docs)
        self.assertEqual(Keyword.get_many(["redis", "database", "a", "the"]), kws)
