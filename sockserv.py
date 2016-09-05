from __future__ import division
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import RPi.GPIO as GPIO
import time
import math
#import sqlite3
import os
import signal
from dbeditor import MovDatabase
from tornado.options import define, options
from Adafruit_PWM_Servo_Driver import PWM
 

# Initialise the PWM device using the default address
pwm1 = PWM(0x42)        #device1 16 servos
pwm1.setPWMFreq(60)
pwm2 = PWM(0x44)        #device2 4 servos
pwm2.setPWMFreq(60)


# Globals
currentmovarray = "ns"
currentmovarraycalc = [] #array used by loop with calculated values
currenttimingarray = []
currentmovid = "ns"
currentmovticks = 0
currentmovpossition = "ns"
currentmovarraycalcinitime = 0
currentmovarraycalcendtime = 0
currentservo = 0
loopamount = 1
currentmovspeed = "ns"
currentstepspeed = "ns"
uptime = 0
startpos = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 20)
endpos =   (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 20)
    
def setupNewClient(client): #initialize the movement menu
    global currentmovid
    global currentmovpossition
    global currentmovarray
    global currentstepspeed
    global currentmovspeed
    movarray = db.getMovList()
    for row in movarray:
        id = str(row[0])
        while len(id) != 3:
            id = "0%s" % (id)
        name = row[1]
        send_to_evoking_client(client, "003%s%s" % (id, name))
    print (movarray)
    if len(movarray) != 0:
        if currentmovid == "ns":
            currentmovid = movarray[0][0]
        movdata = db.getMovQuery(currentmovid)
        send_to_evoking_client(client, "005%s%s" % ("000"[len(str(currentmovid)):] + str(currentmovid), str(movdata[1])))
        if currentmovpossition == "ns":
            currentmovpossition = 0
        currentmovspeed = movdata[2]
        stepsdata = db.getStepQuery(currentmovid)
        #pref = "000"[len(str(len(stepsdata) - 1)):] + str(len(stepsdata) - 1) + "000"[len(str(currentmovpossition)):] + str(currentmovpossition)
        send_to_all_clients("006;" + str(len(stepsdata) - 1) + ";" + str(currentmovpossition))
        if currentmovarray == "ns":
            setMovArray()
        currentstepspeed = currentmovarray[currentmovpossition][20]
        m.servo_update_all_sliders()
        print(stepsdata[0])
        send_to_all_clients("002;" + "22;" + str(currentstepspeed))
        send_to_all_clients("002;" + "21;" + str(loopamount))
            
            
def setMov(command): #sets movlist 
    global currentmovpossition
    global currentmovid
    movid = int(command[:3])
    stepsdata = db.getStepQuery(movid)
    pref = "000"[len(str(len(stepsdata) - 1)):] + str(len(stepsdata) - 1) + "000"
    send_to_all_clients("006;" + str(len(stepsdata) - 1) + ";000")
    currentmovid = movid
    setMovArray()
    currentmovpossition = 0
    array = currentmovarray
    currentstepspeed = array[0][20]
    d = 0
    while d < len(array[0])-1:  # - 1 for the speedstep value
        pos = array[0][d]
        if str(pos) != "None":
            print str(pos)
            m.servo_set(d, pos, 0)
        d += 1
    #m.servo_set(currentmovpossition, newpos, 0)
    send_to_all_clients("002;" + "22;" + str(currentstepspeed))
    movdata = db.getMovQuery(movid)
    currentmovspeed = movdata[2]
    #print (movdata)
    send_to_all_clients("005%s%s" % ("000"[len(str(currentmovid)):] + str(currentmovid), str(movdata[1])))
    print('Movement set')
        
                
def setMovSpeed(command): #sets movment speed
    global currentmovpossition
    global currentmovid
    movid = int(command[:3])
    movdata = db.getMovQuery(movid)
    #print (movdata)
    send_to_all_clients("005%s%s" % ("000"[len(str(currentmovid)):] + str(currentmovid), str(movdata[1])))
    print('Movement set')
    
