"""
Defines the logic of how feedbacks of documents and keywords should be updated(e.g, replace or mixed with the old one?)
"""

class OverrideUpdater(object):
    """
    Old feedback value is **overrided** by the new one
    """
    @classmethod
    def update(cls, session):
        for kw in session.affected_kws:
            session.update_kw_feedback(kw, kw.fb_weighted_sum(session))
            kw.loop_done(session)
            
        for doc in session.affected_docs:
            session.update_doc_feedback(doc, doc.fb_weighted_sum(session))
            doc.loop_done(session)
        
        session.clean_affected_objects()

class MeanUpdater(object):
    """
    The mean of all feedback values in history is calculated and updated
    """
    @classmethod
    def update(cls, session, docs, kws):
        """
        """
    
