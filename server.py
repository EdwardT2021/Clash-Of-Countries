import socket
import threading
import sqlite3
import sys
import random
import ServerErrors as e
import json 

#The following hash is not cryptographically secure, and should only be used to compare objects
def Hash(string: str) -> int:
    hashnum = 0
    for s in string:
        hashnum = (hashnum*607 ^ ord(s)*409) & 0xFFFFFFFF
    return hashnum
# The below class is another abstract class, containing basic details for each type of army.
class Army:
    "Base class for an army, stored in Country"
    def __init__(self, infantry: int, tanks: int, planes: int, defenseArtillery: int, siegeArtillery: int):
        self.infantry = infantry
        self.tanks = tanks
        self.planes = planes
        self.defenseArtillery = defenseArtillery
        self.siegeArtillery = siegeArtillery
        #Below show the troop attack and defense values
        #Infantry: 4 Attack, 12 Defense, 2 Siege Defense
        #Tanks: 25 Attack, 15 Defense, 5 Siege Attack
        #Planes: 30 Attack, 10 Defense
        #Siege and Defense Artillery: 5 Attack, 5 Defense, 20 in their respective siege categories
        self.AttackPower = (self.infantry*4)+(self.tanks*25)+(self.planes*30)+((self.siegeArtillery+self.defenseArtillery)*5)
        self.DefensePower = (self.infantry*12)+(self.tanks*15)+(self.planes*10)+((self.siegeArtillery+self.defenseArtillery)*5)
        self.SiegeAttackPower = (self.siegeArtillery*20)+(self.tanks*5)
        self.SiegeDefensePower = (self.defenseArtillery*20)+(self.infantry*2)
        self.AttackModifier = 1 #Modifiers, controlled by Buffs
        self.DefenseModifier = 1
        self.SiegeAttackModifier = 1
        self.SiegeDefenseModifier = 1
    
    def GetAttackPower(self) -> int:
        return int(self.AttackPower * self.AttackModifier)
    
    def GetDefensePower(self) -> int:
        return int(self.DefensePower * self.DefenseModifier)
    
    def GetSiegeAttack(self) -> int:
        return int(self.SiegeAttackPower * self.SiegeAttackModifier)

    def GetSiegeDefense(self) -> int:
        return int(self.SiegeDefensePower * self.SiegeDefenseModifier)
    
    def Defeat(self):
        "Call upon defeating this army. Reduces army to roughly 65% of its original strength"
        self.infantry = round((self.infantry / 10) * 6.5)
        self.tanks = round((self.tanks / 10) * 6.5)
        self.planes = round((self.planes / 10) * 6.5)
        self.siegeArtillery = round((self.siegeArtillery / 10) * 6.5)
        self.defenseArtillery = round((self.defenseArtillery / 10) * 6.5)
        self.CalculateStats()
    
    def Victory(self):
        "Call upon defeating another army. Reduces army to roughly 85% of its original strength"
        self.infantry = round((self.infantry / 10) * 8.5)
        self.tanks = round((self.tanks / 10) * 8.5)
        self.planes = round((self.planes / 10) * 8.5)
        self.siegeArtillery = round((self.siegeArtillery / 10) * 8.5)
        self.defenseArtillery = round((self.defenseArtillery / 10) * 8.5)
        self.CalculateStats()

    def AddInfantry(self, number: int):
        "Adds a number of infantry and changes stats"
        self.infantry += number
        self.CalculateStats()
    
    def AddTanks(self, number: int):
        "Adds a number of tanks and changes stats"
        self.tanks += number
        self.CalculateStats()
    
    def AddPlanes(self, number: int):
        "Adds a number of planes and changes stats"
        self.planes += number
        self.CalculateStats()
    
    def AddDefenseArtillery(self, number: int):
        "Adds a number of Defense Artillery and changes stats"
        self.defenseArtillery += number
        self.CalculateStats()

    def AddAttackArtillery(self, number: int):
        "Adds a number of Attack Artillery and changes stats"
        self.siegeArtillery += number
        self.CalculateStats()
    
    def CalculateStats(self):
        "Calculates new values for army"
        self.AttackPower = (self.infantry*4)+(self.tanks*25)+(self.planes*30)+((self.siegeArtillery+self.defenseArtillery)*5)
        self.DefensePower = (self.infantry*12)+(self.tanks*15)+(self.planes*10)+((self.siegeArtillery+self.defenseArtillery)*5)
        self.SiegeAttackPower = (self.siegeArtillery*20)+(self.tanks*5)
        self.SiegeDefensePower = (self.defenseArtillery*20)+(self.infantry*1)
    
    def ResetModifiers(self):
        "Resets all modifiers back to 1"
        self.AttackModifier = 1
        self.DefenseModifier = 1
        self.SiegeDefenseModifier = 1
        self.SiegeAttackModifier = 1    

