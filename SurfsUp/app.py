from flask import Flask, jsonify
from datetime import datetime, timedelta

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

#################################################
# Database Setup
#################################################
# reflect an existing database into a new model
engine = create_engine('sqlite:///Resources/hawaii.sqlite')
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each tables
measurements = Base.classes.measurement
stations = Base.classes.station

# Create our session (link) from Python to the DB

#################################################
# Flask Setup
#################################################
#Module10;Lesson 3; Activity 10; app_solution.py
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route("/")
def homepage():
    """List all available routes."""
    return(
        f"Available Routes:<br/>"
        f"/api/v.1.0/precipitation<br/>"
        f"/api/v.1.0/stations<br/>"
        f"/api/v.1.0/tobs<br/>"
        f"/api/v.1.0/start<br/>"
        f"/api/v.1.0/start/end"
    )

@app.route("/api/v.1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # get the most recent date, and subtract 1 year to get two values 12-months apart.
    latestDate = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]
    latestDateMinusOneYear = (datetime.strptime(latestDate.replace("-", "/"), "%Y/%m/%d") - timedelta(days=365)).strftime("%Y-%m-%d")

    #query db to retrieve the latest 12 months of precipitation (prcp) data
    d = session.query(measurements.date, measurements.prcp).\
        filter(measurements.date >= latestDateMinusOneYear).\
        order_by(measurements.date.desc()).\
        all()

    # close link to database.
    session.close()

    #format the query data (d) into a dictionary
    dict = {}
    for n in d:
        dict[n[0]]=n[1]

    return jsonify(dict)


@app.route("/api/v.1.0/stations")
def station():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    #adding all query targets into list
    sel = [stations.station, stations.name, stations.latitude, stations.longitude, stations.elevation]

    #query to retrieve station data
    d = session.query(*sel).all()

    # close link to database.
    session.close()

    #format query data into list of dictionaries
    stations_dict = []
    for n in d:
        station_dict = {}
        station_dict['Name'] = n[1]
        station_dict['Lat'] = n[2]
        station_dict['Lon'] = n[3]
        station_dict['Elevation'] = n[4]
        stations_dict.append({n[0]:station_dict})


    return jsonify(stations_dict)



if __name__ == '__main__':
    app.run(debug=True)

