from flask import Flask
import os
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy


app= Flask(__name__)

db = SQLAlchemy()
def create_app():
    #app= Flask(__name__)
    #db = SQLAlchemy()
    app.config['SECRET_KEY']= os.getenv('SECRET_KEY')
    #app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db" 
    app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://root:@localhost/flask-store-db' 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

    
    db.init_app(app)
  

    from .import models
    jwt = JWTManager(app)
    with app.app_context():
        db.create_all()


    
    #register view
    from .views import views
    #from .auths import auths

    app.register_blueprint(views, url_prefix='/')
    #app.register_blueprint(deletes, url_prefix='/')
    #app.register_blueprint(auths, url_prefix='/')
    
    return app
