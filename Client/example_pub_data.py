from broker_client import broker_client

brocli = broker_client()

answer = brocli.sendMsg('pub/meteo/temp/'+str( 27.5 ) )

print(answer)