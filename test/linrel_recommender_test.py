###############################
# Testing the LinRel recommender
###############################
from util import (config_doc_kw_model, get_session, NumericTestCase)

from scinet3.model import (Document, Keyword)

from scinet3.rec_engine.linrel import LinRelRecommender

_, fmim = config_doc_kw_model()

class LinRelUtilityTest(NumericTestCase):
    def setUp(self):
        self.r = LinRelRecommender(4, 4, 
                                   1., .5, 1., .5,
                                   None, None,
                                   **fmim)

    def test_associated_keywords_from_documents(self):
        kws = self.r.associated_keywords_from_docs(Document.get_many([1,2]))
        self.assertEqual(set(Keyword.get_many(["a", "database", "redis", "the"])),
                         set(kws))
        
        exclude_kws = [Keyword.get("redis")]
        kws = self.r.associated_keywords_from_docs(Document.get_many([1,2]), exclude_kws)
        
        self.assertEqual(set(Keyword.get_many(["a", "database", "the"])), 
                         set(kws))

    def test_filter_objs(self):
        def has_redis_filter(objs):
            return filter(lambda obj: Keyword.get("redis") in obj.keywords,  objs)

        def has_database_filter(objs):
            return filter(lambda obj: Keyword.get("database") in obj.keywords,  objs)

        self.assertEqual(list(Document.get_many([1, 7])),
                         self.r._filter_objs(Document.get_many([1, 7, 8]),
                                             [has_redis_filter, has_database_filter])
        )

    def test_submatrix_and_indexing(self):
        doc_ids = [1,2]
        feature_matrix = fmim["doc2kw_m"] 
        doc2ind_m = fmim["doc_ind"] 
        
        submatrix, doc2ind_submap, ind2doc_submap = self.r._submatrix_and_indexing(doc_ids, feature_matrix, doc2ind_m)
        
        self.assertEqual((2,8), submatrix.shape)
        self.assertEqual({1: 0, 2: 1}, doc2ind_submap)
        self.assertEqual({0: 1, 1: 2}, ind2doc_submap)
        

    def test_generic_rank(self):
        K = fmim["doc2kw_m"]
        fb = {1: .7,
              2: .7, 
              8: .7}
        id2ind_map = fmim["doc_ind"]
        ind2id_map = fmim["doc_ind_r"]
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
                                   **fmim)
        
        
        
        self.session = get_session()

        #giving the feedbacks
        self.session.update_kw_feedback(Keyword.get("redis"), .7)
        self.session.update_kw_feedback(Keyword.get("database"), .6)
        
        self.session.update_doc_feedback(Document.get(1), .7)
        self.session.update_doc_feedback(Document.get(2), .7)
        self.session.update_doc_feedback(Document.get(8), .7)

    def test_recommend_keywords(self):
        kws = self.r.recommend_keywords(self.session, 4, 1, .5)
        self.assertEqual(list(Keyword.get_many(["redis", "database", "the", "mysql"])), 
                         kws)

    def test_recommend_documents(self):
        docs = self.r.recommend_documents(self.session, 4, 1, .5)
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
        self.r = LinRelRecommender(2, 2, 
                                   1., .1, 1., .1,
                                   None, None,
                                   **fmim)
        
        self.session = get_session()
        
        self.session.update_kw_feedback(Keyword.get("redis"), .7)
        self.session.update_kw_feedback(Keyword.get("database"), .6)
        
        self.session.update_doc_feedback(Document.get(1), .7)
        self.session.update_doc_feedback(Document.get(2), .7)
        self.session.update_doc_feedback(Document.get(8), .7)

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
        kws = self.r.recommend_keywords(self.session,
                                        8, 1, 0.5, 
                                        filters = [self.my_kw_filter])
        print Keyword.get("python")
        print Keyword.get("python").docs
        self.assertEqual(list(Keyword.get_many(["redis", "database", "python", "web"])), 
                         kws)

    def test_recommend_documents(self):
        docs = self.r.recommend_documents(self.session,
                                          8, 1, 0.5, 
                                          filters = [self.kw_count_filter, self.has_database_filter])

        self.assertEqual(list(Document.get_many([1,2,6,9,7,3,4,5])), 
                         docs)

    def test_recommend(self):
        docs, kws = self.r.recommend(self.session,
                                     4, 4, 
                                     1, .5,
                                     1., .5,
                                     kw_filters = [self.my_kw_filter],
                                     doc_filters = [self.kw_count_filter, self.has_database_filter])
        self.assertEqual(Document.get_many([1,2,6,9]), docs)
        self.assertEqual(Keyword.get_many(["redis", "database", "python", "web", "a", "the"]), kws)        


    def test_recommend_using_default(self):
        docs, kws = self.r.recommend(self.session)

        self.assertEqual(Document.get_many([1,8]), docs)
        self.assertEqual(Keyword.get_many(["redis", "database", "a", "python"]), kws)
