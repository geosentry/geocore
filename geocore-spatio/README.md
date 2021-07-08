# geocore-spatio

## Runtime
Platform: **Google Cloud Platform**  
Environment: **Cloud Run**  

Runtime: **Python 3.9** (python:3.9-slim)  
Containerization: **Docker**  
Repository: **Artifact Registry**

WSGI Server: **gUnicorn**  
API Framework: **Flask-RESTful**  

## Service Account Permissions
Default Application Credentials
- **Secret Manager Secret Accessor** (Secret Manager)  

Earth Engine Credentials (Stored on Secret Manager)
- **Earth Engine** (Registered as an Earth Engine SA)
- **Storage Object Admin** (Cloud Storage)

## Endpoints

### /reshape
A **GeoCore** API function that reshapes a recieved *GeoJSON* geometry into it's square bounding box and returns its bounds and its area in sq.metres, sq.kilometres, hectares and acres.
It supports ``Point``, ``Polygon`` and ``LineString`` geometries. Multi-feature GeoJSONs will not raise an error but only the first Feature will be reshaped. The different geometry types are handled as follows.

``Point`` - Creates a square buffer of 2.5kms around the point.  
``Polygon`` & ``LineString`` - Creates a square bound around the geometry.

#### Request Format
```json
{
    "geojson": <dict>
}
```
The *geojson* field must be a dictionary and contain the full contents of an RFC7946 compliant GeoJSON. Use geojson.io to generate these dictionaries.

#### Response Format
```json
{
    "bounds": [<float>, <float>, <float>, <float>],
    "areas": {
        "SQM": <float>,
        "SQKM": <float>,
        "HA": <float>,
        "ACRE": <float>
    }
}
```
The *bounds* field contains a list of float values that represent the west, south, east and north bound extents of the reshaped geometry.  
The *areas* field contains a mapping of string units to the area of the reshaped geometry in that unit rounded to 3 decimal places.

### /meta
### /cloud

## Deployment
!todo