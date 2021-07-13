"""
GeoSentry GeoCore API

Google Cloud Platform - Cloud Run

geocore-chrono service
"""
import os
import json
import flask
import flask_restful

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

    def post(self):
        """ The runtime for when the '/check' endpoint recieves a POST request """
        logger = LogEntry("check")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

class Select(flask_restful.Resource):
    """ RESTful resource for the '/select' endpoint. """

    def post(self):
        """ RESTful POST """
        # Create a LogEntry object for the select workflow
        log = LogEntry("select")

        # Parse the request JSON
        request = flask.request.get_json()
        log.addtrace("request parsed.")

        # Retrieve the 'bounds' and 'count' keys from the request
        bounds = request.get("bounds")
        count = request.get("count")

        # Check that bounds is a list.
        if not isinstance(bounds, list):
            # log and return the error
            log.addtrace("could not retrieve bounds.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"select failed. could not retrieve bounds. not a list"}, 400

        # Check that count is a dictionary.
        if not isinstance(count, int):
            # log and return the error
            log.addtrace("could not retrieve count.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"select failed. could not retrieve count. not an int"}, 400

        log.addtrace("bounds and count retrieved.")

        try:
            from terrarium import spatial
            # Generate an Earth Engine Geometry from the bounds
            geometry = spatial.generate_earthenginegeometry_frombounds(*bounds)

        except Exception as e:
            # log and return the error
            log.addtrace("could not generate geometry from bounds.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"select failed. could not generate geometry from bounds. {e}"}, 400

        log.addtrace("geometry generated.")

        try:
            import ee
            import datetime
            from terrarium import temporal

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
            log.addtrace("could not filter sentinel-2 collection.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"select failed. could not filter sentinel-2 collection. {e}"}, 500

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
            log.addtrace("could not select acquisition dates.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"select failed. could not select acquisition dates. {e}"}, 500


app = flask.Flask(__name__)
api = flask_restful.Api(app)

api.add_resource(Check, '/check')
api.add_resource(Select, '/select')

if __name__ == '__main__':

    try:
        import google.cloud.secretmanager as secretmanager
        # Create a Secret Manager Client
        secrets = secretmanager.SecretManagerServiceClient()

        # Retrieve the Project ID from the environment
        project = os.environ["GCP_PROJECT"]

        # Construct the name of the secret
        secret_name = f"projects/{project}/secrets/earthengineone/versions/latest"
        secret_data = secrets.access_secret_version(name=secret_name)
        credentials = secret_data.payload.data

    except KeyError as e:
        logentry = dict(severity="EMERGENCY", message=f"could not obtain earth engine credentials. error: {e} environment variable not set")
        print(json.dumps(logentry))
        os.exit(0)

    except Exception as e:
        logentry = dict(severity="EMERGENCY", message=f"could not obtain earth engine credentials. error: {e}")
        print(json.dumps(logentry))
        os.exit(0)

    try:
        from terrarium import initialize
        # Initialize Earth Engine Session
        initialize(credentials)

    except Exception as e:
        logentry = dict(severity="EMERGENCY", message=f"could not initialize earth engine session. error: {e}")
        print(json.dumps(logentry))
        os.exit(0)

    # Start the Flask App
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
