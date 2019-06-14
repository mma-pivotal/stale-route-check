import json
import re
import subprocess

bashCommand= "cf login -a api.run-13.haas-59.pez.pivotal.io -u admin -p M0SkMbsI0cpNJgEX7djis_75fYFdP7mg -o system -s system --skip-ssl-validation"
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

app = {}

with open('/tmp/routes.json') as routes:
    data=json.load(routes)
    for host in data.keys():
        for item in data[host]:
            address = item['address']
            app[address] = host

with open("/tmp/cfdot.json") as cfdot:
    file_data = cfdot.read()
    file_data = re.sub(r'\n', ',', file_data )
    file_data = file_data[:-1]
    file_data = "[" + file_data + "]"
    lrp = json.loads(file_data)

cfdot_host={}

for key in lrp:
    ip = key["instance"]["address"]
    port = key["instance"]["ports"][0]["host_tls_proxy_port"]
    app_guid = key["instance"]["process_guid"][:36]
    print(app_guid)
    address = ip+":"+str(port)
    if address in app:
        if address in cfdot_host:
            if cfdot_host[address] != app[address]:
                print("Stale Route Found :",address,app[address],cfdot_host[address])
                continue
        cfdot_host[address] = app[address]
