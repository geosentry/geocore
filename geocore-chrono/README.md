# geocore-chrono

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
### /check
A **GeoCore** API function that checks if an acquisition exists in a 12 hour buffer around a given timestamp for a given region. Expects bounding coordinates for the region and the timestamp as an ISO8601 timestamp.

#### Request Format
```json
{
    "bounds": [<float>, <float>, <float>, <float>],
    "timestamp": <isostr>
}
```
The *bounds* field must be a list of float values that represent the west, south, east and north bound extents of the region.  
The *timestamp* field must be an ISO8601 string that represents the timestamp around which to check for an acquisition. 

#### Response Format
```json
{
    "check": <bool>
}
```
The *check* field is a boolean that represents if an acquisition exists for a region within a 12 hour buffer around the *timestamp* in the request.

### /select
A **GeoCore** API function that selects a certain number of acquisition dates for a region. Expects bounding coordinates for the region and the number of acquisition dates to select.

#### Request Format
```json
{
    "bounds": [<float>, <float>, <float>, <float>],
    "count": <int>
}
```
The *bounds* field must be a list of float values that represent the west, south, east and north bound extents of the region.  
The *count* field must be an int that represents the number of acquisition dates to select. 

#### Response Format
```json
{
    "timestamps": <list><isostr>
}
```
The *timestamps* field contains a list of ISO8601 timestamps that represent the acquisition dates for the region. The number of timestamps is determined by the *count* value in the request.

## Deployment
All tags push to the **geosentry/geocore** repository will automatically trigger a workflow to build the docker image, push it to **Artifcat Registry** and deploy it to the **Cloud Run** and register the service with **Service Directory**.  
 The GitHub Actions workflow is defined in the ``.github/workflows/push-deploy.yml`` file.

The gcloud command used to deploy the function is as follows
```bash
gcloud run deploy geocore-chrono \
--platform "managed" \
--region $REGION \
--service-account geocore@$PROJECTID.iam.gserviceaccount.com \
--concurrency 20
--timeout 60 \
--set-env-vars GCP_PROJECT=$PROJECTID GCP_REGION=$REGION MAPS_GEOCODING_APIKEY=$MAPSAPIKEY \
--image $REGION-docker.pkg.dev/$PROJECTID/geocore/geocore-chrono:$TAG 
```

But, the actual workflow file uses the *google-github-actions/deploy-cloudrun* GitHub Action to handle the deployment to Cloud Run. The image build and push are handled by Docker and authenticated with the gcloud SDK.   
The Service Directory registration is handled by the gcloud command as follows
```bash
gcloud service-directory services update geocore-chrono \
--namespace geocore \
--location $REGION \
--annotations url="$SERVICEURL"
```
