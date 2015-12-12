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


# Initialise the PWM device using the default address
pwm = PWM(0x42)


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
            time.sleep(0.02)
            x += 1
        x = 0
        while x < len(motion.servoset):
            self.servo_set(x, 0, 0)
            print "Loop trough %d" % x
            x += 1
            time.sleep(0.02)



m = motion()

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
        pos = int(message[3:])
        if channel < 16:
            m.servo_set(channel, pos, 0)
            print "channel: %d angle: %d" % (channel, pos)
        if channel == 20:
            m.g_left_right(pos, 0)
            print "channel: %d angle: %d" % (channel, pos)
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
            m.servo_slider(pos,1)
            print "step: %d position: %d" % (channel, pos)

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