class AggressiveArmy(Army):
    "Subclass of army for armies controlled by aggressive player countries"
    def __init__(self):
        super(AggressiveArmy, self).__init__(25, 15, 15, 5, 15)

class BalancedArmy(Army):
    "Subclass of army for armies controlled by balanced player countries"
    def __init__(self):
        super(BalancedArmy, self).__init__(50, 10, 10, 10, 10)

class DefensiveArmy(Army):
    "Subclass of army for armies controlled by defensive player countries"
    def __init__(self):
        super(DefensiveArmy, self).__init__(75, 5, 5, 15, 5)
          
#################################################################################

class Buff:
    "Base class for Buffs"
    def __init__(self, statAffected: str, linear: bool, change: int):
        self.statAffected = statAffected
        self.linear = linear
        self.multiplicative = not self.linear
        self.change = change
        self.country = None #type: Country or None

    def ApplyToCountry(self, country: 'Country'):
        "Sets the text displaying which country it is assigned to and stores the country in the .country attribute"
        self.country = country
    
    def __hash__(self) -> str:
        "Simple hashing function for the class. No other unique buff will have this combination string" 
        return Hash(f"{self.change}{self.statAffected}{self.linear}")

    def __getstate__(self) -> dict:
        "Called by pickle.dump/s(), to allow itself to be converted to binary"
        return {"instance": self.__class__}
        #As every subclass of buff has set values, we dont need to try and convert all its attributes to binary and convert back.
        #Instead, we can simply store what class it is, and then call the __init__() method
        #of the class when it is loaded again
    
    def __setstate__(self, d: dict):
        d["instance"].__init__(self, True)
        #Here we can see the above in action, calling the __init__() method of its own class on itself.
        #True is passed as the player values, as only player-owned objects are ever saved.
        #This is because the only object that is pickled is the player object, containing references to these classes
    
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
        self.factories = 50
        self.production = production
        self.towns = towns
        self.fortifications = 0
        self.army = None #type: Army
        self.Buff = None #type: Buff or None
        self.type = str
        self.dead = False
        self.attacking = False
        self.defending = False
        self.dead = False

    def AddBuff(self, Buff: Buff):
        "Add a buff to the country"
        self.Buff = Buff
        if Buff.statAffected == "Attack":
            self.army.AttackModifier = Buff.change
        elif Buff.statAffected == "Defense":
            self.army.DefenseModifier = Buff.change
        elif Buff.statAffected == "SiegeAttack":
            self.army.SiegeAttackModifier = Buff.change
        elif Buff.statAffected == "SiegeDefense":
            self.army.SiegeDefenseModifier = Buff.change
        elif Buff.statAffected == "Towns":
            self.ChangeTowns(-Buff.change)
        elif Buff.statAffected == "Production":
            self.production += Buff.change

    def RemoveBuff(self):
        "Remove the current buff"
        if self.Buff.statAffected == "Towns":
            self.ChangeTowns(self.Buff.change)
        elif self.Buff.statAffected == "Production":
            self.production -= self.Buff.change
        self.Buff = None
        self.army.ResetModifiers()

    def ChangeTowns(self, num: int):
        "Change the number of towns, set the dead flag if it is <= 0"
        self.towns -= num
        if self.towns <= 0:
            self.dead = True
    
    def SetProductionQueue(self, newQueue: list):
        "Set the production queue for a country"
        self.ProductionQueue.ChangeQueue(newQueue)
    
    def AddProductionOutput(self):
        "Calculates and adds the production output to the country"
        production = self.production
        if self.Buff is not None and self.Buff.statAffected == "Production":
            production += self.Buff.change
        productionlist = self.ProductionQueue.CalcOutput(self.factories * production)
        self.army.AddInfantry(productionlist[0])
        self.army.AddTanks(productionlist[1])
        self.army.AddPlanes(productionlist[2])
        self.fortifications += productionlist[3]
        self.army.AddAttackArtillery(productionlist[4])
        self.army.AddDefenseArtillery(productionlist[5])
    
    def Die(self):
        "Sets the dead flag"
        self.dead = True
    
    def __hash__(self) -> str:
        "Creates a unique hash for the country"
        return Hash(f"{self.name}{self.production}{self.towns}{self.type}")
    
    def __getstate__(self) -> dict:
        "Called by pickle.dump/s(), returns the variables needed for instanciation and its class"
        d = {"Production": self.production, "Towns": self.towns, "Name": self.name, "instance": self.__class__}
        return d
    
    def __setstate__(self, d: dict):
        """
        Takes a dictionary containing the variables needed for instanciation and its class.
        Calls the __init__() method of the class and passes in the variables
        """
        production = d["Production"]
        towns = d["Towns"]
        name = d["Name"]
        d["instance"].__init__(self, production, towns, name)
    
    def ToList(self) -> list:
        return [self.name, self.towns, self.type, self.production]

