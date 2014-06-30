
import pickle
import torndb
import json

conn = torndb.Connection("%s:%s" % ('ugluk', 3306), 'scinet3', 'hxiao', 'xh24206688')

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

if __name__ == "__main__":
    # corp = json.load(open('corpus_collection/corpus_collection/john.json', 'r'))
    # corp = filter(lambda doc: len(doc['keywords']) > 0, corp)
    # import_corpus(corp, 'john')

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
     
