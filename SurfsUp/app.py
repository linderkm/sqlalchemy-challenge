# import dependencies (1)
from flask import Flask, jsonify
from datetime import datetime, timedelta

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

#################################################
# Database Setup
#################################################
# reflect an existing database into a new model (1)
engine = create_engine('sqlite:///Resources/hawaii.sqlite')
Base = automap_base()

# reflect the tables (1)
Base.prepare(autoload_with=engine)

# Save references to each table (1)
measurements = Base.classes.measurement
stations = Base.classes.station

#################################################
# Flask Setup
#################################################
#create Flask app object (1)
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

#index route (1)
@app.route("/")
def homepage():
    #List all available routes.
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

    # get the most recent date, and subtract 1 year to get two values 12-months apart. (2)
    latest_date = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]
    latest_date_minus_one_year = (datetime.strptime(latest_date.replace("-", "/"), "%Y/%m/%d") - timedelta(days=365)).strftime("%Y-%m-%d")

    #query db to retrieve the latest 12 months of precipitation (prcp) data
    d = session.query(measurements.date, measurements.prcp).\
        filter(measurements.date >= latest_date_minus_one_year).\
        order_by(measurements.date.desc()).\
        all()

    #end Python connection to db.
    session.close()

    #format the query data (d) into a dictionary
    dict = {}
    for n in d:
        dict[n[0]]=n[1]

    return jsonify(dict) # (1)


@app.route("/api/v.1.0/stations")
def station():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    #adding all query targets to list (3)
    sel = [stations.station, stations.name, stations.latitude, stations.longitude, stations.elevation]

    #query to retrieve station data (3)
    d = session.query(*sel).all()

    #end Python connection to db.
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

    # get the most recent date, and subtract 1 year to get two values 12-months apart. (2)
    latest_date = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]
    latest_date_minus_one_year = (datetime.strptime(latest_date.replace("-", "/"), "%Y/%m/%d") - timedelta(days=365)).strftime("%Y-%m-%d")

    # query to find the most active stations (2)
    station_count = session.query(stations.station,func.count(stations.station)). \
        group_by(stations.station). \
        order_by(func.count(stations.station).desc()). \
        all()

    #query to find most recent 12 months of temperature (tobs) data from most active station (2)
    most_active_station_data = session.query(measurements.date,measurements.tobs).\
        filter(measurements.date >= latest_date_minus_one_year).\
        filter(measurements.station==station_count[0][0]).\
        all()

    # end Python connection to db.
    session.close()

    #format query data into dictionary to jsonify
    dict = {}
    for n in most_active_station_data:
        dict[n[0]]=n[1]

    #dump dictionary into list, to ensure code conforms with challenge requirements
    list = [dict]

    return jsonify(list)


@app.route("/api/v.1.0/<start_date>")
def start_date(start_date):
    #try except block that manages behavior based on user input.
    # If the user inputs the incorrect date format, a ValueError is raised. (4)
    try:
        # check if user input format matches db date format (4)
        bool(datetime.strptime(start_date,"%Y-%m-%d"))
        # Create session (link) from Python to the DB
        session = Session(engine)

        #query the db to determine the earliest and latest record (2)
        earliest_record = session.query(measurements.date).order_by(measurements.date).first()[0]
        latest_record = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]

        #check to ensure user input occurs within the db records
        if start_date <= latest_record and start_date>= earliest_record:

            #setting query parameters (3)
            sel = [func.min(measurements.tobs), func.max(measurements.tobs), func.avg(measurements.tobs)]
            #query db, filtering by records that occur at or after the date submitted in Request (3)
            d = session.query(*sel).filter(measurements.date >= start_date).all()[0]
            # creating dictionary variable with query data.
            values_dict = {'Minimum Recorded Temperature (f)':d[0],
                           'Maximum Recorded Temperature (f)':d[1],
                           'Average Recorded Temperature (f)':d[2]}
            return_dict = {start_date:values_dict}

            return jsonify(return_dict)
        #return error message if Request date value is outside the range of dates stored in the db.
        else:
            return f"Input date out of range. Temperature records are only available from {earliest_record} to {latest_record}."

        # end Python connection to db.
        session.close()

    # raise error (4)
    except ValueError:
        return f"Incorrect date format. Request using format YYY-MM-DD"




@app.route("/api/v.1.0/<start>/<end_date>")
def start_end_date(start,end_date):
    # check if user input, both start and end dates format, matches db date format
    # https: // www.geeksforgeeks.org / python - validate - string - date - format /
    try:
        bool(datetime.strptime(start,"%Y-%m-%d")) and bool(datetime.strptime(end_date,"%Y-%m-%d"))
        # Create session (link) from Python to the DB
        session = Session(engine)
        # query the db to determine the earliest and latest record
        earliest_record = session.query(measurements.date).order_by(measurements.date).first()[0]
        latest_record = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]
        # conditional to check if Request start date input occurs within the db records
        if start <= latest_record and start>= earliest_record:
            # conditional to check if Request end date input occurs within the db records
            if end_date <= latest_record and end_date >= earliest_record:
                # conditional to check if Request start date occurs before Request end date (e.g. prevent start = 2015 and end = 2014)
                if start < end_date:
                    # setting query parameters (3)
                    sel = [func.min(measurements.tobs),
                           func.max(measurements.tobs),
                           func.avg(measurements.tobs)
                           ]
                    # query db, filtering by records that occur between Request start and end date values. (3)
                    d = session.query(*sel).filter(measurements.date >= start).filter(measurements.date <= end_date).all()[0]
                    # creating dictionary variable to store query data.
                    values_dict = {'Minimum Recorded Temperature (f)':d[0],
                                   'Maximum Recorded Temperature (f)':d[1],
                                   'Average Recorded Temperature (f)':d[2]}
                    return_dict = {f"{start} to {end_date}":values_dict}

                    return jsonify(return_dict)

                else:
                    return "Requested start date must occur before requested end date."

            else:
                return f"Requested end date is out of range. Temperature records are only available from {earliest_record} to {latest_record}."

        else:
            return f"Requested start date is out of range. Temperature records are only available from {earliest_record} to {latest_record}."

        #end Python connection to db.
        session.close()

    # raise error (4)
    except ValueError:
        return f"Incorrect date format. Request using format YYY-MM-DD"


#activate Flask api when python file is run. (1)
if __name__ == '__main__':
    app.run(debug=True)

