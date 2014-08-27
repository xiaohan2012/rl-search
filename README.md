
hiit-scinet3
============

System working flow:
1, User starts by typing search query
2, Server respondes with a set of documents and keywords
3, User interacts with the app and clicks the keywords&documents he likes. 
4, Server receives the feedback, refines the search result and return them to user. Go to step 3


Important components:
1, the document/keyword recommender engine, which corresponds to server side code, `engine.py`
2, the feedback manager that determines how feedback from documents/keywords propagate to keywords/feedback, which corresponds to browser side code, `static/js/starter.js`
3, the main web app that glues all above together, which corresponds to `main.py`

Main software/library used:
1, Tornado, Python Web framework
2, MySQL, documents&keywords data storage
3, Redis, key-value database that handles the user interaction session
4, numpy, Python numerical library

Interface


Running the app

python main.py [--param_name1=param_value1] [--param_name2=param_value2] ...
If parameters are not specified, they are set on their default values.

One typical use is:

python main.py --table=archive_500 --recom_doc_num=10 --recom_kw_num=10 --samp_kw_num=5 --samp_doc_num=5 --linrel_doc_c=1 --linrel_kw_c=1

Please use this one for now.


The set of parameters to control the document/keyword recommendation are:

1. recom_kw_num:  recommended keyword number at each iter
2. recom_doc_num:  recommended document number at each iter
3. samp_kw_num:  sampled keyword number from documents
4. samp_doc_num:  extra document number apart from the recommended ones
5. linrel_kw_mu  Value for \mu in the linrel algorithm for keyword
6. linrel_kw_c  Value for c in the linrel algorithm for keyword
7. linrel_doc_mu Value for \mu in the linrel algorithm for document
8. linrel_doc_c  Value for c in the linrel algorithm for document

Basic system setup parameters are:

1. port:  the given port  the web app runs on
2. mysql_port:  database's port 
3. mysql_host: database host
4. mysql_user:  database user
5. mysql_password:   database password
6. mysql_databas:  database name
7. redis_port:  redis' port 
8. redis_host: key-value cache host
9. redis_db: key-value db

table:  db table to be used
refresh_pickle: refresh pickle or not

Feedback 

Thumb of rule

Let's define:
 explicit feedback: the feedback user gives to either the keyword or the document by clicking. For example, if the user clicks keyword Python, Python receives feedback 1
 implicit feedback: the feedback received through feedback propagation. For example, if user clicks some document, then the keywords associated with the document receives some implicit feedback.
 final feedback: which consists of the explicit feeedback and implicit one and it is the value returned to the server.

Thumb of rule on feedback propagation is:
If the keyword/document has receives some explicit feedback, any implicit feedback to it will not contribute to the final feedback. 
Otherwise, the final feedback value will only consider the implicit part.

The intuition of this design is: if the user is quite sure/explicit about the preference over something, any guessing(implicit) is not necessary. Implicit guessing is only used when there is not enough information.

Numerical calculation
Explicit feedback is discrete can only be 1 or 0. It is 1, if the object is clicked and 0 otherwise
Implicit feedback is continuous, from 0 to 1.

Using keyword to illustrate how implicit feedback calculation is done. If $kw_i$ is associted with $doc_1 \cdots \doc_k$(they contain $kw_i$), the implicit feedback value for $kw_i$ is:

\sum{tfidf value of $doc_j$ on $kw_i$ \cdot I(doc_j, kw_i)}

where I(doc_j, kw_i) is an indicator function giving 1 if kw_i in doc_j is clicked and 0 otherwise.

Implicit feedback calculation on document is the same, except using the tf-idf value of keyword on document.

Keyword&document recommendation

Query-based recommender

This is used as initial starting point of the app when user searches by inputing some query. See QueryBasedRecommender in engine.py for the actual code.

The process goes like this:
1, select the 'recom_doc_num' docs by ranking them by the similarity scores to the query. 
2, sample `recom_kw_num` keywords from docs in Step 1.
3, sample `samp_kw_num` keywords from any docs that share any keywords with the docs in Step 1(to diversify the recommended keywords).
4, sample `samp_doc_num` docs from docs that contain any keywords from Step 3(to diversify the recommended documents).

LinRel-based recommender 

This is the recommender engine using LinRel algorithm as its core. See LinRelRecommender in engine.py for the actual code.

Document recommendation:

Using:
1. $y_t$: formed by document feedback history
2. $D_t$: formed by document that have received feedbacks
3. $D$: document to keyword TdIdfmatrix 
to calculate the scores for each document

Return the top `recom_doc_num`


Keyword recommendation:

Similar things happen to the keywords recommendation:

Using:
1. $y_t$: formed by document feedback history
2. $D_t$: formed by document that have received feedbacks
3. $D$: document to keyword TdIdfmatrix 
to calculate the scores for each document

Return the top `recom_doc_num`.

To allow for richer feedback information, keywords associated with the recommended documents in the previous section is also returned to the user(but displayed in a less obvious way)

=======
scinet3
=======

Explorative document retrieval using collaborative feedback
