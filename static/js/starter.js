//what changes:
//- how docs'/kws' feedback should be influenced(doc's feedback to itself and keyword and vice versa)
//1. doc and kw feedback influenced by two sources, itself and its counterpart
//2. how keyword/doc gives feedback to itself
//3. how keyword and doc gives feedback to its counterpart

//- what happens when docs/kws are given feedback internally(numeric change) and externally(click event, style change)


var fb_rule = 
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
	    
	    self._fb_from_its_kw = {};//fb from keyword under it
	    self._fb_from_primary_kw = {}; //fb from keyword in the keyword column
	    
	    self['kws'].forEach(function(kw){
		self._kw2weight[kw['id']] = kw['w'];
		self._fb_from_primary_kw[kw['id']] = 0; //initialize to 0
		self._fb_from_its_kw[kw['id']] = 0; //initialize to 0
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
		doc.feedback_from_kw(kw, fb_num);
	    })
	},
	'indoc_kw_feedback': function(doc, fb_num){
	    var kw = this;
	    doc.feedback_from_kw(kw, fb_num);
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
	    this._fb_from_itself = fb;
	},
	'doc_feedback_from_kw': function(kw, fb){
	    this._fb_from_kws[[kw['id']]] = fb * this._kw2weight[kw['id']];
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
	    return this.alpha * this._fb_from_itself + 
		(1 - this.alpha) * fb_from_doc_sum;
	},    
	'doc_get_feedback': function(){
	    var fb_from_kw_sum = $.map(this._fb_from_kws, function(fb, key){
		return fb;
	    }).reduce(function(acc, val){
		return acc + val;
	    }, 0);
	    
	    //weighted sum
	    return this.alpha * this._fb_from_itself + 
		(1 - this.alpha) * fb_from_kw_sum;
	}
    });

var kw_renderer = new KwRenderer($('#keywordsWrapper>ul'), $('#documentsWrapper>ul'), {
    'get_kw_html': function(options){
	var kw = this;
	var classes = "";
	
	if(options != undefined){
	    classes = options['classes'] || "";
	}
	
	var score_str = ':<span class="feedback">' + (kw['score'] == undefined ? '0' : kw['score'].toFixed(2)) + '</span>';
	var html = '<li class="kw ' +  classes + '"><h3>' + kw['id'] + score_str + '</h3></li>'
	return $(html);
    },
    'clicked.on': function(event, kw, indoc_kw_html, doc_htmls){
	kw.feedback(1); //propagate feedback
	
	$(this).addClass('text-info')
	    .find('.feedback').text(kw.feedback().toFixed(3));
	
	//style change for in doc kw
	indoc_kw_html.find('.body').css({'text-decoration': 'underline'});
	
	//style change for associated doc
	$.each(doc_htmls, function(idx, doc_html){
	    doc_html = $(doc_html);
	    var doc = kw.get_doc_by_id(doc_html.data('id'));
	    doc_html.find('.feedback').text(doc.feedback().toFixed(3));
	});
    },
    'clicked.off': function(event, kw, indoc_kw_html, doc_htmls){
	kw.feedback(0);
	//style change for primary kw
	$(this).removeClass('text-info')
	    .find('.feedback').text(kw.feedback().toFixed(3));
	
	//style change for in doc kw
	indoc_kw_html.find('.body').css({'text-decoration': 'none'});

	//style change for associated doc
	$.each(doc_htmls, function(idx, doc_html){
	    doc_html = $(doc_html);
	    var doc = kw.get_doc_by_id(doc_html.data('id'));
	    doc_html.find('.feedback').text(doc.feedback().toFixed(3));
	});	
    }
})
var doc_renderer= new DocRenderer($('#documentsWrapper>ul'), $('#documentsWrapper>ul'), {
    'get_doc_html': function(){
	var doc = this;
	var score_str = ':<span class="feedback text-danger">' + 
	    (doc['score'] ==  undefined ? '-' : doc['score'].toFixed(2)) + 
	    '</span>';

	return $('<li class="doc"><p>' + doc['title'] + score_str +'</p>' + 
		 '<ul class="kws"></ul></li>'); 
    },
    'get_dockw_html': function(doc){
	var kw = this;
	var kw2doc_weight = doc._kw2weight[kw['id']];
	var doc2kw_weight = kw._doc2weight[doc['id']];
	var w_str = ':<span class="text-warning">'+ 
	    doc2kw_weight.toFixed(2) + ',' + kw2doc_weight.toFixed(2)+ 
	    '</span>';	
	return $('<li class="kw"><span class="body label label-default">' + 
		 kw['id'] +
		 '</span>' + w_str + '</li>');
    },
    'kw_clicked_on': function(e, kw, doc_html, primary_kw_html, doc){
	kw.indoc_feedback(doc, 1);
	
	$(this).find('.body')
	    .addClass('label-info')
	    .removeClass('label-default');
	
	primary_kw_html.find('.feedback').text(kw.feedback().toFixed(3));
	doc_html.find('.feedback').text(doc.feedback().toFixed(3));
    },
    'kw_clicked_off': function(e, kw, doc_html, primary_kw_html, doc){
	kw.indoc_feedback(doc, 0);
	
	$(this).find('.body')
	    .addClass('label-default')
	    .removeClass('label-info');
	
	primary_kw_html.find('.feedback').text(kw.feedback().toFixed(3));
	doc_html.find('.feedback').text(doc.feedback().toFixed(3));
    },
    'doc_clicked_on': function(e, doc, kw_htmls, kws){
	doc.feedback(1);
	kw_htmls.find('.body')
	    .addClass('label-info')
	    .removeClass('label-default');
    },
    'doc_clicked_off': function(e, doc, kw_htmls, kws){
	doc.feedback(0);
	
	kw_htmls.find('.body')
	    .addClass('label-default')
	    .removeClass('label-info');
    }
})

var e = new Engine({
    'fb_rule': fb_rule,
    'kw_renderer': kw_renderer,
    'doc_renderer': doc_renderer
});



var session_id = null;
$(document).ready(function() {
    if(session_id == null){//start a session
	$.post('/api/1.0/recommend', function(res){
	    if(res.errcode === 0){
		$('#responseHtml').html(JSON.stringify(res, undefined, 4));
		
		e.run({
		    'kws': res['kws'], 
		    'docs': res['docs']
		});
	    }
	})
    }
    else{//continue a new session
    }
});


