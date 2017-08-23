import os
import httplib, urllib
import webapp2
import json
import jinja2
import string
import random
import logging
from oauth2client import client, crypt   #Reference this thread https://stackoverflow.com/questions/44011776/import-oauth2client-and-prevent-importerror-no-module-named-oauth2client-clien
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import ndb



cID = "1078886779756-8thit9m7pp2miiubil95eus9atj99b92.apps.googleusercontent.com"    #Set the variables to use throughout. Client ID and secret are provided when setting up credentials
cSec = "xC881hQE82RG4-30XiSMMslM"
callURL = "https://accounts.google.com/o/oauth2/v2/auth"
backURL = "http://localhost:8080/callback"    


class State(ndb.Model):                             #create a new class to hold the state. Must have the value included
    value = ndb.StringProperty(required=True)

def makeState(length=10, chars=string.ascii_uppercase + string.digits):     #I found a function on Stack Overflow to generate random strings. That can be found here: https://goo.gl/ZgLxMe
    return ''.join(random.choice(chars) for _ in range(length))

jinjHelp = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),      #I decided to use a template to just display the proper return values. After doing research, it seemed like jinja would work well
    extensions=['jinja2.ext.autoescape'],                                   #I used this link to get started with Jinja: https://realpython.com/blog/python/primer-on-jinja-templating/. Also noted on piazza that jinja was allowed
    autoescape=True)
    
    
    
def findParentKey(userid):
    if userid is not None:
        parent_key = ndb.Key(Project, repr(userid))
        return parent_key
    else:
        return None

def parseToken(token):                                  #I used this as a reference when making this function: https://developers.google.com/identity/sign-in/web/backend-auth#calling-the-tokeninfo-endpoint
    if token is not None:
        try:
            idinfo = client.verify_id_token(token, None)
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:     #OAuth2client documentation: http://oauth2client.readthedocs.io/en/latest/source/oauth2client.crypt.html
                raise crypt.AppIdentityError("Access Denied")
            if idinfo['aud'] not in [cID]:
                raise crypt.AppIdentityError("Access Denied")
            userid = idinfo['sub']
            return userid
        except crypt.AppIdentityError:
            return None
    else:
        return None
    
class OAuthHandler(webapp2.RequestHandler):                 #This is very similar to what we have done in the past
    def get(self,):
        state_return = self.request.get('state')
        code = self.request.get('code')
        
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
        
        token = returning['id_token']
        
        tempVars = {
            'accessToken': token
        }
        
        template = jinjHelp.get_template('correct.html')        #We want to be able to see the accessToken so we can copy and paste it into Postman
        self.response.write(template.render(tempVars))
        
        
class Person(ndb.Model):                                        #Basic model for a volunteer. They must have a name and of course an access header
    id = ndb.StringProperty()
    access_header = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    passion = ndb.StringProperty()    
    age = ndb.IntegerProperty()
        
