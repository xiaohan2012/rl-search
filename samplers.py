
class SamplerRepository(object):
    ################
    # The following are the samplers
    ################
    
    @classmethod
    def get(cls, sampler_id):
        return None

    @classmethod
    def get_samplers_from_str(cls, s):
        """
        Get a list of samplers from configuration string
        
        Param:
        --------
        s: string|None: the sampler string

        Return:
        ---------
        list of functions:
        """
        if s is None:
            return None
        else:
            filter_ids = map(lambda id_str: id_str.strip(), 
                             s.split(","))
            
            return [cls.get(filter_id) 
                    for filter_id in filter_ids]
