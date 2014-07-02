import torndb, os, random, types

from json import loads, dumps
from pickle import dump, load

from scipy.sparse import lil_matrix
from sklearn.feature_extraction.text import TfidfTransformer

from setting import MYSQL_CONN_SETTING

def get_all_keywords(db='archive', table="brown", keyword_field_name = "processed_keywords", refresh = False):
    db = torndb.Connection("%s:%s" % (MYSQL_CONN_SETTING['host'], MYSQL_CONN_SETTING['port']), db, MYSQL_CONN_SETTING['user'], MYSQL_CONN_SETTING['passwd'])
    
    kw_path = 'pickles/%s-kws.pickle' %table

    #get all keywords
    #if there, load it
    #otherwise, generate and save
    print 'Getting keyword dictionary..'
    if os.path.exists(kw_path) and not refresh:
        print 'there, load it'
        all_keywords = load(open(kw_path, 'r'))    
    else:
        print 'not there, generate it'
        
        all_keywords = set();

        for row in db.query("SELECT %s from %s;" %(keyword_field_name, table)):
            kws = loads(row[keyword_field_name])
            for kw in kws:
                all_keywords.add(kw.lower())
        print len(all_keywords)
        dump(all_keywords, open(kw_path, 'w'))
        
    db.close()
    return sorted(list(all_keywords))

def get_test_data():
    return [{'title': 'redis: key-value-storage database (ONE)',
             'keywords': 'redis database a'.split()},
            {'title': 'redis: key-value-storage database (TWO)',
             'keywords': 'redis database the'.split()},
            {'title': 'tornado: python  web framework(ONE)',
             'keywords': 'tornado web python a'.split()},
            {'title': 'tornado: python  web framework(TWO)',
             'keywords': 'tornado python web the'.split()},
            {'title': 'torndb: python mysql wrapper',
             'keywords': 'python database mysql'.split()},
            {'title': 'pyredis: python redis wrapper',
             'keywords': 'python database redis'.split()},
            {'title': 'mysql: relational database',
             'keywords': 'database mysql'.split()},
            {'title': 'some python page',
             'keywords': 'python a'.split(),},
            {'title': 'some database page',
             'keywords': 'database the'.split(),},
            {'title': 'some random page',
             'keywords': 'web the'.split()}
    ]
    
def insert_test_data(test_data, table = "test"):
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    x = conn.cursor()
    # x.execute('TRUNCATE %s' %test)
    for row in test_data:
        x.execute('INSERT INTO %s(title, keywords) VALUES(%%s, %%s)' %(table), (row['title'], dumps(row['keywords'])))
        conn.commit()
        
def test_matrix():
    docs = list(enumerate(['redis database key-value-storage redis database redis a the the'.split(),
                           'redis database redis a the the'.split(),
                           'tornado web python tornado a the'.split(),
                           'tornado python web web python tornado a the a the'.split(),
                           'python a the  the'.split(),
                           'database a a the'.split(),
                           'web a the a the'.split()]))
    kws = set([w for id, doc in docs  
               for w in doc])
    kw2doc_m = lil_matrix((len(kws), len(docs)))

    return gen_kw_doc_matrix(docs, keywords = kws)


