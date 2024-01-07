from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import threading
import copy
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SECURITY_PASSWORD_SALT'] = 'salt'
app.config['JWT_SECRET_KEY'] = 'jwt_secret'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Simulating a database with version control
floor_plans = {}
floor_plan_history = {}
mutex = threading.Lock()

# Define User and Role models for Flask-Security
class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    roles = db.relationship('Role', secondary='user_roles')

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Setup Flask-Security to use JWT
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_claims_loader
def add_claims_to_access_token(user):
    return {'roles': [role.name for role in user.roles]}

def resolve_conflict(existing_data, new_data):
    # Example conflict resolution logic based on timestamp
    if existing_data['timestamp'] > new_data['timestamp']:
        return existing_data
    else:
        return new_data

def create_revision(floor_id, data):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if floor_id not in floor_plan_history:
        floor_plan_history[floor_id] = []

    floor_plan_history[floor_id].append({
        'timestamp': timestamp,
        'data': copy.deepcopy(data)
    })

@app.route('/upload_floor_plan', methods=['POST'])
@jwt_required()
def upload_floor_plan():
    try:
        uploaded_data = request.json
        floor_id = uploaded_data['floor_id']

        with mutex:
            if floor_id not in floor_plans:
                floor_plans[floor_id] = uploaded_data
                create_revision(floor_id, uploaded_data)
                return jsonify({'message': 'Floor plan uploaded successfully'})

            # Conflict resolution
            existing_data = floor_plans[floor_id]
            resolved_data = resolve_conflict(existing_data, uploaded_data)
            floor_plans[floor_id] = resolved_data
            create_revision(floor_id, resolved_data)

            return jsonify({'message': 'Conflict resolved and floor plan updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_floor_plan_history/<floor_id>', methods=['GET'])
@jwt_required()
def get_floor_plan_history(floor_id):
    try:
        with mutex:
            history = floor_plan_history.get(floor_id, [])
            return jsonify({'history': history})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
