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
@app.route('/product', methods=['POST'])
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
                'image': product['image']
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
    try:
        # Fetch products
        products = list(products_collection.find({}, {
            '_id': 1, 'name': 1, 'description': 1, 'price': 1, 'category': 1,
            'quantity': 1, 'image': 1
        }).limit(20))
        return jsonify(products), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to update product
@app.route('/product/<product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.json
        products_collection.update_one({'_id': ObjectId(product_id)}, {'$set': data})
        return jsonify({'message': 'Product updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to delete product
@app.route('/product/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        products_collection.delete_one({'_id': ObjectId(product_id)})
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    # Run the application on all available IPs on port 8888
    app.run(host='0.0.0.0', port=8888)