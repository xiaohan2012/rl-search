
from util import config_doc_kw_model

config_doc_kw_model()

from scinet3.model import Document, Keyword

Document.load_all_from_db()

def doc_compute(d):
    return d.get(Keyword.get("redis"), 0) * .5 / sum(d.values())

doc = Document.get(1)
print doc._kw_weight
{"a": 0.62981539329519109, "redis": 0.62981539329519109, "database": 0.45460437826405437}

print doc_compute(doc._kw_weight)

doc = Document.get(2)
print doc._kw_weight
{"the": 0.58478244910295341, "redis": 0.6577450118852588, "database": 0.47476413782131072}
print doc_compute(doc._kw_weight)


doc = Document.get(3)
print doc._kw_weight
{"tornado": 0.57555052264377027, "web": 0.50353869621889158, "a": 0.50353869621889158, "python": 0.40204372735417787}
print doc_compute(doc._kw_weight)


def kw_compute(d):
    return d[1] * .5 / sum(d.values())


a_kw = Keyword.get("a")
a = {8: 0.65694939124806184, 1: 0.56689342264886755, 3: 0.49704058656839417}
print kw_compute(a)

redis_kw = Keyword.get("redis")
a = {1L: 0.57735026918962573, 2L: 0.57735026918962573, 6L: 0.57735026918962573}
print kw_compute(a)

database_kw = Keyword.get("database")
a = {1L: 0.3867406571480686, 2L: 0.3867406571480686, 5L: 0.3867406571480686, 6L: 0.3867406571480686, 7L: 0.44817778639437278, 9L: 0.44817778639437278}
print kw_compute(a)