class AggressiveCountry(Country):
    "Subclass of country for aggressive countries"
    def __init__(self, name: str, production: int, towns: int):
        super(AggressiveCountry, self).__init__(production, towns, name)
        self.army = AggressiveArmy()
        self.fortifications = 1
        self.type = "AGG"

class BalancedCountry(Country):
    "Subclass of country for balanced countries"
    def __init__(self, name: str, production: int, towns: int):
        super(BalancedCountry, self).__init__(production, towns, name)
        self.army = BalancedArmy()
        self.fortifications = 2
        self.type = "BAL"

class DefensiveCountry(Country):
    "Subclass of country for defensive countries"
    def __init__(self, name: str, production: int, towns: int):
        super(DefensiveCountry, self).__init__(production, towns, name)
        self.army = DefensiveArmy()
        self.fortifications = 3
        self.type = "DEF"

class Player:

    def __init__(self, username, countries=[], prioritycountries=[], buffs=[], prioritybuffs=[], wins=0, draws=0, losses=0, elo=0, socket=None):
        "Player object containing relevant player data"
        self.username = username #type: str
        self.countries = countries #type: list[Country]
        self.buffs = buffs #type: list[Buff]
        self.prioritycountries = prioritycountries #type: list[Country]
        self.prioritybuffs = prioritybuffs #type: list[Buff]
        self.wins = wins #type: int
        self.losses = losses #type: int
        self.draws = draws #type: int
        self.elo = elo #type: int
        self.Battle = None
        self.socket = socket #type: socket.socket
        print(prioritycountries)
        print(prioritybuffs)
    
    def __repr__(self) -> str:
        return self.username

