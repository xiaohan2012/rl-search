import os
import MySQLdb
from json import loads
from setting import MYSQL_CONN_SETTING
from boilerpipe.extract import Extractor

from codecs import open

from difflib import  SequenceMatcher, Differ, IS_CHARACTER_JUNK, IS_LINE_JUNK
from pprint import pprint

import string

import numpy as np

d = Differ(linejunk = IS_LINE_JUNK, charjunk = IS_CHARACTER_JUNK)

def main(limit = 10, extractor_name = 'ArticleExtractor'):    
    conn = MySQLdb.connect(**MYSQL_CONN_SETTING)
    c = conn.cursor()
    c.execute('SELECT url, plainTextContent,uncompress(crawled_html) from webpage where !isnull(crawled_html) and length(crawled_html) > 0 and !isnull(plainTextContent) and length(plainTextContent) > 0 limit %s', (limit, ))
    stat = {
        'diff': {
            'm': [], 'b': []
        },
        'seq_match': {
            'm': [], 'b': []
        }
    }
    counter = 0
    
    url_file = open('urls.txt', 'w')
    
    while True:
        row = c.fetchone()
        if row is None:
            break
        url = row[0]
        m_content = row[1]
        html = row[2]
        
        if html is None: #data might be corrupted
            continue
            
        counter += 1
        
        
        def is_empty(s):#remove the punctuations as well as spaces 
            exclude = list(string.punctuation) + ['\n', ' ', '\t'] 
            return len([c for c in s if c not in exclude]) != 0

        if os.path.exists('content_samples/o%d.txt' %counter):
            print counter, url
            url_file.write('%d: %s\n' %(counter, url))
            if not os.path.exists('content_samples/m%d.txt' %counter):
                with open('content_samples/m%d.txt' %counter, 'w', 'utf8') as f:
                    f.write(m_content)
            #if not os.path.exists('content_samples/b%d.txt' %counter):
            extractor = Extractor(extractor=extractor_name, html=html)
            b_content = extractor.getText()
            
            with open('content_samples/b%d.txt' %counter, 'w', 'utf8') as f:
                f.write(b_content)
            
            is_junk = lambda x: len(''.join(x.strip().split())) == 0    
            olines = open('content_samples/o%d.txt' %counter, 'r', 'utf8').readlines()
            mlines = open('content_samples/m%d.txt' %counter, 'r', 'utf8').readlines()
            blines = open('content_samples/b%d.txt' %counter, 'r', 'utf8').readlines()
            o_char_count = float(sum([len(l) for l in olines]))
            m_char_count = float(sum([len(l) for l in mlines]))
            b_char_count = float(sum([len(l) for l in blines]))
            
            diffs = [diff for diff in list(d.compare(olines, mlines)) if is_empty(diff[2:])]
            # pprint(diffs)
            acc =  1 - sum([len(diff[2:]) for diff in diffs if diff[0] in ['+', '-'] and is_empty(diff[2:])]) / (o_char_count + m_char_count)
            print 'using diff'
            print 'original and mbrain: %f' %acc
            stat['diff']['m'].append(acc)
            
            
            diffs = [diff for diff in list(d.compare(olines, blines)) if is_empty(diff[2:])]
            # pprint(diffs)
            acc = 1 - sum([len(diff[2:]) for diff in diffs if diff[0] in ['+', '-'] and is_empty(diff[2:])]) / (o_char_count + b_char_count)
            stat['diff']['b'].append(acc)
            print 'original and pipeboiler: %f' %acc

            print 'using sequence matcher'
            o_text = open('content_samples/o%d.txt' %counter, 'r', 'utf8').read()
            m_text = open('content_samples/m%d.txt' %counter, 'r', 'utf8').read()
            b_text = open('content_samples/b%d.txt' %counter, 'r', 'utf8').read()
            s = SequenceMatcher(IS_CHARACTER_JUNK, o_text, m_text)
            score = s.ratio()
            stat['seq_match']['m'].append(score)
            print 'original and mbrain: %f' %score

            s = SequenceMatcher(IS_CHARACTER_JUNK, o_text, b_text)
            score = s.ratio()
            stat['seq_match']['b'].append(score)
            print 'original and boiler: %f\n' %score

    print '\nSummary:'
    print 'Tested %d webpages' %len(stat['diff']['m'])
    print 'Diff-based evaluation:'
    print 'mbrain accuracy mean=%f\nboiler pipe accuracy mean=%f\n' %(np.mean(stat['diff']['m']), np.mean(stat['diff']['b']))
    print 'mbrain accuracy median=%f\nboiler pipe accuracy median=%f\n' %(np.median(stat['diff']['m']), np.median(stat['diff']['b']))

    print 'Sequence matcher evaluation:'
    print 'mbrain ratio mean=%f\nboiler pipe ratio mean=%f\n' %(np.mean(stat['seq_match']['m']), np.mean(stat['seq_match']['b']))
    print 'mbrain ratio median=%f\nboiler pipe ratio median=%f\n' %(np.median(stat['seq_match']['m']), np.median(stat['seq_match']['b']))
    url_file.close()
if __name__ == "__main__":
    import sys
    extractor = sys.argv[1]
    print 'Using %s' %extractor 
    extractors = ['DefaultExtractor',
                  'ArticleExtractor',
                  'ArticleSentencesExtractor',
                  'KeepEverythingExtractor',
                  'KeepEverythingWithMinKWordsExtractor',
                  'LargestContentExtractor',
                  'NumWordsRulesExtractor',
                  'CanolaExtractor']
    if extractor not in extractors:
        print 'Invalid extractor, should be %s' %(repr(extractors))
        sys.exit(-1)

    main(40, extractor)
