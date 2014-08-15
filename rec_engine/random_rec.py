import random
from types import IntType, BooleanType

from scinet3.rec_engine.base import Recommender
from scinet3.model import Document, Keyword
from scinet3.modellist import DocumentList, KeywordList

class RandomRecommender(Recommender):

    def recommend_documents(self, n):
        """
        Randomly sample n documents
        """
        print len(Document.all_docs)
        return random.sample(Document.all_docs, n)

    def recommend_keywords(self, n, docs = None):
        """
        Randomly sample n keywords from docs, if it is given.
        Otherwise, sample n from all keywords
        """
        all_kws = set([kw
                       for doc in Document.all_docs
                       for kw in doc.keywords])
        if docs:
            kws = set([kw
                       for doc in docs
                       for kw in doc.keywords])
            try:
                return random.sample(kws, n)
            except ValueError:#not enough keywords to sample
                return kws | random.sample(all_kws - kws, n - len(kws))
                
        return random.sample(all_kws, n)

    def recommend(self, kw_n = None, doc_n = None, assoc_kws_with_docs = None):
        """
        Recommend keywords and documents

        Param:
        kw_n(optional): integer, keyword number to be recommended
        doc_n(optional): integer, doc number to be recommended
        assoc_kws_with_docs(optional): boolean, whether use recommended docs as the keyword sampling source or not 
        
        If they are not set, then use the value set during intialization.
        
        Return:
        (list of Document, list of Keyword)
        """
        docs = self.recommend_documents(doc_n or self.doc_n)
        
        # If assoc_kws_with_docs is set, then use this one, 
        # Otherwise use the one used during initialization
        assoc_or_not = (assoc_kws_with_docs
                        if (assoc_kws_with_docs is not None)
                        else self.assoc_kws_with_docs)
        
        if assoc_or_not:
            kws = self.recommend_keywords(kw_n or self.kw_n, docs)
        else:
            kws = self.recommend_keywords(kw_n or self.kw_n)
        
        return DocumentList(docs), KeywordList(kws)

    def __init__(self, kw_n, doc_n, assoc_kws_with_docs, *args, **kwargs):
        """
        Param:
        kw_n: integer, keyword number to be recommended
        doc_n: integer, doc number to be recommended
        assoc_kws_with_docs: boolean, whether use recommended docs as the keyword sampling source or not 
        """
        assert type(kw_n) is IntType, "kw_n must be integer, however is %r" %kw_n
        assert type(doc_n) is IntType, "doc_n must be integer, however is %r" %doc_n
        assert type(assoc_kws_with_docs) is BooleanType, "assoc_kws_with_docs must be boolean, however is %r" %assoc_kws_with_docs
        
        self.kw_n = kw_n
        self.doc_n = doc_n
        self.assoc_kws_with_docs = assoc_kws_with_docs
        
        super(RandomRecommender, self).__init__(*args, **kwargs)
