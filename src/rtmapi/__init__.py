import hashlib
import httplib2
import urllib
import xml.etree.ElementTree as ElementTree

__author__ = "Michael Gruenewald <mail@michaelgruenewald.eu>"
__all__ = ('Rtm',)

class RtmException(Exception): pass

class Rtm(object):
    _auth_url = "http://api.rememberthemilk.com/services/auth/"
    _base_url = "http://api.rememberthemilk.com/services/rest/"
    
    """
    @param api_key: your API key
    @param shared_secret: your shared secret
    @param perms: desired access permissions, one of "read", "write"
                  and "delete"
    @param token: token for granted access (optional)
    """
    def __init__(self, api_key, shared_secret, perms = "read", token = None):
        self.api_key = api_key
        self.shared_secret = shared_secret
        self.perms = perms
        self.token = token
        self.http = httplib2.Http()
    
    """
    Authenticate as a desktop application.
    
    @returns: (url, frob) tuple with url being the url the user should open and
                          frob the identifier for usage with retrieve_token
                          after the user authorized the application
    """
    def authenticate_desktop(self):
        rsp = self._call_method("rtm.auth.getFrob", api_key=self.api_key)
        frob = rsp.frob.value
        url = self._make_request_url(self._auth_url, api_key=self.api_key,
                                     perms=self.perms, frob=frob)
        return url, frob
    
    """
    Authenticate as a web application.
    @returns: url
    """
    def authenticate_webapp(self):
        url = self._make_request_url(self._auth_url, api_key=self.api_key,
                                     perms=self.perms)
        return url
    
    """
    Checks whether the stored token is valid.
    @returns: bool validity
    """
    def token_valid(self):
        if self.token is None:
            return False
        try:
            rsp = self._call_method("rtm.auth.checkToken", api_key=self.api_key,
                                                           auth_token=self.token)
        except RtmException:
            return False
        return True
    
    """
    Retrieves a token for the given frob.
    @returns: bool success
    """
    def retrieve_token(self, frob):
        try:
            rsp = self._call_method("rtm.auth.getToken", api_key=self.api_key,
                                                         frob=frob)
        except RtmException, e:
            self.token = None
            return False
        self.token = rsp.auth.token.value
        return True
    
    def _call_method(self, method_name, **params):
        infos, data = self._make_request(method = method_name, **params)
        if infos.status != 200:
            raise RtmException("Request %s failed (HTTP). Status: %s, reason: %s" % (
                    method_name, infos.status, infos.reason))
        rtm_obj = RtmObject(ElementTree.fromstring(data), method_name)
        if rtm_obj.stat == "fail":
            #raise RtmException, (rtm_obj.err.code, rtm_obj.err.msg)
            raise RtmException("Request %s failed. Status: %s, reason: %s" % (
                    method_name, rtm_obj.err.code, rtm_obj.err.msg))
        return rtm_obj
    
    def _call_method_auth(self, method_name, **params):
        all_params = dict(api_key = self.api_key, auth_token = self.token)
        all_params.update(params)
        return self._call_method(method_name, **all_params)
    
    def _make_request(self, request_url = None, **params):
        final_url = self._make_request_url(request_url, **params)
        return self.http.request(final_url,
                                 headers={'Cache-Control':'no-cache, max-age=0'})
    
    def _make_request_url(self, request_url = None, **params):
        all_params = params.items() + [("api_sig", self._sign_request(params))]
        quote_utf8 = lambda s: urllib.quote_plus(s.encode('utf-8'))
        params_joined = "&".join("%s=%s" % (quote_utf8(k), quote_utf8(v))
                                           for k, v in all_params
                                           if v is not None)
        return (request_url or self._base_url) + "?" + params_joined
    
    def _sign_request(self, params):
        param_pairs = params.items()
        param_pairs.sort()
        request_string = self.shared_secret + u''.join(k+v
                                                       for k, v in param_pairs
                                                       if v is not None)
        return hashlib.md5(request_string.encode('utf-8')).hexdigest()
    
    def __getattr__(self, name):
        return RtmName(self, name)


class RtmName(object):
    def __init__(self, rtm, name):
        self.rtm = rtm
        self.name = name
    
    def __call__(self, **params):
        return self.rtm._call_method_auth(self.name, **params)
    
    def __getattr__(self, name):
        return RtmName(self.rtm, "%s.%s" % (self.name, name))


class RtmObject(object):
    _lists = {
        "contacts": "contact",
        "groups": "group",
        "groups/group/contacts": "contact",
        "method/arguments": "argument",
        "method/errors": "error",
        "methods": "method",
        "list/taskseries/notes": "note",
        "list/taskseries/participants": "participant",
        "list/taskseries/task/tags": "tag",
        "lists": "list",
        "locations": "location",
        "tasks": "list",
        "tasks/list": "taskseries",
        "tasks/list/taskseries/notes": "note",
        "tasks/list/taskseries/participants": "participant",
        "tasks/list/taskseries/tags": "tag",
        "timezones": "timezone",
    }
    
    def __init__(self, element, name):
        self._element = element
        self._name = name
    
    def __repr__(self):
        return ("<RtmObject %s>" % self._name).encode('ascii', 'replace')
    
    def __getattr__(self, name):
        newname = "%s/%s" % (self._name, name)
        if name == "value":
            return self._element.text
        elif name in self._element.keys():
            return self._element.get(name)
        else:
            return RtmObject(self._element.find(name), newname)
    
    def _get_collection(self):
        child_name = self._lists.get(self._name.partition("/")[2])
        if child_name is None:
            raise ValueError
        new_name = "%s/%s" % (self._name, child_name)
        return [RtmObject(element, new_name)
                for element
                in self._element.findall(child_name)]
    
    def __nonzero__(self):
        return True
    
    def __getitem(self, key):
        return self._get_collection()[key]
    
    def __iter__(self):
        return iter(self._get_collection())
    
    def __len__(self):
        return len(self._get_collection)
