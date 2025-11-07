'''
Settings for sensors

name   - string - Label for sensor
unit   - string - Unit of sensor
min    - int    - Min value of scale in chart
max    - int    - Max value of scale in chart
revert - int    - 0/1, Revertion of scale 100..0
round  - int    - Round of float value 7.54
type   - string - default/switch/progress, Type of sensor

'''

paramList = {} #Temporary list of configs (Memory-cache)

"""
Get params for sensor
"""
def getParams(device, sensor):
    params = getFromList(device, sensor)
    
    defParams = {'name': sensor, 'unit': '', 'min': 0, 'max': 1, 'revert': 0, 'accuracy': 1, 'type': 'default', 'link': ''}
        
    for dparam in defParams:
        if dparam not in params or params[dparam] == "":
            params[dparam] = defParams[dparam]
        
    return params

'''
Save params to DB
'''
def insert2DB(device, sensor, params):
    f = open('/db/' + device + '.' + sensor + '.conf', 'w')
    f.write(params)
    f.close()

'''
Delete config file
'''
def deleteFromDB(device, sensor):
    import uos
    try:
        uos.remove('/db/'+device+'.'+sensor+'.conf')
    except OSError as e:
        print('No conf found')
    

'''
Get params from DB
'''
def getFromDB(device, sensor):
    params = {}
    try:
        f = open('/db/' + device + '.' + sensor + '.conf')
        dataStr = f.read()
        f.close()
        
        paramPairs = dataStr.split('&')
        
        for pair in paramPairs:
            parts = pair.split('=')
            params[parts[0]] = parts[1]
            
    except OSError as e:
        params = {'name': sensor, 'unit': '', 'min': 0, 'max': 100, 'revert': 0, 'round': 1, 'type': 'default'}
        
    return params

'''
Add params to paramList
'''
def add2List(device, sensor, params):
    if device not in paramList:
        paramList[device] = {}
        
    paramList[device][sensor] = params

'''
Delete params from paramList
'''
def removeFromList(device, sensor):
    paramList[device].pop(sensor)
    if len(paramList[device]) == 0:
        paramList.pop(device)

'''
Get params from paramList,
if not found: load from DB and add to paramList
'''
def getFromList(device, sensor):
    if device in paramList:
        if sensor in paramList[device]:
            return paramList[device][sensor]
    params = getFromDB(device, sensor)
    add2List(device, sensor, params)
    return params