'''
dart
esp broker_server 0.5.4

Publish:
    pub/_device_/_sensor_/_value_ << ok/error:text
    pub/meteo/temp/28.7           << ok
    
Return:
    ret/_device_/_sensor_ << [_value_, _updated_]
    ret/meteo/temp        << [28.7, 153465331]

'''
import network
from utime import sleep_ms
import socket

import config
from broker_controller import broker_controller


class broker_server():
    '''
    Constructor
    '''
    def __init__(self):
        self.connCnt = 0 #Counter of active threads

        self.launchAP()

        self.brocont = broker_controller()

    def onNewClient(self, conn, addr):
        '''
        New client connection
        '''
        self.connCnt += 1

        try:            
            request = str(conn.recv(1024), "utf8")
            #print(">Request from " + str(addr[1]) + "> " + request)
            requestData = self.parseRequest(request)
            print(requestData)           
            
            conn.settimeout(5.0)
            conn_send = conn.send

            response = self.brocont.router(requestData['type'], requestData['path'], requestData['params'])

            if requestData['type'] == 'PLAIN':
                print(response)
                conn.sendall(response)
                
            else:
                if response['code'] == 404:
                    conn_send("HTTP/1.0 404 Not found\r\n")
                    conn_send("Content-Type: text/plain\r\n\r\n")
                    conn_send("Error: Invalid URL")             
                elif response['code'] == 303:
                    conn_send('HTTP/1.1 303 See Other\r\n')
                    conn_send('Location: /\r\n')
                elif response['code'] == 500:
                    conn_send('HTTP/1.1 500 Internal Server Error\r\n')
                    conn_send("Error: Internal Server Error")
                else:
                    conn_send('HTTP/1.1 200 OK\r\n')
                
                    if requestData['path'].endswith(".css"):
                        mimetype = 'text/css'
                    elif requestData['path'].endswith(".js"):
                        mimetype = 'text/javascript'
                    elif requestData['path'].endswith(".ico"):
                        mimetype = 'image/x-icon'                    
                    elif requestData['path'].endswith(".jpg"):
                        mimetype = 'image/jpg'
                    else:
                        mimetype = 'text/html'
                    
                    if requestData['path'].endswith(".gz.js"):
                        conn_send('Content-Encoding: gzip\r\n')
                    
                    if mimetype == 'text/html':
                        conn_send('Cache-Control: no-cache\r\n')
                    else:
                        conn_send('Cache-Control: max-age=31536000, immutable\r\n')
                    
                    if mimetype == 'image/x-icon':
                        conn_send('Content-Type: '+mimetype +'\r\n')
                    else:
                        conn_send('Content-Type: '+mimetype+'; charset=utf-8\r\n')
                    
                    conn_send('X-Content-Type-Options: nosniff\r\n')
                    conn_send('Connection: close\r\n\r\n')
                    
                    if response['body'] != '':
                        conn.sendall(response['body'])
                        
        except OSError as e:
            print("Error in " + str(addr[1]) + ":")            
            print(str(e))
        finally:
            conn.close()
            self.connCnt -= 1
            print("Close connection, left: " + str(self.connCnt))   

        self.brocont.afterAction()

    def parseRequest(self, request):
        '''
        Parse http request
        '''
        data = {'type': 'UNKNOWN', 'path': '', 'params': '', 'ip':''}
        requestRows = request.split('\r\n')
        mainRowData = requestRows[0].split(' ')
            
        if (len(mainRowData) == 1): #plain request from device
            path = mainRowData[0]
            if path.endswith('/'):
                path = path[:-1]
                
            data['type'] = 'PLAIN'
            data['path'] = path
            
        elif (len(mainRowData) == 3): #GET or POST
            secondRowData = requestRows[1].split(': ')
            data['ip'] = secondRowData[1]
            
            params = {}
            
            pathRaw = mainRowData[1]
            
            pathData = pathRaw.split('?')
            
            paramStr = ""
            if len(pathData) == 2:
                paramStr = pathData[1] 
             
            pathStr = pathData[0]
            if pathStr.endswith('/'):
                pathStr = pathStr[:-1]
                
            lastRow = requestRows[len(requestRows) - 1]

            if lastRow != '':
                if paramStr != "":
                    paramStr += "&"
                paramStr += lastRow
                    
            data['type'] = mainRowData[0]
            data['path'] = pathStr
            data['params'] = self.unquote(paramStr)
        
        return data
    
    def launchAP(self):
        '''
        Create Wifi access point
        '''
        #network.hostname("EspNet")
        ap_if = network.WLAN( network.AP_IF )
        sleep_ms(100)
        ap_if.active(True)
        sleep_ms(100)
        ap_if.config( essid=config.AP_SSID,
                      password=config.AP_PASSWORD,
                      max_clients=config.AP_MAX_CLIENTS,
                      channel=config.AP_CHANNEL,
                      hidden=False,
                      authmode=network.AUTH_WPA_WPA2_PSK )
        sleep_ms(100)
        ap_if.active(True)
        sleep_ms(100)
        print("Launch AP")
        
        print(ap_if.ifconfig())
        sleep_ms(100)

    def createSocket(self):
        '''
        Create Socket
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#for error EADDRINUSE
        sock.bind(('', config.SOCKET_PORT))
        sock.listen(config.SOCKET_MAX_CLIENTS)
        
        print("Starting server at port %d..." % config.SOCKET_PORT)
        return sock

    def unquote(self, s):
        '''
        Use for convert html-url to string
        '''
        res = s.split('%')
        for i in range(1, len(res)):
            item = res[i]
            try:
                res[i] = chr(int(item[:2], 16)) + item[2:]
            except ValueError:
                res[i] = '%' + item
        return "".join(res)  
