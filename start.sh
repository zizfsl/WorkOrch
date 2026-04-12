#!/bin/bash

# Start the AlloyDB Auth Proxy in the background. Note: we don't pass standard Service Account creds 
# explicitly, because Cloud Run inherently acts as the Default Compute Engine Service Account implicitly!
echo "Starting AlloyDB Auth Proxy..."
./alloydb-auth-proxy "projects/genaiproject-491818/locations/us-central1/clusters/workorch-cluster/instances/my-primary-inst" --public-ip &

echo "Starting FastAPI Application..."
python workorch/app.py
