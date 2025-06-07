from supabase import db

def insert_user(full_name, email, password): 
    data = {
        "full_name": full_name,
        "email": email,
        "password": password
    }
    response = db.table("users").insert(data).execute()
    return response.data

