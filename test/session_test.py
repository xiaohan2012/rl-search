import unittest

import redis
from scinet3.session import RedisRecommendationSessionHandler

class RedisSessionSessionTest(unittest.TestCase):
    def setUp(self):
        self.redis_conn = redis.StrictRedis(host='ugluk', port=6379, db="test")
        self.session = RedisRecommendationSessionHandler.get_session(self.redis_conn)

    def test_hashmap(self):
        key = "test_key"
        self.session.hmset(key, {"hmkey1": 1.2, "hmkey2": "value", 1: 1.2})
        self.session.hmset(key, {"hmkey3": "value"})
        self.assertEqual(self.session.hgetall(key), {"hmkey1": 1.2, "hmkey2": "value", 1: 1.2, "hmkey3": "value"})

        self.assertEqual(self.session.hget(key, "hmkey1"), 1.2)
        self.assertEqual(self.session.hget(key, "hmkey2"), "value")
        self.assertEqual(self.session.hget(key, 1), 1.2)
        
        self.session.delete(key)
        self.assertEqual(self.session.hgetall(key), {})
        
    def test_get_and_set(self):
        self.session.set("numer_value", 1)
        self.assertEqual(self.session.get("numer_value"), 1)
        
        self.session.set("str_value", "abc")
        self.assertEqual(self.session.get("str_value"), "abc")
        
