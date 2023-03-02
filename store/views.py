from flask import jsonify, request,Blueprint
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from .import app, db
from .models import User, Customer, StoreOwner,Store,Location
from geopy.distance import distance
import openrouteservice

views= Blueprint('views',__name__)
# User registration endpoint
@views.route('/register', methods=['POST'])
def register():
    # Get request data
    email = request.json.get('email')
    password = request.json.get('password')
    user_type = request.json.get('user_type')

    # Get request data for lolation
    country = request.json.get('country')
    city = request.json.get('city')
    state = request.json.get('state')
    postal_code = request.json.get('postal_code')
    street_name = request.json.get('street_name')
    apartment_num = request.json.get('apartment_num')

    # Validate request data
    if not email:
        return jsonify({'message': 'Email is required'}), 400
    if not password:
        return jsonify({'message': 'Password is required'}), 400
    if not user_type:
        return jsonify({'message': 'User type is required'}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User with that email already exists'}), 400

    # Hash password
    hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    
    
    # Check if the location exists in the database
    location= Location.query.filter_by(state=state,country=country, city=city, postal_code=postal_code, street_name=street_name, apartment_num=apartment_num).first()

    # If the location does not exist, create a new location
    if not location:
        location = Location(state=state, country=country, city=city, postal_code=postal_code, street_name=street_name, apartment_num=apartment_num)
        db.session.add(location)
        db.session.commit()

    # Create user based on user_type
    if user_type == 'customer':
        user = Customer(email=email, password=hash_password,location_id=location.id)
    elif user_type == 'store_owner':
        user = StoreOwner(email=email, password=hash_password,location_id=location.id)
    else:
        return jsonify({'message': 'Invalid user type'}), 400
    
    # Add user to database
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

# User login endpoint
@views.route('/login', methods=['POST'])
def login():
    # Get request data
    email = request.json.get('email')
    password = request.json.get('password')

    # Validate request data
    if not email:
        return jsonify({'message': 'Email is required'}), 400
    if not password:
        return jsonify({'message': 'Password is required'}), 400

    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'Invalid email or password'}), 401

    # Check if password is correct
    #if not check_password_hash(user.password, password):
        #return jsonify({'message': 'Invalid email or password'}), 401

    if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        access_token = create_access_token(identity=user.email)
         
        return jsonify({'access_token': access_token}), 200
    # Generate access token
    #access_token = create_access_token(identity=user.email)

    return jsonify({'access_token': access_token}), 200

# Example protected endpoint for store owners
@views.route('/store', methods=['POST'])
@jwt_required()
def create_store():
    # Get user identity from access token
    email = get_jwt_identity()

    # Get store data from request
    store_name = request.json.get('store_name')
    description = request.json.get('description')
    country = request.json.get('country')
    city = request.json.get('city')
    state = request.json.get('state')
    postal_code = request.json.get('postal_code')

    street_name = request.json.get('street_name')
    apartment_num = request.json.get('apartment_num')
   
    # Get store owner
    owner = StoreOwner.query.filter_by(email=email).first()
    if not owner:
        return jsonify({'message': 'Only previledge user can create store'}),404
    owner_id = owner.id
    # Check if the location exists in the database
    store_location= Location.query.filter_by(state=state,country=country, city=city, postal_code=postal_code, street_name=street_name, apartment_num=apartment_num).first()

    # If the location does not exist, create a new location
    if not store_location:
        store_location = Location(state=state, country=country, city=city, postal_code=postal_code, street_name=street_name, apartment_num=apartment_num)
        db.session.add(store_location)
        db.session.commit()
    # Create store and associate with owner
    store = Store(name=store_name, description=description, owner_id=owner_id,location=store_location)
    db.session.add(store)
#    db.session.commit()

    return jsonify({'message': 'Store created successfully'}), 201



@views.route('/nearest-stores', methods=['GET'])
@jwt_required()
def nearest_stores():

    # Query for customer with location
    customer_with_location = Customer.query.join(Location).filter(Location.latitude != None, Location.longitude != None).first()

    # Query for stores with locations
    stores_with_locations = Store.query.join(Location).filter(Location.latitude != None, Location.longitude != None).all()

    # Check if both the customer and store locations have latitude and longitude
    if not customer_with_location or not all(store.location.latitude and store.location.longitude for store in stores_with_locations):
        return jsonify({'error': 'Location could not be tracked.'}), 400

    # Calculate distance between user location and store locations
    store_distances = []
    for store in stores_with_locations:
        store_location = (store.location.latitude, store.location.longitude)
        user_location = (customer_with_location.location.latitude, customer_with_location.location.longitude)
        dist = distance(user_location, store_location).km
        store_distances.append((store, dist))

    # Sort stores by distance
    store_distances.sort(key=lambda x: x[1])

    # Return the 10 closest stores
    closest_stores = []
    for store, dist in store_distances[:10]:
        closest_stores.append({
            'name': store.name,
            'description': store.description,
            'distance': dist,
            'location': {
                'street_name': store.location.street_name,
                'latitude': store.location.latitude,
                'longitude': store.location.longitude
            }
        })

    return jsonify({'stores': closest_stores})



@views.route('/travel-time', methods=['POST'])
@jwt_required()
def travel_time():
    # Get user identity from access token
    email = get_jwt_identity()

    # Get data from request
    store_id = request.json.get('store_id')

    # Get customer with location
    customer = Customer.query.filter_by(email=email).join(Location).filter(Location.latitude != None, Location.longitude != None).first()
    if not customer:
        return jsonify({'message': 'Could not find customer location'}), 404

    # Get store with location
    store = Store.query.filter_by(id=store_id).join(Location).filter(Location.latitude != None, Location.longitude != None).first()
    if not store:
        return jsonify({'message': 'Could not find store location'}), 404

    # Calculate travel time
    client = openrouteservice.Client(key='YOUR_API_KEY')
    coords = ((customer.location.longitude, customer.location.latitude), (store.location.longitude, store.location.latitude))
    routes = client.directions(coords, profile='driving-car', format='geojson')
    if not routes['features']:
        return jsonify({'message': 'Could not calculate travel time'})
    travel_time = routes['features'][0]['properties']['segments'][0]['duration']

    return jsonify({'travel_time': travel_time})
