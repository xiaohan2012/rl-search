"""
keyword related stuff
"""

import MySQLdb
from json import dumps, loads
from pickle import dump
from setting import MYSQL_CONN_SETTING
from collections import Counter,defaultdict

def get_kw_stat():
    """
    return hist keyword and hist for #document that have i keywords
    """
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    
    x = conn.cursor()
    table = 'test_webpage'
    kw_stat = Counter()
    doc_stat = Counter()
    x.execute('SELECT crawled_keywords from %s' %table)

    counter = 0
    while True:
        row = x.fetchone()
        if not row:
            break
        kws = loads(row[0])
        for kw in kws:
            kw_stat[kw] += 1

        doc_stat[len(kws)] += 1
        
        counter += 1

        if counter % 1000 == 0:
            pass
            # print '%d rows processed' %(counter)>
    conn.close()
    return kw_stat, doc_stat

def group_kw_by_freq(stat):
    """
    group the kw by freq
    """
    group = defaultdict(list)
    for kw, freq in stat.items():
        group[freq].append(kw)
    return group

def reduce_kw(kw_by_freq, threshold = 1):
    """
    remove keywords of which the frequency is less than threshold
    """
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    
    x = conn.cursor()
    cu = conn.cursor() #cursor for update
    
    table = 'test_webpage'

    #construct speed to make the lookup faster
    #keywords we will remove
    kw_rm_flag = dict([(kw, True) 
                       for kw in reduce(lambda acc, freq: acc + kw_by_freq[freq], xrange(threshold+1), [])])
    
    #update with keywords we will save
    kw_rm_flag.update(dict([(kw, False) 
                            for kw in reduce(lambda acc, freq: acc + kw_by_freq[freq], xrange(threshold + 1, max(kw_by_freq.keys()) + 1), [])]))

    x.execute('SELECT id, crawled_keywords from test_webpage')

    counter = 0
    while True:
        row = x.fetchone()
        if not row:
            break
        id, kws = row[0], loads(row[1])

        remain_kws = [kw for kw in kws if not kw_rm_flag[kw]]
        
        sql = 'UPDATE %s SET crawled_keywords = %%s WHERE id=%%s' %table
        cu.execute(sql, (dumps(remain_kws), id))
        conn.commit()
        
        counter += 1

        if counter % 1000 == 0:
            pass
            #print '%d rows processed' %(counter)
    conn.close()

if __name__ == "__main__":
    kw_stat, doc_stat = get_kw_stat()
    total_docs = sum(doc_stat.values())

    kw_by_freq = group_kw_by_freq(kw_stat)
    
    print '#docs,%d' %(total_docs)
    print 'Frequency, #keywords, percentage'
    for key in sorted(kw_by_freq.keys()):
        print "%d,%d,%f" %(key, len(kw_by_freq[key]), len(kw_by_freq[key])/float(len(kw_stat)))
    
    print '#keyword, #docs'
    for freq, doc_count in sorted(doc_stat.items()):
        print "%d,%d,%f" %(freq, doc_count, doc_count/float(total_docs))
        
    # print """
    # kw_y=%s;
    # doc_y=%s;
    # figure(1);
    # title('kw');
    # hist(kw_y)
    
    # figure(2);
    # title('doc');
    # hist(doc_y)
    # """ %(repr([len(kw_by_freq[freq]) for freq in sorted(kw_by_freq.keys())]),
    #       repr([doc_stat[freq] for freq in sorted(doc_stat.keys())])
    # )
    
    #reduce_kw(kw_by_freq, 1)
    
    #dump(stat, open('pickles/kw_freq.pickle', 'w'))
    #dump(stat, open('pickles/kw_by_freq.pickle', 'w'))
