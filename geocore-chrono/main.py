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
            "service":self.service,
            "logging.googleapis.com/trace": flask.request.headers.get('X-Cloud-Trace-Context')
        }

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
        import json

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

    def post(self):
        """ The runtime for when the '/select' endpoint recieves a POST request """
        logger = LogEntry("select")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200


app = flask.Flask(__name__)
api = flask_restful.Api(app)

api.add_resource(Check, '/check')
api.add_resource(Select, '/select')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))