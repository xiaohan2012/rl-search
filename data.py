import MySQLdb, os, random

from json import loads
from pickle import dump, load

from scipy.sparse import lil_matrix
from sklearn.feature_extraction.text import TfidfTransformer

from setting import MYSQL_CONN_SETTING

def get_all_keywords(table="brown", refresh = True):
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    x = conn.cursor()

    kw_path = 'pickles/kws.pickle'

    #get all keywords
    #if there, load it
    #otherwise, generate and save
    print 'Getting keyword dictionary..'
    if os.path.exists(kw_path) and not refresh:
        print 'there, load it'
        all_keywords = load(open(kw_path, 'r'))    
    else:
        print 'not there, generate it'
        x.execute("SELECT processed_keywords from %s;" %table)

        all_keywords = set();

        for row in x:
            kws = loads(row[0])
            for kw in kws:
                all_keywords.add(kw.lower())
        print len(all_keywords)
        dump(all_keywords, open(kw_path, 'w'))
        conn.commit()

    return sorted(list(all_keywords))

def kw2doc_matrix(table="brown", tfidf=True, refresh = False):
    """
    get keyword to document matrices as well as the transpose
    if tfidf is True, perform tfidf on both matrix
    """
    pic_path = 'pickles/linrel_matrix.pic'
    if os.path.exists(pic_path) and not refresh:
        print 'linrel matrix pickle exists, load it'
        return load(open(pic_path))
    else:
        print 'linrel matrix pickle NOT exist, generate it'
        all_keywords= get_all_keywords(table)

        #mapping from keyword to index
        kw_ind_map = dict((kw, ind) for ind, kw in enumerate(all_keywords))

        #get the number of documents
        conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
        x = conn.cursor()
        x.execute("SELECT count(id) from %s;" %table)

        doc_c = x.fetchone()[0]; 
        #preallocate the space for doc isd
        #mapping from doc ind to the matrix row index
        doc_id2row = {}

        kw_c = len(all_keywords)
        print kw_c, "x", doc_c, "matrix"

        kw2doc_m = lil_matrix((kw_c, doc_c))

        #generate the matrix
        x = conn.cursor()
        x.execute("SELECT id, processed_keywords from %s;" %table)
        
        print 'loading matrix..'
        for ind, r in enumerate(x):
            doc_id = r[0]
            doc_id2row[doc_id] = ind #save the which row is doc associated with
            for kw in loads(r[1]):
                kdoc_id = kw_ind_map[kw.lower()]
                kw2doc_m[kdoc_id, ind] += 1
        print 'loading matrix done'
        doc2kw_m = kw2doc_m.T #just transpose it
        
        if tfidf:
            print 'tfidf...'
            transformer = TfidfTransformer()
            doc2kw_m = transformer.fit_transform(doc2kw_m)
            kw2doc_m = transformer.fit_transform(kw2doc_m)
            print 'tfidf done'
        return_val = {"kw_ind": kw_ind_map,
                      "doc_ind": doc_id2row,
                      "doc2kw_m": doc2kw_m, 
                      "kw2doc_m": kw2doc_m}
        dump(return_val, open(pic_path, 'w'))
        return return_val
    
if __name__ == "__main__":
    d_ = kw2doc_matrix()
