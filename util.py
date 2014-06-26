
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
        

if __name__ == "__main__":
    # corp = pickle.load(open('pickles/corpus_2000.pickle'))
    # corp = ({'keywords': [word
    #                       for word in text.split(',') if len(word) > 0]}
    #         for text in corp)
    
    
    corp = json.load(open('corpus_collection/corpus_collection/john.json', 'r'))
    corp = filter(lambda doc: len(doc['keywords']) > 0, corp)
    import_corpus(corp, 'john')
