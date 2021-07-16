"""
GeoSentry GeoCore API

Google Cloud Platform - Cloud Run

geocore-chrono service
"""
import os
import json
import datetime

import flask
import flask_restful

import ee
from terrarium import temporal
from terrarium import spatial
from terrarium import initialize

class LogEntry:
    """ A class that represents a serverless log compliant with Google Cloud Platform. """

    service = "geocore-chrono"

    def __init__(self, workflow: str) -> None:
        """ Initialization Method """
        self.workflow: str = workflow
        self.logtrace: list = [f"execution started. worflow - {workflow}."]

        self.baselog = {
            "trace": self.logtrace, 
            "service":self.service
        }

        project = os.environ.get('GCP_PROJECT')
        reqtrace = flask.request.headers.get('X-Cloud-Trace-Context')

        if reqtrace and project:
            tracedata = f"projects/{project}/traces/{reqtrace.split('/')[0]}"
            self.baselog.update({"logging.googleapis.com/trace": tracedata})

    def addtrace(self, trace: str):
        """ A method that adds a trace string to the list of logtraces. """
        self.logtrace.append(trace)

    def flush(self, severity: str, message: str):
        """
        A method of LogEntry that creates and flushes the built log to Cloud Logging as
        a structured log given that it is called within a Cloud Run/Functions Service.
        The method accepts a log severity string and a log message string.

        Accepted log severity values are - EMERGENCY, ALERT, CRITICAL, ERROR, WARNING, NOTICE, INFO, DEBUG and DEFAULT.
        Refer to https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#logseverity for more information.
        """
        self.addtrace("execution ended.")
        logentry = dict(severity=severity, message=message)
        logentry.update(self.baselog)

        print(json.dumps(logentry))

