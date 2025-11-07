'''
dart
esp broker_view 0.2.3
'''
from utime import localtime

import broker_conf
import broker_stat


def formatTime(updated):
    '''
    Format of time
    '''
    #currTime = localtime( updated + (3600 * config.TIMEZONE) )
    currTime = localtime( updated )
    
    newTime = str(currTime[3]) + ':'
    if (currTime[4] < 10):
        newTime += '0'
    newTime += str(currTime[4]) + ':'
    if (currTime[5] < 10):
        newTime += '0'
    newTime += str(currTime[5])    

    return newTime
    

def pageMain( brokList ):
    '''
    Main Page
    '''
    #print(brokList)
    htmlTop = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>ESP-BROKER</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" type="text/css" href="/style.css" />
    <script src="/main.js"></script>
    </head><body>
    <h1>ESP-BROKER<a class="btn add" href="/add">+</a></h1>
    """

    htmlBrok = "<table><tr><th>Device</th><th>Sensor</th><th>Value</th><th>Time</th></tr>"
    for device in brokList:
        csen = len(brokList[device])

        for sensor in brokList[device]:
            value = str(brokList[device][sensor][0])
            updated = int(brokList[device][sensor][1])
            
            params = broker_conf.getParams(device, sensor)
            
            htmlBrok += "<tr>"
            
            #device column
            if csen > 0:
                if device == 'broker':
                    htmlBrok += "<td rowspan='"+str(csen)+"'>"+device+"</td>"
                else:
                    htmlBrok += "<td rowspan='"+str(csen)+"'> <a class='btn' href = '/"+device+"'>"+device+"</a></td> "
                csen = 0
            
            #sensor column
            if device == 'broker' :
                if sensor == 'date':
                    htmlBrok += "<td><a class='btn' href='/synchronize'>"+sensor+"</a></td>"
                else:
                    htmlBrok += "<td>"+sensor+"</td>"
            elif params['type'] == 'text' :
                htmlBrok += "<td>"+sensor+"</td>"
            elif params['type'] == 'photo':
                htmlBrok += "<td><a class='btn' href='"+params['link']+"'>"+sensor+"</a></td>"
            else:
                htmlBrok += "<td><a class='btn' href='/"+device+"/"+sensor+"'>"+sensor+"</a></td>"
            
            #value column
            if params['type'] == 'switch':
                checked = ''
                if value == '1':
                    checked = 'checked'    
                htmlBrok += '<td><form><label class="toggle"><input title="'+params['name']+'" id="'+device+'&'+sensor+'" onchange="chkclk(event)" value="'+value+'" '+checked+' class="toggle-checkbox" type="checkbox"><div class="toggle-switch"></div></label></form></td>'
            elif params['type'] == 'photo':
                htmlBrok += "<td>&#128444;&#128396;</td>"
            elif params['type'] == 'text':
                htmlBrok += "<td>"+value+"</td>"
            else: #default
                htmlBrok += '<td><form><input type="text" class="val" title="'+params['name']+'" id="'+device+'&'+sensor+'" onkeypress="update(event)" value="'+value+'" /></form></td>'
            
            #time column
            htmlBrok += "<td>"+formatTime(updated)+"</td></tr>"
    htmlBrok += "</table>"
    '''
    htmlSub = "<br>"
    if len(broker_subscription.subList) > 0 and broker_subscription.subList != {'main': []}:
        htmlSub += "<table><tr><th>Device</th><th>Sensor</th><th>Subscriber</th><th>Ok/Fail</th><th>Del</th></tr>"
        for device in broker_subscription.subList:
            for sensor in broker_subscription.subList[device]:
                for ip in broker_subscription.subList[device][sensor]:
                    fails = 0
                    success = 0
                    if ip in broker_subscription.subFails:
                        fails = broker_subscription.subFails[ip]
                        
                    if ip in broker_subscription.subSuccess:
                        success = broker_subscription.subSuccess[ip]

                    htmlSub += "<tr><td>"+device+"</td><td>"+sensor+"</td><td><span class='mval'>"+ip+"</span> </td><td>"+str(success)+"/"+str(fails)+"</td>"
                    htmlSub += "<td><input type='button' class='btn del-icon' onclick='unsubscribe(this)' value='x' name='"+ip+"/"+device+"/"+ sensor +"' /></td></tr>"
        htmlSub += "</table>"
    '''
    return htmlTop + htmlBrok + "</body></html>"



def pageDevice(brokList, device):
    '''
    Device Page
    '''
    htmlTop = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>'+device.upper()+'</title>'
    htmlTop += """<meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" type="text/css" href="/style.css" />
    <script src="/main.js"></script>
    </head><body>    
  </head>
  <body>
  """
    htmlBody = "<h1><a href='/'>Top</a> / "+device+"<a class='btn add' href='/add?device="+device+"'>+</a></h1>"
    for sensor in brokList[device]:
        value = 0
        if (brokList[device][sensor][0] != ''):
            if checkValue(brokList[device][sensor][0]) == 'str':
                value = 1
            else:
                value = float(brokList[device][sensor][0])

        #updated = brokList[device][sensor][1]
        params = broker_conf.getParams(device, sensor)
        #print(params)
        
        rv = ''
        if int(params['revert']):
            rv = 'revert'
            
        unit = ''
        if params['unit'] != '':
            unit = '(' + params['unit'] +')'
            
        if params['type'] == 'switch':
            checked = ''
            if value > 0:
                checked = 'checked' 
            htmlBody += '<div class="sensor switch"><form><label class="toggle big"><input id="'+device+'&'+sensor+'" onchange="chkclk(event)" value="'+str(value)+'" '+checked+' class="toggle-checkbox" type="checkbox"><div class="toggle-switch"></div></label>'
            htmlBody += '<div class="toggle-label">'+params['name']+' ' + unit
            htmlBody += '<a class="edit-icon" href="/'+device+'/'+sensor+'/edit">&#9998;</a></div></form></div>'
        elif params['type'] == 'photo':
            htmlBody += '<div class="sensor photo"><img src="'+params['link']+'" name="myCam" onload="refreshSrc(this)">'
            htmlBody += '<div class="toggle-label">'+params['name']+' ' + unit
            htmlBody += '<a class="edit-icon" href="/'+device+'/'+sensor+'/edit">&#9998;</a></div></div>'
        elif params['type'] == 'text':
            htmlBody += '<div class="sensor text"><div class="bigval bord">'+brokList[device][sensor][0]+'</div>'
            htmlBody += '<div class="toggle-label">'+params['name']+' ' + unit
            htmlBody += '<a class="edit-icon" href="/'+device+'/'+sensor+'/edit">&#9998;</a></div></div>'
        else:
            deg = (value - int(params['min']) )/( int(params['max']) - int(params['min']) )*180
            htmlBody += '<div class="sensor speedometer"><a href="/'+device+'/'+sensor+'" class="gauge-wrapper">'
            htmlBody += '<div class="gauge four"><div class="slice-colors '+ rv + '">'
            htmlBody += """
                    <div class="st slice-item"></div>
                    <div class="st slice-item"></div>
                    <div class="st slice-item"></div>
                    <div class="st slice-item"></div>
                </div>
                """
            if ( int(params['accuracy']) ):
                strValue = str(round(value, int(params['accuracy'])))
            else:
                strValue = str(round(value))   
            htmlBody += '<div class="needle" style="transform: rotate('+str(deg)+'deg);"></div>'
            htmlBody += '<div class="gauge-center"><div class="number">'+strValue+'</div></div></div></a>'
            htmlBody += '<div class="label">'+params['name']+' ' + unit +''
            htmlBody += '<a class="edit-icon" href="/'+device+'/'+sensor+'/edit">&#9998;</a></div></div>'    

        
        
    return htmlTop + htmlBody + "</body></html>"


def pageChart(device, sensor, updated, currPeriod = 'minutes'):
    '''
    Chart Page
    '''
    updatedTime = localtime( updated )
                        
    htmlTop = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>'+sensor.upper()+' : '+currPeriod.upper()+ '</title>'
    htmlTop += """<meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="/micro-graph.min.gz.js"></script>
    <link rel="stylesheet" type="text/css" href="/style.css" />
    </head><body>
    """
    params = broker_conf.getParams(device, sensor)
    
    htmlBody = "<h1><a href='/'>Top</a> / <a href='/"+device+"'>"+device+"</a> / "+sensor + "</h1><div>"
    
    stat = broker_stat.getChartDataNLabels(device, sensor, currPeriod, updatedTime)
        
    for period in ['minutes', 'hours', 'days', 'weeks', 'months']:
        if period == currPeriod:
            htmlBody += "<div class='disbtn'>" + period + "</div>"
        else:
            htmlBody += " <a class='btn' href = '/"+device+"/"+sensor+"/"+period+"'>"+period+"</a> "
    
    htmlBody += """<canvas id="chart"></canvas>
