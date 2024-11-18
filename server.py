from flask import Flask, abort, jsonify, request
from bson import ObjectId
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB Atlas connection string
client = MongoClient("mongodb+srv://admin:admin@cluster0.5n6rm.mongodb.net")

# Access the 'wms' database and 'products' collection
db = client.wms
products_collection = db.products

# Root route for health check
@app.route('/')
def home():
    return jsonify({'message': 'Welcome to the Product API'}), 200

# Route to add a new product
@app.route('/products', methods=['POST'])
def add_product():
    # Ensure request JSON exists and is a list
    if not request.json or not isinstance(request.json, list):
        abort(400, "Request must be a list of products with 'name', 'price', 'category', 'quantity', and 'image'.")

    try:
        data = request.json
        new_products = []

        for product in data:
            # Check if each product contains the required fields
            if not all (k in product for k in ('name', 'price', 'category', 'quantity', 'image')):
                abort(400, "Each product must contain 'name', 'price', 'category', 'quantity', and 'image'.")

            new_product = {
                'name': product['name'],
                'description': product.get('description', ''),
                'price': product['price'],
                'category': product['category'],
                'quantity': product['quantity'],
                'image': product['image'],
            }
            new_products.append(new_product)

        # Insert all products in bulk
        products_collection.insert_many(new_products)
        return jsonify({'message': 'Products added successfully'}), 201
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
    in_stock = request.args.get('in_stock')

    # Build query based on parameters
    query = {}

    if category:
        # Case-insensitive
        query['category'] = {'$regex': category, '$options': 'i'}
    if name:
        # Case-insensitive
        query['name'] = {'$regex': name, '$options': 'i'}
    if min_price or max_price:
        query['price'] = {}
        if min_price:
            query['price']['$gte'] = min_price
        if max_price:
            query['price']['$lte'] = max_price
    if in_stock is not None:
        query['quantity'] = {'$gt': 0}

    try:
        # Fetch products
        products = list(products_collection.find(query))
        for product in products:
            product['_id'] = str(product['_id'])
        return jsonify(products), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to update product
@app.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.json
        products_collection.update_one({'_id': ObjectId(product_id)}, {'$set': data})
        return jsonify({'message': 'Product updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to delete product
@app.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        products_collection.delete_one({'_id': ObjectId(product_id)})
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run the application on all available IPs on port 8888
    app.run(host='0.0.0.0', port=8888)