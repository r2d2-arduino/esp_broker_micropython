'''
broker_main 0.2.1
'''
from _thread import start_new_thread
from broker_server import broker_server
#import gc

print("Starting..")

broser = broker_server()
sock = broser.createSocket()
newClient = broser.onNewClient

print("Broker-Server started. Waiting for clients now.")

while True:
    try:
        #gc.collect()
        conn_cl, addr_cl = sock.accept()
        #conn_cl.settimeout(3)
        
        print(">New< connection from: %s:%d" % addr_cl)
        
        start_new_thread( newClient, ( conn_cl, addr_cl ) )
    except OSError as e:
        print('Error in tread:')
        print(e)
    
sock.close()
