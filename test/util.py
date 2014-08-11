########################################
# Utility that helps setting up:
# 1. mysql DB
# 2. redis
# 3. session
# 4. model configuration
# 5. 
########################################

__all__ = ["get_db_conn", "config_doc_kw_model", "get_session"]


import torndb, redis

from scinet3.data import load_fmim
from scinet3.model import config_model
from scinet3.session import RedisRecommendationSessionHandler

def get_db_conn():
    db = 'scinet3'
    return torndb.Connection("%s:%s" % ('ugluk', 3306), db, 'hxiao', 'xh24206688')

def config_doc_kw_model(doc_alpha = .7, kw_alpha = .7):
    conn = get_db_conn()
    table = 'test'    
    print conn
    fmim_dict = load_fmim(conn, table, keyword_field_name = 'keywords').__dict__
    
    config_model(conn, table, fmim_dict, doc_alpha, kw_alpha)

def get_session():
    
    redis_db="test"
    
    redis_conn = redis.StrictRedis(host='ugluk', port=6379, db=redis_db)
    return RedisRecommendationSessionHandler.get_session(redis_conn)
    

    

    
    
