# geocore-lite

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
### /check
### /select

## Deployment
!todo