#########################
# Modeling set of Document/Keyword
#########################
import scinet3.model

from scinet3.decorators import memoized
from scinet3.numerical_util import cosine_similarity

from scipy.sparse import csr_matrix

class ModelSet(set):
    @property
    @memoized
    def centroid(self):
        """
        Get the centroid of the model set
        
        Return:
        The centroid vector: csr_matrix
        """
        if len(self) == 1: #contain only one object, the centroid is itself
            return list(self)[0].vec
        else:
            return (csr_matrix([model.vec.toarray()[0,:] 
                                for model in self]).sum(0) 
                    / len(self))
        
    @property
    def ids_str(self):
        return ",".join(sorted([str(obj.id) for obj in self]))

    #######################
    # following two methods make ModelSet hashable
    #######################
    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.ids_str == other.ids_str
        
    def __hash__(self):
        return hash(self.ids_str)

class DocumentSet(ModelSet):
    @memoized
    def similarity_to(self, other, metric = "cosine"):
        """
        set-to-set similarity
        
        Param:
        docs: DocumentSet

        Return:
        float        
        """
        assert type(other) in (scinet3.model.Document, DocumentSet), "`other` should be either Document or DocumentSet, but is %r" %other
        
        if isinstance(other, scinet3.model.Document):
            other = DocumentSet([other])

        if metric == "cosine":
            return cosine_similarity(self.centroid, other.centroid)
        else:
            raise NotImplementedError("Only cosine similarity metric is implemented for now")


    def __init__(self, iterable):
        objs = list(iterable)

        #checking for datatype
        for obj in objs:
            assert type(obj) is scinet3.model.Document, "obj should be Document, but is %r" %obj
            
        super(DocumentSet, self).__init__(iterable)
        

class KeywordSet(ModelSet):
    @memoized
    def similarity_to(self, other, metric = "cosine"):
        """
        set-to-set similarity
        
        Param:
        docs: KeywordSet

        Return:
        float        
        """
        assert type(other) in (scinet3.model.Keyword, KeywordSet), "`other` should be either Keyword or KeywordSet, but is %r" %other
        
        if isinstance(other, scinet3.model.Keyword):
            other = KeywordSet([other])
        
        if metric == "cosine":
            return cosine_similarity(self.centroid, other.centroid)
        else:
            raise NotImplementedError("Only cosine similarity metric is implemented for now")

    def __init__(self, iterable):
        objs = list(iterable)

        #checking for datatype
        for obj in objs:
            assert type(obj) is scinet3.model.Keyword, "obj should be Keyword, but is %r" %obj
            
        super(KeywordSet, self).__init__(iterable)
        
