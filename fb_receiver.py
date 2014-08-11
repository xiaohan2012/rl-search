############################
# Module that encapsulates **how** the feedback is received.

# The feedback receiving happens **after** the feedback propagation is done.

# To see how the propagation is done, refer to **fb_propagator.py**
############################

__all__ = ["KeywordFeedbackReceiver", "DocumentFeedbackReceiver"]

import scinet3.model

class KeywordFeedbackReceiver(object):
    """
    Should be mixed with `Keyword`
    """
    
    ####################
    # err msg for assertion
    ####################
    _DOC_ERR_MSG = "The document should contain the keyword"
    _KW_ERR_MSG = "keyword cannot be no others but itself"

    ######################
    # redis key template
    ######################
    _KEY_TMPL_FB_KW = "kw_%s_fb_from_kw"
    _KEY_TMPL_FB_DOC = "kw_%s_fb_from_docs"
    
    #########################
    # weighting parameter for fb from kw and doc
    #########################
    alpha = 0.5

    def __init__(self, *args, **kwargs):
        self._redis_key_fb_from_kw = (self.__class__._KEY_TMPL_FB_KW %self.id)
        self._redis_key_fb_from_doc = (self.__class__._KEY_TMPL_FB_DOC %self.id)

        super(KeywordFeedbackReceiver, self).__init__(*args, **kwargs)
        
    @classmethod
    def set_alpha(cls, alpha):
        cls.alpha = alpha

    def fb_from_doc(self, session):
        """
        getter for feedback from document
        """
        # Document should be used as the key, instead of the document id
        new_dict = {}
        for doc_id, fb in session.hgetall(self._redis_key_fb_from_doc).items():
            new_dict[scinet3.model.Document.get(doc_id)] = fb
        
        return new_dict

    def fb_from_kw(self, session):
        """
        getter for feedback from keyword
        """
        return session.get(self._redis_key_fb_from_kw, 0.0)

    def rec_fb_from_doc(self, doc, fb, session):
        """
        receive feedback from document, which should contain the keyword
        
        session: Session, the session used
        doc: Document
        fb: float
        """
        assert (self in doc.keywords), self.__class__._DOC_ERR_MSG
        
        session.hmset(self._redis_key_fb_from_doc, {doc.id: fb})

    def rec_fb_from_dockw(self, kw, doc, fb, session):
        """
        receive feedback from keyword in document, which is actually the same with receiving feedback from document
        kw: Keyword
        doc: Document
        fb: float
        """
        assert (self == kw),  self.__class__._KW_ERR_MSG
        
        #the same with receiving feedback from document
        self.rec_fb_from_doc(doc, fb, session)
    
    def rec_fb_from_kw(self, kw, fb, session):
        """
        receive feedback from keyword(itself)
        kw: Keyword
        fb: float
        """
        assert (self == kw), self.__class__._KW_ERR_MSG

        session.set(self._redis_key_fb_from_kw, fb)
            
    def fb_weighted_sum(self, session):
        """
        Get the feedback received for the **current** loop
        
        Note: this feedback value is not the same as the feedback received along the way
        """
                
        fb_from_doc_sum = sum([self._doc_weight[doc] * fb
                               for doc, fb in self.fb_from_doc(session).items()])
        
        return self.__class__.alpha * self.fb_from_kw(session) + \
            (1 - self.__class__.alpha) * fb_from_doc_sum / sum(self._doc_weight.values())

    ############################
    # This step shall be done 
    # in order to start a new round of feedback receiving
    ############################   
    def loop_done(self, session):
        """
        Tell the session that this loop is done
        """
        session.delete(self._redis_key_fb_from_kw)
        session.delete(self._redis_key_fb_from_doc)
                               
class DocumentFeedbackReceiver(object):
    ####################
    # err msg for assertion
    ####################
    _DOC_ERR_MSG = "Document cannot be no others but itself"
    _KW_ERR_MSG = "The document should contain the keyword"

    ######################
    # redis key template
    ######################
    _KEY_TMPL_FB_KW = "doc_%s_fb_from_kws"
    _KEY_TMPL_FB_DOC = "doc_%s_fb_from_doc"
    
    #########################
    # weighting parameter for fb from kw and doc
    #########################
    alpha = 0.5

    def __init__(self, *args, **kwargs):
        super(DocumentFeedbackReceiver, self).__init__(*args, **kwargs)
        
        self._redis_key_fb_from_kw = (self.__class__._KEY_TMPL_FB_KW %self["id"])
        self._redis_key_fb_from_doc = (self.__class__._KEY_TMPL_FB_DOC %self["id"])
        
    @classmethod
    def set_alpha(cls, alpha):
        cls.alpha = alpha

    def fb_from_doc(self, session):
        """
        getter for feedback from document
        """
        return session.get(self._redis_key_fb_from_doc, 0.0)

    def fb_from_kw(self, session):
        """
        getter for feedback from keyword
        """
        # Document should be used as the key, instead of the document id
        new_dict = {}
        for kw_id, fb in session.hgetall(self._redis_key_fb_from_kw).items():
            new_dict[scinet3.model.Keyword.get(kw_id)] = fb
        
        return new_dict

    def rec_fb_from_doc(self, doc, fb, session):
        """
        receive feedback from document, which should be itself
        
        session: Session, the session used
        doc: Document
        fb: float
        """
        assert (self == doc), self.__class__._DOC_ERR_MSG
        
        session.set(self._redis_key_fb_from_doc, fb)

    def rec_fb_from_dockw(self, kw, doc, fb, session):
        """
        receive feedback from keyword in document, which is actually the same with receiving feedback from keyword
        
        kw: Keyword
        doc: Document
        fb: float
        """
        assert (self == doc),  self.__class__._DOC_ERR_MSG
        
        #the same with receiving feedback from keyword
        self.rec_fb_from_kw(kw, fb, session)
    
    def rec_fb_from_kw(self, kw, fb, session):
        """
        receive feedback from keyword
        kw: Keyword
        fb: float
        """
        assert (kw in self.keywords), self.__class__._KW_ERR_MSG

        session.hmset(self._redis_key_fb_from_kw, {kw.id: fb})
            
    def fb_weighted_sum(self, session):
        """
        Get the feedback received for the **current** loop
        
        Note: this feedback value is not the same as the feedback received along the way
        """
        fb_from_kw_sum = sum([self._kw_weight[kw] * fb
                              for kw, fb in self.fb_from_kw(session).items()])
        
        return self.__class__.alpha * self.fb_from_doc(session) + \
            (1 - self.__class__.alpha) * fb_from_kw_sum / sum(self._kw_weight.values())

    ############################
    # This step shall be done 
    # in order to start a new round of feedback receiving
    ############################   
    def loop_done(self, session):
        """
        Tell the session that this loop is done
        """
        session.delete(self._redis_key_fb_from_kw)
        session.delete(self._redis_key_fb_from_doc)
