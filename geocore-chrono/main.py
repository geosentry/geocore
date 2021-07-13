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
