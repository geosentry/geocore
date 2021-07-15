# geocore-vector

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
- **Cloud Datastore User** (Firestore)

## Endpoints
### /trend
### /stat
### /atmosphere
### /cloud

## Deployment
All tags push to the **geosentry/geocore** repository will automatically trigger a workflow to build the docker image, push it to **Artifcat Registry** and deploy it to the **Cloud Run** and register the service with **Service Directory**.  
 The GitHub Actions workflow is defined in the ``.github/workflows/push-deploy.yml`` file.

The gcloud command used to deploy the function is as follows
```bash
gcloud run deploy geocore-vector \
--platform "managed" \
--region $REGION \
--service-account geocore-vector@$PROJECTID.iam.gserviceaccount.com \
--concurrency 20
--timeout 60 \
--set-env-vars GCP_PROJECT=$PROJECTID GCP_REGION=$REGION MAPS_APIKEY=$MAPSAPIKEY \
--image $REGION-docker.pkg.dev/$PROJECTID/geocore/geocore-vector:$TAG 
```

But, the actual workflow file uses the *google-github-actions/deploy-cloudrun* GitHub Action to handle the deployment to Cloud Run. The image build and push are handled by Docker and authenticated with the gcloud SDK.   
The Service Directory registration is handled by the gcloud command as follows
```bash
gcloud service-directory services update geocore-vector \
--namespace geocore \
--location $REGION \
--annotations url="$SERVICEURL"
```