def setMovArray(): #this also creates a new steptable
    global currentmovarray 
    global currentmovticks
    stepsdata = db.getStepQuery2(currentmovid)
    print(stepsdata)
    currentmovarray = stepsdata
    currentmovticks = len(stepsdata)
    print('Movement array set')
        
def getMovSpeed(command): #gets movement speed
    global currentmovpossition
    global currentmovid
    movid = int(command[:3])
    movdata = db.getMovQuery(movid)
    print (movdata)
    send_to_all_clients("005%s%s" % ("000"[len(str(currentmovid)):] + str(currentmovid), str(movdata[1])))
    print('Movement set')
        
def updateMovMenu(): #this also creates a new steptable
    global currentmovpossition
    global currentmovid
    movarray = db.getMovList()
    i = 0
    send_to_all_clients("008")
    for row in movarray:
    # Add to movement list
        i = i + 1
        sID = str(row[0])
        iID = row[0]
        while len(sID) != 3:
            sID = "0%s" % (sID)
        name = row[1]
        send_to_all_clients("003%s%s" % (sID, name))
        # Set value to current mov id
        if iID == currentmovid:
            send_to_all_clients("005%s%s" % (sID, name))
        
def newMov(movname): #this also creates a new steptable
    global currentmovpossition
    global currentmovid
    global currentmovspeed
    movid = db.addMovQuery(movname, 20)
    movid = (movid[0])
    currentmovid = movid
    currentmovspeed = 20
    #print(movid)
    db.addStepQuery(movid, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 20)    
    m.servo_reset()
    m.servo_reset_sliders()
    #cursor.execute('''SELECT id, name  WHERE name=?''', (movname))
    updateMovMenu()
    send_to_all_clients("006;000;000")
    currentmovpossition = 0
    currentstepspeed = 20
    send_to_all_clients("002;" + "22;" + str(currentstepspeed))
    print('New movement created')
    setMovArray()
        
def delMov(movid): #must remove coresponding steptable
    global currentmovid
    global currentmovspeed
    global currentstepspeed
    global currentmovpossition
    
    movarray = db.getMovList()
    
    if len(movarray) != 1:
        movdata = db.getMovQuery(movid)
        db.delMovQuery(currentmovid)
        id = str(movdata[0])
        name = movdata[1]
        while len(id) != 3:
                id = "0%s" % (id)
        # Remove movement from list
        send_to_all_clients("004%s%s" % (id, name))
        print('Movement query removed')
        
        #cursor.execute('''SELECT * FROM movement ORDER BY ROWID ASC LIMIT 1''')
        #data = cursor.fetchone()
        
        movarray = db.getMovList()
        
        send_to_all_clients("005%s%s" % (str(movarray[0]), movarray[1]))
        currentmovid = movarray[0]
        setMovArray()
        currentstepspeed = currentmovarray[0][20]
        currentmovspeed = movarray[2]
        currentmovpossition = 0
        m.servo_update_all_sliders()
            
def editMov(command): #steptable remains unchanged
    global movspeed
    array = command.split(';')
    print (array)
    newname = array[0]
    mspeed = int(array[1])
    movid = int(array[2])
    db.editMovQuery(newname, mspeed, movid)
    movspeed = mspeed
    updateMovMenu()
    # send_to_all_clients("007%s%s" % (str(data[0]), data[1]))!!!!!!!!!!!!!!!!!!!!!!
    print('Movement query edited')
        
def addStep(command):
    global currentmovpossition
    #movid = int(command[:3])
    #steppos = (int(command[3:]) + 1)
    movid = currentmovid
    steppos = (currentmovpossition + 1)
    stepsdata = db.getStepQuery(movid)
    db.addStepQuery2(movid,steppos,stepsdata)
    i = (len(stepsdata) + 1)
    id = "000"[len(str(i - 1)):] + str(i - 1)
    #pref = "000"[len(str(i)):] + str(i) + "000"[len(str(steppos)):] + str(steppos)
    pref = id + "000"[len(str(steppos)):] + str(steppos)
    send_to_all_clients("006%s" % (pref))
    currentmovpossition = steppos
    print('New step inserted')
    setMovArray()

