#!/bin/bash

# Environment variables are required
# export BOSH_CLIENT= <uaa_bosh_client>
# export BOSH_CLIENT_SECRET= <uaa_bosh_secret>
# export BOSH_CA_CERT= <path_to_ca_cert>
# export BOSH_ENVIRONMENT= <ip_of_bosh_director>
# export APP_NAME= <app_name>
# export DEPLOYMENT_NAME= <dep_name>
# export ROUTER_INSTANCE_NUM= <number_of_gorouter>
# export API_ENDPOINT= <api.sys.DOMAIN>
# export CF_ADMIN_USERNAME= <admin>
# export CF_ADMIN_PASSWORD= <admin password>

bosh -d $DEPLOYMENT_NAME ssh diego_cell/0 -c "source /var/vcap/jobs/cfdot/bin/setup; cfdot actual-lrp-groups > /tmp/cfdot.json; chmod 666 /tmp/cfdot.json"
bosh -d $DEPLOYMENT_NAME scp diego_cell/0:/tmp/cfdot.json /tmp/cfdot.json
#download the cfdot files

for i in $(seq 1 $ROUTER_INSTANCE_NUM); do
  #as there could be multiple gorouters and each may have different routing table, we need to check them one by one
  pass=$(bosh -d $DEPLOYMENT_NAME ssh router/0 -c 'head -5 /var/vcap/jobs/gorouter/config/gorouter.yml' | grep pass | awk '{print $5}' | tr -d '\r')
  bosh -d $DEPLOYMENT_NAME ssh router/$((i-1)) -c "curl router_status:$pass@localhost:8080/routes" | grep stdout | awk '{print $4}' > /tmp/routes.json
  echo "checking router/$((i-1))"
  #call py script as it's much easier when doing json parsing
  result=$(python compare.py)
  if test "$result" != "No Stale Route Found"; then
    echo $result >> result.log
  fi
  echo $result
done

if test -e "result.log"; then
  # for Slack mention
  echo "<!here>" >> result.log
  echo "Stale Route Found."
  cat result.log
  exit 99
fi