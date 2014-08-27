#############################
# Testing for the `filters` utility module
#############################
import unittest
from scinet3.model import (Keyword, Document)
from scinet3.filters import (FilterRepository, 
                             fb_threshold_filter, 
                             kw_fb_threshold_filter,
                             doc_fb_threshold_filter)

from util import (config_doc_kw_model, get_session)
config_doc_kw_model()
Document.load_all_from_db()

class FiltersTest(unittest.TestCase):
    def setUp(self):
        self.session = get_session()


    def test_fb_threshold_filter(self):
        actual = fb_threshold_filter(.1, [("0.1", .1), (".2", .2), (".01", .01)])
        expected = ["0.1", ".2"]
        self.assertEqual(actual, expected)

    def test_kw_fb_threshold_filter_with_prefiltering(self):
        #change the feedback
        self.session.update_kw_feedback(Keyword.get("python"), .2)
        self.session.update_kw_feedback(Keyword.get("a"), .0999999)
        
        actual = kw_fb_threshold_filter(0.1, self.session, 
                                        with_fb = True)
        expected = Keyword.get_many(["python"])

        self.assertEqual(expected, actual)
        
    def test_kw_fb_threshold_filter(self):
        #change the feedback
        self.session.update_kw_feedback(Keyword.get("python"), .2)
        self.session.update_kw_feedback(Keyword.get("a"), .0999999)
        
        actual = kw_fb_threshold_filter(0.1, self.session, 
                                        kws = Keyword.all_kws, with_fb = False)
        expected = Keyword.get_many(["python"])

        self.assertEqual(expected, actual)
        
    def test_doc_fb_threshold_filter_with_prefiltering(self):
        #change the feedback
        self.session.update_doc_feedback(Document.get(1), .2)
        self.session.update_doc_feedback(Document.get(2), .0999999)
        
        actual = doc_fb_threshold_filter(0.1, self.session, 
                                         with_fb = True)
        expected = Document.get_many([1])

        self.assertEqual(expected, actual)

    def test_doc_fb_threshold_filter(self):
        #change the feedback
        self.session.update_doc_feedback(Document.get(1), .2)
        self.session.update_doc_feedback(Document.get(2), .0999999)
        
        actual = doc_fb_threshold_filter(0.1, self.session, 
                                         docs = Document.all_docs, with_fb = False)
        expected = Document.get_many([1])

        self.assertEqual(expected, actual)
        
class FiltersGetterTest(unittest.TestCase):
    """
    Whether the filters can be accessed successfully
    """
    def setUp(self):
        FilterRepository.init(session = None, 
                              kw_fb_threshold = 1, 
                              kw_fb_from_docs_threshold = 1, 
                              doc_fb_threshold = 1,
                              doc_fb_from_kws_threshold = 1)

    def test_get_filters_from_str_None_case(self):
        self.assertEqual(None, FilterRepository.get_filters_from_str(None))

    def test_get_filters_from_str_normal_case(self):
        self.assertEqual([FilterRepository.filters["doc_fb"], 
                          FilterRepository.filters["kw_fb"]], 
                          FilterRepository.get_filters_from_str("doc_fb, kw_fb"))


    def test_get_filters_form_str_nonexistent(self):
        self.assertRaises(NotImplementedError, FilterRepository.get_filters_from_str, "asdflaksjdf;lasf")



class FilterRepositoryTest(unittest.TestCase):
    """
    Whether the filters can be accessed successfully
    """
    def setUp(self):
        self.session = get_session()
        FilterRepository.init(session = self.session, 
                              kw_fb_threshold = .29, 
                              doc_fb_threshold = .37,
        )

        
    def test_kw_fb_filter(self):
        kw = Keyword.get("redis")
        kw.rec_fb_from_doc(Document.get(1), 1, self.session)
        self.session.add_doc_recom_list(Document.get_many([1, 2, 6]))
        self.session.update_kw_feedback(kw, kw.fb_weighted_sum(self.session))

        actual = FilterRepository.filters["kw_fb"]([kw])
        expected = Keyword.get_many(["redis"])

        self.assertEqual(expected, actual)
        
    def test_doc_fb_filter(self):
        doc = Document.get(1)
        doc.rec_fb_from_kw(Keyword.get("redis"), 1, self.session)
        self.session.update_doc_feedback(doc, doc.fb_weighted_sum(self.session))
        
        print "doc.fb(self.session)=", doc.fb(self.session)
        actual = FilterRepository.filters["doc_fb"]([doc])
        expected = Document.get_many([])
        
        print doc.fb(self.session)
        self.assertEqual(expected, actual)                            
