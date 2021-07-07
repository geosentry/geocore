"""
GeoSentry GeoCore API

Google Cloud Platform - Cloud Run

geocore-analytics service
"""
import os
import json
import flask
import flask_restful

class RunLogger:
    """ Class that builds serverless log compliant with Google Cloud Platform """

    service = "geocore-analytics"

    def __init__(self, workflow: str) -> None:
        """ Initialization Method """
        self.workflow: str = workflow
        self.logtrace: list = [f"execution started. worflow - {workflow}."]

        self.baselog = {
            "trace": self.logtrace, 
            "workflow": self.workflow, 
            "service":self.service, 
            "logging.googleapis.com/trace": flask.request.headers.get('X-Cloud-Trace-Context')
        }

    def addtrace(self, trace: str):
        """ A method that adds a trace string to the list of logtraces. """
        self.logtrace.append(trace)

    def flush(self, severity: str, message: str):
        """
        A method that creates and flushes the built log to Cloud Logging as a structured 
        log given that it is called within a Cloud Run/Functions Service. 
        The method accepts a log severity string and a log message string.

        Accepted log severity values are - EMERGENCY, ALERT, CRITICAL, ERROR, WARNING, NOTICE, INFO, DEBUG and DEFAULT.
        Refer to https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#logseverity for more information.
        """
        logentry = dict(severity=severity, message=message)
        logentry.update(self.baselog)
        print(json.dumps(logentry))

class Trend(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/trend' endpoint recieves a POST request """
        logger = RunLogger("trend")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

class Stat(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/stat' endpoint recieves a POST request """
        logger = RunLogger("stat")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

class Cloud(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/cloud' endpoint recieves a POST request """
        logger = RunLogger("cloud")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

app = flask.Flask(__name__)
api = flask_restful.Api(app)

api.add_resource(Trend, '/trend')
api.add_resource(Stat, '/stat')
api.add_resource(Cloud, '/cloud')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
