##############################
# intelligent machine simulated user that 
# gives feedback to keywords/documents
##############################
from scinet3.model import (Document, Keyword, DocumentSet, KeywordSet)

class Robot(object):
    def setGoal(self, docs, kws):
        """
        docs: DocumentSet, the documents desirable
        kws: KeywordSet, the keywords desirable
        """
        assert type(docs) is DocumentSet, "docs should be DocumentSet, but is %r" %docs
        assert type(kws) is KeywordSet, "kws should be KeywordSet, but is %r" %kws
        
        self.target_docs = docs
        self.target_kws = kws

    def give_feedback(self, docs, kws, doc_n=1, kw_n=1):
        """
        Robot selects the doc_n documents and kw_n keywords it likes(in other words, give feedbacks to the docs and kws)
        based on the similarity between the docs/kws to the target docs/kws.
        
        Note: 
        It does not give feedback on keywords within documents. The reason for that is to make things simple. :)
        
        Param:
        docs: list of Document, the documents shown to the robot
        kws: list of Keyword, the keywords shown to the robot
        doc_n: integer, the number documents to give feedback on 
        kw_n: integer, the number keywords to give feedback on 
        
        Return:
        feedback object
        """
        fb = {}
        
        top_docs = sorted(docs, 
                          key = lambda doc: self.target_docs.similarity_to(doc), 
                          reverse = True)[:doc_n]
        top_kws = sorted(kws, 
                         key = lambda kw: self.target_kws.similarity_to(kw), 
                         reverse = True)[:kw_n]

        
        fb["docs"] = [[doc.id, 1] for doc in top_docs]
        fb["kws"] = [[kw.id, 1] for kw in top_kws]

        return fb
