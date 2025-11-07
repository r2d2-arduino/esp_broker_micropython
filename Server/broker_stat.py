'''
dart
esp broker_stat 0.2.1
'''
periods = {'updated': 0, 'minutes': 1, 'hours': 2, 'days': 3, 'weeks': 4, 'months': 5 }


def getChartDataNLabels( device, sensor, currPeriod, currTime ):
    '''
    Main function for chart data
    '''
    months = ['?', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    data = find(device, sensor, currPeriod)
    shiftedPeriod = getShiftedPeriod(currPeriod, currTime)

    shiftedData = []
    shiftedLabels = []

    for pi in shiftedPeriod:
        if (data[pi] != '-'):
            shiftedData.append( data[pi] )
            if currPeriod == 'months':
                shiftedLabels.append( months[pi] )
            else:
                shiftedLabels.append( pi )
    
    return {'data': shiftedData, 'labels': shiftedLabels}



def find( device, sensor, period ):
    '''
    Find data in DB by period
    '''
    try:
        f = open('/db/' + device + '.' + sensor + '.stat')
        for i in range( 0, periods[period] + 1 ):
            dataStr = f.readline()[:-1]
        f.close()

        items = dataStr.split(';')
    except OSError as e:
        print(e)
        items = getDefaultData(period)
    
    return items


def insert( device, sensor, value, currTime ):
    '''
    Insert data to DB
    '''
    if checkValue(value) == 'str':
        return False
        
    year  = currTime[0]
    month = currTime[1]
    day   = currTime[2]
    hour  = currTime[3]
    minute= currTime[4]
    wday  = currTime[6]
    week  = getCurrWeek( currTime[6], currTime[7] )
        
    try:
        f = open('/db/' + device + '.' + sensor + '.stat')
        dataStr = f.read()
        f.close()

        rows = dataStr.split("\n")
        updated = rows[ 0 ].split(';')
        minutes = rows[ periods['minutes'] ].split(';')
        hours   = rows[ periods['hours'] ].split(';')
        days    = rows[ periods['days'] ].split(';')
        weeks   = rows[ periods['weeks'] ].split(';')
        months  = rows[ periods['months'] ].split(';')

    except OSError as e:
        print('No file, creating new')
        updated = [str(year), str(month), str(day), str(hour), str(minute), str(week)]
        minutes = getDefaultData('minutes')
        hours   = getDefaultData('hours')
        days    = getDefaultData('days')
        weeks   = getDefaultData('weeks')
        months  = getDefaultData('months')

    minutes[minute] = str( value )
    hours[hour]     = str( avgValue(hours[hour], value) )
    days[day]       = str( avgValue(days[day], value) )
    weeks[week]     = str( avgValue(weeks[week], value) )
    months[month]   = str( avgValue(months[month], value) )
    
    #New minute - clear passed minutes
    oldMinute = int(updated[4])
    if ( minute != oldMinute ):
        if (minute > oldMinute):
            for mi in range(oldMinute + 1, minute):
                minutes[mi] = '-'
        if (minute < oldMinute):
            for mi in range(oldMinute + 1, 60):
                minutes[mi] = '-'
            for mi in range(0, minute):
                minutes[mi] = '-'
    
    #New hour - calculate average value
    if ( hour != int(updated[3]) ):
        print('!Hour recalc')
        minSum = 0
        minCnt = 60
        for min in minutes:
            if (min == '-'):
                minCnt -= 1
            else:
                minSum += float(min)
        
        if (minCnt > 0):
            hours[ prevHour(hour) ] = str( round( minSum / minCnt, 2) )
        else:
            hours[ prevHour(hour) ] = '-'
            
    #New day - calculate average value
    if ( day != int(updated[2]) ):
        print('!Day recalc')
        hourSum = 0
        hourCnt = 24
        for hr in hours:
            if (hr == '-'):
                hourCnt -= 1
            else:
                hourSum += float(hr)
        
        if (hourCnt > 0):
            days[ prevDay(day, month, year) ] = str( round(hourSum / hourCnt, 2) )
        else:
            days[ prevDay(day, month, year) ] = '-'
            
        #make backup, once a day
        f = open('/backup/' + device + '.' + sensor + '.stat', 'w')
        f.write(dataStr)
        f.close()
        
    #New week - calculate average value
    if ( week != int(updated[5]) ):
        print('!Week recalc')
        wdSum = 0
        wdCnt = 7
        wdays = prevWeekDays(wday, day, month, year)
        for wd in wdays:
            if (days[wd] == '-'):
                wdCnt -= 1
            else:
                wdSum += float(days[wd])
        weeks[ prevWeek(week) ] = str( round(wdSum / wdCnt, 2) )
                        
    #New month - calculate average value
    if ( month != int(updated[1]) ):
        print('!Month recalc')
        daySum = 0
        totalDays = daysInMonth( prevMonth( month ), year )
        dayCnt = totalDays
        for di in range(1, totalDays+1):
            if (days[di] == '-'):
                dayCnt -= 1
            else:
                daySum += float( days[di] )
        months[ prevMonth( month ) ] = str(daySum / dayCnt) 
    
    updated = [str(year), str(month), str(day), str(hour), str(minute), str(week)]
    
    #write to file
    f = open('/db/' + device + '.' + sensor + '.stat', 'w')
    f.write(";".join(updated) + "\n")
    f.write(";".join(minutes) + "\n")
    f.write(";".join(hours) + "\n")
    f.write(";".join(days) + "\n")
    f.write(";".join(weeks) + "\n")
    f.write(";".join(months) + "\n")
    f.close()   

def getCurrWeek( wday, tday ):
    '''
    Get current number of week
    '''
    wdif  = (tday - wday - 1)%7
    week = int((tday - wday - 1 - wdif)/7)
    if wdif > 3:
        week += 1
    return week

def avgValue(oldValue, newValue):
    '''
    Count avg value between two values
    '''
    if (oldValue == '-'):
        return newValue
    else:
        return round( (float(oldValue) + float(newValue)) / 2, 2)


def prevHour(hour):
    '''
    Get previous hour
    '''    
    prev = 23
    if hour > 0:
        prev = hour - 1
    return prev


def daysInMonth(month, year):
    '''
    Get total days in month
    '''
    hiDay = hasHiDay(year)
    dayCount = [0, 31, 28 + hiDay, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return dayCount[month]


def prevDay(day, month, year):
    '''
    Get previous day
    '''
    if day > 1:
        prev = day - 1
    else:
        pMonth = prevMonth(month)
        prev = daysInMonth(pMonth, year)
    return prev


def hasHiDay(year):
    '''
    Is it Leap year 
    '''
    hiDay = 0
    if int(year) % 4 == 0:
        hiDay = 1
    return hiDay


def prevMonth(month):
    '''
    Get previous month
    '''    
    prev = 12
    if month > 1:
        prev = month - 1
    return prev


def prevWeek(week):
    '''
    Get previous week
    '''    
    if week > 1:
        return week - 1
    else:
        return 52

def prevWeekDays(wday, day, month, year):
    '''
    Get previous day of week
    '''    
    pointDay = day
    i = 7
    weekDays = [0, 0, 0, 0, 0, 0, 0]
    
    while wday > 0:
        wday -= 1
        pointDay = prevDay(pointDay, month, year)
        
    while i > 0:
        i -= 1
        pointDay = prevDay(pointDay, month, year)
        weekDays[i] = pointDay
        
    return weekDays

def getShiftedPeriod(period, currTime):
    '''
    Shifting of periods
    '''    
    if (period == 'minutes'):
        return shiftedMinutes(currTime[4])
    
    if (period == 'hours'):
        return shiftedHours(currTime[3])
    
    if (period == 'days'):
        return shiftedDays(currTime[2], currTime[1], currTime[0])
    
    if (period == 'weeks'):
        week = getCurrWeek(currTime[6], currTime[7])
        return shiftedWeeks(week)
    
    if (period == 'months'):
        return shiftedMonths(currTime[1])
    
    return []
    
def shiftedMinutes(minute):
    '''
    Shifted of minutes
    '''
    items = []
    for i in range (minute + 1, 60):
        items.append(i)
    
    for i in range (0, minute + 1):
        items.append(i)
    return items

def shiftedHours(hour):
    '''
    Shifted of hours
    '''
    items = []
    for i in range (hour + 1, 24):
        items.append(i)
    
    for i in range (0, hour + 1):
        items.append(i)
    return items

def shiftedDays(day, month, year):
    '''
    Shifted of days
    '''
    items = []
    pMonth = prevMonth(month)
    prevLastDay = daysInMonth(pMonth, year)

    for i in range (day + 1, prevLastDay + 1):
        items.append(i)
    
    for i in range (1, day + 1):
        items.append(i)
    return items

def shiftedWeeks(week):
    '''
    Shifted of weeks
    '''
    items = []
    for i in range (week + 1, 53):
        items.append(i)
    
    for i in range (1, week + 1):
        items.append(i)
    return items    

def shiftedMonths(month):
    '''
    Shifted of months
    '''
    items = []
    for i in range (month + 1, 13):
        items.append(i)
    
    for i in range (1, month + 1):
        items.append(i)
    return items

def getDefaultData(period):
    '''
    Default data for new DB
    '''
    if period == 'minutes':
        return ['-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-']
    if period == 'hours':
        return ['-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-']
    if period == 'days':
        return ['-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-']
    if period == 'weeks':
        return ['-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-','-']
    if period == 'months':
        return ['-','-','-','-','-','-','-','-','-','-','-','-','-']
    return []

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