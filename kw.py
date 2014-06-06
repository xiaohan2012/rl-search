"""
keyword related stuff
"""

import MySQLdb, nltk
from json import dumps, loads
from pickle import dump
from setting import MYSQL_CONN_SETTING
from collections import Counter,defaultdict

def get_kw_stat(table = 'brown'):
    """
    return hist keyword and hist for #document that have i keywords
    """
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    
    x = conn.cursor()    
    kw_stat = Counter()
    doc_stat = Counter()
    x.execute('SELECT processed_keywords from %s' %table)

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

def reduce_kw(kw_by_freq, le = 1, ge=200, table="brown"):
    """
    remove keywords of which the frequency is less than threshold
    <= le or > ge
    """
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    
    x = conn.cursor()
    cu = conn.cursor() #cursor for update
    
    #construct speed to make the lookup faster
    #keywords we will remove
    kw_rm_flag = dict([(kw, True)  #too rare keywords
                       for kw in reduce(lambda acc, freq: acc + kw_by_freq[freq], xrange(le+1), [])])
    
    kw_rm_flag.update(dict([(kw, True) #too frequent keywords
                       for kw in reduce(lambda acc, freq: acc + kw_by_freq[freq] if kw_by_freq.has_key(freq) else acc, 
                                        xrange(ge, max(kw_by_freq.keys())+1), [])]))
    
    #update with keywords we will save
    kw_rm_flag.update(dict([(kw, False) 
                            for kw in reduce(lambda acc, freq: acc + kw_by_freq[freq], xrange(le + 1, ge), [])]))

    x.execute('SELECT id, processed_keywords from %s' %table)

    counter = 0
    while True:
        row = x.fetchone()
        if not row:
            break
        id, kws = row[0], loads(row[1])

        remain_kws = [kw for kw in kws if not kw_rm_flag[kw]]
        
        sql = 'UPDATE %s SET processed_keywords = %%s WHERE id=%%s' %table
        cu.execute(sql, (dumps(remain_kws), id))
        conn.commit()
        
        counter += 1

        if counter % 1000 == 0:
            pass
            #print '%d rows processed' %(counter)
    conn.close()


# Used when tokenizing words
sentence_re = r'''(?x)      # set flag to allow verbose regexps
([A-Z])(\.[A-Z])+\.?  # abbreviations, e.g. U.S.A.
| \w+(-\w+)*            # words with optional internal hyphens
| \$?\d+(\.\d+)?%?      # currency and percentages, e.g. $12.40, 82%
| \.\.\.                # ellipsis
| [][.,;"'?():-_`]      # these are separate tokens
'''
     
lemmatizer = nltk.WordNetLemmatizer()
stemmer = nltk.stem.porter.PorterStemmer()
    
#Taken from Su Nam Kim Paper...
grammar = r"""
    NBAR:
        {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
        
    NP:
        {<NBAR>}
        {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
"""
chunker = nltk.RegexpParser(grammar)

def extract(text): 
    """
    some simple algorithm for keyword extraction
    """    
     
    toks = nltk.regexp_tokenize(text, sentence_re)
    postoks = nltk.tag.pos_tag(toks)
     
    # print postoks
     
    tree = chunker.parse(postoks)
     
    from nltk.corpus import stopwords
    stopwords = stopwords.words('english')
     
     
    def leaves(tree):
        """Finds NP (nounphrase) leaf nodes of a chunk tree."""
        for subtree in tree.subtrees(filter = lambda t: t.node=='NP'):
            yield subtree.leaves()
     
    def normalise(word):
        """Normalises words to lowercase and stems and lemmatizes it."""
        word = word.lower()
        word = stemmer.stem_word(word)
        word = lemmatizer.lemmatize(word)
        return word
     
    def acceptable_word(word):
        """Checks conditions for acceptable word: length, stopword."""
        accepted = bool(2 <= len(word) <= 40
                        and word.lower() not in stopwords)
        return accepted
     
     
    def get_terms(tree):
        for leaf in leaves(tree):
            term = [ normalise(w) for w,t in leaf if acceptable_word(w) ]
            yield term
     
    terms = get_terms(tree)
        
    return [word 
            for term in terms 
            for word in term]

if __name__ == "__main__":
    kw_stat, doc_stat = get_kw_stat()
    print 'kw_stat', len(kw_stat)
    total_docs = sum(doc_stat.values())

    kw_by_freq = group_kw_by_freq(kw_stat)
    
    print '#docs,%d' %(total_docs)
    print 'Frequency, #keywords, percentage'
    for key in sorted(kw_by_freq.keys()):
        print "%d,%d,%f" %(key, len(kw_by_freq[key]), len(kw_by_freq[key])/float(len(kw_stat)))
    
    # print '#keyword, #docs'
    # for freq, doc_count in sorted(doc_stat.items()):
    #     print "%d,%d,%f" %(freq, doc_count, doc_count/float(total_docs))
        
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
    
    #reduce_kw(kw_by_freq, 4, 200)
    
    #dump(stat, open('pickles/kw_freq.pickle', 'w'))
    #dump(stat, open('pickles/kw_by_freq.pickle', 'w'))
