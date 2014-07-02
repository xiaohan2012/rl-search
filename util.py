
import pickle
import torndb
import json
from tabulate import tabulate

conn = torndb.Connection("%s:%s" % ('ugluk', 3306), 'archive', 'hxiao', 'xh24206688')

def import_corpus(corpus, table_name):
    """
    import corpus: list of docs
    into table_name
    """
    conn.execute('TRUNCATE TABLE %s' %table_name)
    conn.execute('ALTER TABLE %s AUTO_INCREMENT = 1' %table_name)
    for text in corpus:
        
        fields = []
        values = []
        if text.has_key('keywords'):
            fields.append('keywords')
            values.append(json.dumps(text['keywords']));

        if text.has_key('title'):
            fields.append('title')
            values.append(text['title'])

        if text.has_key('url'):
            fields.append('url')
            values.append(text['url'])

        sql_temp = "INSERT INTO %s(%s) values(%s)" %(table_name, ','.join(fields), ','.join(['%s'] * len(fields)))
        conn.execute(sql_temp, *values)

import numpy as np

def get_weights(M, row_idx, col_ind2id_map, row_ind2id_map, col_idx = None):
    """
    Generic function that gets the weights for docs/kws associated with kws/docs
    
    Params:
    M: data matrix, each row for each object
    row_idx: the matrix row indices to be considered
    col_ind2id_map: map from matrix **column** index to object id
    row_ind2id_map: map from matrix **row** index to object id
    col_idx(optional): the matrix column indices(features) to be considered

    Return:
    {'row_obj_id': [{'id': 'col_obj_id', 'w': 'weight value in M'}, ...], ...}
    """
        
    data = {}
    for row_ind in row_idx:
        row = M[row_ind, :]
        
        #get the indices of those column  whose vlaue are non-zero
        _, nonzero_col_idx = np.nonzero(row[0,:])
        
        if col_idx is not None:
            nonzero_col_idx = list(set(nonzero_col_idx).intersection(set(col_idx)))#intersection

        weights = row.toarray()[0, nonzero_col_idx]
        
        #map index to col object id
        col_ids = [col_ind2id_map[col_ind] for col_ind in nonzero_col_idx]
        
        #get the matrix value
        value = [{'id': col_id, 'w': weight} 
                 for col_id, weight in zip(col_ids, weights)]
        
        data[row_ind2id_map[row_ind]] = value
    return data

def tabulize(data):
    """
    Param:
    data: dict(key(str)->list of float) 
    
    Output:
    key1 val1 val2
    key2 val1 val2
    """
    result_str = ''
    keys = sorted(data.keys())
    for key in keys:
        array = data[key]
        number_str = '\t'.join(["%.6s" %num for num in array])
        result_str += "%s\t%s\n" %(str(key).ljust(20), number_str)

    return result_str

def iter_summary(kw_score_hist, kw_explr_score_hist, kw_explt_score_hist,
                 doc_score_hist, doc_explr_score_hist, doc_explt_score_hist,
                 kw_fb_hist, doc_fb_hist,
                 kw_dict,
                 doc_dict):
    """
    kw_dict: {'kw_id': kw_obj}  dict
    doc_dict: {'doc_id': doc_obj}  dict
    
    Output is like:
         explr explt total fb |      explr explt total fb
    id:   .7    .3    1   .8   id:  .8     .3    1.1  .9
       ....
    """
    def get_col(data, i):
        return dict([(id, array[i]) for id, array in data.items()])
        
    def make_rows(keys, getter, *cols):
        return [[unicode(getter[key])] + ['%.3f' %col.get(key, 0) for col in cols]
                for key in keys]

    def make_tbl(explt_score_hist, explr_score_hist, scores, fb, getter):
        explt_score_hist_at_i = get_col(explt_score_hist, i)
        explr_score_hist_at_i = get_col(explr_score_hist, i)
        scores_at_i = get_col(scores, i)
        keys = sorted(explr_score_hist_at_i.keys())
        rows = make_rows(keys, getter, explt_score_hist_at_i, explr_score_hist_at_i, scores_at_i, fb)
        tbl = tabulate(rows,
                       headers = ['id', 'explt', 'explr', 'total', 'fb']) 
        return tbl

    iter_n = len(kw_fb_hist)
    iter_tbls = []
    for i in xrange(iter_n):        
        print 'Iter %d' %i
        kw_tbl = make_tbl(kw_explt_score_hist, kw_explr_score_hist, kw_score_hist, kw_fb_hist[i], kw_dict)
        doc_tbl = make_tbl(doc_explt_score_hist, doc_explr_score_hist, doc_score_hist, doc_fb_hist[i], doc_dict)
        print kw_tbl
        print
        print doc_tbl
        print

def test_iter_summary():
    kw_scores = {'kw1': [.1, .2], 'kw2': [.2, 0.3]}
    kw_explr_scores = {'kw1': [.05, .15], 'kw2': [.1, 0.1]}
    kw_explt_scores = {'kw1': [.05, .05], 'kw2': [.1, 0.2]}
    
    
    doc_scores = {'doc1': [.1, .2], 'doc2': [.2, 0.3]}
    doc_explr_scores = {'doc1': [.05, .15], 'doc2': [.1, 0.11]}
    doc_explt_scores = {'doc1': [.05, .05], 'doc2': [.1, 0.2]}
    
    kw_fbs = [{'kw1': .1, 'kw2': .2}, {'kw1': .3, 'kw2': .1}]
    doc_fbs = [{'doc1': .1, 'doc': .2}, {'doc1': .3, 'doc': .1}] 
    
    iter_summary(kw_scores, kw_explr_scores, kw_explt_scores,
                 doc_scores, doc_explr_scores, doc_explt_scores,
                 kw_fbs, doc_fbs)

def test_get_weight():
    from data import kw2doc_matrix
    d = kw2doc_matrix(table='test', keyword_field_name = 'processed_keywords') 
    
    print get_weights(d._kw2doc_m, 
                      [0,1], 
                      d._doc_ind_r,
                      d._kw_ind_r, 
                      col_idx = None)

    print get_weights(d._kw2doc_m, 
                      [0,1], 
                      d._doc_ind_r,
                      d._kw_ind_r, 
                      col_idx = [0,1,5])
     

def remove_keywords(table, exclude = {None}, keyword_field_name='processed_keywords'):
    """
    remove certain keywords in exclude from the documents in the `table`
    """
    for row in conn.query("select id, %s from %s" %(keyword_field_name, table)):
        print row['id']
        filtered_kws = [kw for kw in json.loads(row[keyword_field_name]) if kw not in exclude]
        conn.execute("UPDATE %s SET %s = %%s where id=%%s" %(table, keyword_field_name), json.dumps(filtered_kws), row['id'])


if __name__ == "__main__":
    # corp = json.lad(open('corpus_collection/corpus_collection/john.json', 'r'))
    # corp = filter(lambda doc: len(doc['keywords']) > 0, corp)
    # import_corpus(corp, 'john')
    remove_keywords('archive', keyword_field_name="keywords")