class Battle:

    def __init__(self, player1: Player, player2: Player):
        self.player1 = player1
        self.player2 = player2
        self.player1.Battle = self
        self.player2.Battle = self
        self.player1first = bool(random.randint(0, 1))
        self.player1countries = player1.prioritycountries.copy()
        self.player2countries = player2.prioritycountries.copy()
    
    def Run(self):
        run = True
        p1received = False
        p2received = False
        while run:
            if not p1received:
                try:
                    p1changes = self.player1.socket.recv(2048)
                    self.player1.socket.send(json.dumps({"Command": "SUCCESS"}))
                    p1received = True
                except: 
                    pass
            if not p2received:
                try:
                    p2changes = self.player2.socket.recv(2048)
                    self.player2.socket.send(json.dumps({"Command": "SUCCESS"}))
                    p2received = True
                except:
                    pass
                
            if not (p1received and p2received):
                continue
            self.player1.socket.send(p2changes)
            self.player2.socket.send(p1changes)
            p1changes = json.loads(p1changes.decode("UTF-8"))
            p2changes = json.loads(p2changes.decode("UTF-8"))

            if self.player1first:
                p1 = self.player1
                p2 = self.player2
                player1countries, player2countries = self.player1countries, self.player2countries
            else:
                p1 = self.player2
                p2 = self.player1
                p1changes, p2changes = p2changes, p1changes
                player1countries, player2countries = self.player2countries, self.player1countries
            countries = player1countries + player2countries
            
            attacks = []
            for i in range(len(player1countries)):
                actions = p1changes[i]
                card = player1countries[i]
                if card.dead:
                    continue
                card.army.AddInfantry(actions[1]["Infantry"])
                card.army.AddTanks(actions[1]["Tank"])
                card.army.AddPlanes(actions[1]["Plane"])
                card.army.AddDefenseArtillery(actions[1]["Defense Artillery"])
                card.army.AddAttackArtillery(actions[1]["Attack Artillery"])
                card.fortifications += actions[1]["Fortification"]
                if actions[2] != None:
                    card.AddBuff(actions[2])
                if actions[0][1] is not None:
                    attacks.append(actions[0])

            for i in range(len(player2countries)):
                actions = p2changes[i]
                card = player2countries[i]
                if card.dead:
                    continue
                card.army.AddInfantry(actions[1]["Infantry"])
                card.army.AddTanks(actions[1]["Tank"])
                card.army.AddPlanes(actions[1]["Plane"])
                card.army.AddDefenseArtillery(actions[1]["Defense Artillery"])
                card.army.AddAttackArtillery(actions[1]["Attack Artillery"])
                card.fortifications += actions[1]["Fortification"]
                if actions[2] != None:
                    card.AddBuff(actions[2])
                if actions[0][1] is not None:
                    attacks.append(actions[0])
            
            for attack in attacks:
                for i in countries:
                    if hash(i) == attack[0]:
                        c1 = i
                    elif hash(i) == attack[1]:
                        c2 = i
                self.CalculateBattleOutcome(c1, c2)
                dead = 0
                for i in player1countries:
                    if i.dead:
                        dead += 1
                if dead == len(player1countries):
                    run = False
                    winner = self.player2
                    loser = self.player1
                dead = 0
                for i in player2countries:
                    if i.dead:
                        dead += 1
                if dead == len(player2countries):
                    run = False
                    winner = self.player1
                    loser = self.player2
        probabilityofwinnerwin = ELOCALC.calculateProbabilityOfWin(winner.elo, loser.elo)
        probabilityofloserwin = ELOCALC.calculateProbabilityOfWin(loser.elo, winner.elo)
        winner.elo = ELOCALC.calculateNewElo(winner.elo, probabilityofwinnerwin, 1)
        loser.elo = ELOCALC.calculateNewElo(loser.elo, probabilityofloserwin, 0)
        winmsg = json.dumps({"Command": "ELO", "Args": winner.elo})
        lossmsg = json.dumps({"Command": "ELO", "Args": loser.elo})
        winner.socket.send(winmsg.encode("UTF-8"))
        loser.socket.send(lossmsg.encode("UTF-8"))
        SERVER.getReward(winner)
        msg = json.dumps({"Command": "REWARD", "Args": None})
        loser.socket.send(msg.encode("UTF-8"))
        winner.Battle = None
        loser.Battle = None

    def CalculateBattleOutcome(self, c1: Country, c2: Country):
        attacker, defender = c1, c2
        siegeAttack = attacker.army.GetSiegeAttack()
        siegeDefense = defender.army.GetSiegeDefense()
        siegeAttack -= round(siegeDefense / 3)
        defender.fortifications -= round(siegeAttack / 40)
        if defender.fortifications < 0:
            defender.fortifications = 0
        attack = attacker.army.GetAttackPower()
        defense = defender.army.GetDefensePower()
        attack -= defender.fortifications * 200
        attack -= defense
        if attack <= 0:
            victory = False
        else:
            victory = True
        if victory:
            townLoss = round(attack / 25)
            defender.towns -= townLoss
            defender.army.Defeat()
            attacker.army.Victory()
            if defender.towns <= 0:
                defender.towns = 0
                defender.Die()
        else:
            defender.army.Victory()
            attacker.army.Defeat()


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
        self.__host = socket.gethostbyname(socket.gethostname()) #Server ip address
        self.__port = 11034 #Server port

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
        mtchmke = Thread(self.__matchmake)
        self.__serverThreads.append(a) #Adds a thread that accepts new connections
        self.__serverThreads.append(cht) #Adds a thread that checks handler threads are all running
        self.__serverThreads.append(mtchmke)
        for thread in self.__serverThreads:
            thread.start()
        print(f"Server Live at {self.__host, self.__port}")

    def __send(self, command: str, conn: socket.socket, *args): #Sends a message through a socket
        message = {"Command": command} #Creates dictionary containing the command and any arguments
        if args:
            message["Args"] = args
        encMessage = json.dumps(message).encode("utf-8") #Converts dictionary into json and encodes it using utf-8
        conn.send(encMessage) #Sends the command through the socket
    
    def __receive(self, conn: socket.socket) -> tuple[str, str]:
        data = json.loads(conn.recv(1024).decode("utf-8"))
        command = data["Command"]
        args = data["Args"]
        print(f"Received {command}: {args}")
        return command, args
        
    def __accept(self): #Accepts new connections
        print("Accepting Connections")
        while True:
            client, address = self.__socket.accept()
            if address not in open("banlist.txt", "r"): #Checks if IP is banned
                print(f"Connection from {address} accepted!")
                self.__handlerThreads.append(Thread(self.__login, client, address)) #Creates a new thread to handle the player

    def __checkHandlerThreads(self): #Checks threads are active and starts them if not, if thread finished it deletes them
        print("Handler threads monitor started")
        while True:
            for thread in self.__handlerThreads:
                if not thread.is_alive():
                    try:
                        thread.start()
                    except RuntimeError:
                        self.__handlerThreads.remove(thread)
                        del(thread)

    def __login(self, client: socket.socket, address: str): #Login function
        with self.__loggedInLock: #Uses log in lock. If more than 10000 threads are using this, it will wait until a space is available
            failed = True
            while failed:
                self.__send("LOGIN", client) #Sends login request
                print("login request sent")
                command, info = self.__receive(client) 
                print(command, info, "received")
                if command == "SIGNUP": #Received if player wants a new account
                    username, password = info #Splits info into variables
                    password = int(password)
                    try:
                        self.__signup(username, password)
                        failed = False
                        self.__send("LOGGEDIN", client)
                    except e.NotUniqueUsernameError:
                        self.__send("LOGINFAILED", client, "Username not unique!")
                    
                elif command == "LOGIN": #Attempts to connect to database and match the hashed passwords
                    username, password = info
                    with self.__databaseLock:
                        try:
                            conn = sqlite3.connect("playerData.sqlite3")
                            cur = conn.cursor()
                            cur.execute(f"SELECT password FROM Player WHERE username = '{username}';")
                            try:
                                passwordDB = cur.fetchone()[0]
                            except:
                                self.__send("LOGINFAILED", client)
                                conn.close()
                                sys.exit()
                        except:
                            raise e.DatabaseAccessError
                        if passwordDB == password:
                            failed = False
                            self.__send("LOGGEDIN", client)
                            print(f"{address} logged in as {username}!")
                        else:
                            print(f"Login for {address} failed")
                        conn.close()
                    

            #Creates statement fetching player, country and buff info. Some data repitition, but necessary to quicken loading timess
            playerinfo = f"SELECT username, wins, draws, losses, elo FROM Player WHERE username = '{username}';"
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
                cur.execute(playerinfo)
                pname, pwins, pdraws, plosses, pelo = cur.fetchone()
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

            player = Player(pname, clist, priorityclist, blist, priorityblist, pwins, pdraws, plosses, pelo, client)
            thread = Thread(self.__handle, client, player) #Creates a handle thread
            
            thread.start() #Not added to handlerThreads as is handled by login thread which is in handlerThreads
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
                query = f"INSERT INTO Player VALUES ('{username}', {password}, 0, 0, 0, 1000);"
                cur.execute(query)
                conn.commit()
                c1 = BalancedCountry("Angola", 25, 40) 
                c2 = AggressiveCountry("Canada", 25, 40)
                query = "INSERT INTO Country (name, playerID, towns, type, production, priority, hash) VALUES "
                c1 = f"('Angola', '{username}', 40, 'BAL', 25, 1, {hash(c1)});"
                c2 = f"('Canada', '{username}', 40, 'AGG', 25, 1, {hash(c2)});"
                cur.execute(query + c1)
                cur.execute(query + c2)
                conn.commit()
                b1 = MajorAttackBuff()
                b2 = MinorTownsBuff()
                query = "INSERT INTO Buff (type, playerID, priority, hash) VALUES "
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
    
    def __handle(self, client: socket.socket, player: Player): #Function that handles each
        print(f"Handling {player.username}")
        while True:
            if player.Battle is not None:
                    continue
            try:
                command, info = self.__receive(client)
            except:
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
            if command == "END":
                print(f"{player.username} has signed off")
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
            elif command == "MATCHMAKE":
                self.__matchmakeInsert(player)
            elif command == "UNMATCHMAKE":
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
            elif command == "ADDCOUNTRY":
                with self.__databaseLock:
                    try:
                        conn = sqlite3.connect("playerData.sqlite3")
                        cur = conn.cursor()
                    except:
                        raise e.DatabaseAccessError
                    if info[2].upper() == "AGG":
                        c = AggressiveCountry(info[0], info[3], info[1])
                    elif info[2].upper() == "BAL":
                        c = BalancedCountry(info[0], info[3], info[1])
                    elif info[2].upper() == "DEF":
                        c = DefensiveCountry(info[0], info[3], info[1])
                    player.countries.append(c)
                    query = "INSERT INTO Country (name, playerID, towns, type, production, priority, hash) VALUES "
                    query += f"('{info[0]}', '{player.username}', {info[1]}, '{info[2]}', {info[3]}, 0, {hash(c)});"
                    cur.execute(query)
                    conn.commit()
                    conn.close()
            elif command == "ADDBUFF":
                with self.__databaseLock:
                    try:
                        conn = sqlite3.connect("playerData.sqlite3")
                        cur = conn.cursor()
                    except:
                        raise e.DatabaseAccessError
                    b = eval(info[0]+"Buff()")
                    player.buffs.append(b)
                    query = "INSERT INTO Buff (type, playerID, priority, hash) VALUES "
                    query += f"('{info[0]}', '{player.username}', 0, {hash(b)});"
                    cur.execute(query)
                    conn.commit()
                    conn.close()
            
            elif command == "DEPRIORITISECOUNTRY":
                with self.__databaseLock:
                    try:
                        conn = sqlite3.connect("playerData.sqlite3")
                        cur = conn.cursor()
                    except:
                        raise e.DatabaseAccessError
                    cur.execute(f"UPDATE Country SET priority = 0 WHERE hash = {info[0]} AND playerID = '{player.username}';")
                    conn.commit()
                    conn.close()
                for i in player.prioritycountries:
                    if hash(i) == info[0]:
                        player.prioritycountries.remove(i)
                        break
            elif command == "PRIORITYCOUNTRY":
                with self.__databaseLock:
                    try:
                        conn = sqlite3.connect("playerData.sqlite3")
                        cur = conn.cursor()
                    except:
                        raise e.DatabaseAccessError
                    cur.execute(f"UPDATE Country SET priority = 1 WHERE hash = {info[0]} AND playerID = '{player.username}';")
                    conn.commit()
                    conn.close()
                for i in player.countries:
                    if hash(i) == info[0]:
                        player.prioritycountries.append(i)
            elif command == "DEPRIORITISEBUFF":
                with self.__databaseLock:
                    try:
                        conn = sqlite3.connect("playerData.sqlite3")
                        cur = conn.cursor()
                    except:
                        raise e.DatabaseAccessError
                    cur.execute(f"UPDATE Buff SET priority = 0 WHERE hash = {info[0]} AND playerID = '{player.username}';")
                    conn.commit()
                    conn.close()
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
            pos = self.__binaryPoolSearchInsert(pool, elo, 0, len(pool) - 1)
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
            poolNum = random.randint(1, 4)
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
                if length >= 2:
                    position = random.randint(0, length-1)
                else:
                    continue
                print("MATCHMAKING")
                player = pool[position]
                value = player.elo
                pool.remove(player)
                opponent = self.__binarySearchMatchmake(pool, value, 0, len(pool)-1)
                pool.remove(opponent)
            print(player, opponent, "are battling!")
            battle = Battle(player, opponent)
            playerd = {"EnemyCountries": [], "EnemyBuffs": [], "Enemy": [player.username, player.wins, player.losses, player.elo], "First": not battle.player1first}
            for c in player.prioritycountries:
                playerd["EnemyCountries"].append(c.ToList())
            for b in player.prioritybuffs:
                playerd["EnemyBuffs"].append(str(b))
            self.__send("BATTLE", opponent.socket, playerd)
            oppd = {"EnemyCountries": [], "EnemyBuffs": [], "Enemy": [opponent.username, opponent.wins, opponent.losses, opponent.elo], "First": battle.player1first}
            for c in opponent.prioritycountries:
                oppd["EnemyCountries"].append(c.ToList())
            for b in opponent.prioritybuffs:
                oppd["EnemyBuffs"].append(str(b))
            self.__send("BATTLE", player.socket, oppd)
            battleThread = Thread(battle.Run)
            self.__battleThreads.append(battleThread)
            battleThread.start()

    def __binarySearchMatchmake(self, pool: list[Player], value: int, first: int, last: int) -> Player:
        if first > last:
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
        if first > last:
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
    
    def getReward(self, client: socket.socket, player: Player) -> list:
        num = random.random()
        if num > 0.3:
            towns = [30, 35, 40, 45, 50, 55, 60]
            towns = towns[random.randint(0, len(towns)-1)]
            production = [20, 25, 30, 35, 40]
            production = production[random.randint(0, len(towns)-1)]
            name = self.__generateName()
            subclass = ["AGG", "BAL", "DEF"]
            subclass = subclass[random.randint(0, len(subclass)-1)]
            if subclass == "AGG":
                card = AggressiveCountry(name, production, towns)
            elif subclass == "BAL":
                card = BalancedCountry(name, production, towns)
            elif subclass == "DEF":
                card = DefensiveCountry(name, production, towns)
            self.__send("REWARD", client, [subclass, towns, production, name])
            with self.__databaseLock:
                try:
                    conn = sqlite3.connect("playerData.sqlite3")
                    cur = conn.cursor()
                except:
                    raise e.DatabaseAccessError
                cur.execute(f"SELECT hash FROM Country WHERE playerID = '{player.username}';")
                hashList = cur.fetchall()
                if hash(card) not in hashList:
                    player.countries.append(card)
                    query = "INSERT INTO Country (name, playerID, towns, type, production, priority, hash) VALUES "
                    query += f"('{name}', '{player.username}', {towns}, '{subclass}', {production}, 0, {hash(card)});"
                    cur.execute(query)
                    conn.commit()
        else:
            subclass = random.random()
            if subclass > 0.3:
                subclass = "Minor"
            else:
                subclass = "Major"
            stats = ["Towns", "Production", "Attack", "Defense", "SiegeAttack", "SiegeDefense", "Fortification"]
            stat = stats[random.randint(0, len(stats)-1)]
            card = eval(subclass + stat + "Buff()")
            self.__send("REWARD", client, subclass+stat)
            with self.__databaseLock:
                try:
                    conn = sqlite3.connect("playerData.sqlite3")
                    cur = conn.cursor()
                except:
                    raise e.DatabaseAccessError
                cur.execute(f"SELECT hash FROM Buff WHERE playerID = '{player.username}';")
                hashList = cur.fetchall()
                if hash(card) not in hashList:
                    player.buffs.append(card)
                    query = "INSERT INTO Buff (type, priority, hash, playerID) VALUES "
                    query += f"('{subclass+stat}', 0, {hash(card)}, '{player.username}');"
                    cur.execute(query)
                    conn.commit()
        conn.close()




class EloCalculator:

    def __init__(self, mean, k):
        self.mean = mean
        self.k = k
    
    def assignElo(self):
        return self.mean

    def calculateProbabilityOfWin(self, player1elo, player2elo):
        return 1/(1+(10**((player1elo-player2elo)//400)))
    
    def calculateNewElo(self, elo, probability, score):
        if elo < 1000:
            k = self.k + 8
        elif elo < 2000:
            k = self.k
        elif elo < 2400:
            k = self.k - 8
        elif elo > 2400:
            k = self.k - 16
        return elo + k*(score - probability)

if __name__ == "__main__":
    ELOCALC = EloCalculator(1000, 24)
    SERVER = Server()
    
