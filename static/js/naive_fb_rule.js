var naive_fb_rule = 
    new FeedbackRule({ 
	/*
	  intialization stuff
	*/
	'kw_alpha': 0.7,
	'doc_alpha': 0.7,
	'kw.init': function(alpha){
	    var self = this;
	    self.alpha = alpha;
	    
	    self._doc2weight = {};
	    
	    self._fb_from_itself = 0;
	    self._fb_from_docs = {};
	    
	    self['docs'].forEach(function(doc){
		self._doc2weight[doc['id']] = doc['w'];
		self._fb_from_docs[doc['id']] = 0; //initialize to 0
	    });
	    
	    self._doc_weight_sum = self.docs.map(function(doc){
		return self._doc2weight[doc['id']];
	    }).reduce(function(acc, v){return acc + v}, 0);
	},
	'doc.init': function(alpha){
	    var self = this;
	    self.alpha = alpha;
	    
	    self._kw2weight = {};
	    
	    self._fb_from_its_kws = {};//fb from keyword under it
	    self._fb_from_primary_kws = {}; //fb from keyword in the keyword column
	    
	    self['kws'].forEach(function(kw){
		self._kw2weight[kw['id']] = kw['w'];
		self._fb_from_primary_kws[kw['id']] = 0; //initialize to 0
		self._fb_from_its_kws[kw['id']] = 0; //initialize to 0
	    });
	    
	    self._kw_weight_sum = self.kws.map(function(kw){
		return self._kw2weight[kw['id']];
	    }).reduce(function(acc, v){return acc + v}, 0);
	},
	/*
	  internal feedback interaction stuff
	*/
	'primary_kw_feedback': function(fb_num){ 
	    var kw = this;
	    //set feedback for `kw` to `fb_num`
	    kw.feedback_from_itself(fb_num);
	    kw.docs.forEach(function(doc){
		doc.feedback_from_primary_kw(kw, fb_num);
	    })
	},
	'indoc_kw_feedback': function(doc, fb_num){
	    var kw = this;
	    doc.feedback_from_its_kw(kw, fb_num);
	    kw.feedback_from_doc(doc, fb_num);
	},
	'doc_feedback': function(fb_num){
	    var doc = this;
	    doc.feedback_from_itself(fb_num);
	    doc.kws.forEach(function(kw){
		kw.feedback_from_doc(doc, fb_num);
	    });
	},
	/*
	  internal numeric update
	*/
	'kw_feedback_from_itself': function(fb){
	    this._fb_from_itself = fb;
	},
	'kw_feedback_from_doc': function(doc, fb){
	    this._fb_from_docs[doc['id']] = fb * this._doc2weight[doc['id']];
	},			 
	'doc_feedback_from_itself': function(fb){
	    var self = this;
	    self.kws.forEach(function(kw){
		self.feedback_from_its_kw(kw, fb);
	    })	    
	},
	'doc_feedback_from_its_kw': function(kw, fb){
	    this._fb_from_its_kws[[kw['id']]] = fb * this._kw2weight[kw['id']];
	},
	'doc_feedback_from_primary_kw': function(kw, fb){
	    this._fb_from_primary_kws[[kw['id']]] = fb * this._kw2weight[kw['id']];
	},
	/*
	  numeric getter
	*/
	'kw_get_feedback': function(){//get the keyword's feedback
	    var fb_from_doc_sum = $.map(this._fb_from_docs, function(fb){
		return fb;
	    }).reduce(function(acc, val){
		return acc + val;
	    }, 0);
	    
	    //weighted sum
	    if(this._doc_weight_sum == 0){ //no doc are associated with it
		return this.alpha * this._fb_from_itself;
	    }
	    else{
		return this.alpha * this._fb_from_itself + 
		    (1 - this.alpha) * fb_from_doc_sum / this._doc_weight_sum;
	    }
	},    
	'doc_get_feedback': function(){
	    var fb_from_primary_kws_sum = $.map(this._fb_from_primary_kws, function(fb){
		return fb;
	    }).reduce(function(acc, val){
		return acc + val;
	    }, 0);

	    var fb_from_its_kws_sum = $.map(this._fb_from_its_kws, function(fb){
		return fb;
	    }).reduce(function(acc, val){
		return acc + val;
	    }, 0);
	    
	    
	    if(this._kw_weight_sum == 0){ //no kw are associated with it
		return this.alpha * fb_from_its_kws_sum;
	    }
	    else{
		//weighted sum
		return (this.alpha * fb_from_its_kws_sum + 
			(1 - this.alpha) * fb_from_primary_kws_sum) / this._kw_weight_sum;
	    }
	    
	}
    });
