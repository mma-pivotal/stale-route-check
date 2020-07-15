#!/bin/bash

source setup.sh

bosh -d $DEPLOYMENT_NAME ssh diego_cell/0 -c "source /var/vcap/jobs/cfdot/bin/setup; cfdot actual-lrps > /tmp/cfdot.json"
bosh -d $DEPLOYMENT_NAME scp diego_cell/0:/tmp/cfdot.json /tmp/cfdot.json
#download the cfdot files

for i in $(seq 1 $ROUTER_INSTANCE_NUM); do
  #as there could be multiple gorouters and each may have different routing table, we need to check them one by one
  pass=$(bosh -d $DEPLOYMENT_NAME ssh router/0 -c 'head -5 /var/vcap/jobs/gorouter/config/gorouter.yml' | grep pass | awk '{print $5}' | tr -d '\r')
  bosh -d $DEPLOYMENT_NAME ssh router/0 -c "curl router_status:$pass@localhost:8080/routes" | grep stdout | awk '{print $4}' > /tmp/routes.json
  echo "checking router/$i"
  python compare.py
  #call py script as it's much easier when doing json parsing
done
