#######################
# Util functions for evaluation of the IR system
#######################

class GoalBasedEvaluator(object):
    """
    Evaluate the IR performance using the similarity to the goal
    """
    
    def setGoal(self, docs, kws):
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
