import random

from scinet3.rec_engine.base import Recommender
from scinet3.model import Document, Keyword

class RandomRecommender(Recommender):
    def recommend_documents(self, n):
        """
        Randomly sample n documents
        """
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

    def recommend(self, kw_n, doc_n, assoc_kws_with_docs):
        """
        Recommend keywords and documents

        Param:
        kw_n: integer, keyword number to be recommended
        doc_n: integer, doc number to be recommended
        assoc_kws_with_docs: whether use recommended docs as the keyword sampling source or not 

        Return:
        (list of Document, list of Keyword)
        """
        docs = self.recommend_documents(doc_n)
        
        if assoc_kws_with_docs:
            kws = self.recommend_keywords(kw_n, docs)
        else:
            kws = self.recommend_keywords(kw_n)
        
        return docs, kws
