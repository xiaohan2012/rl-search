

//global variable,
var Content = function(){
    var self = this;
    
    self.kw_list_html = $('#keywordsWrapper ul');
    self.kw_list_html.extend({
	'_get_kw_html': function(kw, options){
	    var classes = "";
	    
	    if(options != undefined){
		classes = options['classes'] || "";
	    }
	    
	    var score_str = ':<span class="feedback">' + (kw['score'] == undefined ? '0' : kw['score'].toFixed(2)) + '</span>';
	    var kw_html = $('<li class="kw ' +  classes + '"><h3>' + kw['id'] + score_str + '</h3></li>') ;	    	    	
	    kw_html.data('id', kw['id']);
	    kw_html.data('get_internal', function(){
		var lst = self.kws.filter(function(another_kw){
		    return kw['id'] == another_kw['id'];
		});
		return lst[0];
	    });
	    
	    var kw_internal = kw_html.data('get_internal')();
	    
	    kw_internal.update_display = function(doc){
		//if doc is given, update the doc's secondary kewyord display
		//if doc is absent, update the primary keyword display
		if(doc == undefined){
		    kw_html.find('.feedback').text(kw.get_feedback().toFixed(2));
		    if(kw.is_primary_kw_on()){
			kw_html.addClass('text-info');
		    }
		    else{
			kw_html.removeClass('text-info');
		    }
		}
		else{
		    doc.update_kw_display(kw_internal);
		}
		
	    };
	    return kw_html;
	},
	'add': function(kw, options){
	    this.append(this._get_kw_html(kw, options));
	},
	'reset': function(){
	    this.find('li').remove()
	}
    });    
     
    self.doc_list_html = $('#documentsWrapper ul');
    self.doc_list_html.extend({
	'_get_kw_html': function(kw, doc){
	    var kw2doc_weight = self.kws.filter(function(another_kw){ //find the keyword
		 return another_kw['id'] == kw['id'];
	    })[0]['docs']
		.filter(function(another_doc){ //find the document
		    return another_doc['id'] == doc['id'];
		})[0]['w'];
	    
	    var w_str = ':<span class="text-warning">'+ 
		kw['w'].toFixed(2) + ',' + kw2doc_weight.toFixed(2)+ 
		'</span>';
	    var kw2doc_weight = doc['kws'].filter(function(another_kw){
		return another_kw['id'] == kw['id'];
	    })[0]['w'];
	    var kw_html = $('<li class="kw"><span class="body label label-default">' + kw['id'] + '</span>' + w_str + '</li>');
	    kw_html.data('id', kw['id']);
	    kw_html.data('get_internal', function(){//get the associated kw
		var lst = self.kws.filter(function(another_kw){
		    return kw['id'] == another_kw['id'];
		});
		return lst[0];
	    });
	    return kw_html;
	},
	'_get_doc_html': function(doc){
	    var _self =  this;
	    
	    var score_str = ':<span class="feedback text-danger">' + 
		(doc['score'] ==  undefined ? '-' : doc['score'].toFixed(2)) + 
		'</span>';

	    var html = '<li class="doc"><p>' + doc['title'] + score_str +'</p>' + 
		'<ul class="kws"></ul></li>';
	    var doc_html = $(html);	    

	    doc['kws'].forEach(function(kw){
		var kw_html = _self._get_kw_html(kw, doc);
		doc_html.find('.kws').append(kw_html);
	    })
	    doc_html.data('id', doc['id']);
	    doc_html.data('get_internal', function(){
		var result = self.docs.filter(function(another_doc){
		    return doc['id'] == another_doc['id'];
		});
		return result[0];
	    });

	    var doc_internal = doc_html.data('get_internal')();
	    
	    doc_internal.get_kw_html = function(kw_id){
		//get the kw html 
		var kw_html = doc_html.find('.kw').filter(function(idx, kw_html){
		    var kw_html = $(kw_html);
		    return $(kw_html).data('id') == kw_id;
		})[0];

		if(kw_html == undefined){
		    throw "kw_html is undefined with doc_id=" + doc['id'] + ' and kw_id=' + kw_id;
		}
		return $(kw_html);
	    }
	    
	    doc_internal.update_display = function(){
		doc_html.find('.feedback').text(doc.get_feedback().toFixed(2));
	    };

	    doc_internal.highlight_kw = function(kw){
		var kw_html = doc_internal.get_kw_html(kw['id']);
		kw_html.find('.body').removeClass('label-default');
		kw_html.find('.body').addClass('label-info');
	    }
	    
	    doc_internal.underscore_kw = function(kw){
		var kw_html = doc_internal.get_kw_html(kw['id']);		
		kw_html.find('.body').css({'text-decoration': 'underline'});
	    }
	    
	    doc_internal.dehighlight_kw = function(kw){
		var kw_html = doc_internal.get_kw_html(kw['id']);
		kw_html.find('.body').addClass('label-default');
		kw_html.find('.body').removeClass('label-info');
	    }
	    
	    doc_internal.deunderscore_kw = function(kw){
		var kw_html = doc_internal.get_kw_html(kw['id']);
		kw_html.find('.body').css({'text-decoration': 'none'});
	    }
	    
	    doc_internal.update_kw_display = function(kw){
		if(kw.is_primary_kw_on()){
		    doc_internal.underscore_kw(kw);
		}
		else{
		    doc_internal.deunderscore_kw(kw);
		}
		
		if(doc.is_kw_on(kw)){
		    doc_internal.highlight_kw(kw);
		}
		else{
		    doc_internal.dehighlight_kw(kw);
		}

	    };
	    
	    return doc_html;
	},
	'add': function(doc){
	    this.append(this._get_doc_html(doc));
	},
	'reset': function(){
	    this.find('li').remove()
	}	
    });
    
    self.propagate_from_response = function(res){
	//propagate the data from http response to the global variable
	self.session_id = res['session_id'];
	
	self.docs = res['docs'];
	
	self.kws = res['kws'];
	
	self.alpha = 0.7; //parameter controlling the relative weighing of feedback from keyword iteself or document
	self.beta = 0.7;
    }
    
    self.define_update_rules = function(){
	//extend the functionality of the current keyword
	self.kws.forEach(function(kw){
	    kw._fb_from_doc = 0;
	    kw._fb_from_itself = 0;
	    
	    kw._doc2weight = {};
	    kw['docs'].forEach(function(doc){
		kw._doc2weight[doc['id']] = doc['w'];
	    });

	    kw._doc_weights = [];
	    $.each(kw._doc2weight, function(doc, weight){
		kw._doc_weights.push(weight);
	    });
	    kw._doc_weight_sum = kw._doc_weights.reduce(function(acc, v){return acc + v}, 0);
	    
	    kw.on_from_itself = function(){
		kw._fb_from_itself = 1;
	    }	    
	    
	    kw.off_from_itself = function(){
		kw._fb_from_itself = 0;
	    }

	    kw.on_from_doc = function(doc){
		kw._fb_from_doc += (kw._doc2weight[doc['id']] / kw._doc_weight_sum);
	    }

	    kw.off_from_doc = function(doc){
		kw._fb_from_doc -= (kw._doc2weight[doc['id']] / kw._doc_weight_sum);
	    }

	    kw.get_feedback = function(){
		return Math.abs(self.alpha * kw._fb_from_itself +  (1 - self.alpha) * kw._fb_from_doc); //use abs to avoid the -0.00000000000001 problem
	    }

	    //two-way binding
	    var doc_ids = kw['docs'].map(function(doc){return doc['id']}); //doc ids associated with the keyword
	    kw['docs'] = self.docs.filter(function(doc){return doc_ids.indexOf(doc['id']) >= 0});
	});
	
	self.docs.forEach(function(doc){
	    //currently,we are only considering doc's feedback coming from keywords associated with it
	    doc._fb_from_itself = 0;
	    doc._fb_from_kw = 0;
	    
	    doc._kw2weight = {};
	    doc['kws'].forEach(function(kw){
		doc._kw2weight[kw['id']] = kw['w'];
	    });

	    doc._kw_weights = [];
	    $.each(doc._kw2weight, function(kw, weight){
		doc._kw_weights.push(weight);
	    });
	    doc._kw_weight_sum = doc._kw_weights.reduce(function(acc, v){return acc + v}, 0);

	    doc.on_from_itself = function(kw){
		//it means feedback from the keyword in itself
		if(kw == undefined){
		    doc._fb_from_itself = 1;
		}
		else{
		    var w = doc._kw2weight[kw['id']] || 0;
		    doc._fb_from_itself += (w / doc._kw_weight_sum);;
		}
	    }

	    doc.off_from_itself = function(kw){
		if(kw == undefined){
		    doc._fb_from_itself = 1;
		}
		else{
		    var w = doc._kw2weight[kw['id']] || 0;
		    doc._fb_from_itself -= (w / doc._kw_weight_sum);;
		}
	    }

	    doc.on_from_kw = function(kw){
		var w = doc._kw2weight[kw['id']] || 0;
		doc._fb_from_kw += (w / doc._kw_weight_sum);
	    }

	    doc.off_from_kw = function(kw){
		var w = doc._kw2weight[kw['id']] || 0;
		doc._fb_from_kw -= (w / doc._kw_weight_sum);
	    }

	    doc.get_feedback = function(){
		//weighted sum
		console.log('get doc feedback: from itself', doc._fb_from_itself , ' from kw ', doc._fb_from_kw);
		return self.beta * doc._fb_from_itself + (1 - self.beta) * doc._fb_from_kw;
	    }

	    var kw_ids = doc['kws'].map(function(kw){return kw['id']});
	    doc['kws'] = self.kws.filter(function(kw){
		return kw_ids.indexOf(kw['id']) >= 0
	    });
	})
    }
    
    self.define_interaction_rules = function(){
	//feedback directly on docs
	self.docs.forEach(function(doc){
	    doc._is_on = false;
	    doc._is_kw_on_dict = {};
	    
	    doc['is_on'] = function(){
		return doc._is_on;
	    }

	    doc['is_kw_on'] = function(kw){
		if(doc._is_kw_on_dict[kw['id']] == undefined){
		    doc._is_kw_on_dict[kw['id']] = false;
		};
		return  doc._is_kw_on_dict[kw['id']];
	    }
	    
	    doc.get_internal_kw = function(kw_id){
		var kw = doc['kws'].filter(function(kw){
		    return kw['id'] == kw_id;
		})[0];
		if(kw ==  undefined){
		    throw "`kw` is undefined, given kw_id: " + kw_id;
		}
		return kw;
	    }
	    doc['on'] = function(kw){ //doc is active
		if(kw == undefined){
		    console.log('doc', doc['id'], 'becomes ON');		
		    doc._is_on = true;

		    
		    doc['kws'].forEach(function(kw){
			//feedback to itself 
			doc.on_from_itself(kw);
			
			doc._is_kw_on_dict[kw['id']] = true;
			//feedback to the keywords associated with it
			kw.on_from_doc(doc);
		    });
		}
		else{
		    console.log('kw ', kw['id'], ' in doc ', doc['id'], 'becomes ON');		
		    doc._is_kw_on_dict[kw['id']] = true;
		    
		    //feedback to itself 
		    doc.on_from_itself(kw);

		    //feedback to keyword
		    kw.on_from_doc(doc);
		}
		
		console.log('doc', doc['id'], 'feedback is:', doc.get_feedback())
	    }	    	    
	    	    
	    doc['off'] = function(){ //doc is deactivated
		console.log('doc', doc['id'], 'becomes OFF');
		doc._is_on = false;

		//feedback to itself 
		doc.off_from_itself();
		
		//feedback to the keywords associated with it
		doc['kws'].forEach(function(kw){
		    kw.off(doc)
		});
	    }
	});
	
	//feedback directly on keywords
	self.kws.forEach(function(kw){
	    kw._is_primary_on = false;
	    kw._is_doc_on_dict = {};
	    kw['is_doc_on'] = function(doc){
		if(kw._is_doc_on_dict[doc['id']] == undefined){
		    kw._is_doc_on_dict[doc['id']] = false;
		}
		return kw._is_doc_on_dict[doc['id']];
	    }
	    kw['is_primary_kw_on'] = function(){
		return kw._is_primary_on;
	    }

	    kw['on'] = function(doc){ //doc is active
		if(doc == undefined){ //clicked from keyword column
		    kw._is_primary_on = true;
		    
		    console.log('kw', kw['id'], 'becomes ON');
		    //feedback to itself 
		    kw.on_from_itself();
		    
		    //feedback to the documents associated with it
		    kw['docs'].forEach(function(doc){
			
			//feedback to doc
			doc.on_from_kw(kw);

			//kw._is_on_dict[doc['id']] = true;
			console.log('doc', doc['id'], 'feedback is:', doc.get_feedback())
		    });
		}
		else{
		    console.log('keyword clicked from document column');
		    kw.on_from_doc(doc);	
		    
		    //feedback to doc
		    doc.on_from_kw(kw);
		}
		console.log('kw', kw['id'], 'feedback is:', kw.get_feedback());
	    }
	    
	    kw['off'] = function(doc){ //doc is deactivated
		if(doc == undefined){
		    kw._is_primary_on = false;

		    console.log('kw', kw['id'], 'becomes OFF');
		    //feedback to itself
		    kw.off_from_itself();
		    
		    //feedback to the docs associated with it
		    kw['docs'].forEach(function(doc){
			doc.off_from_kw(kw);
			//kw._is_on_dict[doc['id']] = false;
		    });
		}
		else{
		    console.log('keyword clicked from document column');
		    kw._is_doc_on_dict[doc['id']] = false;
		    //feedback to itself
		    kw.off_from_doc(doc);

		    //feedback to doc
		    doc.off_from_kw(kw);
		}
		
	    }
	    
	});
    }
    
    self.resetDisplay = function(){
	self.kw_list_html.reset();
	self.doc_list_html.reset();
    }
    self.display = function(){
	self.resetDisplay();
	
	//render keywords
	$.each(self.kws, function(idx, kw){
	    if(kw['display']){
		self.kw_list_html.add(kw);
	    }
	    else{
		self.kw_list_html.add(kw, {'classes': 'text-muted'});
	    }
	});		
	
	self.kw_list_html.find('.kw').on('mousewheel', function(event, delta){
	    var step = 0.05
	    var val = $(this).data('feedback_from_itself') || 0;
	    if (delta >= 0){
		if (val + step <= 1){
		    val += step;
		}
		else{
		    val = 1;
		}
	    }
	    else{
		if (val -step >= 0){
		    val -= step;
		}
		else{
		    val = 0;
		}
	    }
	    $(this).find('.feedback').html(val.toFixed(2));
	    $(this).data('feedback', val);
	    event.preventDefault();

	    //keyword feedback to document propagation
	}).filter(function(){ //get only those displayed and bind click to them
	    var kw = $(this).data('get_internal')();
	    return kw['display'];
	}).on('click', function(e){
	    
	    var kw = $(this).data('get_internal')();
	    if(kw.is_primary_kw_on()){
		kw.off();		
	    }
	    else{
		kw.on();
	    }

	    //the visual effect stuff
	    kw.update_display();
	    kw['docs'].forEach(function(doc){
		doc.update_display(); //doc changes display
		kw.update_display(doc); //secondary kw changes display
	    });
	    
	    e.stopPropagation();
	});
	
	//render documents
	$.each(self.docs, function(idx, doc){
	    self.doc_list_html.add(doc);
	});
	
	//when document is clicked
	self.doc_list_html.find('.doc').on('click', function(){
	    var doc = $(this).data('get_internal')();
	    
	    if(!doc.is_on()){
		doc.on();
	    }
	    else{
		doc.off();
	    }
	    
	    //visual effect stuff
	    doc.update_display();
	    
	    //all kw 
	    $.each($(this).find('.kw'), function(idx, obj){
		var _self = $(obj);
		var kw = _self.data('get_internal')();		
		kw.update_display(doc);
		kw.update_display();
	    });
	})

	//when keyword under the document is clicked
	self.doc_list_html.find('.kw').on('click', function(e){
	    var doc = $(this).closest('.doc').data('get_internal')();
	    var kw = $(this).data('get_internal')();
	    
	    if(!doc.is_kw_on(kw)){
		kw.on(doc);
	    }
	    else{
		kw.off(doc);
	    }
	    
	    //update the feedback display
	    kw.update_display(doc); //for kw in doc 
	    kw.update_display(); //for primary kw 
	    
	    doc.update_display();
	    
	    e.stopPropagation();
	});

	self.define_update_rules();
	self.define_interaction_rules();
    }
};


var c = new Content();

$(document).ready(function() {
    if(c.session_id == null){//start a session
	$.post('/api/1.0/recommend', function(res){
	    if(res.errcode === 0){
		$('#responseHtml').html(JSON.stringify(res, undefined, 4));
		
		c.propagate_from_response(res);
		c.display();
	    }
	})
    }
    else{//continue a new session
    }
});
