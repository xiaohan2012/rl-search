import tornado
from tornado.options import define, options

from types import StringType

import torndb
import redis

from scinet3.model import (Document, Keyword)

define("port", default=8000, help="run on the given port", type=int)
define("mysql_port", default=3306, help="db's port", type=int)
define("mysql_host", default="ugluk", help="db database host")
define("mysql_user", default="hxiao", help="db database user")
define("mysql_password", default="xh24206688", help="db database password")
define("mysql_database", default="archive", help="db database name")
define("mysql_keyword_fieldname", default="keywords", help="name of field that stores the keywords")

define("redis_port", default=6379, help="redis' port", type=int)
define("redis_host", default="ugluk", help="key-value cache host")
define("redis_db", default="scinet3", help="key-value db")

define("mysql_table", default='john', help="db table to be used")
define("refresh_pickle", default=False, help="refresh pickle or not")

define("recom_kw_num", default=5, help="recommended keyword number at each iter")
define("recom_doc_num", default=10, help="recommended document number at each iter")
define("samp_kw_num_from_doc", default=5, help="sampled keyword number from documents")
define("samp_doc_num", default=5, help="extra document number apart from the recommended ones")

define("linrel_kw_mu", default=1., help="Value for \mu in the linrel algorithm for keyword")
define("linrel_kw_c", default=0.2, help="Value for c in the linrel algorithm for keyword")
define("linrel_doc_mu", default=1., help="Value for \mu in the linrel algorithm for document")
define("linrel_doc_c", default=0.2, help="Value for c in the linrel algorithm for document")

define("kw_fb_threshold", default=0.01, help="The feedback threshold used when filtering keywords")
define("kw_fb_from_docs_threshold", default=0.01, help="The feedback(from documents) threshold used when filtering keywords")
define("doc_fb_threshold", default=0.01, help="The feedback threshold used when filtering documents")
define("doc_fb_from_kws_threshold", default=0.01, help="The feedback(from keywords) threshold used when filtering documents")

define("kw_alpha", default=0.7, help="The weight value used for keyword feedback summarization")
define("doc_alpha", default=0.7, help="The weight value used for document feedback summarization")

