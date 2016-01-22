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
 

# Initialise the PWM device using the default address
pwm = PWM(0x42)

# Globals
currentmovarray = "ns"
currentmovid = "ns"
currentmovticks = 0
currentmovpossition = "ns"
loopamount = 1


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
            speed      INTEGER
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
            FOREIGN KEY(movid) REFERENCES movement(id)
        )''')
        cursor.execute('''SELECT * FROM movement ORDER BY id ASC''')
        data = cursor.fetchall()
        
        for row in data:
            id = str(row[0])
            while len(id) != 3:
                id = "0" + id
            name = row[1]
            send_to_all_clients("003%s%s" % (id, name))
        self.db.commit()
        cursor.close()
        
    def setMovArray(self,command): #this also creates a new steptable
        global currentmovarray 
        global currentmovid
        global currentmovticks
        movid = int(command[:3])
        cursor = self.db.cursor()
        print (movid)
        cursor.execute('''SELECT s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19 FROM steps WHERE movid=? ORDER BY steppos ASC''', (movid,))
        movdata = cursor.fetchall()
        print(movdata)
        currentmovarray = movdata
        currentmovid = movid
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
            #self.setMovQuery(str(curdata[0]))#Dit moet weg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            if currentmovpossition == "ns":
                currentmovpossition = 0
            cursor.execute('''SELECT * FROM steps WHERE movid=? ORDER BY steppos ASC''', (currentmovid,))
            movdata = cursor.fetchall()
            pref = "000"[len(str(len(movdata) - 1)):] + str(len(movdata) - 1) + "000"[len(str(currentmovpossition)):] + str(currentmovpossition)
            send_to_all_clients("006%s" % (pref))
            if currentmovarray == "ns":
                self.setMovArray(str(curdata[0]))
            m.servo_update_all_sliders()
            
    def setMovQuery(self,command): #sets movlist 
        global currentmovpossition
        global currentmovid
        movid = int(command[:3])
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM steps WHERE movid=? ORDER BY steppos ASC''', (movid,))
        movdata = cursor.fetchall()
        #newpos = self.getservopos(movid, "s1" ,0)
        pref = "000"[len(str(len(movdata) - 1)):] + str(len(movdata) - 1) + "000"
        send_to_all_clients("006%s" % (pref))
        self.setMovArray(command)
        currentmovid = movid
        currentmovpossition = 0
        array = currentmovarray
        d = 0
        while d < len(array[0]):
            pos = array[0][d]
            if str(pos) != "None":
                print str(pos)
                m.servo_set(d, pos, 0)
            d += 1
        #m.servo_set(currentmovpossition, newpos, 0)
        cursor.execute('''SELECT * FROM movement WHERE id=? ''', (movid,))
        movdata = cursor.fetchone()
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
        
    def newMovQuery(self,movname): #this also creates a new steptable
        global currentmovpossition
        cursor = self.db.cursor()
        cursor.execute('''INSERT INTO movement (name) VALUES (?)''', (movname,))
        cursor.execute('''SELECT id FROM movement WHERE name=?''', (movname,))
        movid = cursor.fetchone()
        movid = (movid[0])
        cursor.execute('''INSERT INTO steps (movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13 ) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
        , (movid, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        m.servo_reset()
        m.servo_reset_sliders()
        #cursor.execute('''SELECT id, name  WHERE name=?''', (movname))
        cursor.execute('''SELECT * FROM movement ORDER BY id ASC''')
        #data = cursor.fetchone()
        data = cursor.fetchall()
        i = 0
        for row in data:
        # Remove movement from list
            id = str(row[0])
            while len(id) != 3:
                id = "0" + id
            name = row[1]
            send_to_all_clients("004%s%s" % (id, name))
        for row in data:
        # Add to movement list
            i = i + 1
            id = str(row[0])
            while len(id) != 3:
                id = "0%s" % (id)
            name = row[1]
            send_to_all_clients("003%s%s" % (id, name))
            if len(data) == i:
                send_to_all_clients("005%s%s" % (id, name))
        print(data)
        send_to_all_clients("006%s" % ("000000"))
        currentmovpossition = 0
        print('New movement created')
        self.db.commit()
        self.setMovArray(id)
        
    def delMovQuery(self,movid): #must remove coresponding steptable
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
            self.setMovArray(id)
            
    def editMovQuery(self,movid,newname): #steptable remains unchanged
        cursor = db.cursor()
        # Insert user 1
        cursor.execute('''UPDATE movement SET name=? WHERE id=? ''', (newname, movid,))
        self.db.commit()
        print('Movement query edited')
        
    def addStepQuery(self,command):
        global currentmovpossition 
        movid = int(command[:3])
        steppos = (int(command[3:]) + 1)
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
                posdata = cursor.fetchone()
                cursor.execute('''INSERT INTO steps (movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19 ) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                #, (movid, steppos, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
                , (posdata[1:]))
            k = k - 1
        print (data)
        self.db.commit()
        id = "000"[len(str(i - 1)):] + str(i - 1)
        #pref = "000"[len(str(i)):] + str(i) + "000"[len(str(steppos)):] + str(steppos)
        pref = id + "000"[len(str(steppos)):] + str(steppos)
        send_to_all_clients("006%s" % (pref))
        currentmovpossition = steppos
        print('New step inserted')
        self.setMovArray(command)

    def delStepQuery(self,command):
        global currentmovpossition
        movid = int(command[:3])
        steppos = int(command[3:])
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
            id = "000"[len(str(i - 2)):] + str(i - 2)
            pref = id + "000"[len(str(steppos - 1)):] + str(steppos - 1)
            send_to_all_clients("006%s" % (pref))
            currentmovpossition = (steppos - 1)
            print('Step deleted')
            self.setMovArray(command)

    def editStepQuery(self,command):
        movid = int(command[:3])
        id = (command[:3])
        array = map(int, (command[4:]).split('a'))
        s1 = array[0]
        s2 = array[1]
        s3 = array[2]
        s4 = array[3]
        s5 = array[4]
        s6 = array[5]
        s7 = array[6]
        s8 = array[7]
        s9 = array[8]
        s10 = array[9]
        cursor = self.db.cursor()
        cursor.execute('''UPDATE steps SET s1 = ?, s2 = ?, s3 = ?, s4 = ?, s5 = ?, s6 = ?, s7 = ?, s8 = ?, s9= ?, s10 = ?, s11 = ?, s12= ?, s13 = ? WHERE steppos = ? AND movid = ?''',
        (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, 0, 0, 0, currentmovpossition, movid,))
        cursor.execute('''SELECT * FROM steps WHERE movid=?''', (movid,))
        data = cursor.fetchall()
        print (data)
        print('Step query edited')
        self.db.commit()
        self.setMovArray(command)

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
        ["servo00", 368, 368],  # Foot right
        ["servo01", 380, 380],  # Foot left
        ["servo02", 531, 531],  # Leg right bottom
        ["servo03", 479, 479],  # Leg left bottom
        ["servo04", 348, 348],  # Leg right mid
        ["servo05", 374, 374],  # Leg left mid
        ["servo06", 528, 528],  # Leg right top
        ["servo07", 260, 260],  # Leg left top
        ["servo08", 380, 380],  # Hip right
        ["servo09", 485, 485],  # Hip left
        ["servo10", 375, 375],
        ["servo11", 375, 375],
        ["servo12", 375, 375],
        ["servo13", 375, 375],
        ["servo14", 375, 375],
        ["servo15", 304, 304]  # Rotate camera
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
        while d < len(array[currentpos]):
            pos = array[currentpos][d]
            if str(pos) != "None":
                mes = "002" + motion.servoset[d][0] + "%d" % (pos)
                send_to_all_clients(mes)
            d += 1
    
    def servo_update_slider(self, channel, curpos, newpos):
        if curpos != newpos:
            mes = "002" + motion.servoset[channel][0] + "%d" % (newpos)
            send_to_all_clients(mes)
    
    def servo_reset_sliders(self):
        global currentmovpossition
        send_to_all_clients("002" + "servo20" + "0")
        send_to_all_clients("006%s" % ("999000"))
        currentmovpossition = 0
        motion.walkpos = 0
    
    def servo_set(self, channel, pos, incr):
        pwm.setPWMFreq(60)
        curpos = motion.servoset[channel][2] - motion.servoset[channel][1]
        if incr == 1:
            motion.servoset[channel][2] = motion.servoset[channel][2] + pos
        else:
            motion.servoset[channel][2] = motion.servoset[channel][1] + pos
        newpos = motion.servoset[channel][2] - motion.servoset[channel][1]
        pwm.setPWM(channel, 0, int(motion.servoset[channel][2]))
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
        while d < len(array[nextpos]):
            pos = array[nextpos][d]
            if str(pos) != "None" and pos != array[currentpos][d]:
                print ("inloop")
                self.servo_set(d, pos, 0)
            d += 1
        currentmovpossition = nextpos
        pref = "000"[len(str(len(array) - 1)):] + str(len(array) - 1) + "000"[len(str(nextpos)):] + str(nextpos)
        send_to_all_clients("006%s" % (pref))

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

clients = []


def send_to_all_clients(msg):
    for client in clients:
        client.write_message(msg)
        
def send_to_evoking_client(client, msg):
        client.write_message(msg)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print 'new connection'
        send_to_all_clients("new client")
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
            print "channel: %d loopamount: %d" % (channel, int(command))
        if channel == 122:
            db.setmovspeed( int(command), 0)
            print "channel: %d speed: %d" % (channel, int(command))
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
        if channel == 140:  # walk possition slider
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
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(options.port)
    print "Listening on port:", options.port
    tornado.ioloop.IOLoop.instance().start()
