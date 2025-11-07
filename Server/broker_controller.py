'''
dart
broker_controller 0.2.3
'''

from json import dumps
import uos
import config
import broker_view
import broker_stat
import broker_conf
from broker_timer import broker_timer

class broker_controller():
    '''
    Constructor
    '''
    def __init__(self):
        self.brokList = {} #Temporary list of last values of sensors (Memory-cache)
        
        self.checkDirs()
        self.brotime = broker_timer()
        #self.insertToBrokList('broker', 'sunrize', self.brotime.sunrize)
        #self.insertToBrokList('broker', 'sunset',  self.brotime.sunset)
        
        self.conf2brokListMigrate()
        
    
    def afterAction(self):
        self.brotime.checkTimer()

    '''
    Main router
    '''
    def router(self, reqtype, path, params):
        self.updateTime()
        
        if reqtype == 'UNKNOWN':
            return {'code': 500, 'error': 'Unknown type of header'}
        elif reqtype == 'PLAIN':
            return dumps( self.parseBrokerRequest(path) )
        else:
            return self.parseHttpRequest(path, params)

    '''
    Give message to broker
    '''
    def parseBrokerRequest(self, path):   
        part = path.split('/')
        cnt = len(part)
        
        if (cnt < 1):
            return 'error:empty'

        if (part[0] == 'pub'): #publish
            #print('pub')
            if (cnt < 4):
                return 'error:paramcnt'

            self.insertToBrokList(part[1], part[2], part[3])
            broker_stat.insert(part[1], part[2], part[3], self.brotime.getCurrtime())

            #if path not in broker_subscription.subQueue:
            #    broker_subscription.subQueue.append(path)

            return 'pub:ok'
        
        elif (part[0] == 'ret'): #return
            #print('ret')
            if (cnt == 1):
                return self.brokList
            elif (cnt == 2):
                device = part[1]
                
                if device in self.brokList:
                    return self.brokList[device] #return list of sensors in place
                
            elif (cnt == 3):
                device = part[1]
                sensor = part[2]
                
                if device in self.brokList:
                    if sensor in self.brokList[device]:
                        return self.brokList[device][sensor]
            return 'error:paramcnt'
        else:
            return 'error:type'
   
    '''
    Parse Get request
    '''
    def parseHttpRequest(self, path, paramStr = ""):
        part = path.split("/")
        cnt = len(part)
        response = {'code': 404, 'body': ''}
        params = {}
        
        if paramStr != "":
            paramPairs = paramStr.split('&')    
            for pair in paramPairs:
                one = pair.split('=')
                params[one[0]] = one[1]
        
        if cnt == 1 or part[1] == "": #main
            if ('device' in params and 'sensor' in params and 'value' in params):
                print(">>> add sensor")
                #add            
                self.insertToBrokList(params['device'], params['sensor'], params['value'])
                broker_stat.insert(params['device'], params['sensor'], params['value'], self.brotime.getCurrtime())
                
                request = "pub/"+params['device']+"/"+params['sensor']+"/"+params['value']
                #if request not in broker_subscription.subQueue:
                #   broker_subscription.subQueue.append(request)
                if 'ajax' in params:
                    response = {'code': 200, 'body': 'value added'}
                else:
                    response['code'] = 303
            else:    
                print(">>> main")
                response = {'code': 200, 'body': broker_view.pageMain(self.brokList) }
        elif part[1] == "add":        
                print(">>> Form add")
                device = ''
                if 'device' in params:
                    device = params['device']
                    
                response = {'code': 200, 'body': broker_view.pageAddSensor(device) }
        elif part[1] == "synchronize":
            self.brotime.syncTime()
            response['code'] = 303 #redirect
            
        elif part[1].endswith(".css") or part[1].endswith(".js") or part[1].endswith(".ico") or part[1].endswith(".jpg"):
            print(">>> file")
            file = open(part[1], 'rb')
            response = {'code': 200, 'body': file.read() }
            file.close()

        elif cnt == 2: #device page
            print(">>> device")

            if part[1] in self.brokList:
                response = {'code': 200, 'body': broker_view.pageDevice(self.brokList, part[1]) }
            else:
                print(part[1])
                #print(self.brokList)
        elif cnt == 3: #sensor chart page
            print(">>> chart")
            period = 'minutes'
            if part[1] in self.brokList:
                if part[2] in self.brokList[ part[1] ]:
                    updated = int(self.brokList[ part[1] ][ part[2] ][1])
                    response = {'code': 200, 'body': broker_view.pageChart(part[1], part[2], updated, period) }
        elif cnt == 4:
            if part[3] == 'edit': #form edit sensor
                if len(params) > 0:
                    print(">>> Save settings of sensor")
                    broker_conf.insert2DB(part[1], part[2], paramStr)
                    broker_conf.removeFromList(part[1], part[2]) # remove from cache
                    response['code'] = 303
                else:
                    print(">>> Form edit settings of sensor")
                    response = {'code': 200, 'body': broker_view.pageEditSensor(part[1], part[2]) }
                
            elif part[3] == 'delete': #delete sensor
                print(">>> delete")
                if part[1] in self.brokList:
                    if part[2] in self.brokList[ part[1] ]:
                        self.brokList[ part[1] ].pop( part[2] )
                        if len(self.brokList[ part[1] ]) == 0:
                            self.brokList.pop( part[1] )
                        
                        broker_conf.deleteFromDB(part[1], part[2])
                        
                        response['code'] = 303
                    
            elif part[3] in broker_stat.periods:
                print(">>> chart")
                if part[1] in self.brokList:
                    if part[2] in self.brokList[ part[1] ]:
                        updated = int(self.brokList[ part[1] ][ part[2] ][1])
                        response = {'code': 200, 'body': broker_view.pageChart(part[1], part[2], updated, part[3]) }      
            
        return response

    '''
    Insert data to Broker List
    '''
    def insertToBrokList(self, device, sensor, value = ''):
        if device not in self.brokList:
            self.brokList[device] = {} #create new place in list
            
        if sensor not in self.brokList[device]:    
            self.brokList[device][sensor] = [None, 0] 

        self.brokList[device][sensor] = [value, self.brotime.getTimeTZ()]

    '''
    Update broker data
    '''
    def updateTime(self):
        currTime = self.brotime.getCurrtime()
        
        date = ''
        if (currTime[2] < 10):
            date += '0'        
        date += str(currTime[2]) + '.'
        if (currTime[1] < 10):
            date += '0'
        date += str(currTime[1])+'.'+str(currTime[0])+'.'+str( int(currTime[6]) + 1)

        self.insertToBrokList('broker', 'date', date)

    '''
    Load subList to brokList for interaction
    '''
    def subList2brokListMigrate(self):
        for sdev in broker_subscription.subList:
            for ssen in broker_subscription.subList[sdev]:
                if ssen != 'main':
                    self.insertToBrokList(sdev, ssen)
           
    '''
    Check existing of required dirs
    '''
    def checkDirs(self):
        try:
            uos.stat("/db/")
        except OSError as e:
            uos.mkdir("db")
            
        try:
            uos.stat("/backup/")
        except OSError as e:
            uos.mkdir("backup")
            
    '''
    Migrate config to brokList
    '''
    def conf2brokListMigrate(self):
        dblist = uos.listdir("/db/")
        for dbname in dblist:
            if dbname.endswith(".conf"):
                part = dbname.split('.')
                self.insertToBrokList(part[0], part[1])
        
        