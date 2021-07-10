# geocore-spectral

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
### /spectral
### /truecolor

!todo - edit for http endpoint
1. Obtain the path to the *region* document by parsing the event dictionary from the PubSub trigger.
2. Initialize the Firestore Client and Earth Engine Session.
3. Validate that the *region* document is active for acquisitions. (not sure if this check is necessary. needs to be revisited)
4. Construct the geometry from geojson in the *region* document.
5. Check if the 'next_acquisition' field is set in the *region* document.
    - If the field is set, generate a datetime object from it.
    - Otherwise, find the latest acquisition available for the region and generate a datetime object from it.
6. Generate the acquisition image for the latest expected acquisition date and retrieve its Earth Engine Asset ID.
7. Update the *region* document's 'next_acquisition' and 'last_acquisition' fields.
8. Check the cloudiness of the acquisition. (TODO)
9. Generate the asset images based on the *region* document's subscription type.
10. Export the asset images to Cloud Storage Buckets through the Earth Engine Batch System.
11. Create the *acquisition* document with the acquisition metadata, asset export paths, etc.

## Deployment
All tags push to the **geosentry/geocore** repository will automatically trigger a workflow to build the docker image, push it to **Artifcat Registry** and deploy it to the **Cloud Run** and register the service with **Service Directory**.  
 The GitHub Actions workflow is defined in the ``.github/workflows/push-deploy.yml`` file.

The gcloud command used to deploy the function is as follows
```bash
gcloud run deploy geocore-spectral \
--platform "managed" \
--region $REGION \
--service-account geocore@$PROJECTID.iam.gserviceaccount.com \
--concurrency 20
--timeout 60 \
--set-env-vars GCP_PROJECT=$PROJECTID GCP_REGION=$REGION \
--image $REGION-docker.pkg.dev/$PROJECTID/geocore/geocore-spectral:$TAG 
```

But, the actual workflow file uses the *google-github-actions/deploy-cloudrun* GitHub Action to handle the deployment to Cloud Run. The image build and push are handled by Docker and authenticated with the gcloud SDK.   
The Service Directory registration is handled by the gcloud command as follows
```bash
gcloud service-directory services update geocore-spectral \
--namespace geocore \
--location $REGION \
--annotations url="$SERVICEURL"
```
