"""
GeoSentry GeoCore API

Google Cloud Platform - Cloud Run

geocore-spatio service
"""
import os
import flask
import flask_restful

class LogEntry:
    """ A class that represents a serverless log compliant with Google Cloud Platform. """

    service = "geocore-spatio"

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
        import json

        self.addtrace("execution ended.")
        logentry = dict(severity=severity, message=message)
        logentry.update(self.baselog)

        print(json.dumps(logentry))

class Geocode(flask_restful.Resource):
    """ RESTful resource for the '/geocode' endpoint. """

    def post(self):
        """ RESTful POST """
        # Create a LogEntry object for the geocode workflow
        log = LogEntry("geocode")

        # Parse the request JSON
        request = flask.request.get_json()
        log.addtrace("request parsed.")

        # Retrieve the 'coordinates' key from the request
        coordinates = request.get("coordinates")
        # Check that coordinates is a dictionary.
        if not isinstance(coordinates, dict):
            # log and return the error
            log.addtrace("could not retrieve coordinates.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"geocode failed. could not retrieve coordinates. not a dictionary"}, 400

        log.addtrace("coordinate retrieved.")

        # Check if coordinates contains a longitude key
        if "longitude" not in coordinates.keys():
            # log and return the error
            log.addtrace("missing longitude.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"reshape failed. coordinates missing longitude."}, 400

        # Check if coordinates contains a latitude key
        if "latitude" not in coordinates.keys():
            # log and return the error
            log.addtrace("missing latitude.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"reshape failed. coordinates missing latitude."}, 400

        try:
            from terrarium import spatial

            # Genertae the geocode location for the coordinates
            geocode = spatial.generate_location(**coordinates)
            # log the generated values
            log.addtrace(f"geocode location generated. location - {geocode}")
            log.flush("INFO", "runtime complete")

            # Return the geocode response
            return {"geocode": geocode}, 200

        except Exception as e:
            # log and return the error
            log.addtrace("could not generate gecode location.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"reshape failed. could not generate geocode location. {e}"}, 500

class Reshape(flask_restful.Resource):
    """ RESTful resource for the '/reshape' endpoint. """

    def post(self):
        """ RESTful POST """
        # Create a LogEntry object for the reshape workflow
        log = LogEntry("reshape")

        # Parse the request JSON
        request = flask.request.get_json()
        log.addtrace("request parsed.")

        # Retrieve the 'geojson' key from the request
        geojson = request.get("geojson")
        # Check that geojson is a dictionary.
        if not isinstance(geojson, dict):
            # log and return the error
            log.addtrace("could not retrieve geojson.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"reshape failed. could not retrieve geojson. not a dictionary"}, 400

        log.addtrace("geojson retrieved.")

        try:
            import json
            from terrarium import spatial

            # Generate a shape geometry from the geojson 
            shape = spatial.generate_shape_fromgeojson(json.dumps(geojson))
            log.addtrace("shape geometry generated.")

        except RuntimeError as e:
            # log and return the error
            log.addtrace("could not generate shape geometry.")
            log.flush("ERROR", "runtime terminated")
            return {"error": f"reshape failed. could not generate shape geometry. {e}"}, 400

        try:
            # Check the type of the shape geometry and 
            # call the appropriate reshape runtime

            if shape.type == "Polygon":
                log.addtrace("polygon geometry detected.")
                reshaped = spatial.reshape_polygon(shape)

            elif shape.type == "Point":
                log.addtrace("point geometry detected.")
                reshaped = spatial.reshape_point(shape)

            elif shape.type == "LineString":
                log.addtrace("linestring geometry detected.")
                reshaped = spatial.reshape_linestring(shape)

            else:
                log.addtrace("invalid geometry detected.")
                log.flush("ERROR", "runtime terminated")
                return {"error": f"reshape failed. unsupported geometry type: {shape.type}"}, 400

            log.addtrace("geometry reshaped.")

        except RuntimeError as e:
            # log and return the error
            log.addtrace("could not reshape geometry.")
            log.flush("ERROR", "runtime error")
            return {"error": f"reshape failed. could not reshape geometry. {e}"}, 500

        try:
            # Retrieve the bounds of the reshaped geometry
            bounds = list(reshaped.bounds)
            # Generate the areas of the reshaped geometry
            areas = spatial.generate_area(reshaped)
            # Generate the centroid of the reshaped geometry
            centroid = spatial.generate_centroid(reshaped)

            # Isolate the square metres area value
            sqm = areas["SQM"]
            # log the generated values
            log.addtrace(f"reshape data. bounds - {bounds}. area - {sqm}. centroid - {centroid}.")
            log.flush("INFO", "runtime complete")
            
            # Return the reshape response
            return {
                "bounds": bounds, 
                "areas": areas,
                "centroid": centroid
            }, 200
        
        except RuntimeError as e:
            # log and return the error
            log.addtrace("could not generate reshaped data.")
            log.flush("ERROR", "runtime error")
            return {"error": f"reshape failed. could not generate reshaped data. {e}"}, 500


app = flask.Flask(__name__)
api = flask_restful.Api(app)

api.add_resource(Geocode, '/geocode')
api.add_resource(Reshape, '/reshape')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