def gen_kw_doc_matrix(docs, keywords, kw_field_name, doc_n = None, tfidf=True):
    """
    build the kw2doc, doc2kw and kw/doc_id to kw/doc_row_index mapping
    docs: list of dict
    """
    kw_ind_map = dict((kw, ind) for ind, kw in enumerate(keywords)) #keyword to row index mapping
    doc_ind_map = {}

    #if doc number is not given, get it
    if doc_n is None and not isinstance(docs, types.GeneratorType):
        doc_n = len(docs) 
    kw2doc_m = lil_matrix((len(keywords), doc_n))
    
    for doc_ind, doc in enumerate(docs):
        doc_id = doc['id']
        doc_ind_map[doc_id] = doc_ind #save the which row is doc associated with
        keywords = doc[kw_field_name]
            
        for kw in keywords:
            kw_ind = kw_ind_map[kw.lower()]
            kw2doc_m[kw_ind, doc_ind] += 1

    kw2doc_m = kw2doc_m.tocsr() #to Compressed Sparse Column format for faster row indexing and arithmatic operation    
    doc2kw_m = kw2doc_m.T #just transpose it
    if tfidf:
        print 'tfidf...'
        transformer = TfidfTransformer()
        doc2kw_m = transformer.fit_transform(doc2kw_m)
        kw2doc_m = transformer.fit_transform(kw2doc_m)
        print 'tfidf done'

    return {"kw_ind": kw_ind_map,
            "doc_ind": doc_ind_map,
            "doc2kw_m": doc2kw_m, 
            "kw2doc_m": kw2doc_m}

def kw2doc_matrix(db="archive", table="brown", keyword_field_name = 'processed_keywords', keywords = None, tfidf=True, refresh = False):
    """
    get keyword to document matrices as well as the transpose
    if tfidf is True, perform tfidf on both matrix
    """
    pic_path = 'pickles/%s_linrel_matrix.pic' %table
    if os.path.exists(pic_path) and not refresh:
        print 'linrel matrix pickle exists, load it'
        return KwDocData(**load(open(pic_path)))
    else:
        print 'linrel matrix pickle NOT exist, generate it'
        all_keywords= get_all_keywords(db, table, keyword_field_name = keyword_field_name)

        #get the number of documents
        db = torndb.Connection("%s:%s" % (MYSQL_CONN_SETTING['host'], MYSQL_CONN_SETTING['port']), db, MYSQL_CONN_SETTING['user'], MYSQL_CONN_SETTING['passwd']) 
        doc_n = db.get("SELECT count(id) from %s;" %table)['count(id)']

        #generate the matrix
        docs = db.query("SELECT id, %s from %s;" %(keyword_field_name, table))
        for doc in docs:
            doc[keyword_field_name] = loads(doc[keyword_field_name])#parse the json raw string

        return_val = gen_kw_doc_matrix(docs, all_keywords, keyword_field_name, doc_n = doc_n)
        
        dump(return_val, open(pic_path, 'w'))
        db.close()
        return KwDocData(**return_val)


class KwDocData(object):
    """
    data wrapper associated with keyword and document
    """
    @property
    def _kw2doc_m(self):
        return self.__kw2doc_m

    @property
    def _doc2kw_m(self):
        return self.__doc2kw_m

    @property
    def _kw_ind(self):
        return self.__kw_ind

    @property
    def _doc_ind(self):
        return self.__doc_ind

    @property
    def _kw_ind_r(self):                
        if self.__kw_ind_r is None:#cache it if not exist
            self.__kw_ind_r = dict([(ind, kw ) for kw, ind in self.__kw_ind.items()])
        return self.__kw_ind_r

    @property
    def _doc_ind_r(self):
        if self.__doc_ind_r is None:#cache it if not exist
            self.__doc_ind_r = dict([(ind, doc_id ) for doc_id, ind in self.__doc_ind.items()])
        return self.__doc_ind_r

    def __init__(self, kw_ind, doc_ind, kw2doc_m, doc2kw_m):
        """
        kw_ind: keyword id to matrix row index mapping
        doc_ind: doc id to matirx row index mapping
        doc2kw_m: doc to keyword matrix
        kw2doc_m: keyword to doc matrix
        """
        self.__doc2kw_m = doc2kw_m
        self.__kw2doc_m = kw2doc_m
        
        self.__kw_ind = kw_ind
        self.__doc_ind = doc_ind
        
        self.__kw_ind_r = None
        self.__doc_ind_r = None        

if __name__ == "__main__":
    # d = test_matrix()
    # print d['doc2kw_m'].toarray()
    # print d['kw_ind']
    insert_test_data(get_test_data())
