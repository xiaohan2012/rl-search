#######################
# Util functions for evaluation of the IR system
#######################

from contextlib import contextmanager

from scinet3.modellist import (DocumentList, KeywordList)

@contextmanager
def evaluation_manager(desired_docs, desired_kws, session):
    evaluator = GoalBasedEvaluator()
    evaluator.setGoal(desired_docs, desired_kws)
    
    yield

    eval_results = evaluator.evaluate(session.recom_docs, session.recom_kws)

    print "Evaluation results:"

    print "for docs:"
    print eval_results[0]

    print "for kws:"
    print eval_results[1]

    


class GoalBasedEvaluator(object):
    """
    Evaluate the IR performance using the similarity to the goal
    """
    
    def setGoal(self, docs, kws):
        """
        docs: DocumentList, the documents desirable
        kws: KeywordList, the keywords desirable
        """
        
        assert type(docs) is DocumentList, "docs should be DocumentList, but is %r" %docs
        assert type(kws) is KeywordList, "kws should be KeywordList, but is %r" %kws
        
        assert len(docs) > 0, "target_docs shouldn't be empty"
        assert len(kws) > 0, "target_kws shouldn't be empty"
        
        self.desired_docs = docs
        self.desired_kws = kws

    def evaluate(self, recom_doc_history, recom_kw_history):
        """
        Param:
        recom_doc_history: list of DocumentList, the documents be recommended in each iteration, from newest to oldest
        recom_kw_history: list of KeywordList, the keywords be recommended in each iteration, from newest to oldest

        Return:
        (list of float #1, list of float #2)

        #1: similarity scores for each itertion of recommended documents(from newest to oldest)
        #2: similarity scores for each itertion of recommended keywords(from newest to oldest)
        """
        
        return ([self.desired_docs.similarity_to(docs)  #for docs
                 for docs in recom_doc_history],
                [self.desired_kws.similarity_to(kws) #for kws
                 for kws in recom_kw_history])
