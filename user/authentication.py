from flask import Flask, request, jsonify, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from werkzeug.security import check_password_hash, generate_password_hash
from mongoengine import connect
from user_model import User

app = Flask(__name__)

# client = MongoClient("mongodb+srv://admin:admin@cluster0.pnwu9.mongodb.net")
# db = client.test_user
# users_collection = db.users
connect(db="test_user", host="mongodb+srv://admin:admin@cluster0.pnwu9.mongodb.net/test_user", alias="default")

app.config['JWT_SECRET_KEY'] = 'cSiS4280'
jwt = JWTManager(app)

@app.route('/signup', methods=['POST'])
def signup():
    if not request.json or not all(k in request.json for k in ('userName', 'email', 'password')):
        return abort(400, "Request must contain 'Email' and 'Password'.")

    user_name = request.json['userName']
    email = request.json['email']
    password = request.json['password']

    try:
        existing_user = User.objects(email=email).first()

        if existing_user:
            return jsonify({'message': email + ' is already taken.'}), 400

        hashed_password = generate_password_hash(password)

        new_user = User (
            user_name = user_name,
            email = email,
            password = hashed_password,
        )

        new_user.save()

        access_token = create_access_token(identity=str(new_user.id), additional_claims={'role': new_user.role})

        return jsonify({
            'message': 'Success sign up',
            'access_token': access_token,
            'user_info': {
                'id': str(new_user.id),
                'role': new_user.role
            }}), 201
    except Exception as e :
        return jsonify({'message': 'An error occurred during registration', 'error':str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    if not request.json or not all( k in request.json for k in ('email', 'password')):
        return abort(400, "Request must contain 'Email' and 'Password'.")

    email = request.json['email']
    password = request.json['password']

    try:
        user = User.objects(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({'message': 'Invalid login credentials'}), 401

        access_token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
        return jsonify({
            'message': 'Success log in',
            'access_token': access_token,
            'user_info': {
                'id': str(user.id),
                'user_name': user.user_name,
                'role': user.role
            }
        })
    except Exception as e:
        return jsonify({'message': 'An error occured during login', 'error':str(e)}), 500

# Below is NOT tested yet
@app.route('/user_auth', methods=['GET'])
@jwt_required()
def user_auth():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if user:
        return True
    else:
        return False

@app.route('/admin', methods=['GET'])
@jwt_required()
def admin():
    user_id = get_jwt_identity()
    user = User.objects(user_id=user_id).first()
    if user and user.role == 'admin':
        return True
    else:
        return False

if __name__ == '__main__':
    app.run(debug=True)