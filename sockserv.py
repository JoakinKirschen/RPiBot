from __future__ import division
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import RPi.GPIO as GPIO
from Adafruit_PWM_Servo_Driver import PWM
import time
import math
import sqlite3
import os
import signal
 

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
currentmovinitime = 0
currentmovendtime = 0
currentservo = 0
loopamount = 1
currentmovspeed = "ns"
currentstepspeed = "ns"
uptime = 0


class MovDatabase(object):
    # Create a database in RAM
    # db = sqlite3.connect(':memory:')
    # Creates or opens a file called mydb with a SQLite3 DB
    # db = sqlite3.connect('data/mydb')
    
    def __init__(self, db_file="data/data.db"):
        database_already_exists = os.path.exists(db_file)   
        self.db = sqlite3.connect(db_file)
        if not database_already_exists:
            self.setupDefaultData()
    
    def setupDefaultData(self):
        """ create the database tables and default values if it doesn't exist already """
        cursor = self.db.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS movement
        (
            id         INTEGER     PRIMARY KEY     AUTOINCREMENT,
            name       TEXT,
            movspeed   INTEGER
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS steps
        (
            id         INTEGER     PRIMARY KEY     AUTOINCREMENT,
            movid      INTEGER,
            steppos    INTEGER,
            s1         INTEGER,
            s2         INTEGER,
            s3         INTEGER,
            s4         INTEGER,
            s5         INTEGER,
            s6         INTEGER,
            s7         INTEGER,
            s8         INTEGER,
            s9         INTEGER,
            s10        INTEGER,
            s11        INTEGER,
            s12        INTEGER,
            s13        INTEGER,
            s14        INTEGER,
            s15        INTEGER,
            s16        INTEGER,
            s17        INTEGER,
            s18        INTEGER,
            s19        INTEGER,
            s20        INTEGER,
            stepspeed      INTEGER,
            FOREIGN KEY(movid) REFERENCES movement(id)
        )''')
        cursor.execute('''SELECT * FROM movement ORDER BY id ASC''')
        data = cursor.fetchall()
        print ("Tables created")
        for row in data:
            id = str(row[0])
            while len(id) != 3:
                id = "0" + id
            name = row[1]
            send_to_all_clients("003%s%s" % (id, name))
        self.db.commit()
        cursor.close()
        
    def setMovArray(self): #this also creates a new steptable
        global currentmovarray 
        global currentmovticks
        movid = currentmovid
        cursor = self.db.cursor()
        cursor.execute('''SELECT s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20, stepspeed FROM steps WHERE movid=? ORDER BY steppos ASC''', (movid,))
        movdata = cursor.fetchall()
        print(movdata)
        currentmovarray = movdata
        currentmovticks = len(movdata)
        print('Movement array set')
        
    def getservopos(self, movid, servonr, pos):
        servonr = int(servonr[1:])
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM steps WHERE movid = ? AND steppos = ? ORDER BY steppos ASC''', (movid, pos,))
        Ival = cursor.fetchone()
        Ival = Ival[servonr + 2]
        print (Ival) 
        return Ival
    
    def setupNewClient(self, client): #initialize the movement menu
        global currentmovid
        global currentmovpossition
        global currentmovarray
        global currentstepspeed
        global currentmovspeed
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM movement ORDER BY id ASC''')
        #data = cursor.fetchone()
        data = cursor.fetchall()
        for row in data:
            id = str(row[0])
            while len(id) != 3:
                id = "0%s" % (id)
            name = row[1]
            send_to_evoking_client(client, "003%s%s" % (id, name))
        print (data)
        if len(data) != 0:
            if currentmovid == "ns":
                currentmovid = data[0][0]
            cursor.execute('''SELECT * FROM movement WHERE id=? ''', (currentmovid,))
            curdata = cursor.fetchone()
            send_to_evoking_client(client, "005%s%s" % ("000"[len(str(currentmovid)):] + str(currentmovid), str(curdata[1])))
            if currentmovpossition == "ns":
                currentmovpossition = 0
            currentmovspeed = curdata[2]
            cursor.execute('''SELECT * FROM steps WHERE movid=? ORDER BY steppos ASC''', (currentmovid,))
            movdata = cursor.fetchall()
            #pref = "000"[len(str(len(movdata) - 1)):] + str(len(movdata) - 1) + "000"[len(str(currentmovpossition)):] + str(currentmovpossition)
            send_to_all_clients("006;" + str(len(movdata) - 1) + ";" + str(currentmovpossition))
            if currentmovarray == "ns":
                self.setMovArray()
            currentstepspeed = currentmovarray[currentmovpossition][20]
            m.servo_update_all_sliders()
            print(movdata[0])
            send_to_all_clients("002;" + "22;" + str(currentstepspeed))
            send_to_all_clients("002;" + "21;" + str(loopamount))
            
            
    def setMovQuery(self,command): #sets movlist 
        global currentmovpossition
        global currentmovid
        movid = int(command[:3])
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM steps WHERE movid=? ORDER BY steppos ASC''', (movid,))
        movdata = cursor.fetchall()
        #newpos = self.getservopos(movid, "s1" ,0)
        pref = "000"[len(str(len(movdata) - 1)):] + str(len(movdata) - 1) + "000"
        send_to_all_clients("006;" + str(len(movdata) - 1) + ";000")
        currentmovid = movid
        self.setMovArray()
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
        cursor.execute('''SELECT * FROM movement WHERE id=? ''', (movid,))
        movdata = cursor.fetchone()
        currentmovspeed = movdata[2]
        print (movdata)
        send_to_all_clients("005%s%s" % ("000"[len(str(currentmovid)):] + str(currentmovid), str(movdata[1])))
        print('Movement set')
        
                
    def setMovSpeed(self,command): #sets movlist 
        global currentmovpossition
        global currentmovid
        movid = int(command[:3])
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM movement WHERE id=? ''', (movid,))
        movdata = cursor.fetchone()
        print (movdata)
        send_to_all_clients("005%s%s" % ("000"[len(str(currentmovid)):] + str(currentmovid), str(movdata[1])))
        print('Movement set')
        
    def getMovSpeed(self,command): #sets movlist 
        global currentmovpossition
        global currentmovid
        movid = int(command[:3])
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM movement WHERE id=? ''', (movid,))
        movdata = cursor.fetchone()
        print (movdata)
        send_to_all_clients("005%s%s" % ("000"[len(str(currentmovid)):] + str(currentmovid), str(movdata[1])))
        print('Movement set')
        
    def updateMovMenu(self): #this also creates a new steptable
        global currentmovpossition
        global currentmovid
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM movement ORDER BY id ASC''')
        data = cursor.fetchall()
        i = 0
        #for row in data:
        # Remove movement from list
        #    id = str(row[0])
        #    while len(id) != 3:
        #        id = "0" + id
        #    name = row[1]
        #    send_to_all_clients("004%s%s" % (id, name))
        send_to_all_clients("008")
        for row in data:
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
        
    def newMovQuery(self,movname): #this also creates a new steptable
        global currentmovpossition
        global currentmovid
        global currentmovspeed
        cursor = self.db.cursor()
        cursor.execute('''INSERT INTO movement (name, movspeed) VALUES (?, ?)''', (movname, 20))
        cursor.execute('''SELECT id FROM movement WHERE id=?''', ((cursor.lastrowid),))
        movid = cursor.fetchone()
        movid = (movid[0])
        currentmovid = movid
        currentmovspeed = 20
        print(movid)
        cursor.execute('''INSERT INTO steps (movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, stepspeed ) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
        , (movid, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 20))
        self.db.commit()
        m.servo_reset()
        m.servo_reset_sliders()
        #cursor.execute('''SELECT id, name  WHERE name=?''', (movname))
        self.updateMovMenu()
        send_to_all_clients("006;000;000")
        currentmovpossition = 0
        currentstepspeed = 20
        send_to_all_clients("002;" + "22;" + str(currentstepspeed))
        print('New movement created')
        self.setMovArray()
        
    def delMovQuery(self,movid): #must remove coresponding steptable
        global currentmovid
        global currentmovspeed
        global currentstepspeed
        global currentmovpossition
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM movement ORDER BY id ASC''')
        #data = cursor.fetchone()
        data = cursor.fetchall()
        if len(data) != 1:
            cursor.execute('''SELECT id, name FROM movement WHERE id=?''', (movid,))
            data = cursor.fetchone()
            cursor.execute('''DELETE FROM movement WHERE id = ? ''', (movid,))
            cursor.execute('''DELETE FROM steps WHERE movid = ? ''', (movid,))
            self.db.commit()
            id = str(data[0])
            name = data[1]
            while len(id) != 3:
                    id = "0%s" % (id)
            # Remove movement from list
            send_to_all_clients("004%s%s" % (id, name))
            print('Movement query removed')
            cursor.execute('''SELECT * FROM movement ORDER BY ROWID ASC LIMIT 1''')
            data = cursor.fetchone()
            send_to_all_clients("005%s%s" % (str(data[0]), data[1]))
            currentmovid = data[0]
            self.setMovArray()
            currentstepspeed = currentmovarray[0][20]
            currentmovspeed = data[2]
            currentmovpossition = 0
            m.servo_update_all_sliders()
    def editMovQuery(self, command): #steptable remains unchanged
        global movspeed
        array = command.split(';')
        print (array)
        newname = array[0]
        mspeed = int(array[1])
        movid = int(array[2])
        cursor = self.db.cursor()
        # Insert user 1
        cursor.execute('''UPDATE movement SET name=?, movspeed=? WHERE id=? ''', (newname, mspeed, movid,))
        self.db.commit()
        movspeed = mspeed
        self.updateMovMenu()
        # send_to_all_clients("007%s%s" % (str(data[0]), data[1]))!!!!!!!!!!!!!!!!!!!!!!
        print('Movement query edited')
        
    def addStepQuery(self,command):
        global currentmovpossition
        #movid = int(command[:3])
        #steppos = (int(command[3:]) + 1)
        movid = currentmovid
        steppos = (currentmovpossition + 1)
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM steps WHERE movid=?''', (movid,))
        data = cursor.fetchall()
        i = (len(data) + 1)
        k = i
        print (steppos)
        while k >= steppos:
            cursor.execute('''UPDATE steps SET steppos = ? WHERE steppos = ? AND movid = ?''', ((k + 1), k, movid,))
            if k == steppos:
                cursor.execute('''SELECT * FROM steps WHERE movid=? AND steppos=?''', (movid, (steppos - 1)))
                posdata = list(cursor.fetchone())
                posdata[1] = movid
                posdata[2] = steppos
                cursor.execute('''INSERT INTO steps (movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20, stepspeed ) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                #, (movid, steppos, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
                , (posdata[1:]))
            k = k - 1
        print (data)
        self.db.commit()
        #id = "000"[len(str(i - 1)):] + str(i - 1)
        #pref = "000"[len(str(i)):] + str(i) + "000"[len(str(steppos)):] + str(steppos)
        #pref = id + "000"[len(str(steppos)):] + str(steppos)
        send_to_all_clients("006;" + str(i - 1) + ";" + str(steppos))
        currentmovpossition = steppos
        print('New step inserted')
        self.setMovArray()

    def delStepQuery(self,command):
        global currentmovpossition
        global currentstepspeed
        #movid = int(command[:3])
        #steppos = int(command[3:])
        movid = currentmovid
        steppos = currentmovpossition
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM steps WHERE movid=?''', (movid,))
        data = cursor.fetchall()
        i = len(data)
        if i > 1:
            j = steppos
            while j <= i:
                if j == steppos:
                    cursor.execute('''DELETE FROM steps WHERE steppos = ?  AND movid = ?''', (j, movid,))
                    #cursor.execute('''DELETE FROM users WHERE id = ? ''', (delete_userid,))
                    self.db.commit()
                cursor.execute('''UPDATE steps SET steppos = ? WHERE steppos = ?  AND movid = ?''', ((j - 1), j, movid,))
                j = j + 1
            print (data)
            self.db.commit()
            #id = "000"[len(str(i - 2)):] + str(i - 2)
            #pref = id + "000"[len(str(steppos - 1)):] + str(steppos - 1)
            send_to_all_clients("006;" + str(i - 2) + ";" + str(steppos - 1))
            currentmovpossition = (steppos - 1)
            #currentstepspeed = 
            print('Step deleted')
            self.setMovArray()

    def editStepQuery(self,command):
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
        cursor = self.db.cursor()
        cursor.execute('''UPDATE steps SET s1 = ?, s2 = ?, s3 = ?, s4 = ?, s5 = ?, s6 = ?, s7 = ?, s8 = ?, s9= ?, s10 = ?, s11 = ?, s12= ?, s13 = ?, stepspeed = ? WHERE steppos = ? AND movid = ?''',
        (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, 0, 0, 0, stepspeed, currentmovpossition, movid,))
        cursor.execute('''SELECT * FROM steps WHERE movid=?''', (movid,))
        data = cursor.fetchall()
        print (data)
        print('Step query edited')
        self.db.commit()
        self.setMovArray()

    def closedb(self):
        db.close()
