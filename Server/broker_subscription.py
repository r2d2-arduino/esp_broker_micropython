'''
dart
esp broker_subscription 0.0.2
'''

import config
import socket
from json import dumps
import _thread
import gc

subList  = {'main': []} #Temporary list of subscribers (Memory-cache)
subFails = {} #List of fail-counters by ip
subSuccess = {} #List of success-counters by ip
subQueue = [] ##List of queue for sending
subConnCnt = 0 #Counter of active threads

def sendSubscription(brokList):
    '''
    Send new messages to subscribers
    '''
    subDevices = []
    if len(subQueue) > 0:
        updated = brokList['broker']['date'][1] + (3600 * config.TIMEZONE)
    gc.collect()
    
    while len(subQueue) > 0:
        msg = subQueue.pop()
        
        parts = msg.split('/')
        if len(parts) < 4:
            print('Less 4 parts')
            continue
        
        msgDevice  = parts[1]
        msgSensor  = parts[2]
        msgValue   = parts[3]
        
        if msgDevice not in subDevices:
            subDevices.append(msgDevice)
        
        if msgDevice in subList:
            if msgSensor in subList[msgDevice]:
                for subIp in subList[msgDevice][msgSensor]:
                    sendList = {msgSensor: msgValue, 'updated': updated }
                    _thread.start_new_thread( sendMsg, (subIp, sendList) )
       
    #send subscribe for whole device subscribers                        
    while len(subDevices) > 0:
        device = subDevices.pop()
        if device in subList:
            if 'main' in subList[device]:
                for subIp in subList[device]['main']:
                    sendList = { 'updated': updated }
                    for sensor in brokList[device]:
                        sendList[sensor] = brokList[device][sensor][0]
                    
                    _thread.start_new_thread( sendMsg, (ip, sendList) )
                         
def sendMsg(ip, sendList):
    '''
    Send message to Ip
    '''
    global subConnCnt
    print(_thread.get_ident())
    subConnCnt += 1

    sockSub = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #sockSub.settimeout(5.0) #not work
    try:
        print("Connecting to: "+ip)
        sockSub.connect((ip, config.SOCKET_PORT + 1000))
        print('Sending subscription to: '+ip)
        sockSub.sendall( dumps(sendList) )
        
        if ip not in subSuccess:
            subSuccess[ip] = 0
        subSuccess[ip] = subSuccess[ip] + 1       
    except OSError as e:
        print(e)
        
        if ip not in subFails:
            subFails[ip] = 0
        subFails[ip] = subFails[ip] + 1
    finally:
        sockSub.close()
        subConnCnt -= 1
        print('Close sub-connection, left: ' + str(subConnCnt))
    
def insert2DB(subscriber):
    '''
    Save subscriber to DB
    '''
    rows = getFromDB()
        
    f = open('/db/subscription', 'w')

    try:
        isUnique = True
        for row in rows:
            if (row != ""):
                f.write(row + "\n")
            if row == subscriber:
                isUnique = False
        if isUnique:
            f.write(subscriber + "\n")
    finally:
        f.close()

def removeFromDB(subscriber):
    '''
    Delete subscriber from DB
    '''
    rows = getFromDB()
    
    f = open('/db/subscription', 'w')
    try:
        for row in rows:
            if row != subscriber and row != "":
                f.write(row + "\n")
    finally:
        f.close()
        
def getFromDB():
    '''
    Return all subscribers from DB
    '''
    rows = []
    try:
        f = open('/db/subscription')
        dataStr = f.read()
        f.close()

        rows = dataStr.split("\n")
    except OSError as e:
        print('No subscription found')
    
    return rows

def fillListFromDB():
    '''
    Fill subList from DB
    '''
    rows = getFromDB()
    
    for msg in rows:
        if (msg != ""):
            add2List(msg)
        
def add2List(subscriber):
    '''
    Add subscriber to subList
    '''
    parts = subscriber.split('/')
    cntPart = len(parts)

    msgIp = parts[1]
            
    if cntPart > 2:
        msgDevice  = parts[2]
        if msgDevice not in subList:
            subList[msgDevice] = {} #create new place in list

    if cntPart > 3:
        msgSensor  = parts[3]
        if msgSensor not in subList[msgDevice]:
            subList[msgDevice][msgSensor] = [] #create new sensor in place
    
    #add subscriber
    if cntPart == 2:
        if msgIp not in subList['main']:
            subList['main'].append(msgIp)
            
    if cntPart == 3:
        if msgIp not in subList[msgDevice]['main']:
            subList[msgDevice]['main'].append(msgIp)

    if cntPart == 4:
        if msgIp not in subList[msgDevice][msgSensor]:
            subList[msgDevice][msgSensor].append(msgIp)

def removeFromList(ip, device, sensor):
    '''
    Delete subscriber from subList
    '''
    if device in subList:
        if sensor in subList[ device ]:
            if ip in subList[ device ][ sensor ]:
                subList[ device ][ sensor ].remove( ip )
            if len(subList[ device ][ sensor ]) == 0:
                subList[ device ].pop( sensor )
            if len(subList[ device ]) == 0:
                subList.pop( device )
