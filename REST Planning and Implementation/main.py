from google.appengine.ext import ndb
import webapp2
import json

class Boat(ndb.Model):
    id = ndb.StringProperty() 
    name = ndb.StringProperty() 
    type = ndb.StringProperty() 
    length = ndb.IntegerProperty() 
    at_sea = ndb.BooleanProperty(default=True) 
    
class Slip(ndb.Model):
    id = ndb.StringProperty() 
    number = ndb.IntegerProperty() 
    current_boat = ndb.StringProperty(default=None) 
    arrival_date = ndb.StringProperty(default=None) 
    
class BoatHandler(webapp2.RequestHandler):          #The get and post methods were outlined in the lecture video. I just changed the names
    def post(self): #create boat
        boat_data = json.loads(self.request.body)       
        new_boat = Boat(name=boat_data['name'], type=boat_data['type'], length=boat_data['length'])
        new_boat.put()
        new_boat.id = new_boat.key.urlsafe()
        new_boat.put()
        boat_dict = new_boat.to_dict()
        self.response.set_status(201)
        self.response.write(json.dumps(boat_dict))
        

    def get(self, id=None): #View a single boat (by id) or all boats
        if id: #If id is included, return only that boat
            try:
                getBoat = ndb.Key(urlsafe=id).get()
                self.response.set_status(200)
                self.response.write(getBoat)
            except:
                self.response.set_status(404)
                self.response.write('Sorry, cannnot find boat.')
        else: #return all boats
            self.response.set_status(200)
            everyBoat = Boat.query().fetch()
            for b in everyBoat:
                boat_dict = b.to_dict()
                self.response.write(json.dumps(boat_dict))                
                
    def put(self, id): #Put boat to sea
        try:
            putBoat = ndb.Key(urlsafe=id).get() 
            at_sea = putBoat.at_sea     #Check if boat is already at sea
            if at_sea:
                self.response.write('Boat is at sea. Cannot assign boat to sea again.')
            else:
                putBoat.at_sea = True       #Update the boat, find the slip that it's in, and update the slip
                putBoat.put()
                slip = Slip.query(Slip.current_boat == putBoat.id).get()
                slip.current_boat = None
                slip.arrival_date = None
                slip.put()
                self.response.write('Boat now at sea and slip empty.')
        except:                                         #Throw in error handling for user
            everyBoat = Boat.query().fetch()
            if len(everyBoat) < 1: 
                self.response.set_status(404) 
                self.response.write('Sorry, there are no boats available.')
            else:
                self.response.set_status(404) 
                self.response.write('Sorry, cannot find that boat.')
    
    def delete(self, id): #Delete a boat
        try: 
            deleteBoat = ndb.Key(urlsafe=id).get()
            at_sea = deleteBoat.at_sea
            if at_sea == False:             #If the boat is in a slip, we need to query to get the slip and update its arrival date and current boat status
                slip = Slip.query(Slip.current_boat == deleteBoat.id).get()
                slip.current_boat = None
                slip.arrival_date = None
                slip.put()
            deleteBoat.key.delete()
            self.response.set_status(200)
            self.response.write('Deleted boat.')
        except:
            everyBoat = Boat.query().fetch()
            if len(everyBoat) < 1: 
                self.response.set_status(404) 
                self.response.write('Sorry, there are no boats available.')
            else:
                self.response.set_status(404)
                self.response.write('Sorry, cannot find that boat.')
    
    def patch(self, id):                                                        #I had a persistent issue with try/except where it would update properly but still tell the user that it did not work
        if id:                                                                         #That's why I used if/else here instead
            modBoat = ndb.Key(urlsafe=id).get()
            if modBoat:
                boat_data = json.loads(self.request.body)
                if 'name' in boat_data:                   
                    modBoat.name = boat_data['name']                    #Find the proper data and assign it to modBoat (which is equal to the boat specified by the id in the request)
                if  'type' in boat_data:
                    modBoat.type = boat_data['type']
                if 'length' in boat_data:
                    modBoat.length = boat_data['length']
                modBoat.put()
                boat_dict = modBoat.to_dict()
                self.response.set_status(201)
                self.response.write(json.dumps(boat_dict))
            else:
                self.response.set_status(404)
                self.response.write('Sorry, cannot find that boat')
                return
        else:
            self.response.set_status(404)
            self.response.write('Please include id of boat.')   
    