class PersonHandler(webapp2.RequestHandler):
    def get(self, id=None):
        if 'access_header' in self.request.headers:
            header_data = parseToken(self.request.headers['access_header'])     #If access header is there, parse it and assign it to a variable to use
        else:
            self.response.set_status(400)
            self.response.write("Need proper header.")          #Otherwise tell user they need to put a proper header
            return
        if header_data:
            if id:                                                              #If getting a specific user, find them by id and write their values
                person = ndb.Key(urlsafe=id).get()
                if person:
                    if person.access_header == header_data:
                        self.response.set_status(200)
                        person_dict = person.to_dict()
                        person_dict['self'] = "/people/" + person.id
                        self.response.write(json.dumps(person_dict))
                    else:
                        self.response.set_status(403)           #Can't access data without the proper header
                        return
                else:
                    self.response.set_status(404)
                    return
            else:                                                       #Else, find all the people
                parent_key = findParentKey(header_data)
                people = Person.query(ancestor=parent_key).fetch()
                for p in everyPerson:
                    person_dict = p.to_dict()
                    self.response.write(json.dumps(person_dict))  
                else:
                    self.response.set_status(404)
                    self.response.write("No people found.")
                    return
        else:
            self.response.set_status(403)                   #Tell user there is an issue
            self.response.write("Need proper token")
            return
            
    def post(self):
        if 'access_header' in self.request.headers:
           # self.response.write("Okay, there's a token\n")
            token = self.request.headers['access_header']       #same setup for POST. Get access header and use that to set values
            header_data = parseToken(token)
        else:
            self.response.set_status(403)
            self.response.write("Need proper header.")
            return
        person_data = json.loads(self.request.body)
        #self.response.write(person_data)
        #self.response.write(header_data)
        if header_data and 'name' in person_data:
           # self.response.write("got this far")
            if person_data['name']:                         #Set all the values
                self.response.set_status(201)
                new_person = Person(parent=findParentKey(header_data), access_header=header_data, name=person_data['name'], passion = None, age=None)
                if 'passion' in person_data:
                    new_person.passion = person_data['passion']
                if 'age' in person_data:
                    new_person.age = person_data['age']
                new_person.put()                                          #Create new person
                new_person.id = new_person.key.urlsafe()        #create new person id
                new_person.put()                                            #Upate person
                person_dict = new_person.to_dict()
                person_dict['self'] = "/people/" + new_person.id
                
                self.response.write(json.dumps(person_dict))
                
            else:
                self.response.set_status(400)
                return
        else:
            self.response.set_status(400)
            self.response.write("error")
            return
    
    def patch(self, id=None):
        if id:
            if 'access_header' in self.request.headers:
                header_data = parseToken(self.request.headers['access_header'])     #same access header stuff
            else:
                self.response.set_status(400)
                self.response.write("Need proper header.")
                return
            person_data = json.loads(self.request.body)
            person = ndb.Key(urlsafe=id).get()
            if person:
                if header_data == person.access_header:                     #Either update the information or do nothing
                    if 'name' in person_data and person_data['name']:
                        person.name = person_data['name']
                    if 'passion' in person_data:
                        person.passion = person_data['passion']
                    if 'age' in person_data:
                        person.age = person_data['age']
                    person.put()
                    self.response.write("Person updated successfully.")     #Helpful statement in Postman stest
                else:
                    self.response.set_status(403)
            else:
                self.response.set_status(404)
        else:
            self.response.set_status(400)
    
    def put(self, id=None):
        if id:
            if 'access_header' in self.request.headers:
                header_data = parseToken(self.request.headers['access_header'])     #Access header
            else:
                self.response.set_status(400)
                self.response.write("Need proper header.")
                return
            person_data = json.loads(self.request.body)
            person = ndb.Key(urlsafe=id).get()
            if person:
                if header_data == person.access_header:                 #Either update the data or replace it so it is nothing
                    if 'name' in person_data and person_data['name']:
                        person.name = person_data['name']
                        if 'passion' in person_data:
                            person.passion = person_data['passion']
                        else:
                            person.passion = None
                        if 'age' in person_data:
                            person.age = person_data['age']
                        else:
                            person.age = None
                        person.put()
                        self.response.write("Person updated successfully.")     #Another helpful statement
                    else:
                        self.response.set_status(400)
                        self.resposne.write("Error")
                else:
                    self.response.set_status(403)
            else:
                self.response.set_status(404)
        else:
            self.response.set_status(400)
    

    
    def delete(self, id=None):
        if id:
            if 'access_header' in self.request.headers:
                header_data = parseToken(self.request.headers['access_header'])
            else:
                self.response.set_status(400)
                return
            person = ndb.Key(urlsafe=id).get()
            if person:
                if header_data == person.access_header:
                    projectFind = Project.query(Project.volunteer == id).get()     #This is a litlle different in that if a person is assigned to a project, we need to 
                    if projectFind:                                                                #query to find the project and update it to reflect a person no longer being assigned to it
                        projectFind.volunteer = None
                        projectFind.put()
                    self.response.set_status(200)
                    person.key.delete()
                else:
                    self.response.set_status(403)
            else:
                self.response.set_status(404)
                return
        else:
            self.response.set_status(400)
            return
            
            
class Project(ndb.Model):                                       #Class for volunteer projects. Project must have a name. Has a property for a person to add a volunteer
    id = ndb.StringProperty()
    access_header = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    date = ndb.StringProperty()
    focus = ndb.StringProperty()
    volunteer = ndb.StringProperty()
    

