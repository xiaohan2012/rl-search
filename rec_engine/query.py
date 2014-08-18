import random

from types import IntType, ListType
import numpy as np
from numpy import matrix

from scinet3.model import (Document, Keyword)
from scinet3.modellist import (KeywordList, DocumentList)
from scinet3.linrel import linrel
from scinet3.rec_engine.base import Recommender

from scinet3.util.numerical import matrix2array

random.seed(123456)

class QueryBasedRecommender(Recommender):
    """
    query-based IR system 
    """
    def _word_vec(self, words):
        """
        given the word strings return the word binary vector
        
        Params:
        ------
        words: list of string
        
        Return:
        -------
        matrix, the binary vector represeting the presence of word speficifed by words
        """

        kw_total_num = len(self.kw_ind.keys())
        word_vec = np.zeros((kw_total_num, 1))
        for word in words:
            try:
                word_vec[self.kw_ind[word], 0] = 1
            except KeyError: #no existing word
                pass
        return matrix(word_vec)

    def _doc_ids_that_contain_keywords(self, kw_ids):
        """
        Param:
        -------
        kw_ids: list of string, keywords string list
        
        Return:
        -------
        list of integet, ids of documents that contain any of the keywords in kw_strs
        """
        word_vec = self._word_vec(kw_ids)
        row_idx, _ = np.nonzero(self.doc2kw_m * word_vec)
        return [self.doc_ind_r[row_id] 
                for row_id in matrix2array(row_idx)]
        
    def sample_documents_associated_with_keywords(self, keywords, n):
         """
         sample n documents from all documents that contain any of the keywords
         """
         assert type(keywords) in (KeywordList, ListType) , "keywords should be KeywordList, but is %r" %(keywords)
         
         #get all doc ids of which the document contains any of the keywords
         doc_ids = self._doc_ids_that_contain_keywords([kw.id for kw in keywords])
         
         #sample it
         try:
             return Document.get_many(random.sample(doc_ids, n))
         except ValueError: #sample size larger than population
             return Document.get_many(doc_ids)
         
    def recommend_keywords(self, rec_docs, kw_num, kw_num_from_docs, query_keywords = []):
        """
        Given the recommended documents, rec_docs, as well as the number of keywords, kw_num_from_docs to be sampled from rec_docs, return the sampled keywords from:
        1. recommended documents 
        2. documents associated with the recommended documents by keywords

        Param:
        --------
        query_keywords: KeywordList, the keywords in query, which should be contained in the returned keywordlist
        rec_docs: list of Document, the recommended documents
        kw_num: integer, the number of keywords to be recommended
        kw_num_from_docs: integer, number of keywords to be sampled from the rec_docs
        weighted: boolean, using TfIdf weight for the above sampling or not(**NOT IMPLEMENTED BY NOW**))

        Return:
        --------
        KeywordList
        """
        # subtract the quota accordingly 
        # as we are including the query keywords
        kw_num -= len(query_keywords)
        kw_num_from_docs -= len(query_keywords)
        
        if kw_num_from_docs > kw_num:
            raise ValueError('kw_num_from_docs should be less or equal to kw_num')
            
        # sample kw_num_from_docs from the keywords in the documents, 
        all_kws_from_docs = [kw 
                             for doc in rec_docs 
                             for kw in doc.keywords]
        
        try:
            kws_from_docs = query_keywords + random.sample(all_kws_from_docs, kw_num_from_docs)
        except ValueError: # sample larger than population
            kws_from_docs = all_kws_from_docs
            
        print kws_from_docs
        # get all the documents that have keywords in common with the documents being recommended
        assoc_docs = Document.get_many(self._doc_ids_that_contain_keywords([kw.id for kw in kws_from_docs]))
                
        # remaining keywords to be sampled
        keywords = [kw 
                    for doc in assoc_docs 
                    for kw in doc['keywords']]
        kw_from_docs_set = set(kws_from_docs)
        remaining_keywords = [kw 
                              for kw in keywords 
                              if kw not in kw_from_docs_set]
        
        try: 
            extra_keywords = random.sample(list(remaining_keywords), kw_num - kw_num_from_docs)
        except ValueError: # sample larger than population
            extra_keywords = list(remaining_keywords)            
        
        # return the joined set of keywords
        kws = KeywordList([])
        for kw in kws_from_docs:
            kw['recommended'] = True
            kws.append(kw)

        for kw in extra_keywords:
            kw['recommended'] = False
            kws.append(kw)

        return kws
        
    def recommend_documents(self, query, top_n):
        """
        Param:
        query: string, the query string, phrases separated by comma, for example: machine learning, natural language processing
        top_n: integer, the number of documents to be returned
        
        Return:
        DocumentList, the recommended documents
        KeywordList, the query keywords(that exist in the corpus)
        """
        query_keywords = [kw_str.strip() 
                          for kw_str in query.strip().split(",")]
        #prepare the query word binary column vector        
        word_vec = self._word_vec(query_keywords)
        
        existing_keywords = Keyword.get_many([word 
                                              for word in query_keywords
                                              if self.kw_ind.has_key(word)])
        
        #get the scores for documents and score it
        scores = matrix2array((self.doc2kw_m * word_vec).T)
        
        #get none zero scores
        non_zero_scores = filter(None, scores)
        print non_zero_scores
        sorted_scores = sorted(enumerate(non_zero_scores), 
                               key = lambda (_, score): score, 
                               reverse = True)
        
        #get the top_n documents
        docs = DocumentList([])
        for ind, score in sorted_scores[:top_n]:
            doc_id = self.doc_ind_r[ind]
            doc = Document.get(doc_id)
            doc['score'] = score
            doc["recommended"] = True
            docs.append(doc)

        return docs, existing_keywords                         
        
    def recommend(self, query):
        """
        recommend documents and keywords
        
        Param:
        query: string, the query string

        Return:
        (DocumentList, KeywordList)
        """
        #first get documents
        rec_docs, query_keywords = self.recommend_documents(query, self.doc_total_n - self.samp_doc_n)
        

        #then get keywords, associated with documents
        rec_kws = self.recommend_keywords(rec_docs, self.kw_total_n - len(query_keywords), self.kw_from_doc_n - len(query_keywords), 
                                          query_keywords = query_keywords)
    
        #last get more documents associated with keywords(only associated with the associated docs)
        extra_docs = self.sample_documents_associated_with_keywords([kw #only those extra keywords
                                                                     for kw in rec_kws 
                                                                     if not kw['recommended']], 
                                                                    self.samp_doc_n)
        
        assoc_kws = self.associated_keywords_from_docs(rec_docs + extra_docs, rec_kws)
        
        return DocumentList(rec_docs + extra_docs), KeywordList(rec_kws + assoc_kws)

    def __init__(self, 
                 doc_total_n, samp_doc_n, 
                 kw_total_n, kw_from_doc_n,
                 *args, **kwargs):
        """
        Params:
        doc_total_n: integer, number of documents to be recommended in total
        samp_doc_n: integer, how many documents to be sampled(there is a sampling process in order to explore out)
        kw_total_n: integer, number of documents to be recommended in total
        kw_from_doc_n: integer, how many keywords to be selected from documents that are already selected
        
        args: the feature matrix and index mapping stuff
        """

        #type validation
        for attr_name in ["doc_total_n", "samp_doc_n", "kw_total_n", "kw_from_doc_n"]:
            attr_val = eval(attr_name)
            assert type(attr_val) is IntType, "%s should be integer, but is %r" %(attr_name, attr_val)
            setattr(self, attr_name, attr_val)

        super(QueryBasedRecommender, self).__init__(*args, **kwargs)            
