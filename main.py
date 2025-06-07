import os
import datetime
import jwt
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import xrpl_utilities
import db

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
CORS(app)


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "pong"}), 200
    
    
#Address to test functions: rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe
#login
@app.route("/app/login", methods=['POST']) 
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if db.validate_user_login(username, password):
            payload = {
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            return jsonify({'token': token}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

@app.route("/app/register", methods=['POST'])
def register():
    try:
        data = request.get_data(as_text=True)
        data = json.loads(data)
        username = data["username"]
        password = data["password"]

        if db.user_exists(username):
            return jsonify({'error': 'Username already exists'}), 400
        if db.insert_user(username, password):
            return jsonify({'message': 'User registered successfully'}), 201
        else:
            return jsonify({'message': 'Unknown error creating user'}), 500
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

@app.route("/app/user", methods=['GET'])
def get_user():
    try:
        data = request.get_json()
        username = data.get("username")

        data = db.get_user_data_by_username(username)
        if data:
            return jsonify({
                "message": "Success",
                "data": data
            }
            ), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500
    
@app.route("/app/all_users", methods=['GET'])
def get_all_user():
    try:
        data = request.get_json()
        username = data.get("username")
    except:
        username = None
    try:
        data = db.get_all_usernames(username)
        if data:
            return jsonify({
                "message": "Success",
                "data": data
            }
            ), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

@app.route("/app/create_listing", methods=['POST'])
def create_listing():
    try:
        data = request.get_json()
        username = data.get("username")
        listing_name = data.get("listing_name")
        price = data.get("price"),
        listing_desc = data.get("listing_description")
        db.insert_listing(username, listing_name, price, listing_desc)
        return jsonify({'message': 'Listing created successfully'}), 201
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

@app.route("/app/remove_listing", methods=['DELETE'])
def remove_listing():
    try:
        data = request.get_json()
        id = data.get("id")
        db.remove_listing(id)
        return jsonify({'message': 'Listing deleted successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500
    
@app.route("/app/update_buyer", methods=['PUT'])
def update_buyer():
    try:
        data = request.get_json()
        id = data.get("id")
        username = data.get("username")
        db.update_buyer(id, username)
        return jsonify({'message': 'Buyer updated successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

@app.route("/app/update_listing", methods=['PUT'])
def update_listing():
    try:
        data = request.get_json()
        id = data.get("id")
        listing_name = data.get("listing_name")
        price = data.get("price")
        listing_desc = data.get("listing_description")
        db.update_listing(id, listing_name, price, listing_desc)
        return jsonify({'message': 'Listing updated successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500
    
@app.route("/app/all_listings", methods=['GET'])
def all_listings():
    try:
        data = db.get_all_listings()
        return jsonify({
            "message": "Success",
            "data": data
        }
        ), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

@app.route("/app/listing", methods=['GET'])
def listing():
    try:
        data = request.get_json()
        id = data.get("id")
        db.remove_listing(id)
        return jsonify({
            "message": "Success",
            "data": data
        }
        ), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500


@app.route("/escrow/create", methods=['POST'])
def create_escrow():
    data = request.get_json()


# xrp methods
@app.route("/xrp/get_balance")
def get_balance():
    address = request.args.get("address")
    try:
        balance = xrpl_utilities.get_balance(address)
        return jsonify({"balance": balance})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/xrp/get_trustlines")
def get_trustlines():
    address = request.args.get("address")
    try:
        trustlines = xrpl_utilities.TrustLineAnalytics.get_trustlines(address)
        return jsonify({"Trustlines": trustlines})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route("/xrp/summarize_trustlines")
def summarize():
    try:
        address = request.args.get("address")
        summary = xrpl_utilities.TrustLineAnalytics.summarize_trustlines(address)
        return jsonify(summary)
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500


@app.route("/xrp/get_transaction_history")
def get_transaction_history():
    try:
        address = request.args.get("address")
        try:
            transaction_history = xrpl_utilities.Transaction.get_transaction_history(address)
            return jsonify({"Transaction History": transaction_history})
        except Exception as e:
            return jsonify({"error": str(e)})
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500



if __name__ == "__main__":
    app.run(debug=True)