class Check(flask_restful.Resource):
    """ RESTful resource for the '/check' endpoint. """

    def post(self):
        """ RESTful POST """
        # Create a LogEntry object for the check workflow
        log = LogEntry("check")

        # Parse the request JSON
        request = flask.request.get_json()
        log.addtrace("request parsed.")

        try:
            # Retrieve the 'bounds' and 'timestamp' keys from the request
            bounds = request["bounds"]
            timestamp = request["timestamp"]

            # Check that bounds is a list.
            if not isinstance(bounds, list):
                # log and return the error
                log.addtrace("invalid bounds")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"temporal check failed. invalid bounds. must be a list"}, 400

            log.addtrace(f"bounds - {bounds}.")

            # Check that timestamp is a str.
            if not isinstance(timestamp, str):
                # log and return the error
                log.addtrace("invalid timestamp.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"temporal check failed. invalid timestamp. must be an str"}, 400

            log.addtrace(f"timestamp - {timestamp}.")

        except KeyError as e:
            # log and return the error
            log.addtrace(f"missing request parameter {e}.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"temporal check failed. missing request parameter. {e}"}, 400

        log.addtrace(f"request parameters retrieved.")

        try:
            # Initialize Earth Engine Session
            initialize(os.environ.get("GCP_PROJECT")) if not ee.data._initialized else None

        except Exception as e:
            # log and return the error
            log.addtrace(f"{e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"temporal check failed. {e}"}, 500

        try:
            # Generate an Earth Engine Geometry from the bounds
            geometry = spatial.generate_earthenginegeometry_frombounds(*bounds)

            # Obtain the datetime from the timestamp
            date = datetime.datetime.fromisoformat(timestamp)

        except RuntimeError as e:
            # log and return the error
            log.addtrace(f"could not generate geometry from bounds. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"temporal check failed. could not generate geometry from bounds. {e}"}, 400

        except Exception as e:
            # log and return the error
            log.addtrace(f"could not generate date from timestamp. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"temporal check failed. could not generate date from timestamp. {e}"}, 400

        log.addtrace("temporal parameters generated.")

        try:
            # Generate a daterange buffered around the date by 12 hours
            daterange = temporal.generate_daterange(date, 0.5, buffer=True)

            # Create a Sentinel-2 MSI collection
            collection = ee.ImageCollection("COPERNICUS/S2_SR")
            # Filter the collection for the daterange
            collection = collection.filterBounds(geometry).filterDate(*daterange)
            
            # Check if images exist in the the collection
            exists = True if collection.size().getInfo() else False
            # log the generated values
            log.addtrace(f"acquisition check - {exists}")
            log.flush("INFO", "runtime complete")

            # Return the check response
            return {"check": exists}, 200

        except Exception as e:
            # log and return the error
            log.addtrace("could not check if acquisition exists.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"temporal check failed. could not check if acquisition exists. {e}"}, 500
    
class Select(flask_restful.Resource):
    """ RESTful resource for the '/select' endpoint. """

    def post(self):
        """ RESTful POST """
        # Create a LogEntry object for the select workflow
        log = LogEntry("select")

        # Parse the request JSON
        request = flask.request.get_json()
        log.addtrace("request parsed.")

        try:
            # Retrieve the 'bounds' and 'count' keys from the request
            bounds = request["bounds"]
            count = request["count"]

            # Check that bounds is a list.
            if not isinstance(bounds, list):
                # log and return the error
                log.addtrace("invalid bounds")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"temporal select failed. invalid bounds. must be a list"}, 400

            log.addtrace(f"bounds - {bounds}.")

            # Check that count is an int.
            if not isinstance(count, int):
                # log and return the error
                log.addtrace("invalid count")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"temporal select failed. invalid count. must be an int"}, 400

            log.addtrace(f"count - {count}.")

        except KeyError as e:
            # log and return the error
            log.addtrace(f"missing request parameter {e}.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"temporal select failed. missing request parameter. {e}"}, 400

        log.addtrace(f"request parameters retrieved.")

        try:
            # Initialize Earth Engine Session
            initialize(os.environ.get("GCP_PROJECT")) if not ee.data._initialized else None

        except Exception as e:
            # log and return the error
            log.addtrace(f"{e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"temporal select failed. {e}"}, 500
        
        try:
            # Generate an Earth Engine Geometry from the bounds
            geometry = spatial.generate_earthenginegeometry_frombounds(*bounds)

        except RuntimeError as e:
            # log and return the error
            log.addtrace(f"could not generate geometry from bounds. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"temporal select failed. could not generate geometry from bounds. {e}"}, 400

        log.addtrace("spatial parameters generated.")

        try:
             # Obtain the current datetime
            today = datetime.datetime.utcnow()
            # Generate a daterange going back 10 days from the current day
            daterange = temporal.generate_daterange(today, 10)

            # Create a Sentinel-2 MSI collection
            collection = ee.ImageCollection("COPERNICUS/S2_SR")
            # Filter the collection for the daterange
            collection = collection.filterBounds(geometry).filterDate(*daterange)

        except Exception as e:
            # log and return the error
            log.addtrace(f"could not filter sentinel-2 collection. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"temporal select failed. could not filter sentinel-2 collection. {e}"}, 500

        log.addtrace("filtered collection generated.")

        try:
            # Generate a list of dates from the Earth Engine Collection
            datelist = temporal.generate_earthenginecollection_datelist(collection)
            # Select the last date from the datelist as the latest date
            latest = datelist[-1]

            # Generate a list dates for the last 'count' no of acquisitions.
            # Each generation cycles shifts the day 5 days behind and adds it to the list.
            datetimes = [date := latest, *[date := temporal.shift_date(date, -5) for _ in range(count-1)]]
            # Sort the acquisition dates
            datetimes.sort()

            # Convert the acquisition dates to IS08601 strings
            timestamps = [date.isoformat() for date in datetimes]
            # log the generated values
            log.addtrace(f"acquisition dates selected. dates - {timestamps}")
            log.flush("INFO", "runtime complete")

            # Return the select response
            return {"timestamps": timestamps}, 200

        except Exception as e:
            # log and return the error
            log.addtrace(f"could not select acquisition dates. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"temporal select failed. could not select acquisition dates. {e}"}, 500


app = flask.Flask(__name__)
api = flask_restful.Api(app)

api.add_resource(Check, '/check')
api.add_resource(Select, '/select')

if __name__ == '__main__':
    # Initialize Earth Engine Session
    initialize(os.environ.get("GCP_PROJECT")) if not ee.data._initialized else None

    # Start the Flask App
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
