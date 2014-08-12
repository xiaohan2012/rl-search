import numpy as np
import random
from scinet3.model import (Document, Keyword)
from scinet3.linrel import linrel

random.seed(123456)

class QueryBasedRecommender(Recommender):
    """
    query-based IR system 
    """
    def _word_vec(self, words):
        """
        given the word strings return the word binary vector
        """
        kw_total_num = len(self.kw_ind.keys())
        word_vec = np.zeros((kw_total_num, 1))
        for word in words:
            word_vec[self.kw_ind[word], 0] = 1
        return matrix(word_vec)

    def associated_documents_by_keywords(self, keywords, n):
         """
         sample n documents from all documents that contain any of the keywords
         """
         #get all doc ids of which the document contains any of the keywords
         kw_ids = [kw['id'] for kw in keywords]
         word_vec = self._word_vec(kw_ids)
         row_idx, _ = np.nonzero(self.doc2kw_m * word_vec)
         doc_ids= [self.doc_ind_r[row_id] 
                   for row_id in row_idx.tolist()[0]]

         #sample it
         return [Document.get(doc_id)
                 for doc_id in random.sample(doc_ids, n)]
         
    def recommend_keywords(self, rec_docs, kw_num, kw_num_from_docs):
        """
        Given the recommended documents, rec_docs, as well as the number of keywords, kw_num_from_docs to be sampled from the documents, 
        return the sampled keywords from:
        1. recommended documents 
        2. documents associated with the recommended documents by keywords

        Param:
        rec_docs: list of Document, the recommended documents
        kw_num: integer, the number of keywords to be recommended
        kw_num_from_docs: integer, number of keywords to be sampled from the docs
        weighted: boolean, using TfIdf weight for the above sampling or not(**NOT IMPLEMENTED BY NOW**))

        Return:
        list of Keyword
        """
        if kw_num_from_docs > kw_num:
            raise ValueError('kw_num_from_docs should be less or equal to kw_num')
            
        #sample kw_num_from_docs from the keywords in the documents, 
        all_kws_from_docs = set([kw 
                                 for doc in rec_docs 
                                 for kw in doc['keywords']])
        
        if len(all_kws_from_docs) <= kw_num_from_docs:
            kws_from_docs = list(all_kws_from_docs)
        else:
            kws_from_docs = random.sample(list(all_kws_from_docs), kw_num_from_docs)

        #get all the documents that have keywords in common with the documents being recommended
        word_vec = self._word_vec([kw.id for kw in kws_from_docs])
        row_idx, _ = np.nonzero(self.doc2kw_m * word_vec)

        assoc_docs = [Document.get(self.doc_ind_r[idx])
                      for idx in row_idx.tolist()[0]]
                
        keywords = set([kw for doc in assoc_docs for kw in doc['keywords']])
        remaining_keywords = keywords - set(kws_from_docs)
        
        #sample kw_num - kw_num_from_docs keywords from the above document set
        if len(remaining_keywords) <= kw_num - kw_num_from_docs: #not enough population to sample from..
            print 'Not enouth remaining keywords.. use them all'
            extra_keywords = list(remaining_keywords)
        else:
            extra_keywords = random.sample(list(remaining_keywords), kw_num - kw_num_from_docs)
        
        #return the joined set of keywordsn
        kws = []
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
        query: string, the query string
        top_n: integer, the number of documents to be returned
        
        Return:
        list of Document, the recommended documents
        """
        query_words = query.strip().split()
        #prepare the query word binary column vector        
        word_vec = self._word_vec(query_words)
        
        #get the scores for documents and scort it
        scores = self.doc2kw_m * word_vec
        sorted_scores = sorted(enumerate(np.array(scores.T).tolist()[0]), key = lambda (id, score): score, reverse = True)
        
        #get the top_n documents 
        docs = []
        for ind, score in sorted_scores[:top_n]:
            doc_id = self.doc_ind_r[ind]
            doc = Document.get(doc_id)
            doc['score'] = score
            docs.append(doc)

        return docs
        
    def recommend(self, query, doc_total_n, samp_doc_n, kw_total_n, kw_from_doc_n):
        """
        recommend documents and keywords
        
        Param:
        query: string, the query string
        doc_total_n: integer, total number documents to recommended
        samp_doc_n: integer, number documents to sampled
        kw_total_n:: integer, total number keywords to recommended
        kw_from_doc_n: integer, total number keywords to sampled from document

        Return:
        (list of Document, list of Keyword)
        """
        #first get documents
        rec_docs = self.recommend_documents(query, doc_total_n)
        
        #then get keywords, associated with documents
        rec_kws = self.recommend_keywords(rec_docs, kw_total_n, kw_from_doc_n)
    
        #last get more documents associated with keywords
        extra_docs = self.associated_documents_by_keywords([kw #only those extra keywords
                                                            for kw in rec_kws 
                                                            if not kw['recommended']], 
                                                           doc_total_n - samp_doc_n)

        assoc_kws = self.associated_keywords_from_docs(rec_docs + extra_docs, rec_kws)
        
        return (rec_docs + extra_docs), (rec_kws + assoc_kws)
