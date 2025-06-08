import os
import datetime
import jwt
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import xrpl_utilities
from xrpl_client import XRPLClient
from xrpl.transaction import submit_and_wait
from xrpl.clients import JsonRpcClient
import db

# Load environment variables from .env
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
JSON_RPC_URL = os.getenv("JSON_RPC_URL")

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# --- Basic Utility Route ---

# Health check route to test server is alive
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "pong"}), 200


# --- User Authentication ---

# Login route: verifies user credentials and returns a JWT token if valid
@app.route("/app/login", methods=['POST']) 
def login():
    try:
        data = json.loads(request.get_data(as_text=True))
        username = data["username"]
        password = data["password"]

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

# Registration route: creates a new user
@app.route("/app/register", methods=['POST'])
def register():
    try:
        data = json.loads(request.get_data(as_text=True))
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


# --- User Data Retrieval ---

# Get specific user data by username
@app.route("/app/user", methods=['GET'])
def get_user():
    try:
        data = json.loads(request.get_data(as_text=True))
        username = data["username"]
        user_data = db.get_user_data_by_username(username)

        if user_data:
            return jsonify({"message": "Success", "data": user_data}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

# Get all users, optionally excluding the requesting user
@app.route("/app/all_users", methods=['GET'])
def get_all_user():
    try:
        data = json.loads(request.get_data(as_text=True))
        username = data["username"]
    except:
        username = None
    try:
        data = db.get_all_usernames(username)
        if data:
            return jsonify({"message": "Success", "data": data}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

@app.route("/app/update_wallet", methods=['GET'])
def update_wallet():
    try:
        data = json.loads(request.get_data(as_text=True))
        username = data["username"]
        wallet_id = data["wallet_id"]
        data = db.update_wallet(username, wallet_id)
        if data:
            return jsonify({"message": "Success", "data": data}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

# --- Listings ---

# Create a new listing
@app.route("/app/create_listing", methods=['POST'])
def create_listing():
    try:
        data = json.loads(request.get_data(as_text=True))
        username = data["username"]
        listing_name = data["listing_name"]
        price = data["price"]  # Ensure it's not a tuple
        listing_desc = data["listing_description"]
        db.insert_listing(username, listing_name, price, listing_desc)
        return jsonify({'message': 'Listing created successfully'}), 201
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

# Remove a listing by ID
@app.route("/app/remove_listing", methods=['DELETE'])
def remove_listing():
    try:
        data = json.loads(request.get_data(as_text=True))
        id = data["id"]
        db.remove_listing(id)
        return jsonify({'message': 'Listing deleted successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

# Update listing details
@app.route("/app/update_listing", methods=['PUT'])
def update_listing():
    try:
        data = json.loads(request.get_data(as_text=True))
        id = data["id"]
        listing_name = data["listing_name"]
        price = data["price"]
        listing_desc = data["listing_description"]
        db.update_listing(id, listing_name, price, listing_desc)
        return jsonify({'message': 'Listing updated successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

# Get all listings
@app.route("/app/all_listings", methods=['GET'])
def all_listings():
    try:
        data = db.get_all_listings()
        return jsonify({"message": "Success", "data": data}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

# Get a specific listing (seems like it deletes a listing too — potential bug)
@app.route("/app/listing", methods=['GET'])
def listing():
    try:
        data = json.loads(request.get_data(as_text=True))
        id = data["id"]
        db.remove_listing(id)  # NOTE: This deletes a listing, which is unexpected in a GET
        return jsonify({"message": "Success", "data": data}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

@app.route("/app/reset_listing", methods=['PUT'])
def reset_listing():
    try:
        data = json.loads(request.get_data(as_text=True))
        id = data["id"]
        db.update_buyer(id, None, None, None)
        return jsonify({'message': 'Listing updated successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500


# --- XRP Escrow Routes ---

# Create an escrow transaction
@app.route("/escrow/create", methods=['POST'])
def create_escrow():
    try:
        data = json.loads(request.get_data(as_text=True))
        
        listing_id = data["id"]
        buyer = data["buyer"]
        cancel_time = data["cancel_after"]

        response = db.get_listing(listing_id)
        if not response:
            return jsonify({
                "message":"Listing not found"
            }),404
        
        sender = db.get_user_data_by_username(buyer)["wallet_id"]
        destination = db.get_user_data_by_username(response["seller_name"])["wallet_id"]

        if not (sender and destination):
            return jsonify({
                "message":"Buyer or seller wallet not found"
            }),404

        tx, condition, fullfillment = XRPLClient(JSON_RPC_URL).create_escrow_tx(
            sender, destination, response["price"], cancel_time
        )
        db.update_buyer(listing_id, data["buyer"], fullfillment, condition)
        tx = json.loads(json.dumps(tx.to_dict()))

        return jsonify({
            'message': 'Escrow payload and hash created successfully',
            'data': tx
        }), 201
    
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

# Finish an escrow transaction
@app.route("/escrow/finish", methods=['POST'])
def finish_escrow():
    try:
        data = json.loads(request.get_data(as_text=True))
        listing_id = data["id"]
        response = db.get_listing(listing_id)

        if not response:
            return jsonify({'error': 'Listing not found'}), 404

        sender = db.get_user_data_by_username(response["buyer_name"])["wallet_id"]
        destination = db.get_user_data_by_username(response["seller_name"])["wallet_id"]

        if not (sender and 
                destination and 
                response["escrow_condition"] and
                response["escrow_sequence"] and 
                response["escrow_fufill"]):
            return jsonify({'error': 'Escrow was not generated successfully, cannot finish'}), 400
 
        
        payload = json.loads(json.dumps(XRPLClient(JSON_RPC_URL).finish_escrow_tx(
            destination, sender, response["escrow_sequence"], response["escrow_condition"], response["escrow_fufill"]
        ).to_dict()))
        
        return jsonify({'message': 'Escrow finished successfully', 'data': payload}), 201
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500


# Get XRP balance for an address
@app.route("/xrp/get_balance")
def get_balance():
    address = request.args.get("address")
    try:
        balance = xrpl_utilities.get_balance(address)
        return jsonify({"balance": balance})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Get trustlines for an address
@app.route("/xrp/get_trustlines")
def get_trustlines():
    address = request.args.get("address")
    try:
        trustlines = xrpl_utilities.TrustLineAnalytics.get_trustlines(address)
        return jsonify({"Trustlines": trustlines})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Summarize trustlines for an address
@app.route("/xrp/summarize_trustlines")
def summarize():
    try:
        address = request.args.get("address")
        summary = xrpl_utilities.TrustLineAnalytics.summarize_trustlines(address)
        return jsonify(summary)
    except Exception as e:
        print(e)
        return jsonify({'error': 'Unknown error'}), 500

# Get transaction history for an address
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


# --- App Runner ---
if __name__ == "__main__":
    app.run(debug=True)
