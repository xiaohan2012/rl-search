#########################
# Utility filter/filter-making functions
#########################
__all__ = ["FilterRepository"]
import numpy as np
from functools import partial
from tornado.options import options
from scinet3.modellist import (KeywordList, DocumentList)

def fb_threshold_filter(threshold, obj2fb_list):
    """
    Filter objects by feedback value
    
    threshold: float, the threshold value
    obj2fb_list: list of (Model, float), pairs of Model  and its feedback

    Return:
    ModelList
    """
    if len(obj2fb_list) == 0:
        return []

    objs, fbs = zip(*obj2fb_list)
    #make the vector
    vec = np.array(fbs)
    
    #make the mapping
    obj_ind_r =  dict([(_id, obj) for _id, obj in enumerate(objs)])
    
    #filter by threshold, get col indices
    idx = np.where(vec >= threshold)[0]

    #get the keywords
    return [obj_ind_r[ind] 
            for ind in idx.tolist()]


def kw_fb_threshold_filter(threshold, session, kws = None,  with_fb = True):
    """
    Filter keywords by feedback value
    
    threshold: float, the threshold value
    session: Session,
    kws: KeywordList, the keywords to be considered
    with_fb: Boolean, if True, then those without feedback values are filtered in advance(much more efficient)

    Return:
    KeywordList
    """

    if with_fb: #do the filtering beforehand
        kw2fb_list = session.kw_feedbacks.items()
    else:
        assert kws is not None, "kws should't be None"
        kw2fb_list = [(kw, kw.fb(session)) 
                      for kw in kws]
    
    return KeywordList(fb_threshold_filter(threshold, kw2fb_list))


def doc_fb_threshold_filter(threshold, session, docs = None,  with_fb = True):
    """
    Filter documents by feedback value
    
    threshold: float, the threshold value
    session: Session,
    docs: DocumentList, the documents to be considered
    with_fb: Boolean, if True, then those without feedback values are filtered in advance(much more efficient)

    Return:
    DocumentList
    """

    if with_fb: #do the filtering beforehand
        doc2fb_list = session.doc_feedbacks.items()
    else:
        assert docs is not None, "docs should't be None"
        doc2fb_list = [(doc, doc.fb(session)) 
                       for doc in docs]
        print "doc2fb_list", doc2fb_list
    return DocumentList(fb_threshold_filter(threshold, doc2fb_list))


class FilterRepository(object):
    __all__ = ["get", 
               "kw_fb_filter", 
               "doc_fb_filter"]
    
    @classmethod
    def init(cls, **kwargs):
        """
        binding parameters to the filters
        """
        # getting the parameters to be passed into filters
        session = kwargs.get("session")
        kw_fb_threshold = kwargs.get("kw_fb_threshold", 0)
        doc_fb_threshold = kwargs.get("doc_fb_threshold", 0)

        with_fb = kwargs.get("with_fb", 0)
        
        cls.filters = {"kw_fb": partial(kw_fb_threshold_filter, kw_fb_threshold, session, with_fb = with_fb),
                       "doc_fb": partial(doc_fb_threshold_filter, doc_fb_threshold, session, with_fb = with_fb)
        }
    
    @classmethod
    def get(cls, filter_id):
        try:
            return cls.filters[filter_id]
        except KeyError:
            raise NotImplementedError("%s is not in the repository --||" %filter_id)
            
    @classmethod
    def get_filters_from_str(cls, s):
        """
        Get a list of filters from configuration string
        
        Param:
        --------
        s: string|None: the filter string

        Return:
        ---------
        list of functions:
        """
        if not s:
            return None
        else:
            filter_ids = map(lambda id_str: id_str.strip(), 
                             s.split(","))
            
            return [cls.get(filter_id) 
                    for filter_id in filter_ids]