class ProjectHandler(webapp2.RequestHandler):               #These comments will be more cursory as it's very similar to PersonHandler
    def get(self, id=None):
        if 'access_header' in self.request.headers:
            header_data = parseToken(self.request.headers['access_header'])     #Similar access
        else:
            self.response.set_status(400)
            self.response.write("Need proper header")
            return
        if header_data:                                                             #Either get a single project or get all of them that the user has access to
            if id:
                Project = ndb.Key(urlsafe=id).get()
                if Project:
                    if Project.access_header == header_data:
                        Project_dict = Project.to_dict()
                        Project_dict['self'] = "/Projects/" + id
                        self.response.write(json.dumps(Project_dict))
                    else:
                        self.response.set_status(403)
                        return
                else:
                    self.response.set_status(404)
                    return
            else:
                parent_key = findParentKey(header_data)
                Project = Project.query(ancestor=parent_key).fetch()
                if Project:
                    Project_dict = Project.to_dict()
                    Project_dict['self'] = "/Projects/" + id
                    self.response.write(json.dumps(Project_dict))
                else:
                    self.response.set_status(404)
                    return
        else:
            self.response.set_status(400)
            self.response.write("error")
            return
            
    def post(self):
        if 'access_header' in self.request.headers:                 #Create a new project
            token = self.request.headers['access_header']
            header_data = parseToken(token)
        else:
            self.response.set_status(403)
            return
        Project_data = json.loads(self.request.body)
        if header_data and 'name' in Project_data:
            if Project_data['name']:
                self.response.set_status(201)
                new_Project = Project(parent=findParentKey(header_data),access_header=header_data,name=None, date=None,focus=None, volunteer=None)
                if 'name' in Project_data:
                    new_Project.name = Project_data['name']
                if 'date' in Project_data:
                    new_Project.date = Project_data['date']
                if 'focus' in Project_data:
                    new_Project.focus = Project_data['focus']
                if 'volunteer' in Project_data:
                    new_Project.volunteer = Project_data['volunteer']
                new_Project.put()
                new_Project.id = new_Project.key.urlsafe()
                new_Project.put()
                Project_dict = new_Project.to_dict()
                Project_dict['self'] = "/Projects/" + new_Project.id
                self.response.write(json.dumps(Project_dict))
            else:
                self.response.set_status(400)
                return
        else:
            self.response.set_status(400)
            return
    

            
    def patch(self, id=None):                                   #Update project data. This is one way to assign a person to a project
        if id:
            if 'access_header' in self.request.headers:
                header_data = parseToken(self.request.headers['access_header'])
            else:
                self.response.set_status(400)
                return
            Project_data = json.loads(self.request.body)
            Project = ndb.Key(urlsafe=id).get()
            if Project:
                if header_data == Project.access_header:
                    if 'name' in Project_data:
                        Project.name = Project_data['name']
                    if 'focus' in Project_data:
                        Project.focus = Project_data['focus']
                    if 'date' in Project_data:
                        Project.date = Project_data['date']
                    if 'volunteer' in Project_data:
                        Project.volunteer = Project_data['volunteer']
                    Project.put()
                    self.response.write("Project successfully updated.")
                else:
                    self.response.set_status(403)
            else:
                self.response.set_status(404)
                return
        else:
            self.response.set_status(400)
            return
    
    def put(self, id=None):                                     #Replace data. The other way to assign a user to a project
        if id:
            if 'access_header' in self.request.headers:
                header_data = parseToken(self.request.headers['access_header'])
            else:
                self.response.set_status(400)
                return
            Project_data = json.loads(self.request.body)
            Project = ndb.Key(urlsafe=id).get()
            if Project:
                if header_data == Project.access_header:
                    if 'name' in Project_data:
                        Project.name = Project_data['name']
                    else:
                        Project.person1 = None
                    if 'focus' in Project_data:
                        Project.focus = Project_data['focus']
                    else:
                        Project.focus = None
                    if 'date' in Project_data:
                        Project.date = Project_data['date']
                    else:
                        Project.date = None
                    if 'volunteer' in Project_data:
                        new_Project.volunteer = Project_data['volunteer']
                    else:
                        Project.volunteer = None
                    self.response.write("Project successfully replaced.")
                    Project.put()
                else:
                    self.response.set_status(403)
            else:
                self.response.set_status(404)
                return
        else:
            self.response.set_status(400)
            return
    

    
    def delete(self, id=None):                                  #Completely remove a project. Don't need to query for user here
        if id:
            if 'access_header' in self.request.headers:
                header_data = parseToken(self.request.headers['access_header'])
            else:
                self.response.set_status(400)
                return
            Project = ndb.Key(urlsafe=id).get()
            if Project:
                if header_data == Project.access_header:
                    Project.key.delete()
                else:
                    self.response.set_status(403)
            else:
                self.response.set_status(404)
                return
        else:
            self.response.set_status(400)
            return
            

        
    
class MainPage(webapp2.RequestHandler):         #Create the main page by writing the Jinja environment
    def get(self):
        state = makeState()
        new_state = State(value=state)
        new_state.put()
        url = callURL + "?response_type=code&client_id=" + cID + "&redirect_uri=http://localhost:8080/callback" + "&scope=email&state=" + state  #Correct url for sending
        tempVars = {
            'place': url
        }
        
        template = jinjHelp.get_template('index.html')
        self.response.write(template.render(tempVars))        



allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/callback', OAuthHandler),
    ('/people', PersonHandler),
    ('/people/(.*)', PersonHandler),
    ('/projects', ProjectHandler),
    ('/projects/(.*)', ProjectHandler),    

], debug=True)




