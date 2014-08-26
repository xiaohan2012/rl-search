import unittest
import torndb

from scinet3.data import load_fmim

class FmimGenerationTest(unittest.TestCase):
    """
    Test the generation of feature matrix and index mapping
    """
    def setUp(self):
        db = 'scinet3'
        table = 'test'
        
        self.conn = torndb.Connection("ugluk:3306", db, 'hxiao', 'xh24206688')

        self.fmim = load_fmim(self.conn, table, "keywords", tfidf = True, refresh = True)
        
    def test_feature_matrix(self):
        self.assertEqual(self.fmim.kw2doc_m.shape, (8, 10))
        self.assertEqual(self.fmim.doc2kw_m.shape, (10, 8))
        
    def test_index_mapping(self):
        kws = [u'a', u'database', u'mysql', u'python', u'redis', u'the', u'tornado', u'web']
        for ind, kw in enumerate(kws):
            self.assertEqual(self.fmim.kw_ind[kw], ind)
            
        for doc_id in xrange(1, 11):
            self.assertEqual(self.fmim.doc_ind[doc_id], doc_id - 1)

    def test_inverse_index_mapping(self):
        kws = [u'a', u'database', u'mysql', u'python', u'redis', u'the', u'tornado', u'web']
        for ind, kw in enumerate(kws):
            self.assertEqual(self.fmim.kw_ind_r[ind], kw)
            
        for doc_id in xrange(1, 11):
            self.assertEqual(self.fmim.doc_ind_r[doc_id-1], doc_id)

    def tearDown(self):
        self.conn.close()
