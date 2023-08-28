from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'secret key' #change this IRL
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '79b88834c65a99'
app.config['MAIL_PASSWORD'] = '437b6c51bc1c9c'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("database created")


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print("databse cleaned")

@app.cli.command('db_seed')
def db_seed():
    mercury = planet(planet_name="Mercury",
    planet_type='Class-D',
    home_star='Sol',
    mass=3.258e23,
    radius=1856,
    distance=38.98e6)

    venus = planet(planet_name='Venus',
    planet_type='Class-E',
    home_star='Sol',
    mass=3.25e24,
    radius=2098,
    distance=98.65e7)
    
    earth = planet(planet_name="earth",
    planet_type='Class k',
    home_star='Sol',
    mass=6.258e13,
    radius=346,
    distance=28.98e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = user(first_name='William',
    last_name='Ericson',
    email='willer@gmail.com',
    password='pass@ghu')

    db.session.add(test_user)
    db.session.commit()
    print('database seeded')

@app.route("/")
def hello_world():
    return "hello world"


@app.route("/super_simple")
def super_simple():
    return "hello from planetary world..."


@app.route("/url_parameters/<string:name>/<int:age>")
def url_parameters(name:str, age:int):
    if age<18:
        return jsonify(message="Sorry "+name+", you are not old enough.."),404
    else:
        return jsonify(message="Welcome "+name+", you are old enough!")


@app.route('/planet',methods=['GET'])
def planet():
    planets_list = planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(data=result)


@app.route('/register',methods=['POST'])
def register():
    global user,first_name,last_name,password
    email = request.form['email']
    test = user.query.filter_by(email=email).first()
    if test:
        return jsonify(message='email already exist!'),409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = user(first_name=first_name ,last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message='User created successfully!!'), 201


@app.route('/login',methods=['POST'])
def login():
    
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    test = user.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login succeeded!!',access_token=access_token)
    else:
        return jsonify(message="bad password, permission denied"), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email:str):
    global user
    user = user.query.filter_by(email=email).first()
    if user:
        msg = Message("Your planetary password is "+ user.password, sender="admin@planetary-api.com", recipients=[email])
        mail.send(msg)
        return jsonify(message="Password sent to "+ email)
    else:
        return jsonify(message="Email doesnot exist!!"), 401


@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id: int):
    global planet
    planet = planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(data=result)
    else:
        return jsonify(message="planet desnt exist"), 409


@app.route('/planet_add',methods=['POST'])
@jwt_required(optional=False)
def planet_add():
    planet_name = request.form['planet_name']
    test = planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(message="theres already a planet by that name"), 409
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = float(request.form['mass'])
        radius = float(request.form['radius'])
        distance = float(request.form['distance'])

        new_planet = planet(planet_name=planet_name,
        planet_type=planet_type,
        home_star=home_star,
        radius=radius,
        distance=distance,
        mass=mass)

        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="you added a new planet detail!!"), 201


@app.route('/update_planet',methods=['PUT'])
@jwt_required(optional=False)
def update_planet():
    global planet
    planet_id = int(request.form['planet_id'])
    planet = planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        planet.home_star = request.form['home_star']
        planet.mass = float(request.form['mass'])
        planet.radius = float(request.form['radius'])
        planet.distance = float(request.form['distance'])
        db.session.commit()
        return jsonify(message="updated the planet"), 202
    else:
        return jsonify(message="thatplanet doesnt exist"), 404


@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required(optional=False)
def remove_planet(planet_id: int):
    global planet
    planet = planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message="you deleted a planet"), 202
    else:
        return jsonify(message="this planet doesnt exist"), 404
    

# database models
class user(db.Model):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class planet(db.Model):
    __tablename__ = 'planet'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class userSchema(ma.Schema):
    class Meta:
        fields = ('id','first_name','last_name','email','password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id','planet_name','planet_type','home_star','mass','radius','distance')


user_schema = userSchema()
users_schema = userSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
    
    app.run()
