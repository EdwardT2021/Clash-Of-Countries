import socket
import threading
import sqlite3
import sys
import random
import ServerErrors as e
import json 
import rsa
from hashlib import sha256

AUTH = str(sha256("121212".encode("ascii"), usedforsecurity=True).digest()) #Authentication code for network transmissions

#The following hash is not cryptographically secure, and should only be used to compare objects
def Hash(string: str) -> int:
    hashnum = 0
    for s in string:
        hashnum = (hashnum*607 ^ ord(s)*409) & 0xFFFFFFFF
    return hashnum


class Buff:
    "Base class for Buffs"
    def __init__(self, statAffected: str, linear: bool, change: int):
        self.statAffected = statAffected
        self.linear = linear
        self.multiplicative = not self.linear
        self.change = change

    def __hash__(self) -> str:
        "Simple hashing function for the class. No other unique buff will have this combination string" 
        return Hash(f"{self.change}{self.statAffected}{self.linear}")
    
    def __repr__(self) -> str:
        return self.__class__.__name__[:-4]

class LinearBuff(Buff):
    "Subclass of buff for additive changes, ie +5"
    def __init__(self, statAffected: str, change: int):

        super(LinearBuff, self).__init__(statAffected, True, change)
    
class MultiplicativeBuff(Buff):
    "Subclass of buff for multiplicative changes, ie *1.5 (also viewed as +50%)"
    def __init__(self, statAffected: str, change: int):

        super(MultiplicativeBuff, self).__init__(statAffected, False, change)

class MinorBuff(Buff):
    "Subclass for minor buffs"


class MajorBuff(Buff):
    "Subclass for major buffs"

class ProductionBuff(LinearBuff):
    "Subclass for Production buffs, inherits from Linear as all production changes should be additive"
    def __init__(self, change: int):

        super(ProductionBuff, self).__init__("Production", change)

class MinorProductionBuff(ProductionBuff, MinorBuff):
    "Subclass for Minor Production Buffs that inherits from ProductionBuff and MinorBuff. +2 increases"
    def __init__(self):

        super(MinorProductionBuff, self).__init__(2)

class MajorProductionBuff(ProductionBuff, MajorBuff):
    "Subclass for Major Production Buffs that inherits from ProductionBuff and MajorBuff. +4 increase"
    def __init__(self):
        
        super(MajorProductionBuff, self).__init__(4)

class TownsBuff(LinearBuff):
    "Subclass for Town buffs, inherits from Linear as all town changes should be additive"
    def __init__(self, change: int):

        super(TownsBuff, self).__init__("Towns", change)

class MinorTownsBuff(TownsBuff, MinorBuff):
    "Subclass for Minor Towns Buffs that inherits from TownsBuff and MinorBuff. +5 increase"
    def __init__(self):

        super(MinorTownsBuff, self).__init__(5)

class MajorTownsBuff(TownsBuff, MajorBuff):
    "Subclass for Major Towns Buffs that inherits from TownsBuff and MajorBuff. +10 increase"
    def __init__(self):

        super(MajorTownsBuff, self).__init__(10)

class FortificationBuff(LinearBuff):
    "Subclass for Fortification Buffs, inherits from Linear as all fortification changes should be additive"
    def __init__(self, change: int):

        super(FortificationBuff, self).__init__("Fortifications", change)

class MinorFortificationBuff(FortificationBuff, MinorBuff):
    "Subclass for Minor Fortification Buffs that inherits from FortificationBuff and MinorBuff. +1 increase"
    def __init__(self):

        super(MinorFortificationBuff, self).__init__(1)

class MajorFortificationBuff(FortificationBuff, MajorBuff):
    "Subclass for Major Fortification Buffs that inherits from FortificationBuff and MajorBuff. +2 increase"
    def __init__(self):
        
        super(MajorFortificationBuff).__init__(2)

class AttackBuff(MultiplicativeBuff):
    "Subclass for Attack Buffs, inherits from Multiplicative as all attack changes should be multiplicative"
    def __init__(self, change: int):
        
        super(AttackBuff, self).__init__("Attack", change)

class MinorAttackBuff(AttackBuff, MinorBuff):
    "Subclass for Minor Attack Buffs, inherits from AttackBuff and MinorBuff. 10% increase"
    def __init__(self):
        
        super(MinorAttackBuff, self).__init__(1.1)

class MajorAttackBuff(AttackBuff, MajorBuff):
    "Subclass for Major Attack Buffs, inherits from AttackBuff and MajorBuff. 20% increase"
    def __init__(self):
        
        super(MajorAttackBuff, self).__init__(1.2)

