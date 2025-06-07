from supa import db
import bcrypt

# utils
def user_exists(username):
    response = db.table("users").select("*").eq("username", username).execute()
    if response.data==[]:
        return False
    else:
        return True 

# user methods
def validate_user_login(username, password):
    response = db.table("users").select("*").eq("username", username).execute()
    if response.data:
        stored_hashed_pw =response.data[0]["password"].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_hashed_pw)
    return False

def insert_user(username, password): 
    data = {
        "username": username,
        "password": bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    }
    response = db.table("users").insert(data).execute()
    return response.data

def get_user_data_by_username(username):
    response = db.table("users").select("*").eq("username", username).execute()

    if response.data==[]:
        return False
    else:
        return response.data[0]
    
def get_all_usernames(exclude_username=None):
    if exclude_username:
        response = db.table("users").select("username").neq("username", exclude_username).execute()
    else:
        response = db.table("users").select("username").execute()
    return [row["username"] for row in response.data]

#listing methods
def insert_listing(username, listing_name, price, listing_desc):
    data = {
        "username": username,
        "listing_name": listing_name,
        "price": price,
        "listing_description": listing_desc
    }
    response = db.table("listings").insert(data).execute()
    return response.data

def remove_listing(id):
    response = db.table("listings").delete().eq("id", id).execute()
    if response.data==[]:
        return False 
    else:
        return True

def update_buyer(id, username):
    data = {"buyer_name": username}
    response = db.table("listings").update(data).eq("id", id).execute()
    if response.data==[]:
        return False 
    else:
        return True

def update_listing(id, listing_name, price, listing_desc):
    data = {
        "listing_name": listing_name,
        "price": price,
        "listing_description": listing_desc
        }
    response = db.table("listings").update(data).eq("id", id).execute()
    if response.data==[]:
        return False 
    else:
        return True

def get_all_listings():
    response = db.table("listings").select("*").execute()
    if response.data==[]:
        return False 
    else:
        return response.data

def get_listing(id):
    response = db.table("listings").select("*").eq("id", id).execute()
    if response.data==[]:
        return False 
    else:
        return response.data[0]