class SlipHandler(webapp2.RequestHandler):          #Similar to get and post for boats
    def post(self):
        slip_data = json.loads(self.request.body) 
        new_slip = Slip(number=slip_data['number'])
        new_slip.put()
        new_slip.id = new_slip.key.urlsafe()
        new_slip.put()
        slip_dict = new_slip.to_dict()
        self.response.set_status(201)
        self.response.write(json.dumps(slip_dict))
        
        
    def get(self, id=None):
        if id:
            slip = ndb.Key(urlsafe=id).get()
            self.response.write(slip)
            self.response.set_status(200)
        else:
            self.response.set_status(200)
            everySlip = Slip.query().fetch()
            for s in everySlip:
               self.response.write(s)

    def delete(self, id): #Delete a slip (need to check if there's a boat in the slip and set it to sea if there is)     
            try:
                delSlip = ndb.Key(urlsafe=id).get()
                slipBoat = delSlip.current_boat
                if slipBoat:                        #If a boat is in a slip, remove the boat before deleting
                    boat = Boat.query(Boat.id == slipBoat).get()    
                    boat.at_sea = True
                    boat.put()
                    self.response.write('Put boat to sea.')     #Threw in new lines to separate text for user
                    self.response.write('\n')
                    self.response.write('\n')
                delSlip.key.delete()
                self.response.write('Deleted slip.')
            except:
                everySlip = Slip.query().fetch()
                if len(everySlip) < 1: 
                    self.response.set_status(404) 
                    self.response.write('Sorry, there are no slips to delete.')
                else:
                    self.response.set_status(404) 
                    self.response.write('Sorry, cannot find that slip.')
            
    def patch(self, id):        #Modify/replace a slip. I had the same issues with try/except that I did before
        if id:
            modSlip = ndb.Key(urlsafe=id).get()
            if modSlip:
                slip_data = json.loads(self.request.body)
                if 'number' in slip_data:                    
                    modSlip.number = slip_data['number']                    
                if  'arrival_date' in slip_data:
                    modSlip.type = slip_data['arrival_date']                
                modSlip.put()
                slip_dict = modSlip.to_dict()
                self.response.set_status(201)
                self.response.write(json.dumps(slip_dict))
            else:
                self.response.set_status(404)
                self.response.write('Sorry, cannot find that slip.')
                return
        else:
            self.response.set_status(404)
            self.response.write('Please include id of slip.')
            
    def put(self, id): #assign boat to slip
        slip = ndb.Key(urlsafe=id).get()
        if slip.current_boat:                   #If slip is occupied, set to Forbidden per assignment specs
            self.response.set_status(403)
            self.response.write('Slip already occupied.')
            return
        try:
            slip = ndb.Key(urlsafe=id).get()
            slip_data = json.loads(self.request.body)
            boat = Boat.query(Boat.id == slip_data['current_boat']).get()   #Get the boat specified by the request body
            if boat.at_sea == False: 
                self.response.write('Boat already in a slip.')      #If the boat is in a slip, tell user it's already there
            else:                
                slip.current_boat = slip_data['current_boat']   #Update the slip's boat and arrival date
                slip.arrival_date = slip_data['arrival_date']
                slip.put()
                boat.at_sea = False         #The boat is now in a slip, so we need to set it's at sea value to false
                boat.put()
                self.response.write('Put boat in slip.')                
        except:
            everySlip = Slip.query().fetch()
            everyBoat = Boat.query().fetch()            
            if len(everySlip) < 1: 
                self.response.set_status(404) 
                self.response.write('Sorry, there are no slips available.')
            elif len(everyBoat) < 1:
                self.response.set_status(404) 
                self.response.write('Sorry, there are no boats available.')
            else:
                self.response.set_status(404) 
                if slip == None:
                    self.response.write('No slip.')
                if boat == None:
                    self.response.write('No boat.')

class MainPage(webapp2.RequestHandler):             #The main page
    def get(self):
        self.response.write('REST Planning and Implementation')
        
allowed_methods = webapp2.WSGIApplication.allowed_methods           #Taken from Stack Overflow page mentioned in lecture
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods
app = webapp2.WSGIApplication([         #All of our pages
    ('/', MainPage),
    ('/boat', BoatHandler),
    ('/boat/(.*)', BoatHandler),
    ('/slip', SlipHandler),
    ('/slip/(.*)', SlipHandler)
], debug=True)