class SiegeAttackBuff(MultiplicativeBuff):
    "Subclass for Siege Attack Buffs, inherits from Multiplicative as all siege attack changes should be multiplicative"
    def __init__(self, change: int):

        super(SiegeAttackBuff, self).__init__("SiegeAttack", change)

class MinorSiegeAttackBuff(SiegeAttackBuff, MinorBuff):
    "Subclass for Minor Siege Attack Buffs, inherits from SiegeAttackBuff and MinorBuff. 10% increase"
    def __init__(self):

        super(MinorSiegeAttackBuff, self).__init__(1.1)

class MajorSiegeAttackBuff(SiegeAttackBuff, MajorBuff):
    "Subclass for Major Siege Attack Buffs, inherits from SiegeAttackBuff and MajorBuff. 20% increase"
    def __init__(self):

        super(MajorSiegeAttackBuff, self).__init__(1.2)

class DefenseBuff(MultiplicativeBuff):
    "Subclass for Defense Buffs, inherits from Multiplicative as all defense changes should be multiplicative"
    def __init__(self, change: int):
        
        super(DefenseBuff, self).__init__("Defense", change)

class MinorDefenseBuff(DefenseBuff, MinorBuff):
    "Subclass for Minor Defense Buffs, inherits from DefenseBuff and MinorBuff"
    def __init__(self):
        
        super(MinorDefenseBuff, self).__init__(1.1)

class MajorDefenseBuff(DefenseBuff, MajorBuff):
    "Subclass for Major Defense Buffs, inherits from DefenseBuff and MajorBuff. 20% increase"
    def __init__(self):
        
        super(MajorDefenseBuff, self).__init__(1.2)

class SiegeDefenseBuff(MultiplicativeBuff):
    "Subclass for Siege Defense Buffs, inherits from Multiplicative as all siege defense changes should be multiplicative"
    def __init__(self, change: int):

        super(SiegeDefenseBuff, self).__init__("SiegeDefense", change)

class MinorSiegeDefenseBuff(SiegeDefenseBuff, MinorBuff):
    "Subclass for Minor Siege Defense Buffs, inherits from SiegeDefenseBuff and MinorBuff"
    def __init__(self):

        super(MinorSiegeDefenseBuff, self).__init__(1.1)

class MajorSiegeDefenseBuff(SiegeDefenseBuff, MajorBuff):
    "Subclass for Major Siege Defense Buffs, inherits from SiegeDefenseBuff and MajorBuff. 20% increase"
    def __init__(self):

        super(MajorSiegeDefenseBuff, self).__init__(1.2)

class Country:
    "Base class for all countries"
    def __init__(self, production: int, towns: int, name: int):
        self.name = name
        self.production = production
        self.towns = towns
        self.type = str

    def __hash__(self) -> str:
        "Creates a unique hash for the country"
        return Hash(f"{self.name}{self.production}{self.towns}{self.type}")
    
    def ToList(self) -> list:
        return [self.name, self.towns, self.type, self.production]

class AggressiveCountry(Country):
    "Subclass of country for aggressive countries"
    def __init__(self, name: str, production: int, towns: int):
        super(AggressiveCountry, self).__init__(production, towns, name)
        self.type = "AGG"

class BalancedCountry(Country):
    "Subclass of country for balanced countries"
    def __init__(self, name: str, production: int, towns: int):
        super(BalancedCountry, self).__init__(production, towns, name)
        self.type = "BAL"

class DefensiveCountry(Country):
    "Subclass of country for defensive countries"
    def __init__(self, name: str, production: int, towns: int):
        super(DefensiveCountry, self).__init__(production, towns, name)
        self.type = "DEF"

class Player:

    def __init__(self, username, countries=[], prioritycountries=[], buffs=[], prioritybuffs=[], wins=0, losses=0, elo=0, socket=None, key=None):
        "Player object containing relevant player data"
        self.username = username #type: str
        self.countries = countries #type: list[Country]
        self.buffs = buffs #type: list[Buff]
        self.prioritycountries = prioritycountries #type: list[Country]
        self.prioritybuffs = prioritybuffs #type: list[Buff]
        self.wins = wins #type: int
        self.losses = losses #type: int
        self.elo = elo #type: int
        self.Battle = None
        self.enemy = None
        self.socket = socket #type: socket.socket
        self.key = key #type: rsa.PublicKey
    
    def __repr__(self) -> str:
        return self.username

