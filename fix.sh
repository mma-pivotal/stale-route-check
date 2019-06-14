#!/bin/bash

export BOSH_CLIENT= <uaa_bosh_client>
export BOSH_CLIENT_SECRET= <uaa_bosh_secret>
export BOSH_CA_CERT= <path_to_ca_cert>
export BOSH_ENVIRONMENT= <ip_of_bosh_director>
export APP_NAME= <app_name>
export DEPLOYMENT_NAME= <dep_name>
export ROUTER_INSTANCE_NUM= <number_of_gorouter>

bosh -d $DEPLOYMENT_NAME ssh diego_cell/0 -c "source /var/vcap/jobs/cfdot/bin/setup; cfdot actual-lrp-groups > /tmp/cfdot.json"
bosh -d $DEPLOYMENT_NAME scp diego_cell/0:/tmp/cfdot.json /tmp/cfdot.json

for i in $(seq 1 $ROUTER_INSTANCE_NUM); do
  pass=$(bosh -d $DEPLOYMENT_NAME ssh router/0 -c 'head -5 /var/vcap/jobs/gorouter/config/gorouter.yml' | grep pass | awk '{print $5}' | tr -d '\r')
  bosh -d $DEPLOYMENT_NAME ssh router/0 -c "curl router_status:$pass@localhost:8080/routes" | grep stdout | awk '{print $4}' > /tmp/routes.json
  python compare.py
done
