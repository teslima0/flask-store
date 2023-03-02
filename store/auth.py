from flask import jsonify,Blueprint, request
from .models import Customer,Location,Store
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auths=Blueprint('auths',__name__)

@auths.route('/estimated-time', methods=['POST'])
@jwt_required()
def estimated_time():
    """
    In this endpoint, we first retrieve the customer's identity from the JWT access token,
    then get the store ID and start location data from the request.
    We then query the database for the customer and store objects with their respective location data, 
    and check that the data is available. We then use the Google Maps Directions API to calculate the estimated time it will take for the 
    customer to get from their start location to the store. We return the estimated time as a JSON response.
    """

    # Get user identity from access token
    email = get_jwt_identity()

    # Get customer data from request
    store_id = request.json.get('store_id')
    start_location = request.json.get('start_location')

    # Query for customer with location
    customer = Customer.query.join(Location).filter(Customer.email == email, Location.latitude != None, Location.longitude != None).first()

    # Query for store with location
    store = Store.query.get(store_id)
    if not store:
        return jsonify({'message': 'Store not found'}), 404

    # Check if both customer and store have location data
    if not customer.location or not store.location:
        return jsonify({'message': 'Location data not available'}), 400

    # Calculate estimated time using Google Maps Directions API
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_location}&destination={store.location.latitude},{store.location.longitude}&key={'GOOGLE_MAPS_API_KEY'}"
    response = request.get(url)
    if response.status_code != 200:
        return jsonify({'message': 'Error occurred while retrieving data from Google Maps API'}), 500

    data = response.json()
    if data['status'] != 'OK':
        return jsonify({'message': 'Could not calculate estimated time'}), 400

    duration = data['routes'][0]['legs'][0]['duration']['text']

    return jsonify({'estimated_time': duration})
