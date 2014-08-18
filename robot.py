##############################
# intelligent machine simulated user that 
# gives feedback to keywords/documents
##############################
import random

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
    def __init__(self, initial_query):
        self.initial_query = initial_query
        
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
        
        assert len(docs) > 0, "target_docs shouldn't be empty"
        assert len(kws) > 0, "target_kws shouldn't be empty"
        
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
        
        # if the targets appears in the list
        # no hesitating to select them

        doc_intersect = (set(docs) - self.docs_selected).intersection(set(self.target_docs))
        
        top_docs = []
        if doc_intersect:
            if len(doc_intersect) > doc_n: #exceed the desired document number
                #select the one closest to targets
                doc_intersect = set(sorted(doc_intersect, 
                                           key = lambda doc: self.target_docs.similarity_to(doc), 
                                           reverse = True)[:doc_n])
            doc_n -= len(doc_intersect)
            self.docs_selected |= doc_intersect
            top_docs += doc_intersect
            
        kw_intersect = (set(kws) - self.kws_selected).intersection(set(self.target_kws))
        
        top_kws = []
        if kw_intersect:
            if len(kw_intersect) > kw_n: #exceed the desired keyword number
                #select the one closest to targets
                kw_intersect = set(sorted(kw_intersect, 
                                          key = lambda kw: self.target_kws.similarity_to(kw), 
                                          reverse = True)[:kw_n])
            kw_n -= len(kw_intersect)
            self.kws_selected |= kw_intersect
            top_kws += kw_intersect
        
        if doc_n: # there are still documents to select
            top_docs += sorted(set(docs) - self.docs_selected, 
                               key = lambda doc: self.target_docs.similarity_to(doc), 
                           reverse = True)[:doc_n]

        if kw_n: # there are still keywords to select
            top_kws += sorted(set(kws) - self.kws_selected, 
                              key = lambda kw: self.target_kws.similarity_to(kw), 
                              reverse = True)[:kw_n]
        
        fb["docs"] = [[doc.id, 1] 
                      for doc in top_docs]
        
        
        fb["kws"] = [[kw.id, 1] 
                     for kw in top_kws]

        print "Among :"
        print docs
        print "I choose:"
        print top_docs

        print "Among :"
        print kws
        print "I choose:"
        print top_kws
        
        #keep track of what is selected..
        self.kws_selected |= set(top_kws)
        self.docs_selected |= set(top_docs)

        return fb
