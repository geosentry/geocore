"""
GeoSentry GeoCore API

Google Cloud Platform - Cloud Run

geocore-raster service
"""
import os
import sys
import json
import datetime

import flask
import flask_restful

import ee
from terrarium import spatial
from terrarium import export
from terrarium import spectral


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

    service = "geocore-raster"

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

class FalseColor(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/falsecolor' endpoint recieves a POST request """
        logger = LogEntry("falsecolor")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

class TrueColor(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/truecolor' endpoint recieves a POST request """
        # Create a LogEntry object for the truecolor workflow
        log = LogEntry("truecolor")

        # Parse the request JSON
        request = flask.request.get_json()
        log.addtrace("request parsed.")

        try:
            # Retrieve the 'bounds', 'timestamp', 'prefix' and 'bucket' keys from the request
            bounds = request["bounds"]
            timestamp = request["timestamp"]
            bucket = request["bucket"]
            prefix = request["prefix"]

            # Check that bounds is a list.
            if not isinstance(bounds, list):
                # log and return the error
                log.addtrace("invalid bounds. must be a list.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"truecolor generation failed. invalid bounds. must be a list."}, 400

            # Check that timestamp is an str.
            if not isinstance(timestamp, str):
                # log and return the error
                log.addtrace("invalid timestamp. must be an str.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"truecolor generation failed. invalid timestamp. must be an str."}, 400

            # Check that bucket is an str.
            if not isinstance(bucket, str):
                # log and return the error
                log.addtrace("invalid bucket. must be an str.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"truecolor generation failed. invalid bucket. must be an str."}, 400

            # Check that prefix is an str.
            if not isinstance(prefix, str):
                # log and return the error
                log.addtrace("invalid prefix. must be an str.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"truecolor generation failed. invalid prefix. must be an str."}, 400

        except KeyError as e:
            # log and return the error
            log.addtrace(f"missing request parameter {e}.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"truecolor generation failed. missing request parameter. {e}"}, 400

        # Initialize Earth Engine Session
        init() if not ee.data._initialized else None
        
        try:
            # Generate an Earth Engine Geometry from the bounds
            geometry = spatial.generate_earthenginegeometry_frombounds(*bounds)

            # Obtain the datetime from the timestamp
            date = datetime.datetime.fromisoformat(timestamp)

        except RuntimeError as e:
            # log and return the error
            log.addtrace(f"could not generate geometry from bounds. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"truecolor generation failed. could not generate geometry from bounds. {e}"}, 400

        except Exception as e:
            # log and return the error
            log.addtrace(f"could not generate date from timestamp. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"truecolor generation failed. could not generate date from timestamp. {e}"}, 400

        try:
            # Generate the TCI image
            image = spectral.generate_spectral_image(date, geometry, "TCI")

        except Exception as e:
            # log and return the error
            log.addtrace(f"could not generate truecolor image. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"truecolor generation failed. could not generate truecolor image. {e}"}, 400

        try:
            # Append the tci asset id to the prefix
            prefix = f"{prefix}/tci"

            # Generate an Earth Engine Export Task for the image
            exporttask = export.export_image(image, bucket, prefix)
            # Start the task
            exporttask.start()

        except Exception as e:
            # log and return the error
            log.addtrace(f"could not start truecolor export. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"truecolor generation failed. could not start truecolor export. {e}"}, 400

        # log the task id
        log.addtrace(f"truecolor generated and exported. export-task - {exporttask.id}")
        log.flush("INFO", "runtime complete")

        # Initialize PubSub client
        # Compose the task creation PubSub message
        # Publish the message the the 'taskstatus' PubSub topic

        # Return the completion response
        return {"completed": True, "export-task": exporttask.id}, 200

class Spectral(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/spectral' endpoint recieves a POST request """
        # Create a LogEntry object for the spectral workflow
        log = LogEntry("spectral")

        # Parse the request JSON
        request = flask.request.get_json()
        log.addtrace("request parsed.")

        try:
            # Retrieve the 'bounds', 'timestamp', 'prefix', 
            # 'bucket' and 'index' keys from the request
            bounds = request["bounds"]
            timestamp = request["timestamp"]
            bucket = request["bucket"]
            prefix = request["prefix"]
            index = request["index"]

            # Check that bounds is a list.
            if not isinstance(bounds, list):
                # log and return the error
                log.addtrace("invalid bounds. must be a list.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"spectral generation failed. invalid bounds. must be a list."}, 400

            # Check that timestamp is an str.
            if not isinstance(timestamp, str):
                # log and return the error
                log.addtrace("invalid timestamp. must be an str.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"spectral generation failed. invalid timestamp. must be an str."}, 400

            # Check that bucket is an str.
            if not isinstance(bucket, str):
                # log and return the error
                log.addtrace("invalid bucket. must be an str.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"spectral generation failed. invalid bucket. must be an str."}, 400

            # Check that prefix is an str.
            if not isinstance(prefix, str):
                # log and return the error
                log.addtrace("invalid prefix. must be an str.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"spectral generation failed. invalid prefix. must be an str."}, 400

            # Check that index is a list.
            if not isinstance(index, str):
                # log and return the error
                log.addtrace("invalid index. must be an str.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"spectral generation failed. invalid index. must be an str."}, 400

        except KeyError as e:
            # log and return the error
            log.addtrace(f"missing request parameter {e}.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"spectral generation failed. missing request parameter. {e}"}, 400

        # Initialize Earth Engine Session
        init() if not ee.data._initialized else None

        try:
            # Generate an Earth Engine Geometry from the bounds
            geometry = spatial.generate_earthenginegeometry_frombounds(*bounds)

            # Obtain the datetime from the timestamp
            date = datetime.datetime.fromisoformat(timestamp)

        except RuntimeError as e:
            # log and return the error
            log.addtrace(f"could not generate geometry from bounds. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"spectral generation failed. could not generate geometry from bounds. {e}"}, 400

        except Exception as e:
            # log and return the error
            log.addtrace(f"could not generate date from timestamp. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"spectral generation failed. could not generate date from timestamp. {e}"}, 400

        try:
            # Generate the spectral image
            log.addtrace(f"spectral generation for {index}.")
            image = spectral.generate_spectral_image(date, geometry, index)

        except Exception as e:
            # log and return the error
            log.addtrace(f"could not generate spectral image. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"spectral generation failed. could not generate spectral image. {e}"}, 400

        try:
            # Append the tci asset id to the prefix
            prefix = f"{prefix}/{index.lower()}"

            # Generate an Earth Engine Export Task for the image
            exporttask = export.export_image(image, bucket, prefix)
            # Start the task
            exporttask.start()

        except Exception as e:
            # log and return the error
            log.addtrace(f"could not start truecolor export. {e}")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"truecolor generation failed. could not start truecolor export. {e}"}, 400

        # log the task id
        log.addtrace(f"truecolor generated and exported. export-task - {exporttask.id}")
        log.flush("INFO", "runtime complete")

        # Initialize PubSub client
        # Compose the task creation PubSub message
        # Publish the message the the 'taskstatus' PubSub topic

        # Return the completion response
        return {"completed": True, "export-task": exporttask.id}, 200

class SceneClassification(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/scl' endpoint recieves a POST request """
        logger = LogEntry("scl")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

class Altitude(flask_restful.Resource):

    def post(self):
        """ The runtime for when the '/altitude' endpoint recieves a POST request """
        logger = LogEntry("altitude")

        request = flask.request.get_json()
        logger.flush("INFO", f"{request}")

        return f"complete", 200

app = flask.Flask(__name__)
api = flask_restful.Api(app)

api.add_resource(TrueColor, '/truecolor')
api.add_resource(FalseColor, '/falsecolor')
api.add_resource(Spectral, '/spectral')
api.add_resource(Altitude, '/altitude')
api.add_resource(SceneClassification, '/scl')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
