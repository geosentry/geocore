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
A **GeoCore** API function that reshapes a recieved *GeoJSON* geometry into it's square bounding box and returns its bounds, centroid and its area in sq.metres, sq.kilometres, hectares and acres. It supports ``Point``, ``Polygon`` and ``LineString`` geometries. Multi-feature GeoJSONs will not raise an error but only the first Feature will be reshaped. The different geometry types are handled as follows.

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
    },
    "centroid": {
        "longitude": <float>,
        "latitude": <float>
    }
}
```
The *bounds* field contains a list of float values that represent the west, south, east and north bound extents of the reshaped geometry.    
The *areas* field contains a mapping of string units to the area of the reshaped geometry in that unit rounded to 3 decimal places.  
The *centroid* field contains a mapping of latitude and longitude string labels to their float values.

### /meta
### /cloud

## Deployment
All tags push to the **geosentry/geocore** repository will automatically trigger a workflow to build the docker image, push it to **Artifcat Registry** and deploy it to the **Cloud Run** and register the service with **Service Directory**.  
 The GitHub Actions workflow is defined in the ``.github/workflows/push-deploy.yml`` file.

The gcloud command used to deploy the function is as follows
```bash
gcloud run deploy geocore-spatio \
--platform "managed" \
--region $REGION \
--service-account geocore@$PROJECTID.iam.gserviceaccount.com \
--concurrency 20
--timeout 60 \
--set-env-vars GCP_PROJECT=$PROJECTID GCP_REGION=$REGION \
--image $REGION-docker.pkg.dev/$PROJECTID/geocore/geocore-spatio:$TAG 
```

But, the actual workflow file uses the *google-github-actions/deploy-cloudrun* GitHub Action to handle the deployment to Cloud Run. The image build and push are handled by Docker and authenticated with the gcloud SDK.   
The Service Directory registration is handled by the gcloud command as follows
```bash
gcloud service-directory services update geocore-spatio \
--namespace geocore \
--location $REGION \
--annotations url="$SERVICEURL"
```
