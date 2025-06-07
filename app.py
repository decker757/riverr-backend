import os
import datetime
import jwt
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import xrpl_utilities
import database

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
CORS(app)

#Address to test functions: rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe
#login
@app.route("/api/login", methods=['POST']) # Need to change to email instead of username
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if database.validate_user_login(username, password):
        payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401
    

@app.route("/api/get_balance")
def get_balance():
    address = request.args.get("address")
    try:
        balance = xrpl_utilities.get_balance(address)
        return jsonify({"balance": balance})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/get_trustlines")
def get_trustlines():
    address = request.args.get("address")
    try:
        trustlines = xrpl_utilities.TrustLineAnalytics.get_trustlines(address)
        return jsonify({"Trustlines": trustlines})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

@app.route("/api/summarize_trustlines")
def summarize():
    address = request.args.get("address")
    summary = xrpl_utilities.TrustLineAnalytics.summarize_trustlines(address)
    return jsonify(summary)


@app.route("/api/get_transaction_history")
def get_transaction_history():
    address = request.args.get("address")
    try:
        transaction_history = xrpl_utilities.Transaction.get_transaction_history(address)
        return jsonify({"Transaction History": transaction_history})
    except Exception as e:
        return jsonify({"error": str(e)})



if __name__ == "__main__":
    app.run(debug=True)