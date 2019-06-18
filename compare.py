import os
import json
import re
import subprocess

bashCommand= "cf login -a "+os.environ['API_ENDPOINT']+" -u "+os.environ['CF_ADMIN_USERNAME']+" -p "+os.environ['CF_ADMIN_PASSWORD']+" -o system -s system --skip-ssl-validation"
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

for key in lrp:
    ip = key["instance"]["address"]
    port = key["instance"]["ports"][0]["host_tls_proxy_port"]
    address = ip+":"+str(port)
    #address comes from LRP
    app_guid = key["instance"]["process_guid"][:36]
    bashCommand = "cf curl /v2/apps/"+app_guid+"/stats"
    #cf curl /v2/apps/<guid>/stats, uri here comes from LRP
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    output_string = output.decode("utf-8")
    app_stats=json.loads(output_string)
    app_name=app_stats["0"]["stats"]["uris"]
    #app can have multiple routes, so app_name could be a list
    if address in gorouter:
        #if we can find the lrp ip:host in gorouter's routing table
        if not gorouter[address] in app_name:
            #if gorouter's routing table doesn't match LRP's ip:host
            print("Possible Stale Route Found, Gorouter gorouter hostname:",gorouter[address],"\n Diego Cell gorouter hostname:",app_name)
            #this script doesn't work very well with multiple routes, so please manually check the app even if you see a warning
            count += 1

if count == 0:
    # print("No Stale Route Found")
    print("")
