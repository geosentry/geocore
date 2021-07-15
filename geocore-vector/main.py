"""
GeoSentry GeoCore API

Google Cloud Platform - Cloud Run

geocore-vector service
"""
import os
import sys
import json

import flask
import flask_restful

import ee

def init():
    """ 
    A function that generates Earth Engine Credentials from the default application 
    credentials and authenticates an Earth Engine Session with Terrarium. 
    """
    try:
        from terrarium import initialize

        # Retrieve the location of the credentials file from the environment variables set by Google Cloud Platform
        keyfile = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        # Generate a new Earth Engine credential object
        credentials = ee.ServiceAccountCredentials(email=None, key_file=keyfile)

        # Initialize Earth Engine Session
        initialize(credentials)

    except Exception as e:
        logentry = dict(severity="EMERGENCY", message=f"could not intialize earth engine session. error: {e}")
        print(json.dumps(logentry))
        sys.exit(0)

class LogEntry:
    """ A class that represents a serverless log compliant with Google Cloud Platform. """

    service = "geocore-vector"

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

class Trend(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/trend' endpoint recieves a POST request """
        logger = LogEntry("trend")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

class Stat(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/stat' endpoint recieves a POST request """
        logger = LogEntry("stat")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

class Atmosphere(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/atmosphere' endpoint recieves a POST request """
        logger = LogEntry("atmosphere")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

class Cloud(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/cloud' endpoint recieves a POST request """
        logger = LogEntry("cloud")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

app = flask.Flask(__name__)
api = flask_restful.Api(app)

api.add_resource(Trend, '/trend')
api.add_resource(Stat, '/stat')
api.add_resource(Atmosphere, '/atmosphere')
api.add_resource(Cloud, '/cloud')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