class Battle:

    def __init__(self, player1: Player, player2: Player):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Socket specifying using the tcp/ip protocol
        self.__host = socket.gethostbyname(socket.gethostname()) #Server ip address
        self.__port = 11035 #Server port
        self.__socket.bind((self.__host, self.__port))
        self.__socket.listen() #Allows the socket to act like a server
        self.player1 = player1
        self.player1.enemy = player2
        self.player2 = player2
        self.player2.enemy = player1
        self.player1.Battle = self
        self.player2.Battle = self
        self.player1first = bool(random.randint(0, 1))   
        p1connected = False
        p2connected = False
        while not (p1connected and p2connected): #Waits for both players to connect
            try:
                player, address = self.__socket.accept()
                player.settimeout(1)
            except:
                continue
            if address[0] == self.player1.socket.getpeername()[0]:#Checks the player by comparing IP addresses
                self.p1socket = player
                p1connected = True
                print(f"{player1} connected")
            elif address[0] == self.player2.socket.getpeername()[0]:
                self.p2socket = player
                p2connected = True
                print(f"{player2} connected")

        SERVER.send("IP", self.p1socket, self.player1.key, self.player2.socket.getpeername()[0], self.player1first) #Sends player 2s IP address to player 1 and whether player 1 goes first
        key2 = self.player2.key.save_pkcs1("PEM")
        while SERVER.receive(self.p1socket)[0] != "RECEIVED": #Wait for confirmation
            continue
        self.p1socket.send(key2) #Sends player 2s public key to player 1
        SERVER.send("IP", self.p2socket, self.player2.key, self.player1.socket.getpeername()[0], not self.player1first) #Sends player 1s IP address to player 2 and whether player 2 goes first
        key1 = self.player1.key.save_pkcs1("PEM") #Get player 1s key
        while SERVER.receive(self.p2socket)[0] != "RECEIVED": #Waits for confirmation
            continue
        self.p2socket.send(key1) #Sends player 1s key to player 2
        print(f"Battle between {player1.username} and {player2.username} initialised!")
        self.p1socket.close() #Close the sockets
        self.p2socket.close()
        self.__socket.close()

class Thread(threading.Thread): #Custom class for threading

    def __init__(self, target: "function", *args):
        super(Thread, self).__init__(target=target, args=args)
        self.finished = False
    
    def start(self):
        super(Thread, self).start()
        return

