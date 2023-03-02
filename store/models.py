from . import db
from datetime import datetime
from geoalchemy2 import Geometry
from geopy.geocoders import Nominatim

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'user'
    }


class StoreOwner(User):
    __tablename__ = 'store_owners'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    stores = db.relationship('Store', backref='store_owner', lazy='dynamic')

    __mapper_args__ = {
        'polymorphic_identity': 'store_owner'
    }

class Customer(User):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    location = db.relationship('Location', backref='customers')

    __mapper_args__ = {
        'polymorphic_identity': 'customer'
    }

class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(255), nullable=False)
    apartment_num = db.Column(db.String(150), nullable=False)
    street_name = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=True, default=None)
    longitude = db.Column(db.Float, nullable=True, default=None)

    def __init__(self, state, apartment_num, street_name, city, postal_code, country):
        super().__init__(state=state, apartment_num=apartment_num, street_name=street_name, city=city, postal_code=postal_code, country=country)
        self.set_coordinates()

    def set_coordinates(self):
        full_address = f"{self.apartment_num} {self.street_name}, {self.city}, {self.postal_code},{self.state}, {self.country}"
        geolocator = Nominatim(user_agent='store')
        location = geolocator.geocode(full_address)
        if location is None:
            return False
        self.latitude = location.latitude
        self.longitude = location.longitude
        return True


"""
class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    apartment_num = db.Column(db.String(150), nullable=False)
    street_name = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    def set_coordinates(self):
        full_address = f"{self.apartment_num} {self.street_name}, {self.city} {self.postal_code}, {self.country}"
        geolocator = Nominatim(user_agent='store')
        location = geolocator.geocode(full_address)
        if location is None:
            return False
        self.latitude = location.latitude
        self.longitude = location.longitude
        return True
"""
class Store(db.Model):
    __tablename__ = 'stores'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    location = db.relationship('Location', backref='stores')
    owner_id = db.Column(db.Integer, db.ForeignKey('store_owners.id'), nullable=False)