def delStep(command):
    global currentmovpossition
    global currentstepspeed
    #movid = int(command[:3])
    #steppos = int(command[3:])
    movid = currentmovid
    steppos = currentmovpossition
    stepsdata = db.getStepQuery(movid)
    i = len(stepsdata)
    if i > 1:
        db.delStepQuery(movid, steppos, stepsdata)
        id = "000"[len(str(i - 2)):] + str(i - 2)
        pref = id + "000"[len(str(steppos - 1)):] + str(steppos - 1)
        send_to_all_clients("006%s" % (pref))
        currentmovpossition = (steppos - 1)
        #currentstepspeed = 
        print('Step deleted')
        setMovArray()
        
def editStep(command):
    movid = int(command[:3])
    id = (command[:3])
    sarray = (command[4:]).split(';')
    if sarray[0] != 'undefined': s1 = int(sarray[0])
    if sarray[1] != 'undefined': s2 = int(sarray[1])
    if sarray[2] != 'undefined': s3 = int(sarray[2])
    if sarray[3] != 'undefined': s4 = int(sarray[3])
    if sarray[4] != 'undefined': s5 = int(sarray[4])
    if sarray[5] != 'undefined': s6 = int(sarray[5])
    if sarray[6] != 'undefined': s7 = int(sarray[6])
    if sarray[7] != 'undefined': s8 = int(sarray[7])
    if sarray[8] != 'undefined': s9 = int(sarray[8])
    if sarray[9] != 'undefined': s10 = int(sarray[9])
    if sarray[10] != 'undefined': s11 = int(sarray[10])
    if sarray[11] != 'undefined': s12 = int(sarray[11])
    if sarray[12] != 'undefined': s13 = int(sarray[12])
    if sarray[13] != 'undefined': s14 = int(sarray[13])
    if sarray[14] != 'undefined': s15 = int(sarray[14])
    if sarray[15] != 'undefined': s16 = int(sarray[15])
    if sarray[16] != 'undefined': s17 = int(sarray[16])
    if sarray[17] != 'undefined': s18 = int(sarray[17])
    if sarray[18] != 'undefined': s19 = int(sarray[18])
    if sarray[19] != 'undefined': s20 = int(sarray[19])
    if sarray[20] != 'undefined': stepspeed = int(sarray[20])
    db.editStepQuery(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, 0, 0, 0, stepspeed, currentmovpossition, movid)
    #cursor.execute('''SELECT * FROM steps WHERE movid=?''', (movid,))
    #data = cursor.fetchall()
    #print (data)
    print('Step query edited')
    setMovArray()

def closedb(self):
    db.close()
# ===========================================================================
# Example Code
# ===========================================================================

class motion:
    
    walkpos = 0
    servoset = [
        ["servo00", 380, 380],  # Foot right
        ["servo01", 394, 394],  # Foot left
        ["servo02", 391, 391],  # Leg right bottom
        ["servo03", 272, 272],  # Leg left bottom
        ["servo04", 544, 544],  # Leg right mid
        ["servo05", 226, 226],  # Leg left mid
        ["servo06", 352, 352],  # Leg right top
        ["servo07", 544, 544],  # Leg left top
        ["servo08", 362, 362],  # Hip right
        ["servo09", 358, 358],  # Hip left
        ["servo10", 375, 375],
        ["servo11", 375, 375],
        ["servo12", 375, 375],
        ["servo13", 375, 375],
        ["servo14", 375, 375],
        ["servo15", 394, 394],  # Rotate camera
        ["servo16", 375, 375],
        ["servo17", 375, 375],
        ["servo18", 375, 375],
        ["servo19", 375, 375]  
    ]
    
    servoMin = 150  # Min pulse length out of 4096
    servoMax = 600  # Max pulse length out of 4096
    
    def servomov_ticks(matrix):
        x = 0
        y = 0
        max = 0
        while x < len(matrix):
            while y < len(matrix[x]):
                if max < (matrix[x][y][2] + matrix[x][y][3]):
                    max = (matrix[x][y][2] + matrix[x][y][3])
                y += 1
            x += 1 
        return max
    
    
    #ticks1 = servomov_ticks(servomov1)
    #ticks2 = servomov_ticks(servomov2)
    def servo_update_all_sliders(self):
        array = currentmovarray
        ticks = currentmovticks
        currentpos = currentmovpossition
        d = 0
        while d < len(motion.servoset):
            pos = array[currentpos][d]
            if str(pos) != "None":
                mes = "002;" + str(d) + ";" + str(pos)
                send_to_all_clients(mes)
            d += 1
        send_to_all_clients("002;" + "22;" + str(currentstepspeed))
    
    def servo_update_slider(self, sliderid, curpos, newpos):
        if curpos != newpos:
            mes = "002;" + str(sliderid) + ";" + str(newpos)
            #mes = "002" + motion.servoset[channel][0] + "%d" % (newpos)
            send_to_all_clients(mes)
            #print 'slider set'
    
    def servo_reset_sliders(self):
        global currentmovpossition
        send_to_all_clients("002;20;0")
        send_to_all_clients("006;999;0")
        currentmovpossition = 0
        motion.walkpos = 0
    
    def servo_set(self, channel, pos, incr):
