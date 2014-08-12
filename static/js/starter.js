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
	    
	    return this._fb_from_itself > 0 ? this._fb_from_itself : (this._doc_weight_sum == 0? 0 : fb_from_doc_sum / this._doc_weight_sum) ;

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

	    return (fb_from_its_kws_sum > 0 ? fb_from_its_kws_sum : fb_from_primary_kws_sum) / this._kw_weight_sum;
	}
    });


var kw_renderer = new KwRenderer($('#keywordsWrapper>ul'), $('#documentsWrapper>ul'), {
    'get_kw_html': function(){
	var kw = this;
	var classes = "";
	if(!kw['display']){
	    classes = 'text-muted';
	}
	var score_str = ':<span class="feedback">' + (kw['score'] == undefined ? '0' : kw['score'].toFixed(2)) + '</span>';
	var html = '<li class="kw ' +  classes + '"><h3>' + kw['id'] + score_str + '</h3></li>'
	return $(html);
    },
    'clicked.on': function(event, kw, indoc_kw_html, doc_htmls){
	kw.feedback(1); //propagate feedback
	$(this).data('clicked', true);
	indoc_kw_html.data('primary_clicked', true);
    },
    'clicked.off': function(event, kw, indoc_kw_html, doc_htmls){
	kw.feedback(0);
	$(this).data('clicked', false);
	indoc_kw_html.data('primary_clicked', false);
    },
    'kw_update_html': function(){
	var kw = $(this).data('obj');
	$(this).find('.feedback').text(kw.feedback().toFixed(3));

	if($(this).data('clicked')){
	    $(this).addClass('text-info')
	}
	else{
	    $(this).removeClass('text-info')
	}
    }
});
var doc_renderer= new DocRenderer($('#documentsWrapper>ul'), $('#keywordsWrapper>ul'), {
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
    'kw_update_html': function(){
	var kw = $(this).data('obj');
	
	if($(this).data('clicked')){
	    $(this).find('.body')
		.addClass('label-info')
		.removeClass('label-default');
	}
	else{
	    $(this).find('.body')
		.addClass('label-default')
		.removeClass('label-info');	    
	}
	
	if($(this).data('primary_clicked')){
	    $(this).find('.body').css({'text-decoration': 'underline'});	
	}
	else{
	    $(this).find('.body').css({'text-decoration': 'none'});	
	}
    },
    'doc_update_html': function(){
	var doc = $(this).data('obj');
	$(this).find('.feedback').text(doc.feedback().toFixed(3));
    },
    'kw_clicked_on': function(e, kw, doc_html, primary_kw_html, doc, doc_list_dom){
	kw.indoc_feedback(doc, 1);
	$(this).data('clicked', true);
	
	//same keyword in other documents receive feedback also
	$.each(doc_list_dom.find('.doc'), function(idx, doc_html){
	    var doc = $(doc_html).data('obj');
	    $.each($(doc_html).find('.kw'), function(_, kw_html){
		kw_html = $(kw_html);
		if(kw_html.data('id') == kw['id']){
		    kw_html.data('clicked', true);
		    kw_html.data('obj').indoc_feedback(doc, 1);
		}
	    });
	})
    },
    'kw_clicked_off': function(e, kw, doc_html, primary_kw_html, doc){
	kw.indoc_feedback(doc, 0);
	$(this).data('clicked', false);
    },
    'doc_clicked_on': function(e, doc, kw_htmls, primary_kw_htmls, kws){
	doc.feedback(1);
	$(this).data('clicked', true);
	$(this).find('.kw').data('clicked', true);
    },
    'doc_clicked_off': function(e, doc, kw_htmls, primary_kw_htmls, kws){
	doc.feedback(0);
	$(this).data('clicked', false);
	$(this).find('.kw').data('clicked', false);
    }
})

var e = new Engine({
    'fb_rule': fb_rule,
    'kw_renderer': kw_renderer,
    'doc_renderer': doc_renderer
});



var global_data = {
    'session_id': null,
};

$(document).ready(function() {
    function one_iteration(session_id){
	console.log('current session_id =', session_id);
	//clean the html first
	e.reset();
	
	var data = {};	
	if(session_id == undefined || session_id == null){//start a session
	    
	}
	else{//continue a new session
	    /*
	    'session_id': session_id,
	    'doc_fb': [{'id':1, 'score': 0.6}, {'id': 3, 'score': 0.1}],
	    'kw_fb': [{'id': 'python', 'score': 0.1}, {'id': 'database', 'score': 0.6}]
	    */	   
	    data['session_id'] = session_id;
	    data['doc_fb'] = e.doc_fb();
	    data['kw_fb'] = e.kw_fb();
	}
	
	console.log('posting data: ', data);
	$.ajax({
	    url: '/api/1.0/recommend',
	    type: 'POST',
	    data: JSON.stringify(data),
	    contentType: 'application/json; charset=utf-8',
	    dataType: 'json',
	    async: false,
	    success: function(res) {
		if(res.errcode === 0){
		    $('#responseHtml').html(JSON.stringify(res, undefined, 4));
		    e.run({
			'kws': res['kws'], 
			'docs': res['docs']
		    });
		    global_data['session_id'] = res['session_id'];
		    console.log('new session_id=', global_data['session_id']);
		}
	    }
	});	
    }
    
    //one_iteration(); //start!
    var clicked = false;
    $('.btn.btn-search').on('click', function(event){
	//start!
	var query = $(this).closest('form').find('input').val();
	$.ajax({
	    url: '/api/1.0/recommend',
	    type: 'POST',
	    data: JSON.stringify({'query': query}),
	    contentType: 'application/json; charset=utf-8',
	    dataType: 'json',
	    async: false,
	    success: function(res) {
		if(res.errcode === 0){
		    e.reset();
		    
		    $('#responseHtml').html(JSON.stringify(res, undefined, 4));
		    e.run({
			'kws': res['kws'], 
			'docs': res['docs']
		    });
		    global_data['session_id'] = res['session_id'];
		    console.log('new session_id=', global_data['session_id']);

		    
		    // if(!clicked){
		    // 	setTimeout(function(){
		    // 	    $('#keywordsWrapper .kw:eq(0)').click();
		    // 	    $('#documentsWrapper .doc:eq(0)').click();
		    // 	    $('.btn.btn-update').click();
		    // 	    console.log('clicked..');

		    // 	}, 1000);
		    // 	clicked = true;			
		    // }
		    
		}
	    }
	});
    })//.click();
    
    //iter!
    $('.btn.btn-update').on('click', function(e){
	console.log('.btn-update clicked')
	one_iteration(global_data['session_id']);
    })

});
