#!/bin/bash
set -e

sleep 2

#export PYTHONPATH=/opt/blog/backend
alembic upgrade head

#Disabled opentelemetry-instrument with opentelemetry-instrumentation-sqlalchemy brake DefaultTraceProvider
 #if [ $OTELE_TRACE = "True" ]
 #then
     #echo "Running with OpenTelemetry"
   # opentelemetry-instrument uvicorn manage:app --host=127.0.0.1 --port 9000 --reload $(test ${ENVIRONMENT} = "development" && echo "--reload")
 #else
  #  echo "OpenTelemetry isn't enable"
# uvicorn app.main:app --host=0.0.0.0 $(test ${ENVIRONMENT} = "development" && echo "--reload")
# fi


OTEL_RESOURCE_ATTRIBUTES=service.name=JobBoard \
OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317" \
opentelemetry-instrument uvicorn manage:app --host localhost --port 9000 