#        pwm1.setPWMFreq(60)
#        print channel
        curpos = motion.servoset[channel][2] - motion.servoset[channel][1]
        if incr == 1:
            motion.servoset[channel][2] = motion.servoset[channel][2] + pos
        else:
            motion.servoset[channel][2] = motion.servoset[channel][1] + pos
        newpos = motion.servoset[channel][2] - motion.servoset[channel][1]
        if channel < 6:
            pwm1.setPWM(channel, 0, int(motion.servoset[channel][2]))
        else:
            pwm2.setPWM((channel-6), 0, int(motion.servoset[channel][2]))
        self.servo_update_slider(channel, curpos, newpos)
#        print "Servo: %d - Position %d" % (channel, motion.servoset[channel][2])
    
    def g_left_right(self, pos, incr):
        self.servo_set(9, -pos, incr)
        self.servo_set(8, -pos, incr)
        self.servo_set(1, -pos, incr)
        self.servo_set(0, -pos, incr)
            
#    def run(self):
#        global currentmovpossition
#        array = currentmovarray
#        ticks = currentmovticks
#        speed = currentmovspeed
#        devider = 20
#        print (array)
#        z = 0
#        while z < loopamount:
#            currentmovpossition = 0
#            y = 0
#            #send_to_all_clients("006;" + str(ticks - 1) + ";" + str(y))
#            while y < (len(array)):
#                x = 0
#                while x <= devider:
#                    temparray = []
#                    seq = 0
#                    while seq < (len(array[y]))-1:
#                        if y == (len(array))-1:
#                            if array[y][seq] == array[0][seq]:
#                                temparray.append(array[y][seq])
#                            elif array[y][seq] is None:
#                                temparray.append(array[0][seq])
#                            elif array[0][seq] is None:
#                                temparray.append(array[y][seq])
#                            else: 
#                                temparray.append(int(array[y][seq]-((array[y][seq]-array[0][seq])*(x/devider))))
#                        else:
#                            if array[y][seq] == array[y + 1][seq]:
#                                temparray.append(array[y][seq])
#                            elif array[y][seq] is None:
#                                temparray.append(array[y + 1][seq])
#                            elif array[y + 1][seq] is None:
#                                temparray.append(array[y][seq])
#                            else: 
#                                temparray.append(int(array[y][seq]-((array[y][seq]-array[y+1][seq])*(x/devider))))
#                        seq += 1
#                    i = 0
#                    while i < len(temparray):
#                        print (i)
#                        if temparray[i] is not None:
#                            pos = temparray[i]
#                            self.servo_set(i, pos, 0)
#                        i += 1
#                    x += 1
#                    time.sleep(0.02)
#                    print (temparray)
#                y += 1
#                if y == (len(array)):
#                    send_to_all_clients("006;" + str(ticks - 1) + ";" + str(0))
#                    currentmovpossition = 0
#                else:
#                    send_to_all_clients("006;" + str(ticks - 1) + ";" + str(y))
#                    currentmovpossition = y
#            z += 1
    def run (self):  
        movarraysequence = []
        movarraysequence.append(startpos)
        x = 0
        while x < loopamount: # amount of loops
            y = 0
            while y < len(currentmovarray):
                movarraysequence.append(currentmovarray[y])
                y += 1
            x += 1
        movarraysequence.append(endpos)
        self.createmovarray(movarraysequence)