<script>
const data = {
    """
    htmlBody += ' title: "' + str(params['name'])+ '", '
    htmlBody += ' xScale: [{ suffix: "' + currPeriod[:-1] + '", labels: ' + str( stat['labels'] ) + ' }], '
    htmlBody += ' yScale: [{ suffix: "' + str(params['unit']) + '", start: '+str(params['min'])+', end: '+str(params['max'])+'}],'
    htmlBody += ' values: [ ' + str( stat['data'] ) + ' ], '
    htmlBody += ' names: ["' + sensor + '"],'
    htmlBody += """                      
    colors: ['#743ee2'],                               
    height: 300,
    gradient: [1],
}
    const chart = new MicroGraph('chart', data);
    </script>
    """
    
    return htmlTop + htmlBody + "</body></html>"


def pageEditSensor(device, sensor):
    '''
    Edit sensor page
    '''
    params = broker_conf.getParams(device, sensor)
    
    htmlTop = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Edit '+sensor.upper()+'</title>'
    htmlTop += """<meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="/main.js"></script>
    <link rel="stylesheet" type="text/css" href="/style.css" />
    </head><body>
    """
    htmlBody = "<h1><a href='/'>Top</a> / <a href='/"+device+"'>"+device+"</a> / "+sensor + "</h1><div>"    
    
    htmlBody += '<form class="edit" action="/'+device+'/'+sensor+'/edit" method="post">'
    htmlBody += '<div class="frow"><label>Type:</label>'
    htmlBody += '<input type="radio" name="type" id="type0" '+ifc(params['type']=='default', 'checked', '')+' value="default"/><label for="type0" >Default</label>'
    htmlBody += '<input type="radio" name="type" id="type1" '+ifc(params['type']=='switch', 'checked', '')+' value="switch" /><label for="type1" >Switch</label>'
    htmlBody += '<input type="radio" name="type" id="type2" '+ifc(params['type']=='photo', 'checked', '')+' value="photo" /><label for="type2" >Photo</label>'
    htmlBody += '<input type="radio" name="type" id="type3" '+ifc(params['type']=='text', 'checked', '')+' value="text" /><label for="type3" >Text</label></div>'
    
    htmlBody += '<div class="frow"><label for="name" >Name: </label>'
    htmlBody += '<input title="Name of sensor" placeholder="Label of sensor" type="text" id="name" name="name" value="'+params['name']+'" maxlength=12 /></div>'
    htmlBody += '<div class="frow"><label for="unit" >Unit: </label>'
    htmlBody += '<input title="Unit of sensor" placeholder="Unit of sensor" type="text" id="unit" name="unit" value="'+params['unit']+'" maxlength=6 /></div>'
    htmlBody += '<div class="frow"><label for="min" >Min: </label>'
    htmlBody += '<input title="Min value in chart" placeholder="Min value in chart" type="number" id="min" name="min" value="'+str(params['min'])+'" /></div>'
    htmlBody += '<div class="frow"><label for="max" >Max: </label>'
    htmlBody += '<input title="Max value in chart" placeholder="Max value in chart" type="number" id="max" name="max" value="'+str(params['max'])+'" /></div>'
    htmlBody += '<div class="frow"><label for="max" >Accuracy: </label>'
    htmlBody += '<input title="Accuracy of value" placeholder="0..4" type="number" id="accuracy" name="accuracy" value="'+str(params['accuracy'])+'" maxlength=1 min=0 max=4  /></div>'
    htmlBody += '<div class="frow"><label>Revertion:</label><input type="radio" name="revert" id="revert0" '+ifc(str(params['revert'])=='0', 'checked', '')+' value="0"/><label for="revert0" >min to Max</label>'
    htmlBody += '<input type="radio" name="revert" id="revert1" '+ifc(str(params['revert'])=='1', 'checked', '')+' value="1" /><label for="revert1" >Max to min</label></div>'

    htmlBody += '<div class="frow"><label for="link" >Link: </label>'
    htmlBody += '<input title="Link of device" placeholder="Link of device" type="text" id="link" name="link" value="'+params['link']+'" maxlength=250 /></div>'

    htmlBody += '<input class="btn del" type="button" id="' +device+'&'+sensor+ '" onclick="delSensor(this)" value="Delete" /><input class="btn save" type="submit" value="Save" /></form>'
        
    return htmlTop + htmlBody + "</body></html>"

def pageAddSensor(device = ""):
    htmlTop = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Add sensor</title>'
    htmlTop += """<meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="/main.js"></script>
    <link rel="stylesheet" type="text/css" href="/style.css" />
    </head><body>
    """
    htmlBody = "<h1><a href='/'>Top</a> / Add new sensor</h1><div>"
    
    htmlBody += '<form class="edit" action="/" method="post">'
    htmlBody += '<div class="frow"><label for="device" >Device: </label>'
    htmlBody += '<input title="Name of device" placeholder="Name of device" type="text" id="device" name="device" value="'+device+'" maxlength=12 /></div>'
    htmlBody += '<div class="frow"><label for="sensor" >Sensor: </label>'
    htmlBody += '<input title="Name of sensor" placeholder="Name of sensor" type="text" id="sensor" name="sensor" value="" maxlength=12 /></div>'
    htmlBody += '<div class="frow"><label for="value" >Value: </label>'    
    htmlBody += '<input title="Initial value" placeholder="Initial value" type="text" id="value" name="value" value="0" maxlength=6 /></div>'    
    htmlBody += '<input class="btn save" type="submit" value="Save" /></form>'
    
    return htmlTop + htmlBody + "</body></html>"


def ifc(bool, resTrue, resFalse):
    '''
    Short form of if-else
    '''
    if bool:
        return resTrue
    else:
        return resFalse
    


def checkValue(v):
    '''
    Check value
    '''
    try:
        v = float(v)
        if int(v) == v:
            return 'int'
        else:
            return 'float'
        
    except ValueError:
        return 'str'