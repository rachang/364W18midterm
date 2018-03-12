###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length # Here, too
from flask_sqlalchemy import SQLAlchemy
#import statements for api
import urllib.request
import json
api_key = "2669dfc6257b0517"
## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:morningstar@localhost/SI364midterm"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################



##################
##### MODELS #####
##################

class Place(db.Model):
    __tablename__ = "places"
    place_id = db.Column(db.Integer,primary_key=True)
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    conditions = db.relationship('Conditions',backref='Place')
    def __repr__(self):
        return "{}, {}".format(self.city, self.state)

class Conditions(db.Model):
    __tablename__ = "current conditions"
    conditions_id = db.Column(db.Integer,primary_key=True)
    temperature = db.Column(db.String(64))
    weather = db.Column(db.String(64))
    observation_time = db.Column(db.String(280))
    place_id = db.Column(db.Integer,db.ForeignKey("places.place_id"))
    def __repr__(self):
        return "{} and {} at {}".format(self.temperature, self.weather, self.observation_time)

class Place2(db.Model):
    __tablename__ = "newplaces"
    place2_id = db.Column(db.Integer,primary_key=True)
    city = db.Column(db.String(64))
    country = db.Column(db.String(64))
    forecasts = db.relationship('Forecast',backref='Place2')
    def __repr__(self):
        return "{}, {}".format(self.city, self.country)

class Forecast(db.Model):
    __tablename__ = "forecasts"
    forecasts_id = db.Column(db.Integer,primary_key=True)
    day = db.Column(db.String(64))
    morning_forecast = db.Column(db.String(280))
    evening_forecast = db.Column(db.String(280))
    place2_id = db.Column(db.Integer,db.ForeignKey("newplaces.place2_id")) 
    def __repr__(self):
        return "{},{},{}".format(self.day, self.morning_forecast, self.evening_forecast)    


###################
###### FORMS ######
###################

class PlaceForm(FlaskForm):
    city = StringField("Please enter an American city.",validators=[Required()])
    state = StringField("Please enter the 2 letter State Abbreviation.",validators=[Required()])
    def validate_state(form,field):
        message = "the State MUST be 2 letters"
        if len(field.data) != 2:
            raise ValidationError(message)
    submit = SubmitField('Submit')

class InternationalForm(FlaskForm):
    city = StringField("Please enter a Non-US city",validators=[Required()])
    country = StringField("Please enter the country name.",validators=[Required()])
    submit = SubmitField('Submit')     


#######################
###### VIEW FXNS ######
#######################
## Error handling routes - PROVIDED
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/uscity',methods=["GET","POST"])
def index():
    form = PlaceForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if request.method == 'POST' and form.validate_on_submit():
        city = form.city.data
        state = form.state.data
        newplace = Place.query.filter_by(city=city, state=state).first()
        if newplace:
            place_id = newplace.place_id
            print(newplace, "Place already exists")
        else:
            newplace = Place(city=city, state=state) 
            db.session.add(newplace)
            db.session.commit()
            place_id = newplace.place_id
        if " " in city:
            newcity = "_".join(city.split())    
        else:
            newcity = city
        f = urllib.request.urlopen('http://api.wunderground.com/api/'+api_key+'/geolookup/conditions/q/'+state+'/'+newcity+'.json')
        json_string = f.read()
        parsed_json = json.loads(json_string)
        location = parsed_json['location']['city']
        observation_time = parsed_json['current_observation']['observation_time']
        temperature = parsed_json['current_observation']['temp_f']
        weather = parsed_json['current_observation']['weather']
        new_conditions = Conditions.query.filter_by(observation_time=observation_time, place_id=newplace.place_id).first()
        if new_conditions:
            conditions_id = new_conditions.conditions_id
            return redirect(url_for('all_us_cities')) 
        else:
            new_conditions = Conditions(temperature=temperature, weather=weather, observation_time=observation_time, place_id=newplace.place_id)
            db.session.add(new_conditions)
            db.session.commit()
            conditions_id = new_conditions.conditions_id
            return redirect(url_for('index'))
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('index.html',form=form)

@app.route('/uscities')
def all_us_cities():
    places = Place.query.all()
    all_locations = []
    for place in places:
        condition = Conditions.query.filter_by(place_id=place.place_id).first()
        all_locations.append((place.city, place.state, condition.temperature, condition.weather, condition.observation_time))
    return render_template('uscity.html', locations=all_locations)

@app.route('/form')
def formentry():
    form = InternationalForm()
    return render_template('index2.html',form=form)

@app.route('/nonuscity', methods=["GET","POST"])
def index2():
    form=InternationalForm()
    if request.args:
        city = request.args.get('city')
        country = request.args.get('country')
        newplace2 = Place2.query.filter_by(city=city, country=country).first()
        if newplace2:
            place2_id = newplace2.place2_id
            print(newplace2, "Place already exists")
        else:
            newplace2 = Place2(city=city, country=country) 
            db.session.add(newplace2)
            db.session.commit()
            place2_id = newplace2.place2_id
        newcountry = "_".join(country.split(" "))
        new_city = "_".join(city.split(" "))
        f = urllib.request.urlopen('http://api.wunderground.com/api/'+api_key+'/geolookup/forecast/q/'+country+'/'+city+'.json')
        json_string = f.read()
        parsed_json = json.loads(json_string)
        day = parsed_json['forecast']['simpleforecast']['forecastday'][0]["date"]["pretty"]
        morning_forecast = forecasts = parsed_json['forecast']['txt_forecast']['forecastday'][0]["fcttext"]
        evening_forecast = forecasts = parsed_json['forecast']['txt_forecast']['forecastday'][1]["fcttext"]
        new_forecasts = Forecast.query.filter_by(day=day, place2_id=newplace2.place2_id).first()
        if new_forecasts:
            forecasts_id = new_forecasts.forecasts_id
            return redirect(url_for('non_us_cities')) 
        else:
            new_conditions = Forecast(day=day, morning_forecast=morning_forecast, evening_forecast=evening_forecast, place2_id=newplace2.place2_id)
            db.session.add(new_forecasts)
            db.session.commit()
            forecasts_id = new_forecasts.forecasts_id
            return redirect(url_for('index2'))
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return redirect(url_for('formentry'))

@app.route('/nonuscities')
def non_us_cities():
    places = Place2.query.all()
    all_locations = []
    for place in places:
        forecast = Forecast.query.filter_by(place2_id=place.place2_id).first()
        all_locations.append((place.city, place.country, forecast.day, forecast.morning_forecast, forecast.evening_forecast))
    return render_template('nonuscity.html', locations=all_locations)


## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
if __name__ == '__main__':
    db.create_all() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual
