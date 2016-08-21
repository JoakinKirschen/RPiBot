import sqlite3
import os

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
#        for row in data:
#            id = str(row[0])
#            while len(id) != 3:
#                id = "0" + id
#            name = row[1]
#            send_to_all_clients("003%s%s" % (id, name))
        self.db.commit()
        cursor.close()
        print ("Tables created")
        
    def getMovList (self):
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM movement ORDER BY id ASC''')
        data = cursor.fetchall()
        return data
        
    def getMovQuery(self, movid):
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM movement WHERE id=? ''', (movid,))
        curdata = cursor.fetchone()
        return curdata
        
    def delMovQuery(self, movid):
        cursor = self.db.cursor()
        cursor.execute('''DELETE FROM movement WHERE id = ? ''', (movid,))
        cursor.execute('''DELETE FROM steps WHERE movid = ? ''', (movid,))
        self.db.commit()
    
    def editMovQuery(self, newname, mspeed, movid):
        cursor = self.db.cursor()
        cursor.execute('''UPDATE movement SET name=?, movspeed=? WHERE id=? ''', (newname, mspeed, movid,))
        self.db.commit()
        
    def getservopos(self, movid, servonr, pos):
        servonr = int(servonr[1:])
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM steps WHERE movid = ? AND steppos = ? ORDER BY steppos ASC''', (movid, pos,))
        Ival = cursor.fetchone()
        Ival = Ival[servonr + 2]
        print (Ival) 
        return Ival

    def addMovQuery(self,movname,movspeed):
        cursor = self.db.cursor()
        cursor.execute('''INSERT INTO movement (name, movspeed) VALUES (?, ?)''', (movname, movspeed))
        cursor.execute('''SELECT id FROM movement WHERE id=?''', ((cursor.lastrowid),))
        movid = cursor.fetchone()
        self.db.commit()
        return movid

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
        
    def getStepQuery(self, movid):
        cursor = self.db.cursor()
        cursor.execute('''SELECT * FROM steps WHERE movid=? ORDER BY steppos ASC''', (movid,))
        stepsdata = cursor.fetchall()
        return stepsdata
    
    def getStepQuery2(self, movid):
        cursor = self.db.cursor()
        cursor.execute('''SELECT s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20, stepspeed FROM steps WHERE movid=? ORDER BY steppos ASC''', (movid,))
        stepsdata = cursor.fetchall()
        return stepsdata
        
    def addStepQuery(self, movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, stepspeed):
        cursor = self.db.cursor()
        cursor.execute('''INSERT INTO steps (movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, stepspeed ) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
        , (movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, stepspeed))
        self.db.commit()
        
    def addStepQuery2 (movid,steppos,stepsdata):
        cursor = self.db.cursor()
        k = (len(stepsdata) + 1)
        while k >= steppos:
            cursor.execute('''UPDATE steps SET steppos = ? WHERE steppos = ? AND movid = ?''', ((k + 1), k, movid,))
            if k == steppos:
                cursor.execute('''SELECT * FROM steps WHERE movid=? AND steppos=?''', (movid, (steppos - 1)))
                posdata = list(cursor.fetchone())
                posdata[1] = movid
                posdata[2] = steppos
                cursor.execute('''INSERT INTO steps (movid, steppos, s1, s2, s3, s4, s5, s6, s7, s8, 
                s9, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20, stepspeed ) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                #, (movid, steppos, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
                , (posdata[1:]))
            k = k - 1
        self.db.commit()
        
    def delStepQuery(self, movid, steppos, stepsdata):
        cursor = self.db.cursor()
        j = steppos
        i = len(stepsdata)
        while j <= i:
            if j == steppos:
                cursor.execute('''DELETE FROM steps WHERE steppos = ?  AND movid = ?''', (j, movid,))
                #cursor.execute('''DELETE FROM users WHERE id = ? ''', (delete_userid,))
                self.db.commit()
            cursor.execute('''UPDATE steps SET steppos = ? WHERE steppos = ?  AND movid = ?''', ((j - 1), j, movid,))
            j = j + 1
        self.db.commit()
        #print (data)
        
    def editStepQuery(self, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, stepspeed, currentmovpossition, movid):
        cursor = self.db.cursor()
        cursor.execute('''UPDATE steps SET s1 = ?, s2 = ?, s3 = ?, s4 = ?, s5 = ?, s6 = ?, s7 = ?, s8 = ?,
        s9= ?, s10 = ?, s11 = ?, s12= ?, s13 = ?, stepspeed = ? WHERE steppos = ? AND movid = ?''',
        (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, stepspeed, currentmovpossition, movid,))
        self.db.commit()

    def closedb(self):
        db.close()
