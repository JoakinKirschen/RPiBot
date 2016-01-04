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
            name   TEXT
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
        
    def popMovQuery(self): #initialize the movement menu
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM movement ORDER BY id ASC''')
        #data = cursor.fetchone()
        data = cursor.fetchall()
        for row in data:
            id = str(row[0])
            while len(id) != 3:
                id = "0%s" % (id)
            name = row[1]
            send_to_all_clients("003%s%s" % (id, name))
        cursor.execute('''SELECT * FROM movement ORDER BY ROWID ASC LIMIT 1''')
        data = cursor.fetchone()
        if data:
            send_to_all_clients("005%s%s" % (str(data[0]), data[1]))
        
        
    def newMovQuery(self,movname): #this also creates a new steptable
        cursor = self.db.cursor()
        cursor.execute('''INSERT INTO movement (name) VALUES (?)''', (movname,))
        cursor.execute('''SELECT id FROM movement WHERE name=?''', (movname,))
        movid = cursor.fetchone()
        cursor.execute
        ('''INSERT INTO steps (movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13 ) VALUES (?)'''
        , (movid, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,))
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
        print('New movement created')
        self.db.commit()
        
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
            id = str(data[0])
            name = data[1]
            while len(id) != 3:
                    id = "0%s" % (id)
            # Remove movement from list
            send_to_all_clients("004%s%s" % (id, name))
            print('Movement query removed')
            self.db.commit()
            cursor.execute('''SELECT * FROM movement ORDER BY ROWID ASC LIMIT 1''')
            data = cursor.fetchone()
            send_to_all_clients("005%s%s" % (str(data[0]), data[1]))
        
    def editMovQuery(self,movid,newname): #steptable remains unchanged
        cursor = db.cursor()
        # Insert user 1
        cursor.execute('''UPDATE movement SET name=? WHERE id=? ''', (newname, movid,))
        print('Movement query edited')
        db.commit()
        
    def addStepQuery(self,command):
        movid = int(command[:3])
        steppos = (int(command[3:]) + 1)
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM steps WHERE movid=?''', (movid,))
        data = cursor.fetchall()
        i = (len(data) + 1)
        k = i
        print (i)
        print (steppos)
        while k >= steppos:
            cursor.execute('''UPDATE steps SET steppos = ? WHERE steppos = ? ''', ((k + 1), k,))
            if k == steppos:
                cursor.execute('''INSERT INTO steps (movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13 ) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                , (movid, steppos, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
            k = k - 1
        print (data)
        self.db.commit()
        pref = "000"[len(str(i)):] + str(i) + "000"[len(str(steppos)):] + str(steppos)
        send_to_all_clients("006%s" % (pref))
        print('New step inserted')

    def delStepQuery(self,command):
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
                    cursor.execute('''DELETE FROM steps WHERE steppos = ? ''', (j,))
                    #cursor.execute('''DELETE FROM users WHERE id = ? ''', (delete_userid,))
                    self.db.commit()
                cursor.execute('''UPDATE steps SET steppos = ? WHERE steppos = ? ''', ((j - 1), j,))
                j = j + 1
            print (data)
            self.db.commit()
            pref = "000"[len(str(i - 1)):] + str(i - 1) + "000"[len(str(steppos - 1)):] + str(steppos - 1)
            send_to_all_clients("006%s" % (pref))
            print('Step deleted')


    def editStepQuery(self,command):
        movid = int(command[:3])
        s1 = int(command[4:8])
        s2 = int(command[8:12])
        s3 = int(command[12:16])
        s4 = int(command[16:20])
        s5 = int(command[20:24])
        s6 = int(command[24:28])
        s7 = int(command[28:32])
        s8 = int(command[32:36])
        s9 = int(command[36:40])
        s10 = int(command[40:44])
        cursor = self.db.cursor()
        cursor.execute('''UPDATE steps SET (movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13 )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) WHERE steppos = ? '''
        , (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, steppos,))
        print('Step query edited')
        self.db.commit()        

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
        ["servo02", 499, 499],  # Leg right bottom
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

    servomov1 = [
            # servo0 Foot right:
            [[0, 40, 0, 5], [0, -40, 5, 5], [0, 0, 5, 0],
            [0, -40, 10, 5], [0, 40, 15, 5], [0, 0, 15, 0]],
            # servo1 Foot left:
            [[0, 40, 0, 5], [0, -40, 5, 5], [0, 0, 5, 0],
            [0, -40, 10, 5], [0, 40, 15, 5], [0, 0, 15, 0]],
            # servo2 Leg right bottom:
            [[0, 0, 0, 5], [0, 0, 5, 5], [0, 0, 5, 0],
            [0, 15, 10, 5], [0, -15, 15, 5], [0, 0, 15, 0]],
            # servo3 Leg left bottom:
            [[0, 0, 0, 5], [0, -15, 5, 5], [0, 0, 5, 0],
            [0, 15, 10, 5], [0, 0, 15, 5], [0, 0, 15, 0]],
            # servo4 Leg right middle:
            [[0, 60, 0, 5], [0, -60, 5, 5], [0, 0, 5, 0],
            [0, 0, 10, 5], [0, 0, 15, 5], [0, 0, 15, 0]],
            # servo5 Leg left middle:
            [[0, 0, 0, 5], [0, 0, 5, 5], [0, 0, 5, 0],
            [0, -60, 10, 5], [0, 60, 15, 5], [0, 0, 15, 0]],
            # servo6 Leg right top:
            [[0, 130, 0, 5], [0, -130, 5, 5], [0, 0, 5, 0],
            [0, 0, 10, 5], [0, 0, 15, 5], [0, 0, 15, 0]],
            # servo7 Leg left top:
            [[0, 0, 0, 5], [0, 0, 5, 5], [0, 0, 5, 0],
            [ 0, -130, 10, 5], [0, 130, 15, 5], [0, 0, 15, 0]],
            # servo8 Hip right:
            [[0, 22, 0, 2], [0, -22, 5, 5], [0, 0, 5, 0],
            [0, -22, 10, 2], [0, 22, 15, 5], [0, 0, 15, 0]],
            # servo9 Hip left:
            [[0, 22, 0, 2], [0, -22, 5, 5], [0, 0, 5, 0],
            [0, -22, 10, 2], [0, 22, 15, 5], [0, 0, 15, 0]]
    ]

    servomov2 = [
            # servo0 Foot right:
            [[0, 40, 0, 5], [0, -40, 5, 5], [0, 0, 5, 0],
            [0, -40, 10, 5], [0, 40, 15, 5], [0, 0, 15, 0]],
            # servo1 Foot left:
            [[0, 40, 0, 5], [0, -40, 5, 5], [0, 0, 5, 0],
            [0, -40, 10, 5], [0, 40, 15, 5], [0, 0, 15, 0]],
            # servo2 Leg right bottom:
            [[0, 0, 0, 5], [0, 0, 5, 5], [0, 0, 5, 0],
            [0, 15, 10, 5], [0, -15, 15, 5], [0, 0, 15, 0]],
            # servo3 Leg left bottom:
            [[0, 0, 0, 5], [0, -15, 5, 5], [0, 0, 5, 0],
            [0, 15, 10, 5], [0, 0, 15, 5], [0, 0, 15, 0]],
            # servo4 Leg right middle:
            [[0, 60, 0, 5], [0, -60, 5, 5], [0, 0, 5, 0],
            [0, 0, 10, 5], [0, 0, 15, 5], [0, 0, 15, 0]],
            # servo5 Leg left middle:
            [[0, 0, 0, 5], [0, 0, 5, 5], [0, 0, 5, 0],
            [0, -60, 10, 5], [0, 60, 15, 5], [0, 0, 15, 0]],
            # servo6 Leg right top:
            [[0, 130, 0, 5], [0, -130, 5, 5], [0, 0, 5, 0],
            [0, 0, 10, 5], [0, 0, 15, 5], [0, 0, 15, 0]],
            # servo7 Leg left top:
            [[0, 0, 0, 5], [0, 0, 5, 5], [0, 0, 5, 0],
            [ 0, -130, 10, 5], [0, 130, 15, 5], [0, 0, 15, 0]],
            # servo8 Hip right:
            [[0, 22, 0, 2], [0, -22, 5, 5], [0, 0, 5, 0],
            [0, -22, 10, 2], [0, 22, 15, 5], [0, 0, 15, 0]],
            # servo9 Hip left:
            [[0, 22, 0, 2], [0, -22, 5, 5], [0, 0, 5, 0],
            [0, -22, 10, 2], [0, 22, 15, 5], [0, 0, 15, 0]]
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
    
    
    ticks1 = servomov_ticks(servomov1)
    ticks2 = servomov_ticks(servomov2)
    
    def servo_update_slider(self, channel, curpos, newpos):
        if curpos != newpos:
            mes = "002" + motion.servoset[channel][0] + "%d" % (newpos)
            send_to_all_clients(mes)
    
    def servo_reset_sliders(self):
        send_to_all_clients("002" + "servo20" + "0")
        send_to_all_clients("006%s" % ("999000"))
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
    def servo_walk(self, speed, patern):
        if patern == 1:
            array = motion.servomov1
            tick = motion.ticks1
        if patern == 2: 
            array = motion.servomov2
            tick = motion.ticks2
        z = 0
        while z < 2:
            x = 0
            while x < tick:
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
    def servo_slider(self, nextpos, patern):
        b = 0
        c = 0
        if patern == 1:
            array = motion.servomov1
            tick = motion.ticks1
        if patern == 2: 
            array = motion.servomov2
            tick = motion.ticks2
        if nextpos == 0 and motion.walkpos == 20:
            motion.walkpos = 0
        if nextpos == 20 and motion.walkpos == 0:
            motion.walkpos = 20
        if motion.walkpos < nextpos:
            a = 1
            b = motion.walkpos
            c = nextpos
        elif motion.walkpos > nextpos:
            a = -1
            b = nextpos
            c = motion.walkpos
        print nextpos
        print motion.walkpos
            
        while b < c:
            d = 0
            while d < len(array):
                seq = 0
                while seq < len(array[d]):
                    if array[d][seq][2] <= b < array[d][seq][3] + array[d][seq][2]:
                        pos = (array[d][seq][1] / array[d][seq][3]) * a
                        self.servo_set(d, pos, 1)
                    seq += 1
                d += 1
            # time.sleep(0.1)
            b += 1
            motion.walkpos = nextpos
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
        self.write_message(message)
        channel = int(message[0:3])
        command = (message[3:])
        if channel < 16:
            m.servo_set(channel, int(command), 0)
            print "channel: %d angle: %d" % (channel, int(command))
        if channel == 20:
            m.g_left_right( int(command), 0)
            print "channel: %d angle: %d" % (channel, int(command))
        if channel == 30:
            self.write_message("reset")
            m.servo_reset()
            m.servo_reset_sliders()
        if channel == 31:  # walk function from commandline hier gebleven
            self.write_message("walking")
            m.servo_walk(100,1)
        if channel == 32:  # walk function from commandline hier gebleven
            self.write_message("walking")
            m.servo_walk(100,2)
        if channel == 40:  # walk possition slider
            self.write_message("walking")
            m.servo_slider(int(command),1)
            print "step: %d position: %d" % (channel, int(command))
        if channel == 50:  # walk possition slider
            self.write_message("saving current positions")
            #m.servo_slider(pos)
            print "step: %d position: %s" % (channel, command)
        if channel == 51:  # add step 
            db.addStepQuery(command)
            self.write_message("Insert new step behind current posistion")
            #m.servo_slider(pos)
            print "command nr: %d value: %s" % (channel, command)
        if channel == 52:  # Delete step
            db.delStepQuery(command)
            self.write_message("Delete current step")
            #m.servo_slider(pos)
            print "step: %d position: %d" % (channel, int(command))
        if channel == 53:  # Add a new motion
            db.newMovQuery(command)
            self.write_message("Add a new motion")
            #m.servo_slider(pos)
            print "step: %d position: %s" % (channel, command)
        if channel == 54:  # Delete current motion
            db.delMovQuery(int(command))
            self.write_message("Delete current motion")
            #m.servo_slider(pos)
            print "step: %d position: %d" % (channel, int(command))
        if channel == 55:  # Populate movement list
            db.popMovQuery()
            self.write_message("Populating movmlist")
            #m.servo_slider(pos)
            print "step: %d position: %d" % (channel, int(command))

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
