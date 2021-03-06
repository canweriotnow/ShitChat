import hashlib, uuid #for password security
from time import ctime

##########################     LOGIN/ REGISTER        ##########################

user_count = 0
#Creates new user in database.
#user: {string:first_name, string:last_name, string:email int:user_id, int:password, int:salt, list:int:private_walls, list:int:public_walls, list:int:friends, dict:conversations, int:count_unread, boolean:logged_in}
#conversations can be structured :  {person_talked_to: {int:unread_count, messages:[{'sender':who_sent_this_message, string:'message_text', string:'time':'12:04:50', 'date':Jan-20-2015}, more messages....], more people:{}....}
def register_user(form, db):
    user = {}

    user['first_name'] = form['first_name']
    user['last_name'] = form['last_name']
    user['email'] = form['email'] #to be used for log in, since name's arent necessarily unique

    global user_count #to access the global variable
    user_count += 1
    user['user_id'] = user_count #to be used for pointing to other users (classier than email)
        
    #security
    pword = form['password']
    salt = uuid.uuid4().hex #creates salt, randomized string attached to end of password
    hash_pass = hashlib.sha512(salt + pword).hexdigest() #prepend the salt to the password, hash using sha512 algorithm, use hexdigest to store as string
    user['password'] = hash_pass
    user['salt'] = salt

    user['private_walls'] = [] #will be list of ids
    user['public_walls'] = [] #ditto
    user['friends'] = [] #list of other users ids
    user['conversations'] = {}
    user['count_unread'] = 0 #number of total unread messages

    user['walls_upped'] = [] #list of ids of walls already upvoted

    user['logged_in'] = False
    
    return db.users.insert(user)
    

#ensures a valid username and password, when being registered
def validate(form, db):
    email_new = db.users.find_one( { 'email' : form['email'] } , { "_id" : False } )
    if email_new == None:
        if len(form['first_name']) == 0:
            return 'No first name entered'
        if len(form['last_name']) == 0:
            return 'No last name entered'
        elif len(form['password']) < 5:
            return 'Invalid password. Must be at least five characters.'
        elif form['password'] != form['password_confirm']:
            return "Password and confirm don't match"
        else:
            return 'Valid'
    else:
        return "email taken"

#checks that login info is valid, returns the full user info associated with the email if it is
def authenticate(email, password, db):
    #finds user with the listed email
    user = db.users.find_one( { 'email' : email } , { "_id" : False } )
    if user == None:
        return None

    #security check on password
    salt = user["salt"]
    hash_pass = user["password"]
    hash_confirm = hashlib.sha512(salt + password).hexdigest()
    
    if hash_pass == hash_confirm:
        update_user(user['email'], {'logged_in': True}, db)
        user = db.users.find_one( { 'email' : email } , { "_id" : False } ) #make it the one with logged_in set true
        return user
    else:
        return None
        
# update_dict must be in the form {field_to_update : new_val}
def update_user(email, update_dict, db):
    db.users.update({'email' : email}, {'$set' : update_dict}, upsert=True)
    return True

##########################     WALLS        ##########################

wall_count = 0

#creates a dict wall: {string:name, string:description, int:wall_id, int:num_comments, int:up_votes list:dict:comments{string:comment, string:user's name  string:'time':'12:04:50', 'date':Jan-20-2015, int:up_votes, int:comment_id, list:strings:tags}} 
def create_wall(name, description, session, db):
    wall = {}
    if len(name) == 0:
        return "Name required"
    else:
        wall['name'] = name
        #repeated = db.walls.find_one( { 'name' : name } , { "_id" : False } )
        #if repeated != None:
            #return "Name taken"
        wall['description'] = description
        global wall_count #to access the global variable
        wall_count += 1
        wall['wall_id'] = wall_count
        wall['comments'] = []
        wall['num_comments'] = 0
        wall['tags'] = []
        wall['creator'] = session['email']
        wall['up_votes'] = 0
        db.walls.insert(wall)

        #ensures that the user has a list of ids of all walls which he/ she created
        id_list = session['public_walls']
        id_list.append(wall['wall_id'])
        update_user(session['email'], {'public_walls':id_list}, db)

        print "Wall" + name + "created"
        return "Wall " + name + " created"

#adds a comment, must be given form with the comment, name of the current wall, session and db
#if user is not yet liste as having that wall connected, adds the wall's id
def add_comment(form, current_wall, session, db):
    walls = db.walls.find_one( {'name':current_wall} )
    
    comment = {}
    comment['comment'] = form['comment']

    if form['comment'] == None:
        return 'Comment field left blank'

    comment['up_votes'] = 0
    
    #for time stamp
    time_total = str(ctime())
    comment['date'] = time_total[4:10] + ", " + time_total[20:25]
    comment['time'] = time_total[11:19]

    #Points comment to a user
    comment['user_id'] = session['user_id']
    name = str(session['first_name'] + session['last_name']) #For ease of displaying the name
    comment['user_name'] = name
    
    for w in walls:
        wall = w

    #updates the wall with new comment list, and a new number
    old_comments = wall['comments']
    old_comments.append(comment)
    num_comments = wall['num_comments'] + 1
    update_wall(wall['name'], {'comments':comment, 'num_comments':num_comments}, db)

    return "comment added"
    
def search_wall(form, db):
    name = form['name']
    wall_name = db.walls.find( { 'name' : name } , { "_id" : False } )
    wall_tags = db.walls.find( { 'tags': { '$in': [name]}}, { "_id" : False } )
    ret = []
    for w in wall_name:
        ret.append(w)
    for w in wall_tags:
        ret.append(w)
    return ret

#method for when a wall is upvoted
def up_vote(wall_id, session, db):
    #update the wall with the upvote
    wall = db.walls.find_one( {'wall_id': wall_id} )
    up_count = wall['up_votes'] + 1
    update_wall(wall_id, {'up_votes': up_count}, db)

    #update the session with the wall upvoted, so user cant double dip
    walls_upped = session['walls_upped']
    walls_upped.append(wall_id)
    session['walls_upped'] = walls_upped

    #update the user itself
    update_user(session['email'], {'walls_upped': walls_upped}, db)
    
    #so the actual copy of session can be updated
    return session['walls_upped']



# update_dict must be in the form {field_to_update : new_val}
def update_wall(wall_id, update_dict, db):
    db.wall.update({'wall_id' : wall_id}, {'$set' : update_dict}, upsert=True)
    return True
