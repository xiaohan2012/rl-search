from scinet3.model import Document

class Recommender(object):
    """
    Recommendation engine that handles the recommending stuff
    """        
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        
        if not Document.all_docs_loaded:
            print "loading docs from db..."
            Document.load_all_from_db()
 
    def recommend_keywords(self, *args, **kwargs):
        raise NotImplementedError

    def recommend_documents(self, *args, **kwargs):
        raise NotImplementedError
    
    def associated_keywords_from_docs(self, docs, exclude_kws = None):
        """
        get associated keywoeds from documents.

        Param:
        docs: list of Document
        exclude: set of Keyword

        Return:
        list of Keyword
        """
        if not exclude_kws:
            exclude_kws = set()
        else:
            exclude_kws = set(exclude_kws)
            
        return list(set([kw
                for doc in docs 
                for kw in doc['keywords']
                if kw not in exclude_kws]))
