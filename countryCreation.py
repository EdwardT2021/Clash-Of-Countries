import random
names = ["Mouseland", "Nugsland", "Beansland", "Hugsland", "Mugsland", "Houseland", "Land of 12"]
class Army:
    def __init__(self, infantry, tanks, planes, dsiege, asiege):
        self.infantryConstant = infantry
        self.tankConstant = tanks
        self.planeConstant = planes
        self.dsiegeConstant = dsiege
        self.asiegeConstant = asiege
        self.infantry = infantry
        self.tanks = tanks
        self.planes = planes
        self.dsiege = dsiege
        self.asiege = asiege
    
    def GetAttackPower(self):
        return (self.infantry*4)+(self.tanks*25)+(self.planes*30)+((self.asiege+self.dsiege)*5)
    
    def GetDefensePower(self):
        return (self.infantry*12)+(self.tanks*15)+(self.planes*10)+((self.asiege+self.dsiege)*5) - 100
    
    def GetSiegeAttack(self):
        return (self.asiege*20)+(self.tanks*5)

    def GetSiegeDefense(self):
        return (self.dsiege*20)+(self.infantry*1)
    
    def Half(self):
        self.infantry = self.infantry // 2
        self.tanks = self.tanks // 2
        self.planes = self.planes // 2
        self.asiege = self.asiege // 2
        self.dsiege = self.dsiege // 2
    
    def Quarter(self):
        self.infantry = (self.infantry // 4) * 3
        self.tanks = (self.tanks // 4) * 3
        self.planes = (self.planes // 4) * 3
        self.asiege = (self.asiege // 4) * 3
        self.dsiege = (self.dsiege // 4) * 3

    def GetArmy(self):
        troops = f"Infantry: {self.infantry} \nTanks: {self.tanks} \nPlanes: {self.planes} \nAttack Siege: {self.asiege} \nDefense Siege: {self.dsiege} \n"
        attack = self.GetAttackPower()
        defense = self.GetDefensePower()
        siegeDefense = self.GetSiegeDefense()
        siegeAttack = self.GetSiegeAttack()
        return troops + f"Total Attack: {attack} \nTotal Defense: {defense} \nSiege Defense: {siegeDefense} \nSiege Attack: {siegeAttack} \n"

    def AddInfantry(self, number):
        self.infantry += number
    
    def AddTanks(self, number):
        self.tanks += number
    
    def AddPlanes(self, number):
        self.planes += number
    
    def AddDSiege(self, number):
        self.dsiege += number

    def AddASiege(self, number):
        self.asiege += number
    

class AggressiveArmy(Army):
    def __init__(self):
        super(AggressiveArmy, self).__init__(25, 15, 15, 5, 15)

class BalancedArmy(Army):
    def __init__(self):
        super(BalancedArmy, self).__init__(50, 10, 10, 10, 10)

class DefensiveArmy(Army):
    def __init__(self):
        super(DefensiveArmy, self).__init__(75, 5, 5, 15, 5)

class Country:

    def __init__(self, production, towns):
        self.factories = 30
        if production == "High":
            self.production = 40
        elif production == "Medium":
            self.production = 30
        else: 
            self.production = 20
        
        if towns == "High":
            self.towns = 60
        elif towns == "Medium":
            self.towns = 50
        else:
            self.towns = 40
        self.fortifications = 0
        self.army = None
        self.name = names[random.randint(0, len(names) - 1)]
        names.remove(self.name)
        self.subclass = None
        self.unitProducing = ["i", "t", "a", "sa", "ds", "f"]
    
    def UnderAttack(self):
        infantry = int(input("How many infantry are attacking: "))
        tanks = int(input("How many tanks are attacking: "))
        planes = int(input("How many planes are attacking: "))
        siegeArtillery = int(input("How much siege artillery is attacking: "))
        defenseArtillery = int(input("How much defense artillery is attacking: "))
        attackPower = (infantry*4)+(tanks*25)+(planes*30)+((siegeArtillery+defenseArtillery)*5)
        siegePower = (tanks*5)+(siegeArtillery*20)
        siegePower -= self.army.GetSiegeDefense()
        self.fortifications -= siegePower // 100
        if self.fortifications < 0:
            self.fortifications = 0
        attackPower -= self.fortifications * 200
        defensePower = self.army.GetDefensePower()
        outcome = attackPower - defensePower
        if outcome < 0:
            print("You successfully defended!")
            print("You have unfortunately lost 1/4 of your troops :(")
            self.army.Quarter()
        elif outcome == 0:
            print("You drew!")
        else:
            townLoss = outcome//50
            self.towns -= townLoss
            print("You lost", townLoss, "towns!", "You have", self.towns, "remaining!")
            print("You have lost half of your units :(")
            if self.towns <= 0:
                print(f"{self.name} has been destroyed!")
                countries.remove(self)
            self.army.Half()

    def GetArmyDetails(self):
        print(self.army.GetArmy())
    
    def GetDetails(self):
        print(f"{self.name} ({self.subclass}):")
        print(f"Factories: {self.factories} \nProduction per factory: {self.production} \nFortifications: {self.fortifications} \nTowns: {self.towns} \n")
        self.GetArmyDetails()
    
    def SetProduction(self):
        print(f"Set production units for {self.name}")
        print("Infantry (i) costs 50")
        print("Tanks (t) cost 200")
        print("Airplanes (a) cost 200")
        print("Artillery (siege (sa) or defense (da)) costs 150")
        print("Fortifications (f) cost 300")
        print(f"You can produce {self.production * self.factories} points every turn")
        units = ["i", "t", "a", "sa", "ds", "f"]
        self.unitProducing = [] 
        self.unitProducing.append(input("Enter highest priority unit: "))
        self.unitProducing.append(input("Enter second highest priority unit: "))
        self.unitProducing.append(input("Enter third highest priority unit: "))
        self.unitProducing.append(input("Enter fourth highest priority unit: "))
        self.unitProducing.append(input("Enter fifth highest priority unit: "))
        for i in units:
            if i not in self.unitProducing:
                self.unitProducing.append(i)
        print("Your order of priority is:")
        for i in range(len(self.unitProducing)):
            if self.unitProducing[i] == "i":
                print(f"{i+1}. Infantry")
            elif self.unitProducing[i] == "t":
                print(f"{i+1}. Tanks")
            elif self.unitProducing[i] == "a":
                print(f"{i+1}. Planes")
            elif self.unitProducing[i] == "sa":
                print(f"{i+1}. Siege Artillery")
            elif self.unitProducing[i] == "da":
                print(f"{i+1}. Defense Artillery")
            elif self.unitProducing[i] == "f":
                print(f"{i+1}. Fortifications")
    
    def EndTurn(self):
        print(f"{self.name}:")
        production = self.production * self.factories
        for i in self.unitProducing:
            if i == "i":
                num = production // 100
                production -= num * 100
                print(f"{num} infantry created!")
                self.army.AddInfantry(num)
            elif i == "t":
                num = production // 200
                production -= num * 200
                print(f"{num} tanks created!")
                self.army.AddTanks(num)
            elif i == "a":
                num = production // 200
                production -= num * 200
                print(f"{num} planes created!")
                self.army.AddPlanes(num)
            elif i == "sa":
                num = production // 150
                production -= num * 150
                print(f"{num} siege artillery created!")
                self.army.AddASiege(num)
            elif i == "da":
                num = production // 150
                production -= num * 150
                print(f"{num} defense artillery created!")
                self.army.AddDSiege(num)
            elif i == "f":
                num == production // 300
                production -= num * 300
                print(f"{num} fortifications added!")
                self.fortifications += num
        self.GetDetails()

    def Attack(self):
        outcome = input("Outcome (win/loss): ")
        if outcome == "win":
            self.army.Quarter()
        else:
            self.army.Half()

class AggressiveCountry(Country):

    def __init__(self, production, towns):
        super(AggressiveCountry, self).__init__(production, towns)
        self.subclass = "Aggressive"
        self.army = AggressiveArmy()
        self.fortifications = 1

class BalancedCountry(Country):

    def __init__(self, production, towns):
        super(BalancedCountry, self).__init__(production, towns)
        self.subclass = "Balanced"
        self.army = BalancedArmy()
        self.fortifications = 2

class DefensiveCountry(Country):

    def __init__(self, production, towns):
        super(DefensiveCountry, self).__init__(production, towns)
        self.subclass = "Defensive"
        self.army = DefensiveArmy()
        self.fortifications = 3

            
              

breaker = input()
countries = []
for i in range(1):
    subclassProb = random.random()
    if subclassProb <= (1/3):
        subclass = "Defensive"
    elif subclassProb <= (2/3):
        subclass = "Balanced"
    else:
        subclass = "Aggressive"
    productionProb = random.random()
    if productionProb <= (1/6):
        production = "High"
    elif productionProb <= (3/6):
        production = "Medium"
    else:
        production = "Low"
    townProb = random.random()
    if townProb <= (1/6):
        towns = "High"
    elif townProb <= (3/6):
        towns = "Medium"
    else:
        towns = "Low"

    if subclass == "Defensive":
        countries.append(DefensiveCountry(production, towns))
    elif subclass == "Aggressive":
        countries.append(AggressiveCountry(production, towns))
    else:
        countries.append(BalancedCountry(production, towns))

for i in countries:
    i.GetDetails()

while True:
    print("Press 1 to receive an attack")
    print("Press 2 to display details for a country")
    print("Press 3 to display details for all countries")
    print("Press 4 to set production for your countries")
    print("Press 5 to end your turn")
    print("Press 6 to attack")
    choice = input(": ")
    if choice == "1":
        country = input("Name of country being attacked: ")
        for i in countries:
            if i.name == country:
                i.UnderAttack()
    elif choice == "2":
        country = input("Name of country: ")
        for i in countries:
            if i.name == country:
                i.GetDetails()
    elif choice == "3":
        for i in countries:
            i.GetDetails()
    elif choice == "4":
        print("Current production queues:")
        for i in countries:
            print(i.name + ":")
            for j in range(len(i.unitProducing) - 1):
                if i.unitProducing[j] == "i":
                    print(f"{j+1}. Infantry")
                elif i.unitProducing[j] == "t":
                    print(f"{j+1}. Tanks")
                elif i.unitProducing[j] == "a":
                    print(f"{j+1}. Planes")
                elif i.unitProducing[j] == "sa":
                    print(f"{j+1}. Siege Artillery")
                elif i.unitProducing[j] == "da":
                    print(f"{j+1}. Defense Artillery")
                elif i.unitProducing[j] == "f":
                    print(f"{j+1}. Fortifications")
        print("Choose 1 to set for one country")
        print("Choose 2 to set all countries")
        choice = input(":")
        if choice == "1":
            country = input("Name of country: ")
            for i in countries: 
                if i.name == country:
                    i.SetProduction()
        elif choice == "2":
            for i in countries:
                i.SetProduction()
    elif choice == "5":
        print("---------NEW DAY---------")
        for i in countries:
            i.EndTurn()
    elif choice == "6":
        country = input("Name of country you are attacking with: ")
        for i in countries: 
            if i.name == country:
                i.Attack()