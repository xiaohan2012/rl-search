#############################
# Testing for the `filters` utility module
#############################
import unittest
from scinet3.model import (Keyword, Document)
from scinet3.filters import FilterRepository

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
        self.assertEqual([FilterRepository.filters["doc_fb_filter"], 
                          FilterRepository.filters["kw_fb_filter"]], 
                          FilterRepository.get_filters_from_str("doc_fb_filter, kw_fb_filter"))


    def test_get_filters_form_str_nonexistent(self):
        self.assertRaises(NotImplementedError, FilterRepository.get_filters_from_str, "asdflaksjdf;lasf")
        
        

from util import (config_doc_kw_model, get_session)
config_doc_kw_model()


class FiltersTest(unittest.TestCase):
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

        actual = FilterRepository.filters["kw_fb_filter"]([kw])
        expected = [kw]

        self.assertEqual(expected, actual)
        
    def test_doc_fb_filter(self):
        doc = Document.get(1)
        doc.rec_fb_from_kw(Keyword.get("redis"), 1, self.session)
        self.session.update_doc_feedback(doc, doc.fb_weighted_sum(self.session))

        actual = FilterRepository.filters["doc_fb_filter"]([doc])
        expected = []
        
        print doc.fb(self.session)
        self.assertEqual(expected, actual)                            
