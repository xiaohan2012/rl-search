##########################
# Feedback propagation handler.

# It deals how feedback is propagated from source to targets.

# It defines: 

# The logic of **which** objects will be affected during the propagation.

# Not **how** each individual object is affected **numerically**.

# The **how** part is defined in **fb_receiver.py**.
##########################

class FeedbackPropagator(object):
    @classmethod
    def fb_from_doc(cls, doc, fb_numer, session):
        raise NotImplementedError

    @classmethod
    def fb_from_kw(cls, kw, fb_numer, session):
        raise NotImplementedError

    @classmethod
    def fb_from_indockw(cls, kw, doc, fb_numer, session):
        raise NotImplementedError
    
    @classmethod
    def done(cls):
        raise NotImplementedError

class OnePassPropagator(FeedbackPropagator):
    """
    Propagates the feedback only once
    """
    
    @classmethod
    def fb_from_doc(cls, doc, fb_numer, session):
        """
        doc: document
        fb_numer: feedback numerical value
        """
        #from doc to doc itself
        doc.rec_fb_from_doc(doc, fb_numer, session)

        #from doc to associated keywords
        for kw in doc.keywords:
            kw.rec_fb_from_doc(doc, fb_numer, session)        
            
        #those objects' feedback shall be updated
        session.add_affected_docs(doc)
        session.add_affected_kws(*doc.keywords)

    @classmethod
    def fb_from_kw(cls, kw, fb_numer, session):
        """
        kw: keyword
        fb_numer: feedback numerical value
        """
        #from kw to kw itself
        kw.rec_fb_from_kw(kw, fb_numer, session)
        
        #from keywords to associated docs(for the current session)
        kw_docs = filter(lambda doc: kw in doc.keywords, 
                         session.last_recom_docs)
        
        for doc in kw_docs:
            doc.rec_fb_from_kw(kw, fb_numer, session)

        #those objects' feedback shall be updated
        session.add_affected_kws(kw)
        session.add_affected_docs(*kw_docs)
        
    @classmethod
    def fb_from_dockw(cls, kw, doc, fb_numer, session):
        """
        feedback received from in-document keyword
        
        kw: keyword
        doc: associated document
        fb_numer: feedback numerical value
        """
        kw.rec_fb_from_dockw(kw, doc, fb_numer, session)
        doc.rec_fb_from_dockw(kw, doc, fb_numer, session)
    
        #those objects' feedback shall be updated
        session.add_affected_kws(kw)
        session.add_affected_docs(doc)

    @classmethod
    def done(cls, session):
        """
        when propagation is done
        session: Session
        """        
        for kw in session.affected_kws:
            session.update_kw_feedback(kw, kw.fb_weighted_sum(session))
            kw.loop_done(session)
            
        for doc in session.affected_docs:
            session.update_doc_feedback(doc, doc.fb_weighted_sum(session))
            doc.loop_done(session)
        
        session.clean_affected_objects()
        
        
        
class IterativePropagator(FeedbackPropagator):
    """
    Iteratively propagates the feedback
    """
    pass