class CmdApp():
    """
    Command-line application that interacts with the user
    """
    def __init__(self, ppgt, upd, init_recommender, main_recommender):
        """
        ppgt: feedback propagator
        """
        self.ppgt = ppgt
        self.upd = upd
        self.init_recommender = init_recommender
        self.main_recommender = main_recommender

    def recommend(self, start = False, *args, **kwargs):
        """
        recommend documents and keywords.
        
        """
        if start:
            return self.init_recommender.recommend(*args, **kwargs)
        else:
            return self.main_recommender.recommend(*args, **kwargs)
        
    def receive_feedbacks(self, session, feedbacks):
        """
        Receive feedbacks from user
        
        The format of feedback is:
        {
        "docs": [[doc_id, feedback_value], ...],
        "kws": [[keyword_id, feedback_value], ...],
        "dockws": [[keyword_id, doc_id, feedback_value], ...]
        }
        """
        for doc_fb in feedbacks.get("docs", []):
            doc_id, fb = doc_fb
            doc = Document.get(doc_id)
            
            self.ppgt.fb_from_doc(doc, fb, session)

        for kw_fb in feedbacks.get("kws", []):
            kw_id, fb = kw_fb
            kw = Keyword.get(kw_id)
            
            self.ppgt.fb_from_kw(kw, fb, session)

        for dockw_fb in feedbacks.get("dockws", []):
            kw_id, doc_id, fb = dockw_fb
            doc = Document.get(doc_id)
            kw = Keyword.get(kw_id)
            
            self.ppgt.fb_from_dockw(kw, doc, fb, session)

        # propagation is done
        # updates the feedback value 
        self.upd.update(session)

    def interact_with_user(self, docs, kws, simulated_input = []):
        """
        Interact with users to get user feedback 
        
        Param:
        docs: list(Document), the document to be displayed
        kws: list(Keyword), the keyword to be displayed
        (optional)simulated_input: list of str(user input), used for testing
        
        Return:
        feedback: dictionary
        """
        simulated_input.reverse() #reserse it as we are using pop
        
        #ask question about doc
        print "List of documents:"
        index2doc_mapping = dict(enumerate(docs))
        for index, doc in index2doc_mapping.items():
            print "%d: %r" %(index, doc)
            
        if len(simulated_input):
            doc_str = simulated_input.pop()
        else:
            doc_str = raw_input("Pick the document numbers you like(each seperated by space):")
            
        favored_docs = [index2doc_mapping[index] for index in map(int, doc_str.split())]
        
        #ask question about standalone keywords
        # only that are recommended are displayed
        # this does not include the associted ones
        print "List of keywords: "
        index2kw_mapping = dict(enumerate(kws))

        for index, kw in index2kw_mapping.items():
            print "%d: %r" %(index, kw)
                
        if len(simulated_input):
            kw_str = simulated_input.pop()
        else:
            kw_str = raw_input("Pick the keyword numbers you like(each seperated by space).")

        favored_kws = [index2kw_mapping[index] for index in map(int, kw_str.split())]
            
        #ask question about keywords in documents
        favored_dockws = {}
        for index, doc in index2doc_mapping.items():
            index2kw_mapping = dict(enumerate(doc.keywords))
            print "For doc: %r. The keywords are:" %doc
            kws_display = ", ".join(["%d: %s" %(index, kw.id)
                                     for index, kw in index2kw_mapping.items()])
            print kws_display
            
            if len(simulated_input):
                kw_str = simulated_input.pop()
            else:
                kw_str = raw_input("Select the keyword number you like(separated by space):")
                
            favored_dockws[doc] = [index2kw_mapping[index] for index in map(int, kw_str.split())]
            
        #assemble the feedbacks into acceptable format
        fb = {}
        fb["docs"] = [[doc.id, 1] for doc in favored_docs]
        fb["kws"] = [[kw.id, 1] for kw in favored_kws]
        fb["dockws"] = [[kw.id, doc.id, 1]
                        for doc, kws in favored_dockws.items()
                        for kw in kws ]

        return fb
        

