# Viddler Python API 0.1
# Todd Troxell <todd@viddler.com>
#
# Copyright 2008 Todd Troxell
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import MultipartPostHandler
import urllib2
from urllib import urlencode
#from elementtree import ElementTree
from xml.etree.ElementTree import ElementTree
from StringIO import StringIO
from time import time

try:
  import pycurl
  use_pycurl = True
except ImportError, e:
  use_pycurl = False

DEBUG = True
# viddler endpoint
API_URL="http://api.viddler.com/rest/v1/"
# viddler session expires after 5 mins
EXPIRE_SECONDS = "300"

class BaseError(Exception):
  """Base error exception"""
  def __init__(self, reason):
    self.reason = reason

  def __str__(self):
    return str(self.reason)


class InternalApiError(BaseError):
  """Error inside API client"""
  pass


class InvalidParameterError(BaseError):
  """Bad parameters in api call"""
  pass


class RemoteError(BaseError):
  """Error returned from server"""
  pass

                                                                               
class Viddler(object):
  """Represents a connection to viddler API
  Usage: v = Viddler(API_KEY, USER, PASSWORD)
  """

  def __init__(self, API_KEY, USER, PASSWORD):
    self.API_KEY = API_KEY
    self.USER = USER
    self.PASSWORD = PASSWORD
    self.session = {'id': None, 'ctime': None, 'expires': None}

  def _rpc(self, params):
    if not params.has_key('method'):
      raise InternalApiError("Attempt to call _rpc with no method parameter")
    params["api_key"] = self.API_KEY

    # we do something special for upload method
    # this is just for non-curl uploads
    if params['method'] == "viddler.videos.upload":
      opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
      urllib2.install_opener(opener)
      endpoint = params['endpoint']
      del params['endpoint']
      req = urllib2.Request(endpoint, params)
      response = urllib2.urlopen(req).read()
    else:
    # non-upload api calls
      tuple_list = list()
      for k in params.keys():
        tuple_list.append((k,params[k]))
      data = urlencode(tuple_list)
      res = urllib2.urlopen(API_URL, data)
      response = res.read()
    return self._process_response(response)
    
  def _process_response(self, response):
    if DEBUG:
      print response
    sio = StringIO()
    sio.write(response)
    sio.seek(0)
    et = ElementTree()
    et.parse(sio)
    return_dict = {}
    for elem in et.getiterator():
      return_dict[elem.tag] =  elem.text
    if return_dict.has_key("error"):
      raise RemoteError(return_dict)
    return return_dict
  
  def have_valid_session(func):
    """Decorator for making sure we have a valid session"""
    def wrapper(self, *arg, **kwarg):
      need_session = False
      if not self.session['id']:
        need_session = True
      elif not self.session['ctime'] or not self.session['expires']:
        need_session = True
      elif time() >= self.session['expires']:
        need_session = True
      if need_session:
        self.get_session()
      return func(self, *arg, **kwarg)
    return wrapper
  
  def get_session(self):
    params = {"method": "viddler.users.auth",
              "user": self.USER,
              "password": self.PASSWORD}
    result = self._rpc(params)
    # set self.session stuff
    curtime = time()
    self.session['id'] = result['sessionid']
    self.session['ctime'] = curtime
    self.session['expires'] = curtime + float(EXPIRE_SECONDS)

  @have_valid_session
  def prepareUpload(self):
    """Gets a url to use as an upload server"""
    params = {"method": "viddler.videos.prepareUpload",
              "sessionid": self.session['id']}
    return self._rpc(params)

  def _pycurl_upload(self, params, filepath):
    c = pycurl.Curl()
    del params['file']
    endpoint = params['endpoint']
    del params['endpoint']
    
    for key in params:
        params[key] = params[key].encode('UTF-8')
    params['api_key'] = self.API_KEY.encode()
    curlpost = params.items()
    curlpost.append(("file", (c.FORM_FILE, filepath.encode())))
    print curlpost
    out = StringIO()
    c.setopt(c.POST, 1)
    c.setopt(c.URL, endpoint)
    c.setopt(c.HTTPPOST, curlpost)
    c.setopt(c.VERBOSE, 1)
    c.setopt(pycurl.WRITEFUNCTION, out.write)
    c.perform()
    c.close()
    out.seek(0)
    return self._process_response(out.read())
    
  @have_valid_session
  def upload(self, path, title, tags, description, make_public=False):
    """Uploads a video to viddler.
    path: path to video file
    title: video title
    tags: comma separated tag string
    description: video description
    make_public: (optional) enter 1 for public 0 for private
    """
    try:
      fh = open(path, 'r')
    except Exception, e:
      print "Error opening file at path %s: %s" % (path, e)
    if make_public:
      make_public = '1'
    else:
      make_public = '0'
    params = {'method': 'viddler.videos.upload',
             'sessionid': self.session['id'],
             'title': title,
	     'tags': tags,
	     'description': description,
	     'file': fh,
             'make_public': make_public}

    params['endpoint'] = self.prepareUpload()['endpoint']
    if use_pycurl:
      ret = self._pycurl_upload(params, path)
    else:
      ret = self._rpc(params)
    fh.close()
    return ret

  def getProfile(self, user):
    """Gets user's profile info.  Pass viddler username as user. 
    Dict containing user data is returned."""
    params = {"method": "viddler.users.getProfile",
              "user": user}
    return self._rpc(params)

  def getInfo(self):
    """Returns info about remote APi version"""
    params = {"method": "viddler.api.getInfo"}
    return self._rpc(params)

  @have_valid_session
  def setPermaLink(self, video_id, permalink):
    """Set the permalink for a video (link when clicking on the flash)"""
    params = {"method": "viddler.videos.setPermaLink",
              "sessionid": self.session['id'],
              "video_id": video_id,
              "permalink": permalink}
    return self._rpc(params)

  @have_valid_session
  def commentsAdd(self, video_id, text):
    """Add a comment to a video"""
    params = {"method": "viddler.videos.comments.add",
              "sessionid": self.session['id'],
              "video_id": video_id,
              "text": text}
    return self._rpc(params)

  @have_valid_session
  def commentsRemove(self, comment_id):
    """Remove a comment by id"""
    params = {"method": "viddler.videos.comments.remove",
              "sessionid": self.session['id'],
              "comment_id": comment_id}
    return self._rpc(params)

  @have_valid_session
  def videosDelete(self, video_id):
    """Delete a video by id"""
    params = {"method": "viddler.videos.delete",
              "sessionid": self.session['id'],
              "video_id": video_id}
    return self._rpc(params)
    
  @have_valid_session
  def setProfile(self, profile):
    """Set user's profile data.  profile is a dict keyed with the following:
    first_name [20 chars max]
    last_name [20 chars max]
    about_me
    birthdate [yyyy-mm-dd]
    gender [m or f]
    company [100 chars max]
    city [250 chars max]
    To remove any information from profile just send empty parameter value
    If you want to send more data in one request consider using HTTP POST
    method instead of GET.
    """
    if not type(profile) == dict:
      raise InvalidParameterError("profile must be a dict.")
    params = {"method": "viddler.users.setProfile",
              "sessionid": self.session['id']}
    params.update(profile)
    return self._rpc(params)
  
  @have_valid_session
  def register(self, userinfo):
    """Register a user.  This is a restricted function.
    userinfo is a dict keyed with the following:
    user: username to register
    email: users email address
    fname: users first name
    lname: users last name
    password: users password
    question: secret question
    answer: secret answer
    lang: language for this account
    termsaccepted: set to 1 to accept terms
    company: users company (optional)
    """
    if not type(userinfo) == dict:
      raise InvalidParameterError("userinfo must be a dict.")
    params = {"method": "viddler.users.register",
              "sessionid": self.session['id']}
    params.update(userinfo)
    return self._rpc(params)
  
  @have_valid_session
  def setOptions(self, options):
    """Set user account options.  Currently viddler only supports partner 
    options.  options is a dict keyed with the following.  1 indicates
    a true value and 0 indicates a false.
    show_account: toggle account visibility
    tagging_enabled: toggle tagging
    commenting_enabled: toggle commenting
    show_related_videos: toggle showing of related vidoes
    embedding_enabled: toggle embedding
    clicking_through_enabled: toggle click_through
    email_this_enabled: toggle email this
    trackbacks_enabled: toggle trackbacks
    favourites_enabled: toggle favourites
    custom_logo_enabled: toggle custom logo
    """
    if not type(options) == dict:
      raise InvalidParameterError("options must be a dict.")
    params = {"method": "viddler.users.setOptions",
              "sessionid": self.session['id']}
    params.update(userinfo)
    return self._rpc(params)
  
  @have_valid_session
  def getRecordToken(self):
    """Generate token for embedded recorder"""
    params = {"method": "viddler.videos.getRecordToken",
              "sessionid": self.session['id']}
    return self._rpc(params)
  
  # Technicaly a session is not required for getStatus, getDetails,
  # getDetailsByUrl
  # but we can sometimes get more data by being logged in.
  
  @have_valid_session
  def getStatus(self, video_id):
    """Get status codes of a video by video_id"""
    params = {"method": "viddler.videos.getStatus",
             "sessionid": self.session['id'],
	     "video_id": video_id}
    return self._rpc(params)
  
  @have_valid_session
  def getDetails(self, video_id):
    """Get the details for a video by video_id"""
    params = {"method": "viddler.videos.getDetails",
             "sessionid": self.session['id'],
	     "video_id": video_id}
    return self._rpc(params)
  
  @have_valid_session
  def getDetailsByUrl(self, url):
    """Get the details for a video by URL"""
    params = {"method": "viddler.videos.getDetailsByUrl",
             "sessionid": self.session['id'],
	     "url": url}
    return self._rpc(params)
  
  @have_valid_session
  def setDetails(self, video_id, details):
    """Set the details for a video by video_id.  details is a dicte
    keyed with the following.  All details are optional.
    title: video title [500 char max]
    description: video description
    tags: comma separated string of tags.  timed tags like this: sneeze[1000]
      that would cause a timed tag at 1 second.
    view_perm: permissions set to public, shared_all, shared or private
    view_users: comma separated string of users which may view this video
      when view_perm is set to shared. Only friends are allowed here.
    view_use_secret: set to 1 to enable or regenerate secreturl.  set to 0 
      to disable secreturl
    embed_perm: embed permission.  set to public, shared_all, shared or
      private.  May not be more restrictive than view_perm
    embed_users: like view_users, only for embeds
    commenting_perm: public, shared_all, shared or private.
    commenting_users: like view_users, only for comments.
    tagging_perm: public, shared_all, shared or private.
    tagging_users: like view_users, only for tags.
    download_perm: public, shared_all, shared or private.
    download_users: like view_users, only for downloading.
    """
    if not type(details) == dict:
      raise InvalidParameterError("details must be a dict.")
    params = {"method": "viddler.videos.setDetails",
              "sessionid": self.session['id']}
    params.update(userinfo)
    return self._rpc(params)
  
  @have_valid_session
  def getByUser(self, user, page=1, per_page=20):
    """Get videos by username.
    user: viddler username
    page: (optional) page of results (1,2,3,...)
    per_page: (optional) results per page (100 max)

    a dict is returned
    """
    params = {"method": "viddler.videos.getByUser",
             "sessionid": self.session['id'],
	     "user": user,
	     "page": page,
	     "per_page": per_page}
    return self._rpc(params)
  
  def getByTag(self, tag, page=1, per_page=20):
    """"Get videos by tag.
    tag: tag to search
    page: (optional) page of results (1,2,3,...)
    per_page: (optional) results per page (100 max)

    a dict is returned
    """
    params = {"method": "viddler.videos.getByTag",
              "sessionid": self.session['id'],
	      "tag": tag,
	      "page": page,
	      "per_page": per_page}
    return self._rpc(params)
    
  def getFeatured(self):
    """Get currently featured videos"""
    params = {"method": "viddler.videos.getFeatured"}
    return self._rpc(params)
