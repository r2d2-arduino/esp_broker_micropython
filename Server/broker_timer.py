'''
dart
esp broker_timer 0.1.5
'''

from utime import sleep_ms, localtime, time
import ntptime #worldtime
import urequests
from uos import stat
from json import loads
import network
from machine import RTC

#import _thread

import config

class broker_timer():
    
    def __init__(self):
        '''
        Constructor
        '''
        self.prevDay = 0
        self.prevHour = 25
        self.prevMinute = 60
        
        self.wifiActualed = 0
        self.timeActualed = 0
        self.sunrizeActualed = 0
        
        self.sunrize = ''
        self.sunset = ''
        
        self.loadTime()
        #self.loadSunrize()
        
        self.checkTimer()
              
    def saveTime(self):
        '''
        Save Time
        '''  
        if localtime()[0] > 2020:
            #stime = str( time() + (3600 * config.TIMEZONE) )
            stime = str( time() )
            try:
                f = open('/db/timer', 'w')
                f.write(stime)
                f.close()
                print('Save time:' + stime)
            except OSError as e:
                print("Error saving time")
                
            return stime
        else:
            return 0
        
    def loadTime(self):
        '''
        Load Time
        '''          
        try:
            f = open('/db/timer')
            itime = int( f.read() )
            f.close()
        except OSError as e:
            itime = 0
            
        if itime > 0:
            nt = localtime( itime )
            rtc = RTC()
            rtc.datetime( ( nt[0], nt[1], nt[2], nt[6], nt[3], nt[4], nt[5], 0 ) )
            
            print('Load time:' + str(itime) )
            print(time())
            
        return itime
        
    def saveSunrize(self):
        try:
            f = open('/db/sunrize', 'w')
            f.write(self.sunrize + "\n")
            f.write(self.sunset + "\n")
            f.close()
        except OSError as e:
            print("Error saving sunrize")
            
    def loadSunrize(self):        
        try:
            f = open('/db/sunrize')
            self.sunrize = f.readline()[:-1]
            self.sunset  = f.readline()[:-1]

            f.close()
        except OSError as e:
            print("Error loading sunrize")           
        
    def syncTime(self):
        '''
        Sync of time from www
        '''
        print("Sync time")
        ntptime.host = config.TIME_HOST

        try:
          print("Local time：%s" %str(localtime()))
          ntptime.settime()
          print("Local time after synchronization：%s" %str(localtime()))
          self.timeActualed = 1
        except OSError as e:
          print("Error syncing time:")
          print(str(e))
          self.loadTime()
          
        if localtime()[0] > 2020:
            return True
        else:
            return False
        
    def syncSunrise(self):
        '''
        Sync Sunrise
        '''
        print("Sync surize")
        request_url = 'https://api.sunrise-sunset.org/json?lat=50.4500336&lng=30.5241361&formatted=0'
        
        try:
            answer = urequests.get(url=request_url)
            jsonAnswer = loads(answer.text)
            if jsonAnswer != "":
                sunrizeStr = jsonAnswer["results"]['sunrise']
                sunsetStr  = jsonAnswer["results"]['sunset']
                
                sunrizeParts = sunrizeStr.split("T")[1].split(":")
                self.sunrize = str(int(sunrizeParts[0]) + config.TIMEZONE) + ":" + sunrizeParts[1]
                
                sunsetParts = sunsetStr.split("T")[1].split(":")
                self.sunset = str(int(sunsetParts[0]) + config.TIMEZONE) + ":" + sunsetParts[1]
                
                self.saveSunrize()
                self.sunrizeActualed = 1
                
                print("Sunrize: " + self.sunrize)
                print("Sunset: " + self.sunset)
                
                return True            
        except OSError as e:
            print("Error syncing sunrise:")
            print(str(e))
            
        return False
    
    def launchWiFi(self):
        '''
        Create connection to main Wifi
        '''        
        i = 0
        station = network.WLAN(network.STA_IF)
        try:
            if not station.isconnected():
                station.active(True)
                if config.WIFI_ADDR is not None:
                    print("Setting WiFi Address")
                    station.ifconfig(config.WIFI_ADDR)
                station.connect(config.SSID, config.PASSWORD)
            while station.status() == network.STAT_CONNECTING and i < 100:
                sleep_ms(100)
                i += 1
                
            while station.isconnected() == False and i < 100:
                pass
            
            if i < 100:
                print(station.ifconfig())
                print('Connection to main WiFi successful')
                self.wifiActualed = 1
                sleep_ms(100)
            else:
                print("Failed: connection timeout")
        except OSError as e:
            print("Error launch wifi")    
    
    def getTimeTZ(self):
        return time() + (3600 * config.TIMEZONE)

    def getCurrtime(self):
        '''
        Current time with timezone
        '''        
        return localtime( self.getTimeTZ() )
    

    def getTimeFromInt(value):
        '''
        Get time from int format
        '''        
        return localtime( value )
    

    def checkTimer(self):
        '''
        Check Sheduler for events
        '''        
        currTime = self.getCurrtime()

        day   = currTime[2]
        hour  = currTime[3]
        minute= currTime[4]
        
        if self.prevDay != day:
            self.prevDay = day
            self.everyDay()
            
        if self.prevHour != hour:
            self.prevHour = hour
            self.everyHour()
            
        if self.prevMinute != minute:
            if minute%10 == 1 or self.prevMinute == 60:
                self.every10Minute()
                
            self.prevMinute = minute
            self.everyMinute()
            
            
    def everyDay(self):
        #execute events every day
        #self.timeActualed = 0
        #self.sunrizeActualed = 0
        print('* Every Day')
        return True
        
    def everyHour(self):
        #execute events every hour
        print('* Every Hour')
        '''
        if self.timeActualed == 0 and self.wifiActualed == 1:
            self.syncTime()
            sleep_ms(10)
                
        if self.sunrizeActualed == 0 and self.timeActualed == 1 and self.wifiActualed == 1:
            self.syncSunrise()
            sleep_ms(10)
            
            if self.sunrizeActualed == 0: # second try
                self.syncSunrise()
                sleep_ms(10)
        '''
        return True

    def every10Minute(self):
        #execute events every 10 minute
        print('* Every 10 Minutes')
        if self.wifiActualed == 0:
            #_thread.start_new_thread( self.syncTime )
            self.launchWiFi()
  
        return True

    def everyMinute(self):
        #execute events every minute
        print('* Every Minute')
        self.saveTime()
        
        return True