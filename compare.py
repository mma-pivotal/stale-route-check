import json
import re
import subprocess
import os

api_endpoint = os.getenv('API_ENDPOINT')
cf_admin = os.getenv('CF_ADMIN')
cf_pass = os.getenv('CF_PASS')

#Please replace the credentials here, make sure you can cf login with the correct credentails
bashCommand= "cf login -a "+api_endpoint+" -u "+cf_admin+" -p "+cf_pass+" -o system -s system --skip-ssl-validation"
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()

gorouter = {}

#read routes from gorouter routing table
with open('/tmp/routes.json') as routes:
    data=json.load(routes)
    for host in data.keys():
        for item in data[host]:
            address = item['address']
            gorouter[address] = host
            # gorouter example : [{"192.168.1.1:8080","app1.domain.com"},xxx] , key = ip+port, value = route

with open("/tmp/cfdot.json") as cfdot:
    file_data = cfdot.read()
    file_data = re.sub(r'\n', ',', file_data )
    file_data = file_data[:-1]
    file_data = "[" + file_data + "]"
    lrp = json.loads(file_data)
    #ugly file convertion to load single line json object

count=0
#count of stale routes
stale_apps = []
#list of stale apps

for key in lrp:
    ip = key["address"]
    if not ip:
    #if an application container is crashed, it will not have an IP address
    #we only care about running containers so skip this crashed one
        continue
    port = key["ports"][0]["host_tls_proxy_port"]
    address = ip+":"+str(port)
    #address comes from LRP
    app_guid = key["process_guid"][:36]
    bashCommand = "cf curl /v2/apps/"+app_guid+"/stats"
    #cf curl /v2/apps/<guid>/stats, uri here comes from LRP
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    output_string = output.decode("utf-8")
    output_string = output_string.lower()
    if "the app could not be found" in output_string:
        if app_guid in stale_apps:
            continue
        print("Possible stale application found:",app_guid)
        print("This app is listed as actual LRP but could not be found from Cloud Controller")
        stale_apps.append(app_guid)
        continue
    else:
        app_stats=json.loads(output_string)
    app_name=app_stats["0"]["stats"]["uris"]
    #app can have multiple routes, so app_name could be a list
    if address in gorouter:
        #if we can find the lrp ip:host in gorouter's routing table
        if not gorouter[address] in app_name:
            #if gorouter's routing table doesn't match LRP's ip:host
            print("Possible Stale Route Found, Gorouter hostname:",gorouter[address],"\n Diego Cell hostname:",app_name)
            #this script doesn't work very well with multiple routes, so please manually check the app even if you see a warning
            count += 1

if count == 0:
    print("No Stale Route Found")