#        print (movarraysequence)
        

    def createmovarray(self, movarraysequence):
#        global currentmovpossition
        global uptime
        global currentmovarraycalcinitime
        global currentmovarraycalcendtime
        global currentmovarraycalc
        global currenttimingarray
#        print uptime
        currentmovarraycalcinitime = uptime
        currentmovarraycalcendtime = [] 
        currentmovarraycalc = []
        currenttimingarray = [] # array of 
        array = movarraysequence
#        ticks = currentmovticks
        speed = currentmovspeed
#        divider = 20
        timer = 0
#        print (array)
        z = 0
        while z < 1: # amount of loops 
            y = 0
            #send_to_all_clients("006;" + str(ticks - 1) + ";" + str(y))
            while y < (len(array))-1:
                divider = array[y][20]/2
                tempmovpossition = y
                x = 0
#                while x <= devider: #stop using fixed devider make chunks of 10ms to inject in loop
                while x <= divider:
#                    print divider
                    temparray = []
                    seq = 0
                    while seq < (len(array[y])):
#                        if y == (len(array))-1: #this sets the movement after the last possition to reset the loop to possition 0
#                            if array[y][seq] == array[0][seq]:
#                                temparray.append(array[y][seq])
#                            elif array[y][seq] is None:
#                                temparray.append(array[0][seq])
#                            elif array[0][seq] is None:
#                                temparray.append(array[y][seq])
#                            else: 
#                                temparray.append(int(array[y][seq]-((array[y][seq]-array[0][seq])*(x/divider))))
#                        else:
                            if array[y][seq] == array[y + 1][seq]:
                                temparray.append(array[y][seq])
                            elif array[y][seq] is None:
                                temparray.append(array[y + 1][seq])
                            elif array[y + 1][seq] is None:
                                temparray.append(array[y][seq])
                            else: 
                                temparray.append(int(array[y][seq]-((array[y][seq]-array[y+1][seq])*(x/divider))))
                            # add end possition
                            seq += 1
                    i = 0
                    timer = timer + 200 #array[y][(len(array[y]))-1]/divider
#                    print (timer)
                    if y == (len(array)):
#                       send_to_all_clients("006;" + str(ticks - 1) + ";" + str(0))
                        tempmovpossition = 0
                    else:
#                        send_to_all_clients("006;" + str(ticks - 1) + ";" + str(y))
                        tempmovpossition = y
                    currentmovarraycalc.append([temparray,tempmovpossition])
                    currenttimingarray.append(timer) #creates an array of value x 0.2s 
#                    while i < len(temparray):
#                        print (i)
#                        if temparray[i] is not None:
#                            pos = temparray[i]
#                            self.servo_set(i, pos, 0)
#                        i += 1
                    x += 1
#                    time.sleep(0.02)
#                    print (temparray)
#                    print (currentmovarraycalc)
                y += 1
            z += 1
        currentmovarraycalcendtime = currentmovarraycalcinitime + timer