# ===========================================================================
# Example Code
# ===========================================================================
class motion:

    # Initialise the PWM device using the default address
    # pwm = PWM(0x40)
    # Note if you'd like more debug output you can instead run:
    # pwm = PWM(0x40, debug=True)
    
    
    #Servoname, Calibrate, Current_pos
    
    

    walkpos = 0
    servoset = [
        ["servo00", 380, 380],  # Foot right
        ["servo01", 382, 382],  # Foot left
        ["servo02", 391, 391],  # Leg right bottom
        ["servo03", 268, 268],  # Leg left bottom
        ["servo04", 544, 544],  # Leg right mid
        ["servo05", 238, 238],  # Leg left mid
        ["servo06", 360, 360],  # Leg right top
        ["servo07", 536, 536],  # Leg left top
        ["servo08", 362, 362],  # Hip right
        ["servo09", 350, 350],  # Hip left
        ["servo10", 375, 375],
        ["servo11", 375, 375],
        ["servo12", 375, 375],
        ["servo13", 375, 375],
        ["servo14", 375, 375],
        ["servo15", 304, 304],  # Rotate camera
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
            print 'slider set'
    
    def servo_reset_sliders(self):
        global currentmovpossition
        send_to_all_clients("002;20;0")
        send_to_all_clients("006;999;0")
        currentmovpossition = 0
        motion.walkpos = 0
    
    def servo_set(self, channel, pos, incr):
#        pwm1.setPWMFreq(60)
        print channel
        curpos = motion.servoset[channel][2] - motion.servoset[channel][1]
        if incr == 1:
            motion.servoset[channel][2] = motion.servoset[channel][2] + pos
        else:
            motion.servoset[channel][2] = motion.servoset[channel][1] + pos
        newpos = motion.servoset[channel][2] - motion.servoset[channel][1]
        if channel < 16:
            pwm1.setPWM(channel, 0, int(motion.servoset[channel][2]))
        else:
            pwm2.setPWM(channel, 0, int(motion.servoset[channel][2]))
        self.servo_update_slider(channel, curpos, newpos)
        print "Servo: %d - Position %d" % (channel, motion.servoset[channel][2])
    
    def g_left_right(self, pos, incr):
        self.servo_set(9, -pos, incr)
        self.servo_set(8, -pos, incr)
        self.servo_set(1, -pos, incr)
        self.servo_set(0, -pos, incr)
    
    # startpos #endpos #startime #steps
    # make loop with time range arrays to tell servos when to hit
    def servo_walk(self, speed):
        array = currentmovarray
        ticks = currentmovticks
        print (array)
        z = 0
        while z < 2:
            x = 0
            while x < ticks:
                y = 0
                while y < len(array):
                    seq = 0
                    while seq < len(array[y]):
                        if array[y][seq][2] <= x < array[y][seq][3] + array[y][seq][2]:
                            pos = array[y][seq][1] / array[y][seq][3]
                            self.servo_set(y, pos, 1)
                        seq += 1
                    y += 1
                time.sleep(0.1)
                x += 1
            z += 1
            
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

    def run(self):
#        global currentmovpossition
        global uptime
        global currentmovinitime
        global currentmovendtime
        global currentmovarraycalc
        global currenttimingarray
#        print uptime
        currentmovinitime = uptime
        currentmovarraycalc = [] 
        currenttimingarray = [] # array of 
        array = currentmovarray
#        ticks = currentmovticks
        speed = currentmovspeed
#        divider = 20
        timer = 0
#        print (array)
        z = 0
        while z < loopamount: # amount of loops 
            y = 0
            #send_to_all_clients("006;" + str(ticks - 1) + ";" + str(y))
            while y < (len(array)):
                if z == loopamount - 1:
                    w = 0
                else:
                    w = 1
                divider = array[y][20]/2
                tempmovpossition = y
                x = 0
#                while x <= devider: #stop using fixed devider make chunks of 10ms to inject in loop
                while w <= divider:
#                    print divider
                    temparray = []
                    seq = 0
                    while seq < (len(array[y])):
                        if y == (len(array))-1: #this sets the movement after the last possition to reset the loop to possition 0
                            if array[y][seq] == array[0][seq]:
                                temparray.append(array[y][seq])
                            elif array[y][seq] is None:
                                temparray.append(array[0][seq])
                            elif array[0][seq] is None:
                                temparray.append(array[y][seq])
                            else: 
                                temparray.append(int(array[y][seq]-((array[y][seq]-array[0][seq])*(x/divider))))
                        else:
                            if array[y][seq] == array[y + 1][seq]:
                                temparray.append(array[y][seq])
                            elif array[y][seq] is None:
                                temparray.append(array[y + 1][seq])
                            elif array[y + 1][seq] is None:
                                temparray.append(array[y][seq])
                            else: 
                                temparray.append(int(array[y][seq]-((array[y][seq]-array[y+1][seq])*(x/divider))))
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
                    w += 1
#                    time.sleep(0.02)
#                    print (temparray)
#                    print (currentmovarraycalc)
                y += 1
            z += 1
        currentmovendtime = currentmovinitime + timer
#        myInt = 10
#        currenttimingarray = [x / myInt for x in currenttimingarray]
#        print currentmovendtime
#        print (currenttimingarray)
        print (currentmovarraycalc)
    
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
#        pwm.setPWMFreq(60)                       # Set frequency to 60 Hz
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

_SHUTDOWN_TIMEOUT = 5

clients = []

def robotUpdate():
    global currentmovpossition
    global uptime
    global currentmovinitime
    global currentmovendtime
    global currentmovarraycalc
    global currenttimingarray
    global currentservo
    uptime = uptime + 10
    supdate = 200 #ms
    if uptime >= currentmovinitime and uptime < currentmovendtime:
        index = currenttimingarray.index(int(math.floor((uptime - currentmovinitime)/supdate))*supdate + supdate)
#        print currentmovarraycalc[index][currentservo]
        if str(currentmovarraycalc[index][0][currentservo]) != "None":
            m.servo_set(currentservo, currentmovarraycalc[index][0][currentservo], 0)
#            print currentservo
            print currentmovarraycalc[index][0][currentservo]
            pass
        currentservo = currentservo + 1
        if currentservo == 19:
            currentservo = 0
    
#    print uptime
#    print currentservo
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
            db.editStepQuery(command)
            print "step: %d position: %s" % (channel, command)
        if channel == 151:  # Add step 
            db.addStepQuery(command)
            self.write_message("Insert new step behind current posistion")
            print "command nr: %d value: %s" % (channel, command)
        if channel == 152:  # Delete step
            db.delStepQuery(command)
            self.write_message("Delete current step")
            print "step: %d position: %d" % (channel, int(command))
        if channel == 153:  # Add a new motion
            db.newMovQuery(command)
            self.write_message("Add a new motion")
            print "step: %d position: %s" % (channel, command)
        if channel == 154:  # Delete current motion
            db.delMovQuery(int(command))
            self.write_message("Delete current motion")
            print "step: %d position: %d" % (channel, int(command))
        if channel == 155:  # Populate movement list
            db.setupNewClient(self)
            self.write_message("Populating movmlist")
            print "step: %d position: %d" % (channel, int(command))
        if channel == 156:  # Set movement list
            db.setMovQuery(command)
            self.write_message("Setting movmlist")
            print "command: %d set movement list: %s" % (channel, command)
        if channel == 157:  # Set movement list
            db.editMovQuery(command)
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
            (r"/js/(.*)", tornado.web.StaticFileHandler, {"path": "./js"},),
            (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "./css"},)
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
    
    

