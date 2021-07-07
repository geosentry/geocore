# geocore
![Banner](banner.jpg)

Serverless Microservice Containers for the GeoCore API, used internally for the core geospatial functionalities of the GeoSentry 🌍 Platform facilitated by the Terrarium package and Google Cloud Platform's Cloud Run and API Gateway services.

The repository contains the server runtimes for a handful of microservices that are packaged as Docker containers. The containers are hosted on GCP's Artifact Registry. The individual microservices are stitched together and exposed as a single endpoint using API Gateway. The OpenAPI Swagger spec is implemented in the [geosentry/cloud]() repository and deployed as part of its Terraform Manifest.

Refer to the [geosentry/eventhandlers]() repository for information about how event handlers interact with the GeoCore API. The documentation and capabilities of each microservice container is available in the respective directory.
