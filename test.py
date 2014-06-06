"""
Get the K matrix
"""
import MySQLdb, os, random
import db, params
from json import loads
from pickle import dump, load

from scipy.sparse import lil_matrix


conn = db.get_conn()
x = conn.cursor()

kw_path = 'kws.pickle'

#get all keywords
#if there, load it
#otherwise, generate and save
if os.path.exists(kw_path):
    print 'there, load it'
    all_keywords = load(open(kw_path, 'r'))    
else:
    print 'not there, generate it'
    x.execute("SELECT keywords from webpage;")

    all_keywords = set();

    for row in x:
        kws = loads(row[0])
        for kw in kws:
            all_keywords.add(kw.lower())
    print len(all_keywords)
    dump(all_keywords, open(kw_path, 'w'))
    conn.commit()

all_keywords = sorted(list(all_keywords))

#build the keyword to index mapping
#so that the index can be retrieved faster

kw_ind_map = dict((kw, ind) for ind, kw in enumerate(all_keywords))

#get the number of documents
x = conn.cursor()
x.execute("SELECT count(id) from webpage;")

row_c = x.fetchone()[0]; 
#preallocate the space for doc isd
#mapping from doc ind to the matrix row index
doc_id2row = {}

col_c = len(all_keywords)
print row_c, "x", col_c, "matrix"

K = lil_matrix((row_c, col_c))

#generate the matrix
x = conn.cursor()
x.execute("SELECT id, keywords from webpage;")

for ind, r in enumerate(x):
    wid = r[0]
    doc_id2row[wid] = ind #save the which row is doc associated with
    for kw in loads(r[1]):
        kwid = kw_ind_map[kw.lower()]
        K[wid, kwid] = 1

#Convert the matrix using TF-IDF 
#but first, I need to how it works

#so now we have the K matrix

M = 5; N = 20;

#select the first M keywords 
#and make a keyword -> relevance score dict
#the relevance scores are initialized as 0
selected_kws = random.sample(all_keywords, M)
kw_rel = dict([(kw, 0) for kw in selected_kws]) 

#select the first N docs
#and make a doc -> relevance score dict
#the relevance scores are initialized as 0
selected_doc_ids = random.sample(doc_ids, N)
doc_rel = dict([(doc_id, 0) for doc_id in selected_doc_ids]) 

#get the docs by id 
print "get the docs by id"

#Some AJAX
#display both the keywords as well as documents to the user

#the browser side
#the user can give feedback to both keywords and documents
#also the feedback from keywords as well as documents can influence each other
#For example:
#When user favors  some keyword by clicking, then documents containing the keyword should receive some positive feedback
#Or when the user favors some doc by clicking, then keywords associating with the doc should receive some positive feedback as well

#the server receives the feedbacks
kw_fb = req.get_param('kw_fb') #[[kw1, score1], [kw2, score], ...]
doc_fb = req.get_param('doc_fb') #[[doc1_id, score1], [doc2_id, score], ...]

for kw,fb in kw_fb:
    kw_rel[kw] = fb

for doc,fb in doc_fb:
    doc_rel[doc] = fb

#Before that we can compute the linear regression part, (K^T * K + mu * I)^{-1} * X^T
#as this part is commonly used
#do the LinRel part for keywords
#for each keyword, compute its uppder confidence bound

for doc in doc_ids:
    
#do the LinRel part for documents
