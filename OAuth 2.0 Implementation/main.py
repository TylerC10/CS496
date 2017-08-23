import os
import httplib
import urllib
import webapp2
import json
import string
import random
import jinja2
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from google.appengine.api import users


cID = "273307956570-0kps41093h3clvabemi4088d7k0do1fm.apps.googleusercontent.com"    #Set the variables to use throughout. Client ID and secret are provided when setting up credentials
cSec = "s6cd2fatHfcAe3Snn3fYZt8R"
callURL = "https://accounts.google.com/o/oauth2/v2/auth"
backURL = "https://oauth2-174410.appspot.com/oauth"        


class State(ndb.Model):                             #create a new class to hold the state. Must have the value included
    value = ndb.StringProperty(required=True)

def makeState(length=10, chars=string.ascii_uppercase + string.digits):     #I found a function on Stack Overflow to generate random strings. That can be found here: https://goo.gl/ZgLxMe
    return ''.join(random.choice(chars) for _ in range(length))

jinjHelp = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),      #I decided to use a template to just display the proper return values. After doing research, it seemed like jinja would work well
    extensions=['jinja2.ext.autoescape'],                                   #I used this link to get started with Jinja: https://realpython.com/blog/python/primer-on-jinja-templating/. Also noted on piazza that jinja was allowed
    autoescape=True)
    
    
class OAuthHandler(webapp2.RequestHandler):
    def get(self,):
        code = self.request.get('code')                     #Get the code and the state
        corrState = self.request.get('state')       
        
        header = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        payload = {                                 #This was outlined for us in the lecture video
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': cID,
        'client_secret': cSec,
        'redirect_uri': backURL}
        result = urlfetch.fetch(url='https://www.googleapis.com/oauth2/v4/token', headers=header, payload=urllib.urlencode(payload), method=urlfetch.POST)  #Create the proper request and send it
        returning = json.loads(result.content)
        
        authorization = "Bearer " + returning['access_token']
        
        header = {                              #Set proper authorization
            'Authorization': authorization
        }
        response = urlfetch.fetch(url='https://www.googleapis.com/plus/v1/people/me', headers=header, method=urlfetch.GET)  #Get this response and use it to display the template variables
        returning = json.loads(response.content)
        returningName = returning['name']           #The response for the name has a dict within the return dict called name. So I need to access that dict by setting it to a variable
        
        tempVars = {                                         #Set the proper template variables
            'givenName': returningName['givenName'],
            'familyName': returningName['familyName'],
            'url': returning['url'],
            'state': corrState
        }        
        
        template = jinjHelp.get_template('correct.html')    #The request was successful so it should load properly
        self.response.write(template.render(tempVars))

class MainPage(webapp2.RequestHandler):
    def get(self):
        state = makeState()
        createState = State(value=state)                                #Format to send the first request. This was also outlined for us in lecture. Per assignment specs, we're only allowed to use email for scope
        createState.put()
        url = callURL + "?response_type=code&client_id=" + cID + "&redirect_uri=https://oauth2-174410.appspot.com/oauth" + "&scope=email&state=" + state
        tempVars = {
            'place': url            #Set the correct URL for the button
        }
        
        template = jinjHelp.get_template('start.html')              
        self.response.write(template.render(tempVars))


        
app = webapp2.WSGIApplication([     #All of the pages
    ('/', MainPage),
    ('/oauth', OAuthHandler)
], debug=True)





