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
When a HTTP request is recieved, parse the request for a GeoJSON and reshape it according to the following spec,
- If GeoJSON is a point geometry, construct a bounding circle with a 500m radius and reshape into a bounding square.
- If GeoJSON is a linestring geomerty, construct a bounding circle with the line centroid and radius based on line extent from centroid and then reshape into a bounding square.
- If GeoJSON is a polygon, construct a bounding circle and reshape into a bounding square.
- If GeoJSON is a multi-polygon or multi-linestring, simplify into a single feature and reshape.

# /meta
# /cloud

## Deployment
!todo