from flask import Flask, abort, jsonify, request
from bcrypt import hashpw, gensalt, checkpw
from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB Atlas connection string
client = MongoClient('mongodb+srv://admin:admin@cluster0.5n6rm.mongodb.net')

# Access the 'wms' database and 'products' collection
db = client.wms
products_collection = db.products
users_collection = db.users
transactions_collection = db.transactions

# Root route for health check
@app.route('/')
def home():
    return jsonify({'message': 'Welcome to the Product and User API.'}), 200

# Route to add a new product
@app.route('/users', methods=['POST'])
def add_user():
    # Ensure request JSON exists and is a list
    if not request.json or not all(k in request.json for k in ('username', 'password')):
        abort(400, "Request must be a list of products with 'username', 'password'.")

    try:
        data = request.json
        # Check if user already exists
        existing_user = users_collection.find_one({'username': data['username']})
        if existing_user:
            return jsonify({'message': f'{data['username']} is already taken. Try another username.'}), 400

        # Create new user document
        new_user = {
            'username': data['username'],
            'password': data['password'],
            'isAdmin': False, # Default role
            'address': '',
            'phone': '',
            'profileImg': ''
        }

        # Insert the new user into the collection
        users_collection.insert_one(new_user)
        return jsonify({'message': 'User added successfully.'}), 201

    except Exception as e:
        return jsonify({'message': 'An error occurred during registration.', 'error': str(e)}), 500

# Route to get all users
@app.route('/users', methods=['GET'])
def get_users():
    try:
        # Fetch users
        users = list(users_collection.find())
        for user in users:
            user['_id'] = str(user['_id'])
        return jsonify(users), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to get a user by username
@app.route('/users/<username>', methods=['GET'])
def get_user_by_username(username):
    try:
        # Find user by username
        user = users_collection.find_one({'username': username})
        if user:
            # Convert MongoDB object to JSON serializable
            user['_id'] = str(user['_id'])
            return jsonify(user), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to login
@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        # Validate input
        if not data or not all(k in data for k in ('username', 'password')):
            return jsonify({'error': 'Username and password are required.'}), 400
        
        username = data['username']
        password = data['password']

        # Fetch user from database
        user = users_collection.find_one({'username': username})
        if user and checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            user_data = {
                'id': str(user['_id']),
                'username': user['username'],
                'isAdmin': user['isAdmin'],
                'address': user['address'],
                'phone': user['phone'],
                'profileImg': user['profileImg']
            }
            return jsonify(user_data), 200
        else:
            return jsonify({'error': 'Invalid username or password.'}), 401
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}.'}), 500

# Route to update a user
@app.route('/users/<username>', methods=['PUT'])
def update_user(username):
    data = request.json
    # Ensure request JSON exists and is a list
    if not username:
        return jsonify({'error': 'Username is required.'}), 400
    try:
        update_fields = {}
        # Optional fields for updating
        if 'username' in data:
            update_fields['username'] = data['username']
        if 'password' in data:
            update_fields['password'] = data['password']
        if 'isAdmin' in data:
            update_fields['isAdmin'] = data['isAdmin']
        if 'address' in data:
            update_fields['address'] = data['address']
        if 'phone' in data:
            update_fields['phone'] = data['phone']
        if 'profileImg' in data:
            update_fields['profileImg'] = data['profileImg']

        if not update_fields:
            return jsonify({'error': 'No fields to update provided.'}), 400
        
        # Update user in MongoDB
        updated_user = users_collection.update_one(
            {'username': username},
            {'$set': update_fields}
        )

        if updated_user.matched_count == 0:
            return jsonify({'error': 'User not found.'}), 404
        
        return jsonify({'message': 'User updated successfully.'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to add a new product
@app.route('/products', methods=['POST'])
def add_product():
    try:
        # Get product data from request
        data = request.json

        # Validate required fields
        required_fields = ['name', 'description', 'price', 'category', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f"'{field}' is required."}), 400

        new_product = {
            'name': data['name'],
            'description': data.get('description', ''),
            'price': data['price'],
            'category': data['category'],
            'quantity': data['quantity'],
            'imgName': data.get('imgName', None) # image is optional
        }

        # Insert new product into database
        products_collection.insert_one(new_product)

        return jsonify({'message': 'Products added successfully.'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to get all products
@app.route('/products', methods=['GET'])
def get_products():

    # Get optional query parameters for filtering
    name = request.args.get('name')
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    available = request.args.get('available')

    # Build query based on parameters
    query = {}

    if category:
        # Case-insensitive
        query['category'] = {'$regex': category, '$options': 'i'}
    if name:
        # Case-insensitive
        query['name'] = {'$regex': name, '$options': 'i'}

    if min_price is not None or max_price is not None:
        query['price'] = {}
        if min_price:
            query['price']['$gte'] = min_price
        if max_price:
            query['price']['$lte'] = max_price
    
    if available is not None:
        available = available.lower() == 'true'
        if available:
            query['quantity'] = {'$gt': 0}
        else:
            query['quantity'] = {'$lte': 0}

    try:
        # Fetch products
        products = list(products_collection.find(query))
        for product in products:
            product['_id'] = str(product['_id'])
        return jsonify(products), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Route to delete a user
@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        users_collection.delete_one({'_id': ObjectId(user_id)})
        return jsonify({'message': 'User deleted successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to get a product by id
@app.route('/products/<product_id>', methods=['GET'])
def get_product_by_id(product_id):
    try:
        # Validate and convert the product ID
        product = products_collection.find_one({'_id': ObjectId(product_id)})
        if not product:
            return jsonify({'error': 'Product not found.'}), 404
        
        # Convert the product data to JSON serializable format
        product['_id'] = str(product['_id'])
        return jsonify(product), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to update a product
@app.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.json
        products_collection.update_one({'_id': ObjectId(product_id)}, {'$set': data})
        return jsonify({'message': 'Product updated successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to delete a product
@app.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        products_collection.delete_one({'_id': ObjectId(product_id)})
        return jsonify({'message': 'Product deleted successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Route to get transaction by date
@app.route('/transactions', methods=['GET'])
def get_transaction():

    # Get optional query parameter for filtering
    date = request.args.get('date')

    # Build query based on parameters
    query = {}
    
    current_date = datetime.now().strftime("%Y-%m-%d")

    if date is not None:
        query['date'] = date
    else:
        query['date'] = current_date

    try:
        # Fetch products
        transactions = list(transactions_collection.find(query))
        for transaction in transactions:
            transaction['_id'] = str(transaction['_id'])
        return jsonify(transactions), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transactions', methods=['POST'])
def add_transaction():
    try:
        # Get the transaction data from the request
        data = request.json

        # Validate required fields
        required_fields = ['image', 'name', 'price', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f"'{field}' is required."}), 400

        # Insert transaction into database
        transaction = {
            'image': data['image'],
            'name': data['name'],
            'price': float(data['price']),
            'date': data['date'],
        }
        if 'id' in data and data['id'] is not None:
            transaction['_id'] = data['id']
        
        result = users_collection.insert_one(transaction)

        # Return success response
        return jsonify({
            'message': 'Transaction added successfully.',
            'transaction_id': str(result.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the application on all available IPs on port 8888
    app.run(host='0.0.0.0', port=8888)