#        myInt = 10
#        currenttimingarray = [x / myInt for x in currenttimingarray]
#        print currentmovendtime
        print (currenttimingarray)
        print "333333333333333333"
        print (currentmovarraycalc)
        print "333333333333333333"
    
    def servo_slider(self, nextpos):
        global currentmovpossition
        b = 0
        c = 0
        array = currentmovarray
        ticks = currentmovticks
        currentpos = currentmovpossition
        if nextpos == 0 and currentpos == ticks:
            currentpos = 0
        if nextpos == ticks and currentpos == 0:
            currentpos = ticks
        if currentpos < nextpos:
            a = 1
            b = currentpos
            c = nextpos
        elif currentpos > nextpos:
            a = -1
            b = nextpos
            c = currentpos
        d = 0
        
        print(array)
        print(len(motion.servoset))
        
        while d < len(motion.servoset):
            pos = array[nextpos][d]
            if str(pos) != "None" and pos != array[currentpos][d]:
                print ("inloop")
                self.servo_set(d, pos, 0)
            d += 1
        stepspeed = currentmovarray[nextpos][20]
        send_to_all_clients("002;" + "22;" + str(stepspeed))
        currentmovpossition = nextpos
        #pref = "000"[len(str(len(array) - 1)):] + str(len(array) - 1) + "000"[len(str(nextpos)):] + str(nextpos)
        send_to_all_clients("006;" + str(len(array) - 1) + ";" + str(nextpos))

    def servo_reset(self):
        walkpos = 0
        y = 0
        resolution = 20.0
        devider = []
        while y < len(motion.servoset):
            devider.append((motion.servoset[y][2] - motion.servoset[y][1]) / resolution)
            print "Loop trough %d" % devider[y]
            y += 1
        x = 0
        while x < resolution:
            y = 0
            while y < len(motion.servoset):
                self.servo_set(y, -devider[y], 1)
                y = y + 1
            time.sleep(0.01)
            x += 1
        x = 0
        while x < len(motion.servoset):
            self.servo_set(x, 0, 0)
            print "Loop trough %d" % x
            x += 1
            time.sleep(0.01)

m = motion()
db = MovDatabase()

from tornado.options import define, options
define("port", default=8090, help="run on the given port", type=int)

_SHUTDOWN_TIMEOUT = 2

clients = []

def robotUpdate():
    global currentmovpossition
    global uptime
    global currentmovarraycalcinitime
    global currentmovarraycalcendtime
    global currentmovarraycalc
    global currenttimingarray
    global currentservo
    uptime = uptime + 10
    supdate = 200 #ms
    if uptime >= currentmovarraycalcinitime and uptime < currentmovarraycalcendtime:
        index = currenttimingarray.index(int(math.floor((uptime - currentmovarraycalcinitime)/supdate))*supdate + supdate)
        print index
        print len(currentmovarraycalc)
#        print currentmovarraycalc[index][currentservo]
        if str(currentmovarraycalc[index][0][currentservo]) != "None":
            m.servo_set(currentservo, currentmovarraycalc[index][0][currentservo], 0)
#            print currentservo
#            print currentmovarraycalc[index][0][currentservo]
            pass
        currentservo = currentservo + 1
        if currentservo == 20:
            currentservo = 0
            print currentmovarraycalc[index][0][currentservo]
            print uptime - currentmovarraycalcinitime
#        print currentservo
#    print currenttimingarray
#    global robot
#    global isClosing
    
#    if isClosing:
#        tornado.ioloop.IOLoop.instance().stop()
#        return
        
#    if robot == None:
        
#        if not robotConnectionResultQueue.empty():
            
#            robot = robotConnectionResultQueue.get()
        
#    else:
                
#        robot.update()

def send_to_all_clients(msg):
    for client in clients:
        client.write_message(msg)
        
def send_to_evoking_client(client, msg):
        client.write_message(msg)
        
def make_safely_shutdown(server):
    io_loop = server.io_loop or ioloop.IOLoop.instance()
    def stop_handler(*args, **keywords):
        def shutdown():
            server.stop() # this may still disconnection backlogs at a low probability
            deadline = time.time() + _SHUTDOWN_TIMEOUT
            def stop_loop():
                now = time.time()
                if now < deadline and (io_loop._callbacks or io_loop._timeouts):
                    io_loop.add_timeout(now + 1, stop_loop)
                else:
                    io_loop.stop()
            stop_loop()
        io_loop.add_callback(shutdown)
    signal.signal(signal.SIGQUIT, stop_handler) # SIGQUIT is send by our supervisord to stop this server.
    signal.signal(signal.SIGTERM, stop_handler) # SIGTERM is send by Ctrl+C or supervisord's default.
    signal.signal(signal.SIGINT, stop_handler)
    
