from broker_client import broker_client
import json

brocli = broker_client()

answer = brocli.sendMsg('ret') # get data from server

if answer != "":
    data = json.loads(answer)
    print(data)
    print(data["meteo"]["temp"][0])
    
#brocli.disconnect()