from functools import partial

def make_threshold_filter(value_getter, threshold, above = True):
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

make_fb_filter = partial(make_threshold_filter, 
                         value_getter = (lambda o: getattr(o, 'fb')))
make_fb_from_kws_filter = partial(make_threshold_filter, 
                                  value_getter = (lambda o: getattr(o, 'fb_from_kws')))
make_fb_from_docs_filter = partial(make_threshold_filter, 
                                  value_getter = (lambda o: getattr(o, 'fb_from_docs')))

def test():
    from collections import namedtuple
    Keyword = namedtuple('Keyword', 'body fb')
    kws = [Keyword('kw1', 1), Keyword('kw2', 0.2), Keyword('kw3', 0.5)]
    
    filter_func = make_fb_filter(threshold=0.2)
    
    print filter_func(kws)
    
if __name__ == "__main__":
    test()
