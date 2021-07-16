# geocore-raster

## Runtime
Platform: **Google Cloud Platform**  
Environment: **Cloud Run**  

Runtime: **Python 3.9** (python:3.9-slim)  
Containerization: **Docker**  
Repository: **Artifact Registry**

WSGI Server: **gUnicorn**  
API Framework: **Flask-RESTful**  

## Service Account Permissions
- **Earth Engine** (Registered as an Earth Engine SA)
- **Earth Engine Resource Admin** (Earth Engine)
- **Storage Object Admin** (Cloud Storage)

## Endpoints
### /spectral
A **GeoCore** API function that generates a spectral image and exports it

#### Request Format
```json
{
    "bounds": [<float>, <float>, <float>, <float>],
    "timestamp": <isostr>,
    "prefix": <str>,
    "bucket": <str>,
    "index": <str>
}
```
The *bounds* field must be a list of float values that represent the west, south, east and north bound extents of the region.     
The *timestamp* field must be an ISO8601 string that represents the timestamp around which to check for an acquisition.    
The *prefix* field must be string and represents the filename prefix for the generated asset. The index is the appended to this prefix to form the full asset name.   
The *bucket* field must be a string that represents the bucket the asset is exported to.  
The *index* field must be a string that represent the spectral index to generate. Current supported values are TCI and NDVI.

#### Response Format
```json
{
    "completed": <bool>,
    "export-task" <str>,
}
```
The *completed* field is a boolean that represents if the image was generated and the export was succesfully.   
The *export-task* field is a string that represents the task ID of the export task.
(status of the export task can be queried with geocore-chrono's /taskstatus endpoint)

### /truecolor
A **GeoCore** API function that generates a true color image and exports it

#### Request Format
```json
{
    "bounds": [<float>, <float>, <float>, <float>],
    "timestamp": <isostr>,
    "prefix": <str>,
    "bucket": <str>
}
```
The *bounds* field must be a list of float values that represent the west, south, east and north bound extents of the region.     
The *timestamp* field must be an ISO8601 string that represents the timestamp around which to check for an acquisition.    
The *prefix* field must be string and represents the filename prefix for the generated asset. 'tci' is the appended to this prefix to form the full asset name.   
The *bucket* field must be a string that represents the bucket the asset is exported to. 

#### Response Format
```json
{
    "completed": <bool>,
    "export-task" <str>,
}
```
The *completed* field is a boolean that represents if the image was generated and the export was succesfully.   
The *export-task* field is a string that represents the task ID of the export task.
(status of the export task can be queried with geocore-chrono's /taskstatus endpoint)

### /falsecolor
### /scl
### /altitude

## Deployment
All tags push to the **geosentry/geocore** repository will automatically trigger a workflow to build the docker image, push it to **Artifcat Registry** and deploy it to the **Cloud Run** and register the service with **Service Directory**.  
 The GitHub Actions workflow is defined in the ``.github/workflows/push-deploy.yml`` file.

The gcloud command used to deploy the function is as follows
```bash
gcloud run deploy geocore-raster \
--platform "managed" \
--region $REGION \
--service-account geocore-raster@$PROJECTID.iam.gserviceaccount.com \
--concurrency 20
--timeout 60 \
--set-env-vars GCP_PROJECT=$PROJECTID GCP_REGION=$REGION MAPS_APIKEY=$MAPSAPIKEY \
--image $REGION-docker.pkg.dev/$PROJECTID/geocore/geocore-raster:$TAG 
```

But, the actual workflow file uses the *google-github-actions/deploy-cloudrun* GitHub Action to handle the deployment to Cloud Run. The image build and push are handled by Docker and authenticated with the gcloud SDK.   
The Service Directory registration is handled by the gcloud command as follows
```bash
gcloud service-directory services update geocore-raster \
--namespace geocore \
--location $REGION \
--annotations url="$SERVICEURL"
```
