#!/bin/bash
# Complete Cloud Run deployment with all settings

gcloud run deploy sight-api \
  --image=europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/api:latest \
  --region=europe-central2 \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=2Gi \
  --cpu=1 \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=3 \
  --add-cloudsql-instances=gen-lang-client-0508446677:europe-central2:sight \
  --set-secrets="DATABASE_URL=DATABASE_URL_CLOUD:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest,NEO4J_PASSWORD=NEO4J_PASSWORD:latest,NEO4J_URI=NEO4J_URI:latest,POSTGRES_PASSWORD=POSTGRES_PASSWORD:latest,REDIS_URL=REDIS_URL:latest,SECRET_KEY=SECRET_KEY:latest" \
  --set-env-vars="NEO4J_USER=neo4j,ENVIRONMENT=production,DEBUG=False,DEFAULT_LLM_PROVIDER=google,DEFAULT_MODEL=gemini-2.5-flash,PERSONA_GENERATION_MODEL=gemini-2.5-flash,ANALYSIS_MODEL=gemini-2.5-pro,TEMPERATURE=0.7,MAX_TOKENS=8000"
