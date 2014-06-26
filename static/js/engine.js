function Engine(config){
    var fb_rule = config['fb_rule'];
    var kw_renderer = config['kw_renderer'];
    var doc_renderer = config['doc_renderer'];
    
    this.run = function(data){
	fb_rule.propagate_data(data['kws'], data['docs'])
	fb_rule.associate_doc_kw();
	
	kw_renderer.render(data['kws'])
	doc_renderer.render(data['docs']);
    }

    this.kw_fb = function(){
	return fb_rule.kw_fb();
    }

    this.doc_fb = function(){
	return fb_rule.doc_fb();
    }

    this.reset = function(){
	kw_renderer.empty_html();
	doc_renderer.empty_html();
    }
}

function FeedbackRule(options){
    DEFAULT_KW_ALPHA = 0.7;
    DEFAULT_DOC_ALPHA = 0.7;
    var self = this;       
    
    self.propagate_data = function(kws, docs){
	self.kws = kws;
	kws.forEach(function(kw){
	    var alpha = options['kw_alpha'] || DEFAULT_KW_ALPHA;
	    options['kw.init'].call(kw, alpha);//initialization
	    
	    kw['feedback_from_doc'] = function(doc, feedback){
		options['kw_feedback_from_doc'].call(kw, doc, feedback);
	    };
	    kw['feedback_from_itself'] = function(feedback){
		options['kw_feedback_from_itself'].call(kw, feedback);
	    };
	    
	    kw['feedback_from_doc'] = options['kw_feedback_from_doc'];
	    kw['feedback'] = function(number){
		//if number given, this sets the feedback
		//otherwise, it's a getter
		if(number == undefined){
		    return options['kw_get_feedback'].call(kw);
		}
		else{
		    options['primary_kw_feedback'].call(kw, number);
		}
	    }
	    
	    kw['indoc_feedback'] = function(doc, fb){
		options['indoc_kw_feedback'].call(kw, doc, fb);
	    }	    	    
	    
	    //some getter method
	    kw['get_doc_by_id'] = function(id){
		return kw['docs'].filter(function(doc){
		    return doc['id'] == id;
		})[0];
	    }
	});

	self.docs = docs;
	docs.forEach(function(doc){
	    var alpha = options['doc_alpha'] || DEFAULT_DOC_ALPHA;
	    options['doc.init'].call(doc, alpha);
	    doc['feedback_from_primary_kw'] = function(kw, feedback){
		options['doc_feedback_from_primary_kw'].call(doc, kw, feedback);
	    };
	    doc['feedback_from_its_kw'] = function(kw, feedback){
		options['doc_feedback_from_its_kw'].call(doc, kw, feedback);
	    };
	    doc['feedback_from_itself'] = function(feedback){
		options['doc_feedback_from_itself'].call(doc, feedback);
	    };

	    doc['feedback'] = function(number){
		//if number given, this sets the feedback
		//otherwise, it's a getter
		if(number == undefined){
		    return options['doc_get_feedback'].call(doc);
		}
		else{
		    options['doc_feedback'].call(doc, number);
		}
	    }
	});

	self.kw_fb = function(){
	    var fb = []
	    self.kws.forEach(function(kw){
		fb.push({'id': kw['id'], 
			 'score': kw.feedback()});	    
	    });
	    return fb;
	}

	self.doc_fb = function(){
	    var fb = []
	    self.docs.forEach(function(doc){
		fb.push({'id': doc['id'], 
			 'score': doc.feedback()});	    
	    });
	    return fb;
	}
    }

    self.associate_doc_kw = function(){//two way binding(cyclic)
	self.kws.forEach(function(kw){
	    var doc_ids = kw['docs'].map(function(doc){return doc['id']});
	    kw['docs'] = self.docs.filter(function(doc){return doc_ids.indexOf(doc['id']) >= 0});
	});
	
	self.docs.forEach(function(doc){
	    var kw_ids = doc['kws'].map(function(kw){return kw['id']});
	    doc['kws'] = self.kws.filter(function(kw){ return kw_ids.indexOf(kw['id']) >= 0});
	});
    }
}

