import datetime
import json
import urllib
import urllib2
import tornado.web

#=======================================
# Global Variables & Constants
#=======================================
ERR_OK = 0
MSG_OK = "OK"

# #RELEASE
SITE_PREFIX = "http://127.0.0.1/"
# DATA_DIR = "/home/netdong/data/"
# #DEBUG
# SITE_PREFIX = "http://115.29.41.100/"
# DATA_DIR = "/home/netdong/data/"

API_HOST = "%sapi/1.0/" % SITE_PREFIX
API_TIMEOUT = 60

#=======================================
# Global Functions
#=======================================
def json_default(o):
    if type(o) is datetime.date or type(o) is datetime.datetime:
        return o.isoformat()

def api_call(interface, post_params={}):
    headers = {"User-Agent": "ocn_web", "Referer": "ocn_web_handlers"}
    api_url = "%s%s" % (API_HOST, interface)
    if post_params: # POST request
        post_data = urllib.urlencode(post_params)
        req = urllib2.Request(api_url, post_data, headers)
    else:
        req = urllib2.Request(api_url, None, headers)

    try:
        res = urllib2.urlopen(req, timeout=API_TIMEOUT)
        content = res.read()
        return json.loads(content)
    except Exception, e:
        print e
        print "Fail to api_call api_url: %s" % api_url
        return None

#=======================================
# Handlers
#=======================================
class BaseHandler(tornado.web.RequestHandler):
    @property                  
    def db(self):   
        return self.application.db    
                
    @property     
    def redis(self):                  
        return self.application.redis  

    def get_current_user(self):     
        user_id = self.get_secure_cookie("userid")      
        return self.get_user(user_id)

    def get_user(self, uid):
        if not uid: return None 
        sql_get = "SELECT * FROM user WHERE id = %s"
        return self.db.get(sql_get, int(uid))
                
    def get_admin(self):            
        admin_email = self.get_secure_cookie("aue")     
        if not admin_email: return None                 
                
    def json_ok(self, data):        
        info = {"errcode": ERR_OK, "msg": MSG_OK}             
        info.update(data)
        j_ = json.dumps(info, default=json_default)       
        self.set_header("Content-Type", "application/json")                 
        self.finish("%s\n" % j_)             
                
    def json_fail(self, errcode, errmsg="unknown error", field=None):                   
        info = {"errcode": errcode, "msg": errmsg}      
        if field:
            info['errfield'] = field
        j_ = json.dumps(info)       
        self.set_header("Content-Type", "application/json")                 
        self.finish("%s\n" % j_)            

    def custom_404(self):
        self.custom_error("&gt;_&lt;|| You've reached a desolation of OCN.", 404)

    def custom_error(self, msg='Unknown error!', status=400):
        self.clear()
        self.set_status(status)
        self.finish("<html><body><center><h1><br/><br/>%s</h1></center></body></html>" % msg)
