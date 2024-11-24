from flask import Flask, jsonify
from datetime import datetime, timedelta

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from tornado.autoreload import start

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
    latest_date = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]
    latest_date_minus_one_year = (datetime.strptime(latest_date.replace("-", "/"), "%Y/%m/%d") - timedelta(days=365)).strftime("%Y-%m-%d")

    #query db to retrieve the latest 12 months of precipitation (prcp) data
    d = session.query(measurements.date, measurements.prcp).\
        filter(measurements.date >= latest_date_minus_one_year).\
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

    #adding all query targets to list
    sel = [stations.station, stations.name, stations.latitude, stations.longitude, stations.elevation]

    #query to retrieve station data
    d = session.query(*sel).all()

    # close link to database
    session.close()

    #format query data into list of dictionaries
    stations_list = []
    for n in d:
        station_dict = {}
        station_dict['Name'] = n[1]
        station_dict['Lat'] = n[2]
        station_dict['Lon'] = n[3]
        station_dict['Elevation'] = n[4]
        stations_list.append({n[0]:station_dict})

    return jsonify(stations_list)


@app.route("/api/v.1.0/tobs")
def tobs():
    session= Session(engine)

    # get the most recent date, and subtract 1 year to get two values 12-months apart.
    latest_date = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]
    latest_date_minus_one_year = (datetime.strptime(latest_date.replace("-", "/"), "%Y/%m/%d") - timedelta(days=365)).strftime("%Y-%m-%d")

    # query to find the most active stations
    station_count = session.query(stations.station,func.count(stations.station)). \
        group_by(stations.station). \
        order_by(func.count(stations.station).desc()). \
        all()

    #query to find most recent 12 months of temperature (tobs) data from most active station
    most_active_station_data = session.query(measurements.date,measurements.tobs).\
        filter(measurements.date >= latest_date_minus_one_year).\
        filter(measurements.station==station_count[0][0]).\
        all()

    # close link to database
    session.close()

    #format query data into dictionary to jsonify
    dict = {}
    for n in most_active_station_data:
        dict[n[0]]=n[1]

    #dumping dictionary into list, to ensure code conforms with challenge requirements
    list = [dict]

    return jsonify(list)


@app.route("/api/v.1.0/<start_date>")
def start_date(start_date):

    #check if user input format matches db date format
    #https: // www.geeksforgeeks.org / python - validate - string - date - format /

    try:
        bool(datetime.strptime(start_date,"%Y-%m-%d"))

        session = Session(engine)

        earliest_record = session.query(measurements.date).order_by(measurements.date).first()[0]
        latest_record = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]

        if start_date <= latest_record and start_date>= earliest_record:

            sel = [func.min(measurements.tobs),
                   func.max(measurements.tobs),
                   func.avg(measurements.tobs)
                   ]

            d = session.query(*sel).filter(measurements.date >= start_date).all()

            values_dict = {'Minimum Recorded Temperature (f)':d[0][0],
                           'Maximum Recorded Temperature (f)':d[0][1],
                           'Average Recorded Temperature (f)':round(d[0][2],2)}
            return_dict = {start_date:values_dict}

            return jsonify(return_dict)

        else:
            return f"Input date out of range. Temperature records are only available from {earliest_record} to {latest_record}."

        session.close()


    except ValueError:

        return f"Incorrect date format. Request using format YYY-MM-DD"



if __name__ == '__main__':
    app.run(debug=True)