def main(desired_doc, desired_kw, session):    
    ######################
    #Global variables to be set
    ######################
    AUTO_INTERACT = True
    MAX_ITER = 10
    INTIAL_QUERY = "Neuron"
    
    ######################
    # This is our robot
    ######################
    if AUTO_INTERACT:
        from robot import NearSightedRobot
        robot = NearSightedRobot(INTIAL_QUERY)
        robot.setGoal(desired_docs, desired_kws)

    ######################
    # Just an example of  feedback
    # *** not used by the program ***
    ######################

    feedback = {"docs": [[1, .8], [1001, .9]],
                "kws": [["model selection", .8], ["computational lingustics", .7]],
                "dockws": [["information retrieval", 1, .8], ["information extraction", 1003, .7]]
    }

    ######################
    # Filter creation
    ######################
    from scinet3.filters import make_threshold_filter
    
    kw_fb_filter = make_threshold_filter(lambda o: o.fb(session), options.kw_fb_threshold)
    fb_from_docs_filter = make_threshold_filter(lambda o: o.fb_from_kws(session), options.kw_fb_from_docs_threshold)
    
    doc_fb_filter = make_threshold_filter(lambda o: o.fb(session), options.doc_fb_threshold)
    fb_from_kws_filter = make_threshold_filter(lambda o: o.fb_from_docs(session), options.doc_fb_from_kws_threshold)    

    # this part should be configurable 
    # so that different filters can be passed
    kw_filters = [kw_fb_filter, fb_from_docs_filter]
    doc_filters = [doc_fb_filter, fb_from_kws_filter]

    ########################
    # Recommender initialization
    # including filter binding to recommender
    ########################
    from scinet3.rec_engine.query import QueryBasedRecommender
    init_recommender = QueryBasedRecommender(options.recom_doc_num, options.samp_doc_num, 
                                             options.recom_kw_num, options.samp_kw_num_from_doc,
                                             **fmim_dict)
    
    from scinet3.rec_engine.linrel import LinRelRecommender
    
    main_recommender = LinRelRecommender(options.recom_kw_num, options.recom_doc_num, 
                                         options.linrel_kw_mu, options.linrel_kw_c, 
                                         options.linrel_doc_mu, options.linrel_doc_c, 
                                         None, None,
                                         **fmim_dict)

    ######################
    # This is our main app
    ######################
    # The choice of propagator and updater should be congifurable 
    from scinet3.fb_propagator import OnePassPropagator
    from scinet3.fb_updater import OverrideUpdater
    
    app = CmdApp(OnePassPropagator, OverrideUpdater, init_recommender, main_recommender)

    #######################
    # Our main app starts!!
    #######################
    just_started = True
    iter_n = 0
    
    while True: 
        iter_n += 1
        print "At iteration %d" %iter_n
                        
        if just_started:
            docs, kws = app.recommend(start = just_started, query = robot.initial_query)
        else:
            docs, kws = app.recommend(start = just_started, session = session)

        just_started = False
        
        kws_to_be_displayed = filter(lambda kw: kw.has_key("recommended") and kw["recommended"], #kinda weird, kw.get("recommended", False) **should** be OK, but ...
                                     kws)
        
        #session records recommendation
        session.add_doc_recom_list(docs)
        session.add_kw_recom_list(kws)
        
        if AUTO_INTERACT:#if robot is asked to come into stage
            print "%d / %d" %(iter_n, MAX_ITER)
            if iter_n > MAX_ITER:
                break
            
            feedback = robot.give_feedback(docs, kws_to_be_displayed)
        else:
            feedback = app.interact_with_user(docs, kws_to_be_displayed)
        
                    
        app.receive_feedbacks(session, feedback)

        # action_tracker.record_feedback(feedback)
        # action_tracker.record_recommendation(docs, keywords)
        
if __name__ == "__main__":    
    tornado.options.parse_command_line()
    
    from scinet3.util.profiler import profile_manager
    from scinet3.util.ir_eval import evaluation_manager

    ######################
    # Configure the database, session and model
    ######################
    db_conn = torndb.Connection("%s:%s" % (options.mysql_host, options.mysql_port), 
                                options.mysql_database, options.mysql_user, options.mysql_password)

    from scinet3.data import load_fmim
    fmim_dict = load_fmim(db_conn, options.mysql_table, keyword_field_name = options.mysql_keyword_fieldname, refresh = options.refresh_pickle).__dict__

    from scinet3.model import config_model    
    config_model(db_conn, options.mysql_table, fmim_dict, options.doc_alpha, options.kw_alpha)

    #########################
    # Redis-based session confuguration
    #########################
    from scinet3.session import RedisRecommendationSessionHandler
    redis_conn = redis.StrictRedis(host=options.redis_host, port=options.redis_port, db=options.redis_db)

    session = RedisRecommendationSessionHandler.get_session(redis_conn, None)
    
    #########################
    # Desired docs/kws
    #########################
    desired_docs = Document.get_many([3, 161, 207, 234, 237, 264, 269, 282, 283, \
                                      295, 296, 305, 329, 330, 335, 338, 354, 374, \
                                      375, 383, 385, 469, 470, 497])
    
    desired_kws = Keyword.get_many(["Artificial neural network", "Neuron", \
                                    "Computational neuroscience", "Biological neural network"])

    
    with evaluation_manager(desired_docs, desired_kws, session):
        main(desired_docs, desired_kws, session)

