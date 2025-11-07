#v 0.4.1
import network
import config
from utime import sleep_ms
import socket

class broker_client:
    '''
    Constructor
    '''
    def __init__(self):
        self.currentIP = ''
        self.serverIP  = ''
        self.station = network.WLAN(network.STA_IF)

    '''
    Connect to server WiFi
    '''
    def connect(self):
        if not self.station.isconnected():
            print('Connecting to network...')
            if self.station.active() == False:
                self.station.active(True)

            self.station.connect(config.AP_SSID, config.AP_PASSWORD)

            while self.station.status() == network.STAT_IDLE: #1000
                sleep_ms(100)
                
            while self.station.status() == network.STAT_CONNECTING: #1001
                sleep_ms(100)

            status = self.station.status()
            if status == network.STAT_GOT_IP: #1010
                print('Network config:', self.station.ifconfig())
            else:    
                if status == network.STAT_WRONG_PASSWORD: #202
                    status = "WRONG PASSWORD"
                elif status == network.STAT_NO_AP_FOUND: #201
                    status = "NETWORK '%s' NOT FOUND" % config.AP_SSID
                elif status == network.STAT_BEACON_TIMEOUT: #200
                    status = "WIFI BEACON TIMEOUT"
                elif status == network.STAT_ASSOC_FAIL: #203
                    status = "WIFI ASSOC FAIL"                    
                elif status == network.STAT_HANDSHAKE_TIMEOUT: #204
                    status = "WIFI HANDSHAKE TIMEOUT"                   
                elif status == network.STAT_IDLE: #1000
                    status = "NO CONNECTION TO '%s'" % config.AP_SSID
                else:
                    status = "Status code %d" % status
                print("Connection failed: %s!" % status)
                return False
        else:
            print('Already connected:', self.station.ifconfig())
            
        self.currentIP = self.station.ifconfig()[0]
        self.serverIP  = self.station.ifconfig()[3]
        
        return True
    
    '''
    Disable server
    '''
    def disconnect(self):
        self.station.active(False)

    '''
    Get socket
    '''
    def getSocket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.serverIP, config.SOCKET_PORT))
        except OSError as e:
            sock.close()
            print('Failed connect')
            print(e)
            return None
        
        return sock  

    '''
    Send message to server
    ''' 
    def sendMsg(self, msg, buff = 1024):
        sock = None
        while True:
            if self.connect():
                sock = self.getSocket()
                if sock == None:
                    print('Trying reconnect')
                    self.disconnect()
                    sleep_ms(10000)
                else:
                    break
            else:
                print('Trying connecting again')
                self.disconnect()
                sleep_ms(10000)
            
        answer = ''
        sock.settimeout(5)
        try:
            sock.send(msg)
            answer = sock.recv(buff).decode()
        except OSError as e:
            print(e)            
        finally:
            sock.close()
        
        return answer
