##############################
# intelligent machine simulated user that 
# gives feedback to keywords/documents
##############################
from scinet3.model import (Document, Keyword)
from scinet3.modellist import (DocumentList, KeywordList)

class Robot(object):
    """
    Generic robot class
    """
    def give_feedback(self, docs, kws, doc_n=1, kw_n=1):
        raise NotImplementedError


class NearSightedRobot(object):
    """
    Robot that are near sighted. 
    It chooses the docs/kws that are most similar to the goal
    """
    def __init__(self):
        #keeping track of what has been selected
        self.kws_selected = set()
        self.docs_selected = set()

        
    def setGoal(self, docs, kws):
        """
        docs: DocumentList, the documents desirable
        kws: KeywordList, the keywords desirable
        """
        assert type(docs) is DocumentList, "docs should be DocumentList, but is %r" %docs
        assert type(kws) is KeywordList, "kws should be KeywordList, but is %r" %kws
        
        self.target_docs = docs
        self.target_kws = kws

    def give_feedback(self, docs, kws, doc_n=1, kw_n=1):
        """
        Robot selects the doc_n documents and kw_n keywords it likes(in other words, give feedbacks to the docs and kws)
        based on:
        1. the similarity between the docs/kws to the target docs/kws.
        2. it has been selected before or not
        
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
        
        top_docs = sorted(set(docs) - self.docs_selected, 
                          key = lambda doc: self.target_docs.similarity_to(doc), 
                          reverse = True)[:doc_n]

        top_kws = sorted(set(kws) - self.kws_selected, 
                         key = lambda kw: self.target_kws.similarity_to(kw), 
                         reverse = True)[:kw_n]
        
        fb["docs"] = [[doc.id, 1] 
                      for doc in top_docs]
        
        fb["kws"] = [[kw.id, 1] 
                     for kw in top_kws]

        #keep track of what is selected..
        self.kws_selected |= set(top_kws)
        self.docs_selected |= set(top_docs)

        return fb
