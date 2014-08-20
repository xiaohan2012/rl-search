#########################
# Utility filter/filter-making functions
#########################
__all__ = ["FilterRepository"]

from functools import partial
from tornado.options import options



class FilterRepository(object):
    __all__ = ["get", 
               "kw_fb_filter", 
               "doc_fb_filter"]
    
    @classmethod
    def make_threshold_filter(cls, value_getter, threshold, above = True):
        """
        @param value_getter: function that gets the specific field of value of and object
        @param threshold: when threshold to be used when filtering
        @param above: whether we desire values above the threshold or below(or equal) it

        Return a function that filters by certain threshold value
        """
        
        match = (lambda v: v > threshold) \
                if above else \
                   (lambda v: v <= threshold)
        
        def func(objs):
            return [obj for obj in objs if match(value_getter(obj))]

        return func
            
    @classmethod
    def init(cls, **kwargs):
        """
        binding parameters to the filters
        """
        # getting the parameters to be passed into filters
        session = kwargs.get("session")
        kw_fb_threshold = kwargs.get("kw_fb_threshold")
        doc_fb_threshold = kwargs.get("doc_fb_threshold")
        
        def fb_getter(o):
            fb = o.fb(session)
            return fb

        # creating the actual filters
        cls.filters = {
            "kw_fb_filter": cls.make_threshold_filter(fb_getter, kw_fb_threshold),
            "doc_fb_filter": cls.make_threshold_filter(fb_getter, doc_fb_threshold),
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