function KwRenderer(kw_list_dom, doc_list_dom, config){
    var get_kw_html = config['get_kw_html'];
    var clicked_on = config['clicked.on'];
    var clicked_off = config['clicked.off'];    
    
    this.empty_html = function(){
	kw_list_dom.find('.kw').remove();
    }
    
    this.render = function(kws){
	function get_indoc_kw_htmls(kw){
	    //get the keyword dom object associated with the primary keyword
	    return doc_list_dom.find('.kw').filter(function(idx, kw_html){
		return $(kw_html).data('id') == kw['id'];
	    });
	}
	
	//kw to doc html mapping
	function get_assoc_doc_htmls(kw){
	    var doc_ids =  kw.docs.map(function(doc){
		return doc['id'];
	    });

	    return doc_list_dom.find('.doc').filter(function(idx, doc_html){
		return doc_ids.indexOf($(doc_html).data('id')) >= 0;
	    });
	}
	
	kws.forEach(function(kw){
	    var html = get_kw_html.call(kw);
	    html.data('id', kw['id']);
	    html.data('clicked', false);
	    
	    html.on('click', function(event){
		var clicked = html.data('clicked');
		if(!clicked){
		    clicked_on.call(this, event, kw, get_indoc_kw_htmls(kw), get_assoc_doc_htmls(kw));		    
		    html.data('clicked', true);
		}
		else{
		    clicked_off.call(this, event, kw, get_indoc_kw_htmls(kw), get_assoc_doc_htmls(kw));
		    html.data('clicked', false);
		}
	    });
	    kw_list_dom.append(html)
	});
    }
}

function DocRenderer(doc_list_dom, kw_list_dom, config){
    var get_doc_html = config['get_doc_html'];
    var get_dockw_html = config['get_dockw_html'];
    var kw_clicked_on = config['kw_clicked_on'];
    var kw_clicked_off = config['kw_clicked_off'];
    var doc_clicked_on = config['doc_clicked_on'];
    var doc_clicked_off = config['doc_clicked_off'];
    
    this.empty_html = function(){
	doc_list_dom.find('.doc').remove();
    }
    
    this.render = function(docs, kws){
	function get_primary_kw_html(kw){
	    return kw_list_dom.find('.kw').filter(function(idx, dom){
		return $(dom).data('id') == kw['id'];
	    });
	}
	docs.forEach(function(doc){
	    var doc_html = get_doc_html.call(doc);
	    doc_html.data('id', doc['id']);
	    doc_html.data('clicked', false);
	    doc.kws.forEach(function(kw){
		var kw_html = get_dockw_html.call(kw, doc);
		//data to be saved
		kw_html.data('id', kw['id']);
		kw_html.data('clicked', false);
		
		//when it is clicked
		kw_html.on('click', function(e){
		    var clicked = kw_html.data('clicked');
		    if(!clicked){
			kw_clicked_on.call(this, e, kw, doc_html, get_primary_kw_html(kw), doc);
			kw_html.data('clicked', true);
		    }
		    else{
			kw_clicked_off.call(this, e, kw, doc_html, get_primary_kw_html(kw), doc);
			kw_html.data('clicked', false);
		    }
		    e.stopPropagation();
		})

		doc_html.find('ul.kws').append(kw_html);
	    });
	    
	    doc_html.on('click', function(e){
		var clicked = doc_html.data('clicked');
		if(!clicked){
		    doc_clicked_on.call(this, e, doc, 
					doc_html.find('.kw'),
					doc.kws.map(function(kw){
					    return get_primary_kw_html(kw);
					}),
					doc.kws);
		    doc_html.data('clicked', true);
		}
		else{
		    doc_clicked_off.call(this, e, doc, 
					doc_html.find('.kw'),
					doc.kws.map(function(kw){
					    return get_primary_kw_html(kw);
					}),
					doc.kws);
		    doc_html.data('clicked', false);
		}
	    });
	    doc_list_dom.append(doc_html);
	});
    }
}