class Server: #Class containing server methods and attributes

    def __init__(self):

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Socket specifying using the tcp/ip protocol
        self.__socket.settimeout(1)
        self.__host = socket.gethostbyname(socket.gethostname()) #Server ip address
        self.__port = 11034 #Server port
        self.__pubkey, self.__privkey = rsa.newkeys(2048)
        self.__CountryNames = [] #type: list[str]
        with open("countries.txt", "r") as f:
            for line in f.readlines():
                self.__CountryNames.append(line.strip())
        self.__socket.bind((self.__host, self.__port))
        self.__socket.listen() #Allows the socket to act like a server

        self.__serverThreads = [] #type: list[Thread] #Threads performing server tasks
        self.__handlerThreads = [] #type: list[Thread] #Threads handling players
        self.__battleThreads = [] #type: list[Thread]
        #Multiple pools to allow for multiple matchmakes at one time and to allow more fair matchmaking
        self.__pool1 = [] #type: list[Player] #Matchmaking pool for Elo 0-1000 inclusive
        self.__pool2 = [] #type: list[Player] #Matchmaking pool for Elo 1001-1500 inclusive
        self.__pool3 = [] #type: list[Player] #Matchmaking pool for Elo 1501-2000 inclusive
        self.__pool4 = [] #type: list[Player] #Matchmaking pool for Elo 2001-2400 inclusive

        self.__loggedInLock = threading.BoundedSemaphore(10000) #A lock allowing only 10000 users to be logged-in at once
        self.__databaseLock = threading.BoundedSemaphore(20) #A lock allowing a maximum of 10 database connections at a time
        self.__pool1Lock = threading.Lock() #Resource locks on the relevant matchmaking pools, to prevent players being put into battles more than once at a time.
        self.__pool2Lock = threading.Lock() 
        self.__pool3Lock = threading.Lock()
        self.__pool4Lock = threading.Lock()
        a = Thread(self.__accept)
        cht = Thread(self.__checkHandlerThreads)
        cht2 = Thread(self.__checkHandlerThreads)
        mtchmke = Thread(self.__matchmake)
        self.__serverThreads.append(a) #Adds a thread that accepts new connections
        self.__serverThreads.append(cht) #Adds a thread that checks handler threads are all running
        self.__serverThreads.append(cht2) #Adds a thread that checks handler threads are all running
        self.__serverThreads.append(mtchmke) #Adds a thread that goes through the matchmaking pool
        for thread in self.__serverThreads:
            thread.start()
        print(f"Server Live at {self.__host, self.__port}")

    def send(self, command: str, conn: socket.socket, key: rsa.PublicKey, *args): #Sends a message through a socket
        message = {"AUTH": AUTH, "Command": command, "Args": ()} #Creates dictionary containing the command and any arguments
        if args:
            message["Args"] = args
        print("sent", message)
        encMessage = json.dumps(message).encode("utf-8") #Converts dictionary into json and encodes it using utf-8
        conn.send(rsa.encrypt(encMessage, key)) #Sends the command through the socket
    
    def receive(self, conn: socket.socket) -> tuple[str, str]:
        try:
            data = conn.recv(2048)
        except Exception as e:
            if str(e) == socket.errorTab[10054] or str(e) == socket.errorTab[10053]: #If the socket has closed unexpectedly, tell the caller that the client disconnected
                return "DISCONNECT", None
            return None, None
        new = rsa.decrypt(data, self.__privkey) #Decrypt and load the message, check the authorization code
        data = json.loads(new.decode("utf-8"))
        command = data["Command"]
        args = data["Args"]
        if data["AUTH"] != AUTH:
            return False, False
        print(f"Received {command}: {args}")
        return command, args
        
    def __accept(self): #Accepts new connections
        print("Accepting Connections")
        while True: #Loops, waiting for connections
            try:
                client, address = self.__socket.accept()
            except:
                continue
            if address not in open("banlist.txt", "r"): #Checks if IP is banned
                print(f"Connection from {address} accepted!")
                t = Thread(self.__login, client, address)
                self.__handlerThreads.append(t) #Creates a new thread to handle the player

    def __checkHandlerThreads(self): #Checks threads are active and starts them if not, if thread finished it deletes them
        print("Handler threads monitor started")
        while True:
            for thread in self.__handlerThreads:
                if not thread.is_alive():
                    try:
                        thread.start()
                    except RuntimeError:
                        try:
                            self.__handlerThreads.remove(thread) #Thread not explicitly deleted as handled more efficiently by garbage collector
                                                                 #Threads can also change IDs which can cause the del() function to raise an error. I cannot find a solution to this
                        except:
                            pass

    def __login(self, client: socket.socket, address: str): #Login function
        with self.__loggedInLock: #Uses log in lock. If more than 10000 threads are using this, it will wait until a space is available
            failed = True
            while failed:
                try:
                    data = client.recv(4096)
                    servkey = self.__pubkey.save_pkcs1("PEM") #Attempts to get the server key and the client key then send the server key and load the client key
                    client.send(servkey)
                except:
                    continue
                key = rsa.PublicKey.load_pkcs1(data, "PEM")
                failed = False
            failed = True
            while failed:
                self.send("LOGIN", client, key) #Sends login request
                received = False
                while not received:
                    try:
                        command, info = self.receive(client) 
                        received = True
                        if command == False:
                            print("Unauthorized connection from ", client.getpeername()[0]) #If the receive function detected unauthorised request, break off the thread
                            break
                    except:
                        pass
                print(command, info, "received")
                if command == "SIGNUP": #Received if player wants a new account
                    username, password = info #Splits info into variables
                    try:
                        self.__signup(username, password)
                        failed = False
                        self.send("LOGGEDIN", client, key)
                    except e.NotUniqueUsernameError:
                        self.send("LOGINFAILED", client, key, "Username not unique!")
                    
                elif command == "LOGIN": #Attempts to connect to database and match the hashed passwords
                    username, password = info
                    with self.__databaseLock:
                        try:
                            conn = sqlite3.connect("playerData.sqlite3")
                            cur = conn.cursor()
                        except:
                            raise e.DatabaseAccessError
                        cur.execute(f"SELECT password FROM Player WHERE username = '{username}';")
                        try:
                            passwordDB = cur.fetchone()[0]
                        except:
                            self.send("LOGINFAILED", client, key)
                            conn.close()
                            sys.exit()
                    
                        if passwordDB == password:
                            failed = False
                            self.send("LOGGEDIN", client, key)
                            print(f"{address} logged in as {username}!")
                        else:
                            print(f"Login for {address} failed")
                        conn.close()
                    

            #Creates statement fetching player, country and buff info. Some data repitition, but necessary to quicken loading timess
            playerinfo = f"SELECT username, wins, losses, elo FROM Player WHERE username = '{username}';"
            prioritycinfo = f"SELECT name, production, towns, type FROM Country WHERE playerID = '{username}' AND priority = 1;"
            countryinfo = f"SELECT name, production, towns, type FROM Country WHERE playerID = '{username}';"
            prioritybinfo = f"SELECT type from Buff WHERE playerID = '{username}' AND priority = 1;"
            buffinfo = f"SELECT type from Buff WHERE playerID = '{username}';"
            with self.__databaseLock:
                try:
                    conn = sqlite3.connect("playerData.sqlite3")
                    cur = conn.cursor()
                except:
                    raise e.DatabaseAccessError
                cur.execute(playerinfo) #execute the statements and load the data
                pname, pwins, plosses, pelo = cur.fetchone()
                cur.execute(countryinfo)
                clist = []
                for country in cur.fetchall():
                    subclass = country[3]
                    if subclass == "AGG":
                        c = AggressiveCountry(country[0], country[1], country[2])
                    elif subclass == "BAL":
                        c = BalancedCountry(country[0], country[1], country[2])
                    elif subclass == "DEF":
                        c = DefensiveCountry(country[0], country[1], country[2])
                    clist.append(c)
                cur.execute(buffinfo)
                blist = []
                for buff in cur.fetchall():
                    buff = buff[0]
                    buff += "Buff()"
                    b = eval(buff)
                    blist.append(b)
                cur.execute(prioritycinfo)
                priorityclist = []
                results = cur.fetchall()
                for country in results:
                    subclass = country[3]
                    if subclass == "AGG":
                        country = AggressiveCountry(country[0], country[1], country[2])
                    elif subclass == "BAL":
                        country = BalancedCountry(country[0], country[1], country[2])
                    elif subclass == "DEF":
                        country = DefensiveCountry(country[0], country[1], country[2])
                    for c in clist:
                        if hash(c) == hash(country):
                            priorityclist.append(c)
                cur.execute(prioritybinfo)
                priorityblist = []
                for buff in cur.fetchall():
                    buff = buff[0]
                    buff += "Buff()"
                    buff = eval(buff)
                    for b in blist:
                        if hash(b) == hash(buff):
                            priorityblist.append(b)
                conn.close()

            player = Player(pname, clist, priorityclist, blist, priorityblist, pwins, plosses, pelo, client, key)
            thread = Thread(self.__handle, client, player) #Creates a handle thread
            
            self.__handlerThreads.append(thread)
            thread.start() 
            thread.join() #Waits for the thread to terminate (player sends LOGOUT request or stops responding)

    def __signup(self, username: str, password: int): #Attempts to sign up 
        print(f"Signing up {username}")
        with self.__databaseLock:
            try:
                conn = sqlite3.connect("playerData.sqlite3") 
                cur = conn.cursor()
            except:
                raise e.DatabaseAccessError
            try:
                query = f"INSERT INTO Player VALUES ('{username}', '{password}', 0, 0, 1000);" #Sets up and executes basic set up scripts for player accounts, creating the player entry
                cur.execute(query)
                conn.commit()
                c1 = BalancedCountry("Angola", 25, 40) 
                c2 = AggressiveCountry("Canada", 25, 40) 
                query = "INSERT INTO Country (name, playerID, towns, type, production, priority, hash) VALUES " #and creating the base country entries
                c1 = f"('Angola', '{username}', 40, 'BAL', 25, 1, {hash(c1)});"
                c2 = f"('Canada', '{username}', 40, 'AGG', 25, 1, {hash(c2)});"
                cur.execute(query + c1)
                cur.execute(query + c2)
                conn.commit()
                b1 = MajorAttackBuff()
                b2 = MajorProductionBuff()
                query = "INSERT INTO Buff (type, playerID, priority, hash) VALUES " #and the base buff entries
                b1 = f"('MajorAttack', '{username}', 1, {hash(b1)});"
                b2 = f"('MinorTowns', '{username}', 1, {hash(b2)});"
                cur.execute(query + b1)
                cur.execute(query + b2)
                conn.commit()
                print(f"Successfully signed up {username}")
                conn.close()
            except sqlite3.IntegrityError:
                print(f"{username} already exists")
                raise e.NotUniqueUsernameError            
    
    def __handle(self, client: socket.socket, player: Player): #Function that handles each client
        print(f"Handling {player.username}")
        disconnectCounter = 0
        while True:
            if disconnectCounter >= 100:
                print(f"{player.username} has disconnected")
                client.close()
                elo = player.elo
                if elo <= 1000:
                    pool = self.__pool1
                elif elo <= 2000:
                    pool = self.__pool2
                elif elo <= 3000:
                    pool = self.__pool3
                else:
                    pool = self.__pool4
                try:
                    pool.remove(player)
                except:
                    pass
                break
            try:
                command, info = self.receive(client)
                print(command, info, " received in handle")
                if command == False:
                    print("Unauthorized connection from ", client.getpeername()[0])
                    break
                elif command == "DISCONNECT":
                    print(f"{player.username} has disconnected unexpectedly")
                    break
            except:
                continue
            if command == "END":
                print(f"{player.username} has signed off") #Remove the player from any matchmaking pools and close the player connection
                client.close()
                elo = player.elo
                if elo <= 1000:
                    pool = self.__pool1
                elif elo <= 2000:
                    pool = self.__pool2
                elif elo <= 3000:
                    pool = self.__pool3
                else:
                    pool = self.__pool4
                try:
                    pool.remove(player)
                except:
                    pass
                break
            elif command == "MATCHMAKE": #Add the player to the matchmaking pools
                self.__matchmakeInsert(player)
            elif command == "UNMATCHMAKE": #Attempt to remove the player from the pools
                elo = player.elo
                if elo <= 1000:
                    pool = self.__pool1
                elif elo <= 2000:
                    pool = self.__pool2
                elif elo <= 3000:
                    pool = self.__pool3
                else:
                    pool = self.__pool4
                try:
                    pool.remove(player)
                except:
                    pass
            elif command == "DEPRIORITISECOUNTRY": 
                with self.__databaseLock:
                    try:
                        conn = sqlite3.connect("playerData.sqlite3")
                        cur = conn.cursor()
                    except:
                        raise e.DatabaseAccessError
                    cur.execute(f"UPDATE Country SET priority = 0 WHERE hash = {info[0]} AND playerID = '{player.username}';") #Deprioritise a country given the hash
                    conn.commit()
                    conn.close()
                for i in player.prioritycountries:
                    if hash(i) == info[0]:
                        player.prioritycountries.remove(i) #Remove the country from the player priority countries list
                        break
            elif command == "PRIORITYCOUNTRY":
                with self.__databaseLock:
                    try:
                        conn = sqlite3.connect("playerData.sqlite3")
                        cur = conn.cursor()
                    except:
                        raise e.DatabaseAccessError
                    cur.execute(f"UPDATE Country SET priority = 1 WHERE hash = {info[0]} AND playerID = '{player.username}';") #Prioritise the country and add it to the priority countries list
                    conn.commit()
                    conn.close()
                for i in player.countries:
                    if hash(i) == info[0]:
                        player.prioritycountries.append(i)
                        break
            elif command == "DEPRIORITISEBUFF": 
                with self.__databaseLock:
                    try:
                        conn = sqlite3.connect("playerData.sqlite3")
                        cur = conn.cursor()
                    except:
                        raise e.DatabaseAccessError
                    cur.execute(f"UPDATE Buff SET priority = 0 WHERE hash = {info[0]} AND playerID = '{player.username}';") #Deprioritise a buff
                    conn.commit()
                    conn.close()
                for i in player.buffs:
                    if hash(i) == info[0]:
                        player.prioritybuffs.remove(i)
                        break
            elif command == "PRIORITYBUFF":
                with self.__databaseLock:
                    try:
                        conn = sqlite3.connect("playerData.sqlite3")
                        cur = conn.cursor()
                    except:
                        raise e.DatabaseAccessError
                    cur.execute(f"UPDATE Buff SET priority = 1 WHERE hash = {info[0]} AND playerID = '{player.username}';")
                    conn.commit()
                    conn.close()
                for i in player.buffs:
                    if hash(i) == info[0]:
                        player.prioritybuffs.append(i)
                        break
            elif command == "GETREWARDTUTORIAL":
                self.getReward(client, player, tutorial=True) #Get the tutorial reward
            
            elif command == "GETREWARDWIN": #Get the reward if a battle was won
                if player.Battle is not None:
                    probabilityOfWin = ELOCALC.calculateProbabilityOfWin(player.elo, player.enemy.elo)
                    newElo = ELOCALC.calculateNewElo(player.elo, probabilityOfWin, 1)
                    player.elo = newElo
                    self.getReward(client, player)
                    data = self.receive(client)
                    while data[0] != "RECEIVED":
                        data = self.receive(client) 
                    self.send("ELO", client, player.key, newElo)
            elif command == "GETREWARDLOSS": #Get the reward if a battle was lost
                if player.Battle is not None:
                    probabilityOfWin = ELOCALC.calculateProbabilityOfWin(player.elo, player.enemy.elo)
                    newElo = ELOCALC.calculateNewElo(player.elo, probabilityOfWin, 0)
                    num = random.random()
                    if num <= 0.3: #If the battle was lost, there is a 30% chance the loser gets a reward
                        self.getReward(client, player)
                    else:
                        self.send("REWARD", client, player.key, None)
                    data = self.receive(client)
                    while data[0] != "RECEIVED":
                        data = self.receive(client) 
                    self.send("ELO", client, player.key, newElo)
                    player.elo = newElo
            
    def __matchmakeInsert(self, player: Player):
        elo = player.elo 
        if elo <= 1000: 
            lock = self.__pool1Lock
            pool = self.__pool1
            poolnum = 1
            print(f"{player.username} placed in pool 1")
        elif elo <= 2000:
            lock = self.__pool2Lock
            pool = self.__pool2
            poolnum = 2
            print(f"{player.username} placed in pool 2")
        elif elo <= 3000:
            lock = self.__pool3Lock
            pool = self.__pool3
            poolnum = 3
            print(f"{player.username} placed in pool 3")
        else:
            lock = self.__pool4Lock
            pool = self.__pool4
            poolnum = 4
            print(f"{player.username} placed in pool 4")
        with lock:
            pos = self.__binaryPoolSearchInsert(pool, elo, 0, len(pool) - 1) #Gets the correct position using a binary search
            if poolnum == 1:
                self.__pool1 = pool[:pos] + [player] + pool[pos:]
                print("Current pool1: ", self.__pool1)
            elif poolnum == 2:
                self.__pool2 = pool[:pos] + [player] + pool[pos:]
                print("Current pool2: ", self.__pool2)
            elif poolnum == 3:
                self.__pool3 = pool[:pos] + [player] + pool[pos:]
                print("Current pool3: ", self.__pool3)
            elif poolnum == 4:
                self.__pool4 = pool[:pos] + [player] + pool[pos:]
                print("Current pool4: ", self.__pool4)

    def __matchmake(self):
        while True:
            poolNum = random.randint(1, 4) #Matchmake a random player in a random pool
            if poolNum == 1:
                lock = self.__pool1Lock
                pool = self.__pool1
            elif poolNum == 2:
                lock = self.__pool2Lock
                pool = self.__pool2
            elif poolNum == 3:
                lock = self.__pool3Lock
                pool = self.__pool3
            else:
                lock = self.__pool4Lock
                pool = self.__pool4
            with lock:
                length = len(pool)
                if length >= 2: #If less than two players in the pool, dont try and matchmake
                    position = random.randint(0, length-1)
                else:
                    continue
                print("MATCHMAKING")
                player = pool[position]
                value = player.elo
                pool.remove(player)
                opponent = self.__binarySearchMatchmake(pool, value, 0, len(pool)-1) #Get the player with the closest elo
                pool.remove(opponent)
            print(player, opponent, "are battling!")
            self.send("MATCHMADE", player.socket, player.key) #Send confirmation to players that theyve been matchmade
            self.send("MATCHMADE", opponent.socket, opponent.key)
            battleThread = Thread(Battle, player, opponent) #Create a thread for a battle object and add to the list, then start the thread
            self.__battleThreads.append(battleThread)
            battleThread.start()

    def __binarySearchMatchmake(self, pool: list[Player], value: int, first: int, last: int) -> Player:
        if first > last: #Simple binary search to get player objects in a list
            return pool[first]
        else:
            midpoint = (first + last) // 2
            if pool[midpoint].elo == value:
                return pool[midpoint]
            elif pool[midpoint].elo < value:
                first = midpoint + 1
                return self.__binarySearchMatchmake(pool, value, first, last)
            elif pool[midpoint].elo > value:
                last = midpoint - 1
                return self.__binarySearchMatchmake(pool, value, first, last)


    def __binaryPoolSearchInsert(self, pool: list[Player], value: int, first: int, last: int) -> int: #binary search for insertion sort
        if first > last: #Simple binary search to get an index in a list
            return first
        else:
            midpoint = (first + last) // 2
            if pool[midpoint].elo == value:
                return midpoint + 1
            elif pool[midpoint].elo < value:
                first = midpoint + 1
                return self.__binaryPoolSearchInsert(pool, value, first, last)
            elif pool[midpoint].elo > value:
                last = midpoint - 1
                return self.__binaryPoolSearchInsert(pool, value, first, last)
    
    def __generateName(self) -> str:
        return self.__CountryNames[random.randint(0, len(self.__CountryNames)-1)]
    
    def getReward(self, client: socket.socket, player: Player, tutorial=False) -> list:
        towns = [30, 35, 40, 45, 50, 55, 60] #Generate lists of possible values for each statistic
        production = [20, 25, 30, 35, 40]
        if tutorial:
            towns = towns[:4]
            production = production[:2]
        num = random.random()
        if num > 0.3: #70% chance the card is a country
            towns = towns[random.randint(0, len(towns)-1)] #Randomly select the values and generate the card, send the card to the player and add to the database and player object
            production = production[random.randint(0, len(production)-1)]
            name = self.__generateName()
            subclass = ["AGG", "BAL", "DEF"]
            subclass = subclass[random.randint(0, len(subclass)-1)]
            if subclass == "AGG":
                card = AggressiveCountry(name, production, towns)
            elif subclass == "BAL":
                card = BalancedCountry(name, production, towns)
            elif subclass == "DEF":
                card = DefensiveCountry(name, production, towns)
            self.send("REWARD", client, player.key, "COUNTRY", name, towns, subclass, production) #Send the player the reward country
            with self.__databaseLock:
                try:
                    conn = sqlite3.connect("playerData.sqlite3")
                    cur = conn.cursor()
                except:
                    raise e.DatabaseAccessError
                cur.execute(f"SELECT hash FROM Country WHERE playerID = '{player.username}';") #Get a list of hashes of the player countries and add it to the database if the country doesnt exist
                hashList = cur.fetchall()
                if hash(card) not in hashList:
                    player.countries.append(card)
                    query = "INSERT INTO Country (name, playerID, towns, type, production, priority, hash) VALUES "
                    query += f"('{name}', '{player.username}', {towns}, '{subclass}', {production}, 0, {hash(card)});"
                    cur.execute(query)
                    conn.commit()
        else: #30% chance the card is a buff
            subclass = random.random()
            if subclass > 0.3 or tutorial: #70% chance of it being a minor buff, or always if its a tutorial reward
                subclass = "Minor"
            else:
                subclass = "Major"
            stats = ["Towns", "Production", "Attack", "Defense", "SiegeAttack", "SiegeDefense", "Fortification"]
            stat = stats[random.randint(0, len(stats)-1)]
            card = eval(subclass + stat + "Buff()")
            self.send("REWARD", client, player.key, "BUFF", subclass+stat) #Send the reward buff
            with self.__databaseLock:
                try:
                    conn = sqlite3.connect("playerData.sqlite3")
                    cur = conn.cursor()
                except:
                    raise e.DatabaseAccessError
                cur.execute(f"SELECT hash FROM Buff WHERE playerID = '{player.username}';") #If the buff does not exist in the players account, add it
                hashList = cur.fetchall()
                if hash(card) not in hashList:
                    player.buffs.append(card)
                    query = "INSERT INTO Buff (type, priority, hash, playerID) VALUES "
                    query += f"('{subclass+stat}', 0, {hash(card)}, '{player.username}');"
                    cur.execute(query)
                    conn.commit()
        conn.close()

class EloCalculator:
    "Class containing methods for calculating elo gain or loss"
    def __init__(self, mean, k):
        self.mean = mean #Mean is the default starting value
        self.k = k #the k value affects the sensitivity of each result to your score. A higher k value increases the volatility of the score whereas a lower k value decreases it
    
    def assignElo(self):
        return self.mean

    def calculateProbabilityOfWin(self, player1elo, player2elo):
        return 1/(1+(10**((player1elo-player2elo)//400)))
    
    def calculateNewElo(self, elo, probability, score):
        if elo < 1000:
            k = self.k + 8 #When using varied k values, it makes more sense to have higher k values for lower score players, so that they can feel they are improving at a greater pace
        elif elo < 2000:
            k = self.k
        elif elo < 2400: #With higher score players, its better to use a lower k value so that one bad day cannot completely ruin a hard earned score
            k = self.k - 8
        elif elo > 2400:
            k = self.k - 16
        return elo + round(k*(score - probability)) #Ensure the final result is an integer

if __name__ == "__main__":
    ELOCALC = EloCalculator(2000, 24)
    SERVER = Server()
    