def shutdown():
    #logging.info('Stopping http server')
    httpServer.stop()

    #logging.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.instance()

    deadline = time.time() + 3

    def stop_loop():
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_loop)
        else:
            io_loop.stop()
            #logging.info('Shutdown')
    stop_loop()
        

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print 'new connection'
        send_to_all_clients("new client")
        self.stream.set_nodelay(True)
        clients.append(self)

    def on_message(self, message):
        print 'message received %s' % message
        global loopamount
        #self.write_message(message)
        #channel 1XX is from editor
        #channel 2XX is from remote
        channel = int(message[0:3])
        command = (message[3:])
        if channel < 116:
            m.servo_set(int(message[1:3]), int(command), 0)
            print "channel: %d angle: %d" % (channel, int(command))
        if channel == 120:
            m.g_left_right( int(command), 0)
            print "channel: %d angle: %d" % (channel, int(command))
        if channel == 121:
            loopamount = int(command)
            send_to_all_clients("002;" + "21;" + str(loopamount))
            print "channel: %d loopamount: %d" % (channel, int(command))
#        if channel == 122:
#            db.setmovspeed( int(command), 0)
#            print "channel: %d speed: %d" % (channel, int(command))
        if channel == 130:
            self.write_message("reset")
            m.servo_reset()
            m.servo_reset_sliders()
        if channel == 131:  # walk function from commandline hier gebleven
            self.write_message("walking")
            m.servo_walk(100,1)
        if channel == 132:  # walk function from commandline hier gebleven
            self.write_message("walking")
            m.servo_walk(100,2)
        if channel == 133:  # walk function from commandline hier gebleven
            self.write_message("walking")
            m.run()
        if channel == 135:  # shutdown server
            self.write_message("shutting down the server")
            shutdown()
        if channel == 140:  # movement possition slider
            self.write_message("walking")
            m.servo_slider(int(command))
            print "step: %d position: %d" % (channel, int(command))
        if channel == 150:  # Save current position
            self.write_message("saving current positions")
            editStep(command)
            print "step: %d position: %s" % (channel, command)
        if channel == 151:  # Add step 
            addStep(command)
            self.write_message("Insert new step behind current posistion")
            print "command nr: %d value: %s" % (channel, command)
        if channel == 152:  # Delete step
            delStep(command)
            self.write_message("Delete current step")
            print "step: %d position: %d" % (channel, int(command))
        if channel == 153:  # Add a new motion
            newMov(command)
            self.write_message("Add a new motion")
            print "step: %d position: %s" % (channel, command)
        if channel == 154:  # Delete current motion
            delMov(int(command))
            self.write_message("Delete current motion")
            print "step: %d position: %d" % (channel, int(command))
        if channel == 155:  # Populate movement list
            setupNewClient(self)
            self.write_message("Populating movmlist")
            print "step: %d position: %d" % (channel, int(command))
        if channel == 156:  # Set movement list
            setMov(command)
            self.write_message("Setting movmlist")
            print "command: %d set movement list: %s" % (channel, command)
        if channel == 157:  # Set movement list
            editMov(command)
            self.write_message("Setting movmlist")
            print "command: %d set movement list: %s" % (channel, command)

    def on_close(self):
        clients.remove(self)
        send_to_all_clients("removing client")
        print 'connection closed'

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/ws", WebSocketHandler),
            (r"/www/(.*)", tornado.web.StaticFileHandler, {"path": "./www"},),
            (r"/www/js/(.*)", tornado.web.StaticFileHandler, {"path": "./www/js"},),
            (r"/www/css/(.*)", tornado.web.StaticFileHandler, {"path": "./www/css"},)
        ]
    )
    
    global httpServer
    
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)
    
    res = 10
    robotPeriodicCallback = tornado.ioloop.PeriodicCallback( 
        robotUpdate, res, io_loop=tornado.ioloop.IOLoop.instance() )
    robotPeriodicCallback.start()
    
    print "Listening on port:", options.port
    make_safely_shutdown(httpServer)
    tornado.ioloop.IOLoop.instance().start()
