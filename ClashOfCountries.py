import socket as s
import random as r
from urllib.parse import non_hierarchical
import clientErrors as er
import pygame
from os import path
import sys
import pickle
from time import time
from math import log10, sin, cos
import json
from hashlib import sha256
import threading
import rsa

# Below are the colour values used

BLUE = "#356288"
ROYALBLUE = "#aacfdd"
BLACK = "#000000"
WHITE = "#ffffff"

AUTH = str(sha256("121212".encode("ascii"), usedforsecurity=True).digest())

# This is the multiplier for how the velocity of the card should decrease every time the card is updated.
# This results in an exponential graph of the order y = 1/x
GRAVITY = 0.95
# The below function is necessary to allow your one file executable program to find the location of its assets.
# It uses _MEIPASS which is a temporary folder for pyinstaller to create to store assets in upon loading the executable.
# This function checks for the temporary folder, and if it cannot be found, sets the base path to the path of the executable.
def resource_path(relative_path):
    "Gets the path for the resource relative to the base folder. Allows for assets to work within an executable"
    try:
        base_path = sys._MEIPASS
    except:
        base_path = path.abspath(".")

    return path.join(base_path, relative_path)

#The below function is a custom 32 bit hash generator that is NOT CRYPTOGRAPHICALLY SECURE used for quick object comparisons 
def Hash(string: str) -> int:
    hashnum = 0
    for s in string:
        hashnum = (hashnum*607 ^ ord(s)*409) & 0xFFFFFFFF
    return hashnum

class Card(pygame.sprite.Sprite):
    "Base class for everything represented by a card"
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        # This class contains attributes for the back of the card, the card movement and states, and flags representing these.
        # It also declares some key variables and sets them to none, which classes that inherit from this class should set.
        # This class should never be directly instantiated. It is an abstract class.
        # This class implements polymorphism, by setting methods for the subclasses Buff and Country.
        # This provides a single interface through which the position and state of the cards can be manipulated.
        self.x = 0
        self.y = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.targetX = 0
        self.targetY = 0
        self.down = False
        self.up = False
        self.left  = False
        self.right = False
        self.cardSize = (150, 245.5)
        self.highlighted = False
        self.highlightImage = pygame.image.load(resource_path("art/highlight.png")).convert_alpha() 
        self.highlightImage = pygame.transform.scale(self.highlightImage, self.cardSize)
        self.priority = False
        priorityImage = pygame.image.load(resource_path("art/priority.png")).convert_alpha()
        self.priorityImage = pygame.transform.scale(priorityImage, self.cardSize)
        cardBack = pygame.image.load(resource_path("art/CardBack.png")).convert_alpha()
        self.cardBack = pygame.transform.scale(cardBack, self.cardSize)
        self.image = self.cardBack #The actual image that will be displayed
        self.flipping = False
        self.flipped = False
        self.flippedImage = None #type: pygame.Surface
        self.inPos = False
        self.statsUpdate = True

    
    # This function simply sets the cards target position to a defined value, sets the flags to show which direction
    # the card is moving in, and sets the velocity.
    def UpdatePosition(self, pos: 'tuple[int, int]'):
        "Provide a new position for the card to move towards every time Update is called"
        self.targetX = pos[0]
        self.targetY = pos[1]
        
        if self.targetX < self.rect.x:
            self.left = True
            self.right = False
        elif self.targetX > self.rect.x:
            self.left = False
            self.right = True
        else:
            self.left = False
            self.right = False

        self.velocity_x = (self.targetX - self.x) / 19
        
        if self.targetY > self.rect.y:
            self.down = True
            self.up = False
        elif self.targetY < self.rect.y:
            self.down = False
            self.up = True
        else:
            self.down = False
            self.up = False
        
        self.velocity_y = (self.targetY - self.y) / 19
        if self.up:
            self.velocity_y = -self.velocity_y
        
    # This method should be called once on every iteration of the game loop.
    # It defines how the cards position should change, relative to its target position and its velocity     
    def Update(self):
        "Simple update function that deals with movement and flipping"
        if self.rect.centerx != self.targetX and not self.flipping:
            self.velocity_x *= GRAVITY
            dx = self.velocity_x
            if (self.right and self.rect.centerx + dx > self.targetX):
                self.rect.centerx = self.targetX
                self.velocity_x = 0
            elif (self.left and self.rect.centerx + dx < self.targetX):
                self.rect.centerx = self.targetX
                self.velocity_x = 0
            else:
                self.rect.centerx += dx

        if self.rect.centery != self.targetY and not self.flipping:
            self.velocity_y *= GRAVITY
            dy = self.velocity_y
            if (self.down and self.rect.centery + dy > self.targetY):
                self.rect.centery = self.targetY
                self.velocity_y = 0
            elif (self.up and self.rect.centery + dy < self.targetY):
                self.rect.centery = self.targetY
                self.velocity_y = 0
            else:
                self.rect.centery += dy
        
        if self.rect.center == (self.targetX, self.targetY):
            self.inPos = True
        
        if self.flipping:
            change = 10
            if self.image != self.flippedImage:
                change *= -1
            self.rect.width += change
            self.rect.left += (change*-1)/2

        if self.rect.width <= 2:
            self.image = self.flippedImage
        
        if self.rect.size[0] == self.cardSize[0] and self.image == self.flippedImage:
            self.flipping = False
            self.flipped = True


    # This method checks to see if the card is the right size, and makes a gradual adjustment towards the correct size
    # if not. Then it draws the stats of the card onto the card, and blits a border, and then the card, to the game screen
    def Draw(self):
        "Draws the card to the game surface"
        if self.rect.width != self.cardSize[0]: 
            image = pygame.Surface(self.rect.size).convert_alpha()
            rect = image.get_rect()
            image.blit(self.image, (rect.centerx-(self.cardSize[0]/2), 0))
        else:
            image = self.image.copy()
            if isinstance(self, Country) and self.flipped:
                for i in range(len(self.stats)): #Draw the country stats onto the card
                    if self.dead:
                        image.blit(self.stats[0], (15, 160))
                        break
                    stat = self.stats[i]
                    image.blit(stat, (10, 140+14*i))
            
            if isinstance(self, Buff) and self.flipped: 
                for i in range(len(self.stats)):
                    stat = self.stats[i]
                    image.blit(stat, (10, 150+20*i))
                if self.country is not None:
                    image.blit(self.countryText, (10, 200)) 

        border = pygame.Rect(self.rect.x-2, self.rect.y-2, self.rect.width+4, self.rect.height+4) #Border created via a rectangle slightly bigger than the original
        pygame.draw.rect(GAME.screen, BLACK, border)
        GAME.screen.blit(image, self.rect.topleft)
        if self.highlighted:
            GAME.screen.blit(self.highlightImage, self.rect.topleft) #Draw the highlighted image on top if its highlighted
        if self.priority and self.image != self.cardBack and self.rect.width == self.cardSize[0]:
            GAME.screen.blit(self.priorityImage, self.rect.topleft)

    #A simple method that sets the flipping flag
    def Flip(self):
        "Flip the card"
        self.flipping = True

    #This method is empty, as it is meant to be overridden by its subclasses
    def SetDetails(self): 
        "Re-calculate statistics/relevant attributes"
        pass       
    
    #This method resets all flags and positions for the card, returning it to its default state
    def ResetPosition(self):
        self.velocity_x = 0
        self.velocity_y = 0
        self.x = 0
        self.y = 0
        self.right = False
        self.left = False
        self.up = False
        self.down = False
        self.rect = pygame.Rect(0, 0, self.cardSize[0], self.cardSize[1])
        self.inPos = False
        self.highlighted = False
        self.image = self.cardBack
        self.flipped = False
        self.flipping = False
        self.priority = False

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
        if isinstance(self, EnemyArmy): #If it is an enemy army, old values are stored for comparison
            self.oldAttackPower = self.AttackPower
            self.oldDefensePower = self.DefensePower
            self.oldSiegeDefensePower = self.SiegeDefensePower
            self.oldSiegeAttackPower = self.SiegeAttackPower
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

class PlayerArmy(Army):
    "Subclass of army for armies controlled by player countries"
    def __init__(self, infantry: int, tanks: int, planes: int, defenseArtillery: int, siegeArtillery: int):
        
        super(PlayerArmy, self).__init__(infantry, tanks, planes, defenseArtillery, siegeArtillery)
    
class PlayerAggressiveArmy(PlayerArmy):
    "Subclass of army for armies controlled by aggressive player countries"
    def __init__(self):
        super(PlayerAggressiveArmy, self).__init__(25, 15, 15, 5, 15)

class PlayerBalancedArmy(PlayerArmy):
    "Subclass of army for armies controlled by balanced player countries"
    def __init__(self):
        super(PlayerBalancedArmy, self).__init__(50, 10, 10, 10, 10)

class PlayerDefensiveArmy(PlayerArmy):
    "Subclass of army for armies controlled by defensive player countries"
    def __init__(self):
        super(PlayerDefensiveArmy, self).__init__(75, 5, 5, 15, 5)

class EnemyArmy(Army):
    "Subclass of army for armies controlled by enemy countries"
    def __init__(self, infantry, tanks, planes, defenseArtillery, siegeArtillery):

        super(EnemyArmy, self).__init__(infantry, tanks, planes, defenseArtillery, siegeArtillery)
        #Start values below are set to tell the class when to be precise about its strength and when to return a symbol indicator
        self.startAttack = True
        self.startDefense = True
        self.startSiegeAttack = True
        self.startSiegeDefense = True
        self.oldAttackPower = self.AttackPower
        self.oldDefensePower = self.DefensePower
        self.oldSiegeAttackPower = self.SiegeAttackPower
        self.oldSiegeDefensePower = self.SiegeDefensePower

    def GetAttackPower(self) -> int or str:
        "Return the attack power or a comparative symbol, depending on the start flags within the army"
        if self.startAttack: #Checks to see if it should return the actual amount
            self.startAttack = False #If it should, sets that back to False and returns the correct power
            return int(self.AttackPower * self.AttackModifier)
        else: #If it doesnt, compares old attack power to the new one, and returns a comparative symbol
            if self.AttackPower > self.oldAttackPower:
                if self.AttackPower > self.oldAttackPower + 100:
                    return "^^^"
                elif self.AttackPower > self.oldAttackPower + 50:
                    return "^^"
                return "^"
            else:
                return "-"
    
    def GetDefensePower(self) -> int or str:
        "Return the defense power or a comparative symbol, depending on the start flags within the army"
        if self.startDefense: #See GetAttackPower
            self.startDefense = False
            return int(self.DefensePower * self.DefenseModifier)
        else:
            if self.DefensePower > self.oldDefensePower:
                if self.DefensePower > self.oldDefensePower + 150:
                    return "^^^"
                elif self.DefensePower > self.oldDefensePower + 100:
                    return "^^"
                return "^"
            elif self.DefensePower < self.oldDefensePower:
                return "v"
            else:
                return "-"
    
    def GetSiegeAttack(self) -> int or str:
        "Return the siege attack power or a comparative symbol, depending on the start flags within the army"
        if self.startSiegeAttack:
            self.startSiegeAttack = False
            return int(self.SiegeAttackPower * self.SiegeAttackModifier)
        else:
            if self.SiegeAttackPower > self.oldSiegeAttackPower:
                if self.SiegeAttackPower > self.oldSiegeAttackPower + 150:
                    return "^^^"
                elif self.SiegeAttackPower > self.oldSiegeAttackPower + 100:
                    return "^^"
                return "^"
            elif self.SiegeAttackPower < self.oldSiegeAttackPower:
                return "v"
            else:
                return "-"

    def GetSiegeDefense(self) -> int or str:
        "Return the siege defense power or a comparative symbol, depending on the start flags within the army"
        if self.startSiegeDefense:
            self.startSiegeDefense = False
            return int(self.SiegeDefensePower * self.SiegeDefenseModifier)
        else:
            if self.SiegeDefensePower > self.oldSiegeDefensePower:
                if self.SiegeDefensePower > self.oldSiegeDefensePower + 150:
                    return "^^^"
                elif self.SiegeDefensePower > self.oldSiegeDefensePower + 100:
                    return "^^"
                return "^"
            elif self.SiegeDefensePower < self.oldSiegeDefensePower:
                return "v"
            else:
                return "-"
    
    def ResetStart(self):
        "Sets all start flags, allowing the Get methods to return exact values for power"
        self.startSiegeAttack = True
        self.startSiegeDefense = True
        self.startAttack = True
        self.startDefense = True
    

#Below are army subclasses dictating unit compositions
class EnemyAggressiveArmy(EnemyArmy):
    "Subclass of army for armies controlled by aggressive enemy countries"
    def __init__(self):

        super(EnemyAggressiveArmy, self).__init__(25, 15, 15, 5, 15)

class EnemyBalancedArmy(EnemyArmy):
    "Subclass of army for armies controlled by balanced enemy countries"
    def __init__(self):

        super(EnemyBalancedArmy, self).__init__(50, 10, 10, 10, 10)

class EnemyDefensiveArmy(EnemyArmy):
    "Subclass of army for armies controlled by defensive enemy countries"
    def __init__(self):

        super(EnemyDefensiveArmy, self).__init__(75, 5, 5, 15, 5)
          
#################################################################################

class Buff(Card):
    "Base class for Buffs"
    def __init__(self, statAffected: str, linear: bool, change: int, player: bool):
        Card.__init__(self)
        self.statAffected = statAffected
        self.linear = linear
        self.multiplicative = not self.linear
        self.change = change
        self.symbol = str
        self.player = player
        self.country = None #type: Country or None
        self.countryText = None #type: pygame.Surface or None
        self.stats = [] #Used to store text needing placed upon card
    
    def SetDetails(self):
        "Display a symbol based on if it is minor or major buff, and the statistic the buff affects"
        self.stats = []
        Text = self.statAffected
        statsText = GAME.smallBoldFont.render(Text, True, BLACK)
        self.stats.append(statsText)

    def ApplyToCountry(self, country: 'Country'):
        "Sets the text displaying which country it is assigned to and stores the country in the .country attribute"
        self.country = country
        ctext = "Applied to: " + country.name
        self.countryText = GAME.tinyBoldFont.render(ctext, True, BLACK)
    
    def Reset(self):
        self.country = None
        self.countryText = None
        self.ResetPosition()
    
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
        return type(self).__name__ #Returns the name of the subclass when printed or used as argument for str()
        
class LinearBuff(Buff):
    "Subclass of buff for additive changes, ie +5"
    def __init__(self, statAffected: str, change: int, player: bool):

        super(LinearBuff, self).__init__(statAffected, True, change, player)
    
    def SetDetails(self):
        "Overload of the base method, but calls that base method and adds upon it"
        Buff.SetDetails(self)
        if isinstance(self, ProductionBuff):
            change = 50*self.change
        else:
            change = self.change
        change = "+" + str(change) + f" {self.statAffected}" 
        changeText = GAME.tinyBoldFont.render(change, True, BLACK)
        self.stats.append(changeText)
    
class MultiplicativeBuff(Buff):
    "Subclass of buff for multiplicative changes, ie *1.5 (also viewed as +50%)"
    def __init__(self, statAffected: str, change: int, player: bool):

        super(MultiplicativeBuff, self).__init__(statAffected, False, change, player)

    def SetDetails(self):
        "Overload of the base method, but calls that base method and adds upon it"
        Buff.SetDetails(self)
        change = "+" + str(round((self.change-1)*100, 2)) + "%"
        changeText = GAME.tinyBoldFont.render(change, True, BLACK)
        self.stats.append(changeText)

class MinorBuff(Buff):
    "Subclass for minor buffs, used to decide the symbol needing to be represented"
    def setSymbol(self):
        self.symbol = "+"
        Text = GAME.smallBoldFont.render(self.symbol, True, BLACK)
        self.flippedImage.blit(Text, (5, 5))

class MajorBuff(Buff):
    "Subclass for major buffs, used to decide the symbol needing to be represented"
    def setSymbol(self):
        self.symbol = "++"
        Text = GAME.smallBoldFont.render(self.symbol, True, BLACK)
        self.flippedImage.blit(Text, (5, 5))

class ProductionBuff(LinearBuff):
    "Subclass for Production buffs, inherits from Linear as all production changes should be additive"
    def __init__(self, change: int, player: bool):

        super(ProductionBuff, self).__init__("Production", change, player)
        card = pygame.image.load(resource_path("art/ProductionBuff.png")).convert_alpha()
        card = pygame.transform.scale(card, self.cardSize)
        self.flippedImage = pygame.Surface(self.cardSize).convert_alpha()
        self.flippedImage.blit(card, (0, 0))
        self.rect = self.flippedImage.get_rect()

class MinorProductionBuff(ProductionBuff, MinorBuff):
    "Subclass for Minor Production Buffs that inherits from ProductionBuff and MinorBuff. +2 increases"
    def __init__(self, player: bool):

        super(MinorProductionBuff, self).__init__(2, player)
        self.setSymbol()

class MajorProductionBuff(ProductionBuff, MajorBuff):
    "Subclass for Major Production Buffs that inherits from ProductionBuff and MajorBuff. +4 increase"
    def __init__(self, player: bool):
        
        super(MajorProductionBuff, self).__init__(4, player)
        self.setSymbol()

class TownsBuff(LinearBuff):
    "Subclass for Town buffs, inherits from Linear as all town changes should be additive"
    def __init__(self, change: int, player: bool):

        super(TownsBuff, self).__init__("Towns", change, player)
        card = pygame.image.load(resource_path("art/TownBuff.png")).convert_alpha()
        card = pygame.transform.scale(card, self.cardSize)
        self.flippedImage = pygame.Surface(self.cardSize).convert_alpha()
        self.flippedImage.blit(card, (0, 0))
        self.rect = self.flippedImage.get_rect()

class MinorTownsBuff(TownsBuff, MinorBuff):
    "Subclass for Minor Towns Buffs that inherits from TownsBuff and MinorBuff. +5 increase"
    def __init__(self, player: bool):

        super(MinorTownsBuff, self).__init__(5, player)
        self.setSymbol()

class MajorTownsBuff(TownsBuff, MajorBuff):
    "Subclass for Major Towns Buffs that inherits from TownsBuff and MajorBuff. +10 increase"
    def __init__(self, player: bool):

        super(MajorTownsBuff, self).__init__(10, player)
        self.setSymbol()

class FortificationBuff(LinearBuff):
    "Subclass for Fortification Buffs, inherits from Linear as all fortification changes should be additive"
    def __init__(self, change: int, player: bool):

        super(FortificationBuff, self).__init__("Fortifications", change, player)
        card = pygame.image.load(resource_path("art/FortificationBuff.png")).convert_alpha()
        card = pygame.transform.scale(card, self.cardSize)
        self.flippedImage = pygame.Surface(self.cardSize).convert_alpha()
        self.flippedImage.blit(card, (0, 0))
        self.rect = self.flippedImage.get_rect()

class MinorFortificationBuff(FortificationBuff, MinorBuff):
    "Subclass for Minor Fortification Buffs that inherits from FortificationBuff and MinorBuff. +1 increase"
    def __init__(self, player: bool):

        super(MinorFortificationBuff, self).__init__(1, player)
        self.setSymbol()

class MajorFortificationBuff(FortificationBuff, MajorBuff):
    "Subclass for Major Fortification Buffs that inherits from FortificationBuff and MajorBuff. +2 increase"
    def __init__(self, player: bool):
        
        super(MajorFortificationBuff).__init__(2, player)
        self.setSymbol()

class AttackBuff(MultiplicativeBuff):
    "Subclass for Attack Buffs, inherits from Multiplicative as all attack changes should be multiplicative"
    def __init__(self, change: int, player: bool):
        
        super(AttackBuff, self).__init__("Attack", change, player)

        card = pygame.image.load(resource_path("art/AttackBuff.png")).convert_alpha()
        card = pygame.transform.scale(card, self.cardSize)
        self.flippedImage = pygame.Surface(self.cardSize).convert_alpha()
        self.flippedImage.blit(card, (0, 0))
        self.rect = self.flippedImage.get_rect()

class MinorAttackBuff(AttackBuff, MinorBuff):
    "Subclass for Minor Attack Buffs, inherits from AttackBuff and MinorBuff. 10% increase"
    def __init__(self, player: bool):
        
        super(MinorAttackBuff, self).__init__(1.1, player)
        self.setSymbol()

class MajorAttackBuff(AttackBuff, MajorBuff):
    "Subclass for Major Attack Buffs, inherits from AttackBuff and MajorBuff. 20% increase"
    def __init__(self, player: bool):
        
        super(MajorAttackBuff, self).__init__(1.2, player)
        self.setSymbol()

class SiegeAttackBuff(MultiplicativeBuff):
    "Subclass for Siege Attack Buffs, inherits from Multiplicative as all siege attack changes should be multiplicative"
    def __init__(self, change: int, player: bool):

        super(SiegeAttackBuff, self).__init__("SiegeAttack", change, player)

        card = pygame.image.load(resource_path("art/SiegeAttackBuff.png")).convert_alpha()
        card = pygame.transform.scale(card, self.cardSize)
        self.flippedImage = pygame.Surface(self.cardSize).convert_alpha()
        self.flippedImage.blit(card, (0, 0))
        self.rect = self.flippedImage.get_rect()

class MinorSiegeAttackBuff(SiegeAttackBuff, MinorBuff):
    "Subclass for Minor Siege Attack Buffs, inherits from SiegeAttackBuff and MinorBuff. 10% increase"
    def __init__(self, player: bool):

        super(MinorSiegeAttackBuff, self).__init__(1.1, player)
        self.setSymbol()

class MajorSiegeAttackBuff(SiegeAttackBuff, MajorBuff):
    "Subclass for Major Siege Attack Buffs, inherits from SiegeAttackBuff and MajorBuff. 20% increase"
    def __init__(self, player: bool):

        super(MajorSiegeAttackBuff, self).__init__(1.2, player)
        self.setSymbol()

class DefenseBuff(MultiplicativeBuff):
    "Subclass for Defense Buffs, inherits from Multiplicative as all defense changes should be multiplicative"
    def __init__(self, change: int, player: bool):
        
        super(DefenseBuff, self).__init__("Defense", change, player)

        card = pygame.image.load(resource_path("art/DefenseBuff.png")).convert_alpha()
        card = pygame.transform.scale(card, self.cardSize)
        self.flippedImage = pygame.Surface(self.cardSize).convert_alpha()
        self.flippedImage.blit(card, (0, 0))
        self.rect = self.flippedImage.get_rect()

class MinorDefenseBuff(DefenseBuff, MinorBuff):
    "Subclass for Minor Defense Buffs, inherits from DefenseBuff and MinorBuff"
    def __init__(self, player: bool):
        
        super(MinorDefenseBuff, self).__init__(1.1, player)
        self.setSymbol()

class MajorDefenseBuff(DefenseBuff, MajorBuff):
    "Subclass for Major Defense Buffs, inherits from DefenseBuff and MajorBuff. 20% increase"
    def __init__(self, player: bool):
        
        super(MajorDefenseBuff, self).__init__(1.2, player)
        self.setSymbol()

class SiegeDefenseBuff(MultiplicativeBuff):
    "Subclass for Siege Defense Buffs, inherits from Multiplicative as all siege defense changes should be multiplicative"
    def __init__(self, change: int, player: bool):

        super(SiegeDefenseBuff, self).__init__("SiegeDefense", change, player)

        card = pygame.image.load(resource_path("art/SiegeDefenseBuff.png")).convert_alpha()
        card = pygame.transform.scale(card, self.cardSize)
        self.flippedImage = pygame.Surface(self.cardSize).convert_alpha()
        self.flippedImage.blit(card, (0, 0))
        self.rect = self.flippedImage.get_rect()

class MinorSiegeDefenseBuff(SiegeDefenseBuff, MinorBuff):
    "Subclass for Minor Siege Defense Buffs, inherits from SiegeDefenseBuff and MinorBuff"
    def __init__(self, player: bool):

        super(MinorSiegeDefenseBuff, self).__init__(1.1, player)
        self.setSymbol()

class MajorSiegeDefenseBuff(SiegeDefenseBuff, MajorBuff):
    "Subclass for Major Siege Defense Buffs, inherits from SiegeDefenseBuff and MajorBuff. 20% increase"
    def __init__(self, player: bool):

        super(MajorSiegeDefenseBuff, self).__init__(1.2, player)
        self.setSymbol()

#################################################################################

class Country(Card):
    "Base class for all countries"
    def __init__(self, production: int, towns: int, name: str):
        Card.__init__(self)
        self.name = name
        self.factories = 50
        self.production = production
        self.baseTowns = towns
        self.towns = towns
        self.fortifications = 0
        self.basefortifications = 0
        self.army = None #type: Army
        self.Buff = None #type: Buff or None
        self.type = None #type: str
        self.dead = False
        self.attacking = False
        self.defending = False
        self.prodpower = self.factories * self.production
        self.prodpowerbuffadded = False
        #The below line is only used for passing data when in a battle across networks
        self.UnitsBought = [0, 0, 0, 0, 0, 0]
        self.dead = False
        self.deathImage = pygame.image.load(resource_path("art/Death.png")).convert_alpha() 
        self.deathImage = pygame.transform.scale(self.deathImage, self.cardSize)
        self.armyunits = None #type: pygame.Surface
        self.Opponent = None

    def DrawUnits(self):
        if self.image == self.cardBack:
            return
        x = self.rect.right + 2
        y = self.rect.centery - (self.cardSize[1]/4)
        rect = self.armyunits.get_rect()
        w = rect.width + 4
        h = rect.height + 4
        rect = pygame.Rect(x - 2, y-2, w, h)
        pygame.draw.rect(GAME.screen, BLACK, rect)
        GAME.screen.blit(self.armyunits, (x, y))
    
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
            self.prodpower += Buff.change * self.factories
            self.prodpowerbuffadded = True
        self.SetDetails()

    def RemoveBuff(self):
        "Remove the current buff"
        if self.Buff.statAffected == "Towns":
            self.ChangeTowns(self.Buff.change)
        elif self.Buff.statAffected == "Production":
            self.prodpower = max(self.prodpower - self.Buff.change, 0)
        self.Buff = None
        self.army.ResetModifiers()
        self.SetDetails()

    def ChangeTowns(self, num: int):
        "Change the number of towns, set the dead flag if it is <= 0"
        self.towns -= num
        if self.towns <= 0:
            self.dead = True
    
    def SetDetails(self):
        "Set and render the statistics and details of the country, ready to be displayed by the draw function"
        #Below checks to see if card is dead and just puts its name on it if it is
        if self.dead:
            self.stats = [GAME.boldFont.render(self.name, True, WHITE)]
            return
        #Below sets stats displayed upon the card
        attributes = []
        nameText = GAME.tinyBoldFont.render(self.name, True, WHITE)
        attributes.append(nameText)
        towns = "Towns: " + str(self.towns)
        townsText = GAME.tinyBoldFont.render(towns, True, WHITE)
        attributes.append(townsText)
        armyMight = "Might: " + str(self.army.GetAttackPower())
        armyMightText = GAME.tinyBoldFont.render(armyMight, True, WHITE)
        attributes.append(armyMightText)
        armyDefense = self.army.GetDefensePower()
        armyDefense = "Defense: " + str(armyDefense)
        armyDefenseText = GAME.tinyBoldFont.render(armyDefense, True, WHITE)
        attributes.append(armyDefenseText)
        armySiegeAttack = "Siege Attack: " + str(self.army.GetSiegeAttack())
        armySiegeAttackText = GAME.tinyBoldFont.render(armySiegeAttack, True, WHITE)
        attributes.append(armySiegeAttackText)
        armySiegeDefense = "Siege Defense: " + str(self.army.GetSiegeDefense())
        armySiegeDefenseText = GAME.tinyBoldFont.render(armySiegeDefense, True, WHITE)
        attributes.append(armySiegeDefenseText)
        forts = "Forts: " + f"+{self.fortifications*200} defense"
        fortsText = GAME.tinyBoldFont.render(forts, True, WHITE)
        attributes.append(fortsText)
        self.stats = attributes
        #Below sets the values for the box on the right of the country card
        infantry = GAME.tinyBoldFont.render("Infantry: "+str(self.army.infantry), True, WHITE)
        tanks = GAME.tinyBoldFont.render("Tanks: "+str(self.army.tanks), True, WHITE)
        planes = GAME.tinyBoldFont.render("Planes: "+str(self.army.planes), True, WHITE)
        sdefense = GAME.tinyBoldFont.render("Defense Artillery: "+str(self.army.defenseArtillery), True, WHITE)
        sattack = GAME.tinyBoldFont.render("Attack Artillery: "+str(self.army.siegeArtillery), True, WHITE)
        forts = GAME.tinyBoldFont.render("Forts: "+str(self.fortifications), True, WHITE)
        rect = pygame.Surface((130, self.cardSize[1]/2))
        rect.fill(BLUE)
        temp = [infantry, tanks, planes, sdefense, sattack, forts]
        for i in range(len(temp)):
            rect.blit(temp[i], (2, 10+(17*i)))
        self.armyunits = rect
    
    def PurchaseUnit(self, unit: str):
        "Purchase a unit, where the string is the same as the button strings shown"
        #Check if theres enough production power left, remove it and add one to the unit
        if unit == "Infantry":
            if self.prodpower >= 75:
                self.army.AddInfantry(1)
                self.prodpower -= 75
                self.UnitsBought[0] += 1
        elif unit == "Tank":
            if self.prodpower >= 150:
                self.army.AddTanks(1)
                self.prodpower -= 150
                self.UnitsBought[1] += 1
        elif unit == "Plane":
            if self.prodpower >= 150:
                self.army.AddPlanes(1)
                self.prodpower -= 150
                self.UnitsBought[2] += 1
        elif unit == "Defense Artillery":
            if self.prodpower >= 100:
                self.army.AddDefenseArtillery(1)
                self.prodpower -= 100
                self.UnitsBought[3] += 1
        elif unit == "Attack Artillery":
            if self.prodpower >= 100:
                self.army.AddAttackArtillery(1)
                self.prodpower -= 100
                self.UnitsBought[4] += 1
        elif unit == "Fortification":
            if self.prodpower >= 300:
                self.fortifications += 1
                self.prodpower -= 300
                self.UnitsBought[5] += 1
        #Reset card details
        self.SetDetails()
    
    def Die(self):
        "Sets the dead flag and sets the image to the death image"
        self.image = self.deathImage
        self.dead = True
    
    def Reset(self):
        self.towns = self.baseTowns
        self.dead = False
        self.fortifications = self.basefortifications
        self.army = self.army.__class__()
        self.SetDetails()
        self.ResetPosition()
    
    def ToList(self) -> list:
        return [self.name, self.towns, self.type, self.production]
    
    def __hash__(self) -> str:
        "Creates a unique hash for the country"
        return Hash(f"{self.name}{self.production}{self.baseTowns}{self.type}")
    
    def __getstate__(self) -> dict:
        "Called by pickle.dump/s(), returns the variables needed for instanciation and its class"
        d = {"Production": self.production, "Towns": self.baseTowns, "Name": self.name, "instance": self.__class__}
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

class PlayerCountry(Country):
    "Subclass of country for player countries"
    def __init__(self, production, towns, name):

        Country.__init__(self, production, towns, name)
        self.player = True
    
class EnemyCountry(Country):
    "Subclass of country for enemy countries"
    def __init__(self, production, towns, name):

        Country.__init__(self, production, towns, name)
        self.player = False
        self.army = None #type: EnemyArmy

class AggressiveCountry(Country):
    "Subclass of country for aggressive countries"
    def __init__(self):
        if self.player:
            self.army = PlayerAggressiveArmy()
        else:
            self.army = EnemyAggressiveArmy()
        self.fortifications = 3
        self.basefortifications = 3
        card = pygame.image.load(resource_path("art/AggressiveCountry.png")).convert_alpha()
        card = pygame.transform.scale(card, self.cardSize)
        self.flippedImage = pygame.Surface(self.cardSize).convert_alpha()
        self.flippedImage.blit(card, (0, 0))
        self.rect = self.flippedImage.get_rect()
        self.type = "AGG"

class BalancedCountry(Country):
    "Subclass of country for balanced countries"
    def __init__(self):
        if self.player:
            self.army = PlayerBalancedArmy()
        else:
            self.army = EnemyBalancedArmy()
        self.fortifications = 4
        self.basefortifications = 4
        card = pygame.image.load(resource_path("art/BalancedCountry.png")).convert_alpha()
        card = pygame.transform.scale(card, self.cardSize)
        self.flippedImage = pygame.Surface(self.cardSize).convert_alpha()
        self.flippedImage.blit(card, (0, 0))
        self.rect = self.flippedImage.get_rect()
        self.type = "BAL"

class DefensiveCountry(Country):
    "Subclass of country for defensive countries"
    def __init__(self):
        if self.player:
            self.army = PlayerDefensiveArmy()
        else:
            self.army = EnemyDefensiveArmy()
        self.fortifications = 5
        self.basefortifications = 5
        card = pygame.image.load(resource_path("art/DefensiveCountry.png")).convert_alpha()
        card = pygame.transform.scale(card, self.cardSize)
        self.flippedImage = pygame.Surface(self.cardSize).convert_alpha()
        self.flippedImage.blit(card, (0, 0))
        self.rect = self.flippedImage.get_rect()
        self.type = "DEF"

### Below, multiple inheritance is used again. Class A

class PlayerAggressiveCountry(PlayerCountry, AggressiveCountry):
    "Subclass of country for player aggressive countries"
    def __init__(self, production: int, towns: int, name: int):
        PlayerCountry.__init__(self, production, towns, name)
        AggressiveCountry.__init__(self)
   
class PlayerDefensiveCountry(PlayerCountry, DefensiveCountry):
    "Subclass of country for player defensive countries"
    def __init__(self, production, towns, name):
        PlayerCountry.__init__(self, production, towns, name)
        DefensiveCountry.__init__(self)
        
class PlayerBalancedCountry(PlayerCountry, BalancedCountry):
    "Subclass of country for player balanced countries"
    def __init__(self, production, towns, name):
        PlayerCountry.__init__(self, production, towns, name)
        BalancedCountry.__init__(self)

class EnemyAggressiveCountry(EnemyCountry, AggressiveCountry):
    "Subclass of country for enemy aggressive countries"
    def __init__(self, production, towns, name):
        EnemyCountry.__init__(self, production, towns, name)
        AggressiveCountry.__init__(self)
    
class EnemyBalancedCountry(EnemyCountry, BalancedCountry): 
    "Subclass of country for enemy balanced countries"
    def __init__(self, production, towns, name):
        EnemyCountry.__init__(self, production, towns, name)
        BalancedCountry.__init__(self)

class EnemyDefensiveCountry(EnemyCountry, DefensiveCountry):

    def __init__(self, production, towns, name):
        EnemyCountry.__init__(self, production, towns, name)
        DefensiveCountry.__init__(self)

###################################################################################

class Connection:

    def __init__(self):
        t = Thread(target=LoadScreen, args=["Connecting to server!"])
        self.HOST = "81.157.207.171"
        self.PORT = 11034
        self.SOCK = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.regularSock = self.SOCK
        self.regularSock.settimeout(1)
        self.battleSock = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.battleSock.settimeout(1)
        self.battleEnemySock = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.battleEnemySock.settimeout(1)
        for event in GAME.getevent():
            pass
        self.__PUBLICKEY, self.__PRIVATEKEY = rsa.newkeys(2048)
        failed = True
        errorcount = 0
        while failed:
            for event in GAME.getevent():
                pass
            try:
                self.regularSock.connect((self.HOST, self.PORT))
                failed = False
            except Exception as e:
                print(e)
                errorcount += 1
            if errorcount == 15:
                raise er.InitialConnectionError
        self.SOCK.send(self.__PUBLICKEY.save_pkcs1("PEM"))
        failed = True
        while failed:
            for event in GAME.getevent():
                pass
            try:
                data = self.regularSock.recv(2048)
                self.__SERVERKEY = rsa.PublicKey.load_pkcs1(data, "PEM")
            except Exception as e:
                print(e)
                continue
            failed = False
        t.quit()
        t.join()

    def Receive(self) -> dict:
        "Receive a decoded dictionary containing necessary arguments"
        try:
            data = self.SOCK.recv(2048)
        except s.error as e:
            return {"Command": None, "Args": None}
        try:
            data = rsa.decrypt(data, self.__PRIVATEKEY)
        except Exception as e:
            print(e)
            return {"Command": None, "Args": None}
        asString = data.decode("utf-8")
        dictionary = json.loads(asString)
        print(f"{dictionary['Command']}", f"{dictionary['Args']} received")
        if dictionary["AUTH"] != AUTH:
            raise er.UnauthorisedMessageError
        return dictionary


    def Send(self, command: str, *args):
        "Takes a command and arguments and encodes and sends to server"
        d = {"AUTH": AUTH, "Command": None, "Args": None}
        d["Command"] = command
        if args:
            d["Args"] = args
        message = json.dumps(d)
        self.SOCK.send(rsa.encrypt(message.encode("utf-8"), self.__SERVERKEY))
        print(d["Command"], d["Args"], "sent to", self.SOCK.getpeername())
    

    def Login(self) -> bool:
        t = Thread(target=LoadScreen, args=["Logging In..."])
        data = CONN.Receive()
        while data["Command"] != "LOGIN":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
        if GAME.New:
            command = "SIGNUP"
        else:
            command = "LOGIN"
        self.Send(command, GAME.PLAYER.username, GAME.PLAYER.password)
        print("message sent")
        command = self.Receive()["Command"]
        while command == None:
            for event in GAME.getevent():
                pass
            command = self.Receive()["Command"]
        t.quit()
        t.join()
        if command == "LOGGEDIN":
            return True
        else:
            return False
    
    def AddCountry(self, c: Country):
        if hash(c) in [hash(x) for x in GAME.PLAYER.countries]:
            return
        GAME.PLAYER.countries.append(c)
        #self.Send("ADDCOUNTRY", c.name, c.towns, c.type, c.production)
    
    def AddBuff(self, b: Buff):
        if hash(b) in [hash(x) for x in GAME.PLAYER.buffs]:
            return
        GAME.PLAYER.buffs.append(b)
        a = [type(b).__name__[:-4]]
        #self.Send("ADDBUFF", a)
    
    def SetBattleMode(self):
        self.SOCK = self.battleSock
        connected = False
        while not connected:
            try:
                self.SOCK.connect((self.HOST, 11035))
                connected = True
            except Exception as e:
                if e == s.timeout:
                    continue
                else:
                    print(e)
    
    def SetNormalMode(self):
        try:
            self.battleSock.close()
        except:
            pass
        try:
            self.battleEnemySock.close()
        except:
            pass
        self.PORT = 11034
        self.SOCK = self.regularSock
    
    def SetBattlePlayerMode(self, enemyIP: str, first: bool):
        self.battleEnemySock = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.battleEnemySock.settimeout(1)
        if first:
            connected = False
            self.battleEnemySock.bind((self.SOCK.getsockname()[0], 11036))
            self.battleEnemySock.listen(1)
            while not connected:
                try:
                    self.newSock = self.battleEnemySock.accept()[0]
                    connected = True
                except Exception as e:
                    print(e)
                for event in GAME.getevent():
                    pass
            self.SOCK = self.newSock
        else:
            connected = False
            while not connected:
                try:
                    print(enemyIP)
                    self.battleEnemySock.connect((enemyIP, 11036))
                    connected = True
                except Exception as e:
                    print(e)
                    break
                for event in GAME.getevent():
                    pass
            self.SOCK = self.battleEnemySock
        self.battleSock.close()
    
    def SendToPlayer(self, command: str, key: rsa.PublicKey, *args):
        "Takes a command and arguments and encodes and sends to server"
        d = {"AUTH": AUTH, "Command": None, "Args": None}
        d["Command"] = command
        if args:
            d["Args"] = args
        message = json.dumps(d)
        data = rsa.encrypt(message.encode("utf-8"), key)
        self.SOCK.send(data)
        print(d["Command"], d["Args"], "sent to", self.SOCK.getpeername())

##################################################################################

class Player:

    def __init__(self, username="", password=0, countries=[], buffs=[], wins=0, losses=0, elo=0, ip="", key=""):
        "Player object containing relevant player data"
        self.username = username #type: str
        self.password = password #type: str
        self.countries = countries #type: list[Country]
        self.buffs = buffs #type: list[Buff]
        self.wins = wins #type: int
        self.losses = losses #type: int
        self.elo = elo #type: int
        self.ip = ip
        self.prioritycountries = [] #type: list[Country]
        self.prioritybuffs = [] #type: list[Buff]
        self.key = key #type: rsa.PublicKey
        if isinstance(self.key, rsa.PublicKey):
            print("key: ", self.key._save_pkcs1_pem())
    
    def Text(self) -> str:
        "Returns a string in the form USERNAME - Elo: ELO"
        return f"{self.username} - Elo: {self.elo}"
    
    def SetPassword(self, password: str):
        "Takes a plaintext password, then hashes and stores it in the password attribute"
        self.password = sha256(password.encode("utf-8"), usedforsecurity=True).hexdigest()
    
    def SetUsername(self, username: str):
        self.username = username
    
    def SetPriority(self, card: Card):
        if isinstance(card, Buff):
            priority = self.prioritybuffs
        else:
            priority = self.prioritycountries
        if card in priority:
            return
        priority.append(card)
        card.priority = True
        CONN.Send("PRIORITYCOUNTRY", hash(card))
        while len(priority) > 2:
            old = priority.pop(0)
            old.priority = False
            CONN.Send("DEPRIORITISECOUNTRY", hash(old))
    
    def ChangeElo(self, newElo: int):
        self.elo = newElo

    def __getstate__(self) -> dict:
        return self.__dict__
    
    def __setstate__(self, d: dict):
        self.__dict__ = d

###################################################################################

class Game:

    def __init__(self):
        "Object containing necessary game data and initialisation procedure. Also deals with saving the game"
        pygame.init()
        pygame.display.set_caption("Clash Of Countries") 
        self.SCREENWIDTH = 1080
        self.SCREENHEIGHT = 720
        self.__screen = pygame.display.set_mode((self.SCREENWIDTH, self.SCREENHEIGHT))
        pygame.display.set_icon(pygame.image.load(resource_path("clashofcountries.ico")).convert_alpha())
        self.screen = pygame.Surface((self.SCREENWIDTH, self.SCREENHEIGHT)).convert_alpha()
        self.FPS = 65
        self.boldFont = pygame.font.Font(resource_path("fonts/rexlia.otf"), 24)
        self.regularFont = pygame.font.Font(resource_path("fonts/rexlia.otf"), 14)
        self.tinyBoldFont = pygame.font.Font(resource_path("fonts/rexlia.otf"), 11)
        self.smallBoldFont = pygame.font.Font(resource_path("fonts/rexlia.otf"), 16)
        self.bigBoldFont = pygame.font.Font(resource_path("fonts/rexlia.otf"), 40)
        self.clock = pygame.time.Clock()
        self.PLAYER = Player(username="PLACEHOLDER", elo="1000")
        background = pygame.image.load(resource_path("art/battle.png")).convert_alpha()
        self.background = pygame.transform.scale(background, (1080, 720))
        self.titlescreen = pygame.image.load(resource_path("art/titlescreen.png")).convert_alpha()
        self.shaking = False
        self.shakeMagnitude = 0
        self.shakeMagnitudeRange = 0
        self.shaken = False
        self.MainMenuItems = [] #type: list[Button]
        self.Area = "MainMenu"
        pygame.mixer.init()
        self.MusicPlayer = pygame.mixer.music
        self.SFXPlayer = pygame.mixer.Sound
        self.ClickSound = pygame.mixer.Sound(resource_path("sfx/click.ogg"))
        self.BattleSound = []
        for i in range(1, 4):
            self.BattleSound.append(pygame.mixer.Sound(resource_path(f"sfx/shots{i}.ogg")))
        self.MarchingSound = pygame.mixer.Sound(resource_path("sfx/march.ogg"))
    
    def LoadPlayer(self):
        t = Thread(LoadScreen, ["Loading Player Data..."])
        try:
            with open(path.abspath(path.dirname(sys.argv[0])) + "/COC.save", "rb") as f:
                self.PLAYER = pickle.load(f)
                if not isinstance(self.PLAYER, Player):
                    raise TypeError
                f.close()
            self.New = False
        except:
            self.Save()
            self.New = True
        t.quit()
        t.join()
        

    def Draw_bg(self):
        "Draws background for the battles"
        self.screen.blit(self.background, (0, 0))
    
    def Draw_menu(self):
        "Adds "
        if self.MainMenuItems == []:
            xOffset = GAME.SCREENWIDTH // 12
            PlayButton = Button("Play", BLACK, BLUE, ROYALBLUE, GAME.boldFont, xOffset, 620, 100, 50)
            self.MainMenuItems.append(PlayButton)
            TutorialButton = Button("Tutorial", BLACK, BLUE, ROYALBLUE, GAME.boldFont, 5*xOffset, 620, 100, 50)
            self.MainMenuItems.append(TutorialButton)
            exitButton = Button("Exit", BLACK, BLUE, ROYALBLUE, GAME.boldFont, 9*xOffset, 620, 100, 50)
            self.MainMenuItems.append(exitButton)
        
    def SetArea(self, area):
        self.Area = area

    def Save(self):
        "Saves the player object to COC.save"
        t = Thread(LoadScreen, ["Saving Game..."])
        with open(path.abspath(path.dirname(sys.argv[0])) + "/COC.save", "wb") as f:
            pickle.dump(self.PLAYER, f)
            f.close()
        t.quit()
        t.join()

    def Update(self):
        self.__screen.fill(BLACK)
        if self.shaking: #Checks if shaking flag set
            self.shakeMagnitudeRange *= -1 #Flip the offset from left to right or right to left
            if self.shakeMagnitudeRange > 0: #If its not 0, decrement the absolute value by 0.5
                self.shakeMagnitudeRange -= 0.5
            elif self.shakeMagnitudeRange < 0:
                self.shakeMagnitudeRange += 0.5
            elif self.shakeMagnitudeRange == 0:           
                self.shaking = False #If its 0, it is no longer shaking
            num = r.random() 
            if num < 0.4:
                self.shakeMagnitude = 0 #set offset to 0 40% of the time to Add uniqueness and fluidity
            else:
                self.shakeMagnitude = self.shakeMagnitudeRange
            self.UpdateFPS()
            self.__screen.blit(self.screen, (self.shakeMagnitudeRange, 0)) #Blit game surface to the display with the offset
        else:
            self.UpdateFPS()
            self.__screen.blit(self.screen, (0, 0)) #If not shaking, skip comparisons and operations and blit it to display normally
        self.clock.tick(self.FPS) #Add one to the frame counter
        
        pygame.display.update() #Updates display
        self.screen.fill(BLACK)

    def Shake(self, magnitude: int):
        "Sets the screen Shake flags and sets the magnitude in pixels"
        self.shaking = True
        self.shakeMagnitudeRange = magnitude
        self.shaken = True
    
    def Reset(self):
        "Resets the screen Shake flags"
        self.shaking = False
        self.shaken = False
        self.shakeMagnitude = 0
    
    def UpdateFPS(self):
        fps = "FPS: " + str(int(self.clock.get_fps()))
        text = self.smallBoldFont.render(fps, True, BLACK)
        GAME.screen.blit(text, (10, 51))
    
    def getevent(self) -> list:
        return pygame.event.get()
        
#####################################################################################

class GameMessage(pygame.sprite.Sprite):
    def __init__(self, Text: str, font: pygame.font.Font, colour: str, rect: pygame.Rect, timer: int, infinite=False):
        "Class containing both timed and infinite game messages - use infinite flag to set infinite timer"
        pygame.sprite.Sprite.__init__(self)
        self.string = Text
        self.font = font
        if infinite:
            self.timer = 1
            self.UpdateBool = False
        else:
            self.UpdateBool = True
            self.timer = timer
        self.rect = rect
        self.textColour = colour
        self.boxColour = BLUE
    
    def Draw(self):  #Not my function, obtained and modified from www.pygame.org/wiki/TextWrap
        "Fits Text inside the message and Draws it to the screen"
        rect = self.rect
        border = pygame.Rect(rect.left-2, rect.top-2, rect.width+4, rect.height+4)
        y = rect.top
        lineSpacing = -2
        font = self.font
        # get the height of the font
        fontHeight = GAME.boldFont.size("Tg")[1]
        Text = self.string
        pygame.draw.rect(GAME.screen, BLACK, border)
        pygame.draw.rect(GAME.screen, BLUE, rect)
        while Text:
            i = 1

            # determine if the row of Text will be outside our area
            if y + fontHeight > rect.bottom:
                break

            # determine maximum width of line
            while font.size(Text[:i])[0] < rect.width and i < len(Text):
                i += 1

            # if we've wrapped the Text, then adjust the wrap to the last word      
            if i < len(Text): 
                i = Text.rfind(" ", 0, i) + 1

            # render the line and blit it to the surface
            image = font.render(Text[:i], 1, self.textColour)

            GAME.screen.blit(image, (rect.left+2, y))
            y += fontHeight + lineSpacing

            # remove the Text we just blitted
            Text = Text[i:]

#####################################################################################

class MessageQueue():
    "Class containing game message queue, so that messages cannot override each other"
    def __init__(self, length):
        self._items = []
        self._start = 0
        self._end = 0
        self._length = length
        for i in range(0, length):
            self._items.append(None)
                
    def QueuePop(self):
        if self._start == self._length - 1:
            self._start = 0
        else:
            self._start += 1
    def Add(self, item: GameMessage):
        self._items[self._end] = item
        if self._end == self._length - 1:
            self._end = 0
        else:
            self._end += 1

    def Update(self):
        "Draw item onto the screen, reduce the timer by 1, and kill the object if the timer hits 0"
        if self._items[self._start] is not None:
            if self._items[self._start].UpdateBool:
                self._items[self._start].timer -= 1
                self._items[self._start].Draw()
            if self._items[self._start].timer <= 0:
                self._items[self._start].kill()
                self._items[self._start] = None
                self.QueuePop()
    
    def IsEmpty(self) -> bool:
        if self._items[self._start] is None:
            return True
        return False
#####################################################################################

class Button:
    "Class for a simple button"
    def __init__(self, Text: str, textColour: str, boxColour: str, highlightColour: str, font: pygame.font.Font, left: float, top: float, width: float, height: float, hintText="", highlighttext=[]):
        self.string = str(Text)
        self.left = float(left)
        self.top = float(top)
        self.width = float(width)
        self.height = float(height)
        self.rect = pygame.Rect(self.left, self.top, self.width, self.height)
        self.textHeight = self.top + (self.height // 2)
        self.textCentre = self.left + (self.width // 2)
        self.textColour = textColour
        self.boxColour = boxColour
        self.font = font
        self.Text = self.font.render(Text, True, self.textColour)
        self.TextBox = self.Text.get_rect(center=(self.textCentre, self.textHeight))
        self.highlightColour = highlightColour
        self.border = pygame.Rect(self.left-2, self.top-2, self.width+4, self.height+4)
        self.hintText = GAME.smallBoldFont.render(hintText, True, WHITE)
        self.hintBox = self.hintText.get_rect(center=(self.textCentre, self.textHeight-25))
        if highlighttext != []:
            self.highlightBox = pygame.Rect(left, top - 82, width, 80)
            self.hboxborder = pygame.Rect(left-2, top-84, width + 4, 84)
            self.highlighttext = []
            for text in highlighttext:
                self.highlighttext.append(GAME.tinyBoldFont.render(text, True, WHITE))
        else:
            self.highlighttext = False
    def Draw(self):
        "Draw button and a black border around it to the screen"
        pygame.draw.rect(GAME.screen, BLACK, self.border)
        pygame.draw.rect(GAME.screen, self.boxColour, self.rect)
        GAME.screen.blit(self.Text, self.TextBox)
        GAME.screen.blit(self.hintText, self.hintBox)
        
    def Highlight(self):
        "Draw highlighted button"
        pygame.draw.rect(GAME.screen, self.highlightColour, self.rect)
        GAME.screen.blit(self.Text, self.TextBox)
        GAME.screen.blit(self.hintText, self.hintBox)
        if self.highlighttext is not False:
            pygame.draw.rect(GAME.screen, BLACK, self.hboxborder)
            pygame.draw.rect(GAME.screen, self.boxColour, self.highlightBox)
            y = self.highlightBox.y + 10
            for text in self.highlighttext:
                GAME.screen.blit(text, (self.highlightBox.x+3, y))
                y += 12
    
    def UpdateString(self, string: str):
        self.string = string
        self.Text = self.font.render(string, True, self.textColour)
        self.TextBox = self.Text.get_rect(center=(self.textCentre, self.textHeight))

##########################################################################################

class Battle:
    "Class containing logic for each battle"
    def __init__(self, player: Player, playerCountries: 'list[PlayerCountry]', playerBuffs: 'list[Buff]', enemy: Player, enemyCountries: 'list[EnemyCountry]', enemyBuffs: 'list[Buff]', playerFirst: bool):
        self.playerFirst = playerFirst
        self.playerCountries = playerCountries
        self.playerBuffs = playerBuffs
        self.enemy = enemy
        self.enemyCountries = enemyCountries
        self.enemyBuffs = enemyBuffs
        self.countries = self.playerCountries + self.enemyCountries #type: list[Country]
        self.buffs = self.playerBuffs + self.enemyBuffs #type: list[Buff]
        self.cards = self.countries + self.buffs #type: list[Country or Buff]
        for card in self.cards:
            card.Reset()
            card.SetDetails()
        self.background = GAME.background
        self.setPlayerPositions() #type: list[tuple[int, int]]
        self.setEnemyPositions() #type: list[tuple[int, int]]
        self.messageQueue = MessageQueue(50)
        self.GameBar = GameBar(player, enemy, playerFirst)
        self.NextTurnButton = Button("Confirm Actions", BLACK, BLUE, ROYALBLUE, GAME.tinyBoldFont, 900, 55, 150, 30)
        self.StageManager = StageManager(enemyCountries, enemyBuffs, playerCountries, playerBuffs, self)
        self.victoryScreen = pygame.image.load(resource_path("art/Victory.png")).convert_alpha()
        self.defeatScreen = pygame.image.load(resource_path("art/Defeat.png")).convert_alpha()
        self.run = False
        self.TutorialDialogue = False
        GAME.MusicPlayer.unload()
        GAME.MusicPlayer.load(resource_path("music/Battle.ogg"))
        self.PlayerActions = [[[hash(self.countries[0]), None], [], None], [[hash(self.countries[1]), None], [], None]]
    
    def Run(self):
        "Begin the battle game loop"
        GAME.MusicPlayer.set_volume(0.1)
        GAME.MusicPlayer.play(-1)
        click = False
        clicked = False
        self.run = True
        while self.run: #Game loop
            if click and not clicked: #Only lets one click occur instead of keeping the flag at true for the frames
                click = True          #where the left mouse button is pressed down
                clicked = True
            else:
                click = False

            GAME.Draw_bg() #Blits background to game surface
            self.GameBar.Draw(self.StageManager.GetTurn()) #Blits top game bar to game surface
            mx, my = pygame.mouse.get_pos() #Gets mouse position
            self.messageQueue.Update() #Updates game messages
            renderableobjs = self.StageManager.UpdateAndGetRenderables()       
            for renderable in renderableobjs:
                renderable.Draw()
                if renderable.rect.collidepoint((mx, my)):
                    if isinstance(renderable, Button):
                        if click:
                            GAME.SFXPlayer.play(GAME.ClickSound)
                            self.StageManager.ButtonClicked(renderable)
                        renderable.Highlight()
                    elif isinstance(renderable, Card):
                        if click:
                            GAME.SFXPlayer.play(GAME.ClickSound)
                            self.StageManager.CardClicked(renderable)
                    
            for event in GAME.getevent():                       #Gets user input events, iterates through them
                if event.type == pygame.QUIT: 
                    GAME.SFXPlayer.play(GAME.ClickSound)           #If cross in corner pressed, stop running this game loop
                    if not isinstance(self, TutorialBattle):
                        CONN.SendToPlayer("RESIGN", self.enemy.key)
                    self.BattleFinished(False)
                    self.run = False                               #This will return you to the Main Menu
                elif event.type == pygame.MOUSEBUTTONDOWN:         #Checks for clicks
                    if event.button == 1:                          #If left click
                        click = True                               #Set click flag
                elif event.type == pygame.MOUSEBUTTONUP:           #If stopped clicking
                    clicked = False                                #Allow clicks to work again
                    

            GAME.Update() #Update the game

        for card in self.playerCountries:
            card.Reset()
        for card in self.playerBuffs:
            card.Reset()
    
    def setPlayerPositions(self):
        "Set player positions with respect to the screen size"
        for i in range(2):
            pos = (GAME.SCREENWIDTH/4+50, 220+270*i)
            self.playerCountries[i].UpdatePosition(pos)
        for i in range(2):
            pos = (130, 220+270*i)
            self.playerBuffs[i].UpdatePosition(pos)
    
    def setEnemyPositions(self):
        "Set enemy positions with respect to the screen size"
        for i in range(2):
            pos = ((GAME.SCREENWIDTH/4)*3-50, 220+270*i)
            self.enemyCountries[i].UpdatePosition(pos)
        for i in range(2):
            pos = (GAME.SCREENWIDTH-130, 220+270*i)
            self.enemyBuffs[i].UpdatePosition(pos)

    def ReceiveEnemyActions(self) -> list:
        CONN.SendToPlayer("READYTORECEIVE", self.enemy.key)
        data = CONN.Receive()
        while data["Command"] != "CHANGES":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
        CONN.SendToPlayer("RECEIVED", self.enemy.key)
        data2 = CONN.Receive()
        while data2["Command"] != "CHANGES":
            for event in GAME.getevent():
                pass
            data2 = CONN.Receive()
        CONN.SendToPlayer("RECEIVED", self.enemy.key)
        temp = [data["Args"][0], data2["Args"][0]]
        print(temp)
        return temp

    def SendPlayerActions(self):
        CONN.SendToPlayer("CHANGES", self.enemy.key, self.PlayerActions[0])
        data = CONN.Receive()
        while data["Command"] != "RECEIVED":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
        CONN.SendToPlayer("CHANGES", self.enemy.key, self.PlayerActions[1])
        data = CONN.Receive()
        while data["Command"] != "RECEIVED":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()

    def GetEnemyActions(self) -> list:
        "Get the enemy players choices and send off your own"
        t = Thread(target=LoadScreen, args=["Waiting for enemy..."])
        for i in range(2):
            self.PlayerActions[i][2] = hash(self.playerCountries[i].Buff)
            self.PlayerActions[i][1] = self.playerCountries[i].UnitsBought
        if self.playerFirst:
            CONN.SendToPlayer("READY", self.enemy.key)
            data = CONN.Receive()
            while data["Command"] != "READY" and data["Command"] != "RESIGN":
                for event in GAME.getevent():
                    pass
                data = CONN.Receive()
        else:
            data = CONN.Receive()
            while data["Command"] != "READY" and data["Command"] != "RESIGN":
                for event in GAME.getevent():
                    pass
                data = CONN.Receive()
            CONN.SendToPlayer("READY", self.enemy.key)
        
        if data["Command"] == "RESIGN":
            t.quit()
            t.join()
            self.BattleFinished(True)
            return
        if self.playerFirst:
            self.SendPlayerActions()
            CONN.SendToPlayer("READYTORECEIVE", self.enemy.key)
            data = self.ReceiveEnemyActions()
        else:
            data = self.ReceiveEnemyActions()
            data2 = CONN.Receive()
            while data2["Command"] != "READYTORECEIVE":
                for event in GAME.getevent():
                    pass
                data2 = CONN.Receive()
            self.SendPlayerActions()
        self.PlayerActions = [[[hash(self.countries[0]), None], [], None], [[hash(self.countries[1]), None], [], None]]
        t.quit()
        t.join()
        return data

    def BattleFinished(self, win: bool):
        t = Thread(target=LoadScreen, args=["Getting rewards..."])
        if win:
            msg = "GETREWARDWIN"
            screen = self.victoryScreen
        else:
            msg = "GETREWARDLOSS"
            screen = self.defeatScreen
        if not isinstance(self, TutorialBattle):
            CONN.SetNormalMode()
        else:
            msg = "GETREWARDTUTORIAL"
        CONN.Send(msg)
        rewardCard = self.GetRewards() #type: Card
        timeTaken = self.GameBar.GetBattleTime()
        timeTaken = GAME.smallBoldFont.render(timeTaken, True, WHITE)
        enemyString = self.GameBar.enemy.username
        enemyString = GAME.smallBoldFont.render(enemyString, True, WHITE)
        if isinstance(self, TutorialBattle):
            eloGain = "0"
        else:
            data = CONN.Receive()
            while data["Command"] != "ELO":
                for event in GAME.getevent():
                    pass
                data = CONN.Receive()
                continue
            elo = int(data["Args"][0])
            eloGain = str(elo - int(GAME.PLAYER.elo))
            GAME.PLAYER.ChangeElo(elo)
        if isinstance(rewardCard, Country):
            CONN.AddCountry(rewardCard)
        elif isinstance(rewardCard, Buff):
            CONN.AddBuff(rewardCard)
        eloGain = GAME.smallBoldFont.render(eloGain, True, WHITE)
        rewardCard.rect.topleft = (660, 250)
        rewardCard.Flip()
        rewardCard.SetDetails()
        timer = 0
        t.quit()
        t.join()
        while timer <= 500:
            timer += 1
            GAME.screen.blit(screen, (0, 0))
            GAME.screen.blit(timeTaken, (440, 205))
            GAME.screen.blit(enemyString, (440, 263))
            GAME.screen.blit(eloGain, (440, 325))
            rewardCard.Update()
            rewardCard.Draw()
            for event in GAME.getevent():                       #Gets user input events, iterates through them
                if event.type == pygame.QUIT:                      #If cross in corner pressed, stop running this game loop
                    break
            GAME.Update()
        self.run = False

    def GetRewards(self) -> Card:
        data = CONN.Receive()
        while data["Command"] != "REWARD":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
        card = None
        if data["Args"][0] == "COUNTRY":
            name = data["Args"][1]
            towns = data["Args"][2]
            subclass = data["Args"][3]
            production = data["Args"][4]
            if subclass == "AGG":
                card = PlayerAggressiveCountry(production, towns, name)
            elif subclass == "BAL":
                card = PlayerBalancedCountry(production, towns, name)
            elif subclass == "DEF":
                card = PlayerDefensiveCountry(production, towns, name)
        elif data["Args"][0] == "BUFF":
            card = eval(data["Args"][1]+"Buff(True)")
        CONN.Send("RECEIVED")
        return card

class TutorialBattle(Battle):
    "Class containing the slightly different logic from a normal battle"
    def __init__(self, playerName, playerCountries: list, playerBuffs: list, enemyName, enemyCountries: list, enemyBuffs: list):
        super(TutorialBattle, self).__init__(playerName, playerCountries, playerBuffs, enemyName, enemyCountries, enemyBuffs, True)
        if GAME.New:
            self.TutorialDialogue = False

    def GetEnemyActions(self) -> list:
        "Returns a list containing actions for each country, from top to bottom. list[0] = [[ATTACKLIST], [PRODUCTIONLIST], [BUFFLIST]]"
        actionList = []
        actions = ["Production", "Attack", "ApplyBuff"]
        productionList = ["Infantry", "Tank", "Plane", "Defense Artillery", "Attack Artillery", "Fortification"]
        buffs = self.enemyBuffs.copy()
        countries = self.enemyCountries
        for country in countries:
            if country.dead:
                actionList.append([])
                continue
            buff = None
            enemyCard = None
            for action in actions:
                if action == "Attack":
                    if r.random() > 0.5:
                        enemyCard = self.playerCountries[r.randint(0, len(self.playerCountries)-1)]
                        while enemyCard.dead:
                            enemyCard = self.playerCountries[r.randint(0, len(self.playerCountries)-1)]
                elif action == "Production":
                    while country.prodpower >= 75:
                        unit = productionList[r.randint(0, len(productionList)-1)]
                        country.PurchaseUnit(unit)
                elif action == "ApplyBuff":
                    if country.Buff is None:
                        try:
                            num = r.randint(0, len(buffs)-1)
                        except ValueError:
                            num = 0
                        buff = buffs[num]
                        buffs.remove(buff)
                        buff.ApplyToCountry(country)
            templist = [[hash(country), None], country.UnitsBought.copy(), None]
            if enemyCard is not None:
                templist[0][1] = hash(enemyCard)
            if buff is not None:
                templist[2] = hash(buff)
            actionList.append(templist)
                    
        return actionList
      
################################################################################################################

class StageManager:
    "Class to manage the game progression thats seperate to the game loop"
    def __init__(self, enemyCountries: list["EnemyCountry"], enemyBuffs: list["Buff"], playerCountries: list["PlayerCountry"], playerBuffs: list["Buff"], battle: Battle):
        self._Stage = "Move"
        self._cards = enemyCountries + enemyBuffs + playerCountries + playerBuffs #type: list[Card]
        self._Countries = enemyCountries + playerCountries #type: list[Country]
        self._PlayerCountries = playerCountries
        self._PlayerBuffs = playerBuffs
        self._EnemyCountries = enemyCountries
        self._EnemyBuffs = enemyBuffs
        self._AttackTracker = AttackTracker()
        self._Renderables = {"Move": None, "Flip": None, "CountryOptions": None, "BuffOptions": None, "Attack": None, "Production": None,  
                            "Attacking": None, "Victory": None, "Defeat": None, "ActionDenied": None, "ApplyBuff": None, "Tutorial": None}
        self._ActionBox = Box((1080, 100), BLUE, (0, GAME.SCREENHEIGHT-100))
        self._NextTurnButton = Button("Next Turn", BLACK, BLUE, ROYALBLUE, GAME.smallBoldFont, 940, 55, 110, 30)
        self._CardSelected = None #type: PlayerCountry or Buff
        self._TempProductionQueue = []
        self._Battle = battle
        self._Turn = 1
        self._ActionDeniedTimer = 0
        self._ClickableStages = ["CountryOptions", "BuffOptions", "ChooseBuff", "Game", "ChooseAttack", "ChooseProduction"]
        self._AttackInProgress = False
        self._Combatants = () #type: tuple[Country, Country]
        self.GunShotsPlaying = False
        self.BattleWaitTime = 0
        self.PlayerCardsDead = 0
        self.EnemyCardsDead = 0

    def UpdateAndGetRenderables(self):
        renderables = [self._NextTurnButton]
        renderables += self._cards
        if self.PlayerCardsDead == 2:
            self._Battle.BattleFinished(False)
        elif self.EnemyCardsDead == 2:
            self._Battle.BattleFinished(True)

        for card in self._PlayerCountries:
            if card.highlighted and self._Stage == "ChooseProduction":
                card.DrawUnits()
        if self._Stage == "Move":
            renderables += self.RenderMoveStage()
        elif self._Stage == "Flip":
            renderables += self.RenderFlipStage()
        elif self._Stage == "CountryOptions":
            renderables += [self._ActionBox]
            renderables += self.RenderCountryOptions()
        elif self._Stage == "BuffOptions":
            renderables += [self._ActionBox]
            renderables += self.RenderBuffOptions()
        elif self._Stage == "ChooseAttack":
            renderables += [self._ActionBox]
            renderables += self.RenderAttackOptions()
        elif self._Stage == "ChooseProduction":
            renderables += [self._ActionBox]
            renderables += self.RenderProductionOptions()
        elif self._Stage == "ChooseBuff":
            renderables += [self._ActionBox]
            renderables += self.RenderApplyBuffOptions()
        elif self._Stage == "ActionsAttacking":
            renderables += self.PerformAttack()
        elif self._Stage == "ActionDenied":
            renderables += self.ActionDenied()
        elif self._Stage == "Tutorial":
            renderables += self.RenderTutorial()
        return renderables 

    def ButtonClicked(self, button: Button):
        if self._Stage not in self._ClickableStages:
            return
        if button.string == "Next Turn" and not self._Stage.startswith("Actions"):
            self._Stage = "NewTurn"
            self.NewTurn()
            return
        elif button.string == "Attack":
            self._Stage = "ChooseAttack"
        elif button.string == "Build Units":
            self._Stage = "ChooseProduction"
        elif self._Stage == "BuffOptions":
            self.HandleBuffOptions(button.string)
        elif self._Stage == "ChooseProduction":
            self.HandleProductionChoices(button)
        
    def CardClicked(self, card: Card):
        if self._Stage not in self._ClickableStages:
            return
        if isinstance(card, PlayerCountry):
            if self._Stage == "ChooseBuff":
                self.ApplyBuff(card)
            else:
                self.CountryClicked(card)
        elif isinstance(card, Buff) and card.player:
            self.BuffClicked(card)
        elif isinstance(card, EnemyCountry) and self._Stage == "ChooseAttack":
            self.HandleAttackChoice(card)
    
    def CountryClicked(self, country: Country):
        if country.dead:
            return
        if country == self._CardSelected:
            self.Reset()
            self.NextStage()
        else:
            self.Reset()
            self._CardSelected = country
            self._CardSelected.highlighted = True
            self._Stage = "CountryOptions"

    def BuffClicked(self, buff: Buff):
        if self._Stage not in self._ClickableStages:
            return
        if buff == self._CardSelected:
            self.Reset()
            self.NextStage()
        else:
            self.Reset()
            self._CardSelected = buff
            buff.highlighted = True
            self._Stage = "BuffOptions"
    
    def ApplyBuff(self, country: PlayerCountry):
        if country.dead:
            self._Stage = "ActionDenied"
            return
        if self._CardSelected.country is not None:
            self._CardSelected.country.RemoveBuff()
        if country.Buff is not None:
            country.Buff.country = None
            country.RemoveBuff()
        country.AddBuff(self._CardSelected)
        if isinstance(self._CardSelected, Buff):
            self._CardSelected.ApplyToCountry(country)
        for country in self._PlayerCountries:
            country.highlighted = False
        self.Reset()
    
    def RenderApplyBuffOptions(self):
        if self._Renderables["ApplyBuff"] is not None:
            return self._Renderables["ApplyBuff"]
        Text = TextBox("Select a country to buff!", WHITE, 20, GAME.SCREENHEIGHT-80, 60, 1040, font=GAME.boldFont)
        tempList = [Text]
        self._Renderables["ApplyBuff"] = tempList + self._PlayerCountries
        
        for country in self._PlayerCountries:
            country.highlighted = True
        
        return self._Renderables["ApplyBuff"]

    def RenderMoveStage(self):
        if self._Renderables["Move"] is not None:
            cards = self._Renderables["Move"]
        else:
            tempList = self._Countries + self._PlayerBuffs + self._EnemyBuffs
            self._Renderables["Move"] = tempList
            cards = self._Renderables["Move"]

        inProgress = False
        for card in cards:
            if not card.inPos:
                inProgress = True
            card.Update()

        if not inProgress:
            self.NextStage()
        return []

    def RenderFlipStage(self):
        if self._Renderables["Flip"] is not None:
            cards = self._Renderables["Flip"]
        else:
            tempList = self._Countries + self._PlayerBuffs + self._EnemyBuffs
            self._Renderables["Flip"] = tempList
            cards = self._Renderables["Flip"]
        inProgress = False
        for card in cards:
            if not card.flipped:
                inProgress = True
                if not card.flipping:
                    card.Flip()
            card.Update()
        if not inProgress:
            self.NextStage()
        return []

    def RenderProductionOptions(self):
        if self._Renderables["Production"] is not None:
            pp = str(self._CardSelected.prodpower)
            productiontext = Text("Production Power: " + pp, 5, 70)
            return self._Renderables["Production"] + [productiontext]
        infantry = Button("Infantry", BLACK, BLUE, ROYALBLUE, GAME.smallBoldFont, 5, 625, 170, 75, hintText="Cost: 75pp", highlighttext=["Attack: 4", "Defense: 12", "Siege Attack: 0", "Siege Defense: 2"])
        tanks = Button("Tank", BLACK, BLUE, ROYALBLUE, GAME.smallBoldFont, 185, 625, 170, 75, hintText="Cost: 150pp", highlighttext=["Attack: 25", "Defense: 15", "Siege Attack: 5", "Siege Defense: 0"])
        planes = Button("Plane", BLACK, BLUE, ROYALBLUE, GAME.smallBoldFont, 365, 625, 170, 75, hintText="Cost: 150pp", highlighttext=["Attack: 30", "Defense: 10", "Siege Attack: 0", "Siege Defense: 0"])
        sdefense = Button("Defense Artillery", BLACK, BLUE, ROYALBLUE, GAME.smallBoldFont, 545, 625, 170, 75, hintText="Cost: 125pp", highlighttext=["Attack: 5", "Defense: 5", "Siege Attack: 20", "Siege Defense: 0"])
        sattack = Button("Attack Artillery", BLACK, BLUE, ROYALBLUE, GAME.smallBoldFont, 725, 625, 170, 75, hintText="Cost: 125pp", highlighttext=["Attack: 5", "Defense: 5", "Siege Attack: 0", "Siege Defense: 20"])
        forts = Button("Fortification", BLACK, BLUE, ROYALBLUE, GAME.smallBoldFont, 905, 625, 170, 75, hintText="Cost: 350pp", highlighttext=["+1 Fort", "Defense: 200"])
        pp = str(self._CardSelected.prodpower)
        productiontext = TextBox("Production Power: " + pp, BLACK, 5, self._ActionBox.rect.y-32, 30, 300, GAME.smallBoldFont, border=True)
        tempList = [infantry, tanks, planes, sdefense, sattack, forts]
        self._Renderables["Production"] = tempList
        return self._Renderables ["Production"] + [productiontext]
        
    def RenderCountryOptions(self):
        if self._Renderables["CountryOptions"] is not None:
            return self._Renderables["CountryOptions"]
        AttackButton = Button("Attack", BLACK, BLUE, ROYALBLUE, GAME.boldFont, GAME.SCREENWIDTH//8, 645, 150, 50)
        ProductionButton = Button("Build Units", BLACK, BLUE, ROYALBLUE, GAME.smallBoldFont, ((GAME.SCREENWIDTH//8)*2)+100, 645, 150, 50)
        self._Renderables["CountryOptions"] = [AttackButton, ProductionButton]
        return self._Renderables["CountryOptions"]
    
    def RenderBuffOptions(self):
        if self._Renderables["BuffOptions"] is not None:
            return self._Renderables["BuffOptions"]
        ApplyBuffButton = Button("Apply", BLACK, BLUE, ROYALBLUE, GAME.boldFont, GAME.SCREENWIDTH//8, 645, 150, 50)
        RemoveBuffButton = Button("Remove", BLACK, BLUE, ROYALBLUE, GAME.boldFont, (GAME.SCREENWIDTH//8)*2 + 100, 645, 150, 50)
        self._Renderables["BuffOptions"] = [ApplyBuffButton, RemoveBuffButton]
        return self._Renderables["BuffOptions"]
        
    def RenderAttackOptions(self):
        if self._Renderables["Attack"] is None:
            Text = TextBox("Select a country to attack!", WHITE, 20, GAME.SCREENHEIGHT-80, 60, 1040, font=GAME.boldFont)
            tempList = [Text]
            self._Renderables["Attack"] = tempList + self._EnemyCountries

        for country in self._EnemyCountries:
            country.highlighted = True
        
        return self._Renderables["Attack"]
    
    def RenderTutorial(self):
        if self._Renderables["Tutorial"] != None:
            if self._Battle.messageQueue.IsEmpty():
                self.NextStage()
        else:
            rect = pygame.Rect(GAME.SCREENWIDTH/2-125, GAME.SCREENHEIGHT/2-180, 250, 180)
            with open(resource_path("txt/t.txt"), "r") as f:
                for line in f.readlines():
                    message = GameMessage(line.strip(), GAME.smallBoldFont, WHITE, rect, 310)
                    self._Battle.messageQueue.Add(message)
                f.close()
            self._Renderables["Tutorial"] = True
        return []

    def PerformAttack(self):
        for card in self._cards:
            card.highlighted = False
        if not self._AttackInProgress:
            try:
                print(self._AttackTracker.Queue)
            except:
                pass
            attack = self._AttackTracker.Queue.GetAttack()
            if attack == (None):
                self._AttackTracker.Queue = AttackQueue()
                self.NextStage()
                return []
            for country in self._PlayerCountries:
                if hash(country) == attack[0]:
                    attack[0] = country
                    break
            for country in self._EnemyCountries:
                if hash(country) == attack[0]:
                    attack[0] = country
                    break
            if isinstance(attack[0], EnemyCountry):
                for country in self._PlayerCountries:
                    if hash(country) == attack[1]:
                        attack[1] = country
                        break
            elif isinstance(attack[0], PlayerCountry):
                for country in self._EnemyCountries:
                    if hash(country) == attack[1]:
                        attack[1] = country
                        break
            self._Combatants = attack
            if attack[0].dead:
                rect = pygame.rect.Rect(GAME.SCREENWIDTH/2-125, GAME.SCREENHEIGHT/2-55, 250, 110)
                message = f"{attack[0].name} cannot attack {attack[1].name} as {attack[0].name} has been destroyed!"
                message = GameMessage(message, GAME.boldFont, WHITE, rect, 60)
                self._Battle.messageQueue.Add(message)
                return []
            elif attack[1].dead:
                rect = pygame.rect.Rect(GAME.SCREENWIDTH/2-125, GAME.SCREENHEIGHT/2-55, 250, 110)
                message = f"{attack[0].name} cannot attack {attack[1].name} as {attack[1].name} has been destroyed!"
                message = GameMessage(message, GAME.boldFont, WHITE, rect, 60)
                self._Battle.messageQueue.Add(message)
                return []
            GAME.SFXPlayer.play(GAME.MarchingSound, loops=3)
            self.GenerateDaggers(attack[0], attack[1])
            self._AttackInProgress = True
            self.BattleWaitTime = 120
        for dagger in self._Renderables["Attacking"]:
            dead = dagger.Update()
            if dead:
                self._Renderables["Attacking"].remove(dagger)
        if self._Renderables["Attacking"] == []:
            if not self.GunShotsPlaying:
                GAME.SFXPlayer.play(GAME.BattleSound[r.randint(0, 2)])
                self.GunShotsPlaying = True
            self.BattleWaitTime -= 1
            if self.BattleWaitTime <= 0:
                self._AttackInProgress = False
                for card in self._Countries:
                    card.highlighted = False
                self.GunShotsPlaying = False
                self.CalculateBattleOutcome() 
        return self._Renderables["Attacking"]

    def GenerateDaggers(self, attacker: Country, defender: Country):
        attacker.highlighted = True
        defender.highlighted = True
        self._Renderables["Attacking"] = []
        for i in range(3):
            starty = attacker.rect.centery-100+50*i
            endy = defender.rect.centery-100+50*i
            dagger = Dagger(attacker, defender, starty, endy)
            self._Renderables["Attacking"].append(dagger)
    
    def NextStage(self):
        if self._Stage == "Move":
            self._Stage = "Flip"
        elif self._Stage == "Flip":
            GAME.Shake(10)
            if self._Battle.TutorialDialogue:
                self._Stage = "Tutorial"
            else:
                self._Stage = "Game"
        elif self._Stage == "NewTurn":
            self._Stage = "ActionsAttacking"
        elif self._Stage.startswith("Actions"):
            if self._Stage == "ActionsAttacking":
                self._Stage = "Game"
        elif self._Stage != "Game":
            self._Stage = "Game"
    
    def CalculateBattleOutcome(self):
        attacker, defender = self._Combatants
        if isinstance(attacker, EnemyCountry):
            attacker.army.ResetStart()
        elif isinstance(defender, EnemyCountry):
            defender.army.ResetStart()
        siegeAttack = attacker.army.GetSiegeAttack()
        siegeDefense = defender.army.GetSiegeDefense()
        siegeAttack -= siegeDefense // 3
        newForts = defender.fortifications - siegeAttack // 60
        attacker.army.siegeArtillery = max(attacker.army.siegeArtillery - defender.fortifications, 0)
        defender.fortifications = newForts
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
        rect = pygame.rect.Rect(GAME.SCREENWIDTH//2-125, GAME.SCREENHEIGHT//2-55, 250, 110)
        if victory:
            townLoss = round(attack / 25)
            defender.towns -= townLoss
            defender.army.Defeat()
            attacker.army.Victory()
            message = f"{defender.name} was defeated by {attacker.name}! {townLoss} towns were lost!"
            if defender.towns <= 0:
                defender.towns = 0
                defender.Die()
                if isinstance(defender, EnemyCountry):
                    self.EnemyCardsDead += 1
                elif isinstance(defender, PlayerCountry):
                    self.PlayerCardsDead += 1
                message = f"{defender.name} was defeated by {attacker.name}! {defender.name} is totally destroyed!"
        else:
            message = f"{defender.name} successfully defended against {attacker.name}!"
            defender.army.Victory()
            attacker.army.Defeat()
        message = GameMessage(message, GAME.smallBoldFont, WHITE, rect, 70)
        self._Battle.messageQueue.Add(message)
        if isinstance(attacker, EnemyCountry):
            attacker.army.ResetStart()
        else:
            defender.army.ResetStart()
        defender.SetDetails()
        attacker.SetDetails()
        defender.Opponent = None
        attacker.Opponent = None

    def HandleAttackChoice(self, country: Country):
        if self._AttackTracker.CheckCountry(self._CardSelected):
            self.ActionDenied()
            return
        self._AttackTracker.AddAttackToQueue(self._CardSelected, country)
        pos = self._Battle.playerCountries.index(self._CardSelected)
        self._Battle.PlayerActions[pos][0][1] = hash(country)
        for card in self._EnemyCountries:
            card.highlighted = False
        self.Reset()

    def HandleProductionChoices(self, button: Button):
        self._CardSelected.PurchaseUnit(button.string)

    def HandleBuffOptions(self, button: str):
        if button == "Apply":
            self._Stage = "ChooseBuff"
        elif button == "Remove":
            self.RemoveBuff()
    
    def RemoveBuff(self):
        if isinstance(self._CardSelected, Buff):
            if self._CardSelected.country is None:
                return
            self._CardSelected.country.RemoveBuff()
            self._CardSelected.country.SetDetails()
            self._CardSelected.country = None
    
    def NewTurn(self):
        self._Turn += 1
        self._CardSelected = None
        self._Renderables["Production"] = None
        messageRect = pygame.rect.Rect(GAME.SCREENWIDTH//2-60, GAME.SCREENHEIGHT//2-20, 120, 40)
        message = GameMessage(f"Turn {self._Turn}", GAME.boldFont, WHITE, messageRect, 100)
        self._Battle.messageQueue.Add(message)
        enemyActions = self._Battle.GetEnemyActions()
        attacks = []
        for i in range(len(self._EnemyCountries)):
            actions = enemyActions[i]
            card = self._EnemyCountries[i]
            if card.dead:
                continue
            card.army.AddInfantry(actions[1][0])
            card.army.AddTanks(actions[1][1])
            card.army.AddPlanes(actions[1][2])
            card.army.AddDefenseArtillery(actions[1][3])
            card.army.AddAttackArtillery(actions[1][4])
            card.fortifications += actions[1][5]
            if actions[2] != None:
                if not isinstance(actions[2], Buff):
                    for i in self._EnemyBuffs:
                        if actions[2] == hash(i):
                            buff = i
                            i.ApplyToCountry(card)
                            break
                else:
                    buff = actions[2]
                card.AddBuff(buff)
        for card in self._Countries:
            card.prodpower = card.factories * card.production
            card.prodpowerbuffadded = False
            if card.Buff is not None and card.Buff.statAffected == "Production":
                card.prodpower += card.Buff.change * card.factories
                card.prodpowerbuffadded = True
            
        self._AttackTracker.NewTurn(attacks, self._Battle.playerFirst, self._PlayerCountries, self._EnemyCountries)
        self.NextStage()
    
    def ActionDenied(self):
        if self._Renderables["ActionDenied"] is not None:
            self._ActionDeniedTimer -= 1
            if self._ActionDeniedTimer <= 0:
                self._ActionDeniedTimer = 0
                self._Renderables["ActionDenied"] = None
                self.Reset()
            return []
        rect = pygame.rect.Rect(GAME.SCREENWIDTH//2 - 130, GAME.SCREENHEIGHT//2 - 20, 260, 40)
        deniedMessage = GameMessage("Action not available!", GAME.smallBoldFont, WHITE, rect, 120)
        self._Battle.messageQueue.Add(deniedMessage)
        self._ActionDeniedTimer = 120
        self._Stage = "ActionDenied"
        self._Renderables["ActionDenied"] = []
        return []

    def GetTurn(self):
        return self._Turn

    def Reset(self):
        self._Stage = "Game"
        self._CardSelected = None
        for card in self._cards:
            card.highlighted = False

################################################################################################################

class TextBox:

    def __init__(self, Text: str, textColour: str, left: int, top: int, height: int, width: int, font: pygame.font.Font, border=False):
        self.string = str(Text)
        self.left = float(left)
        self.top = float(top)
        self.height = float(height)
        self.width = float(width)
        self.rect = pygame.Rect(self.left, self.top, self.width, self.height)
        self.textColour = textColour
        self.font = font
        self.DrawTime = time()
        self.border = border
        

    def Draw(self): #Not my function, obtained and modified from www.pygame.org/wiki/TextWrap
        if self.border:
            border = pygame.Rect(self.rect.x-2, self.rect.y-2, self.rect.width+4, self.rect.height+4)
            pygame.draw.rect(GAME.screen, BLACK, border)
        rect = self.rect
        y = rect.top
        lineSpacing = -2
        font = self.font
        # get the height of the font
        fontHeight = GAME.regularFont.size("Tg")[1]
        Text = self.string
        pygame.draw.rect(GAME.screen, BLUE, self.rect)
        while Text:
            i = 1

            # determine if the row of Text will be outside our area
            if y + fontHeight > rect.bottom:
                break

            # determine maximum width of line
            while font.size(Text[:i])[0] < rect.width and i < len(Text):
                i += 1

            # if we've wrapped the Text, then adjust the wrap to the last word      
            if i < len(Text): 
                i = Text.rfind(" ", 0, i) + 1

            # render the line and blit it to the surface
            image = font.render(Text[:i], 1, self.textColour)

            GAME.screen.blit(image, (rect.left, y))
            y += fontHeight + lineSpacing

            # remove the Text we just blitted
            Text = Text[i:]

    
    def ChangeText(self, newString: str):
        self.string = newString
        
#################################################################################################################

class GameBar:

    def __init__(self, player: Player, enemy: Player, playerfirst: bool):
        self.startTime = time()
        self.time = 0
        image = pygame.image.load(resource_path("art/GameBar.png")).convert_alpha()
        self.flippedImage = pygame.Surface((1080, 50))
        self.flippedImage.blit(image, (0, 0))
        self.border = pygame.Rect(0, 0, 1080, 52)
        self.player = player
        self.enemy = enemy
        playertext = player.Text()
        enemytext = enemy.Text()
        if playerfirst:
            playertext = "1. " + playertext
            enemytext = "2. " + enemytext
        else:
            playertext = "2. " + playertext
            enemytext = "1. " + enemytext
        self.playertext = GAME.boldFont.render(playertext, True, ROYALBLUE)
        self.enemytext = GAME.boldFont.render(enemytext, True, ROYALBLUE)
        self.flippedImage.blit(self.playertext, (15, 8))
        self.flippedImage.blit(self.enemytext, (610, 8))
        self.timeBox = pygame.Rect((GAME.SCREENWIDTH/2)-37.5, 55, 75, 25)
        self.timeBorder = pygame.Rect((GAME.SCREENWIDTH/2)-39.5, 53, 79, 29)
        self.TurnBox = pygame.Rect((GAME.SCREENWIDTH/2)-50, 82, 100, 25)
        self.TurnBorder = pygame.Rect((GAME.SCREENWIDTH/2)-52, 80, 104, 29)
    
    def Draw(self, turn: int):
        self.time = int(time() - self.startTime)
        seconds = self.time % 60
        minutes = self.time // 60
        if seconds > 0:
            secondsDigits = int(log10(seconds)) + 1
        elif seconds == 0:
            secondsDigits = 1
        
        Text = f"{minutes}:"
        for i in range(2-secondsDigits):
            Text += "0"
        Text += str(seconds)
        Text = GAME.boldFont.render(Text, True, BLACK)
        turnText = GAME.smallBoldFont.render(f"Turn: {turn}", True, WHITE)
        pygame.draw.rect(GAME.screen, BLACK, self.border)
        pygame.draw.rect(GAME.screen, BLACK, self.timeBorder)
        pygame.draw.rect(GAME.screen, BLUE, self.timeBox)
        pygame.draw.rect(GAME.screen, BLACK, self.TurnBorder)
        pygame.draw.rect(GAME.screen, BLUE, self.TurnBox)
        GAME.screen.blit(self.flippedImage, (0, 0))
        GAME.screen.blit(Text, (self.timeBox.x+2, self.timeBox.y-4))
        GAME.screen.blit(turnText, (self.TurnBox.x+2, self.TurnBox.y+2))

    def GetBattleTime(self) -> str:
        seconds = self.time % 60
        minutes = self.time // 60
        if seconds > 0:
            secondsDigits = int(log10(seconds)) + 1
        elif seconds == 0:
            secondsDigits = 1
        
        Text = f"{minutes}:"
        for i in range(2-secondsDigits):
            Text += "0"
        Text += str(seconds)
        return Text

##############################################################################################################

class Box(pygame.sprite.Sprite):
    "Class for a simple box"
    def __init__(self, size: tuple, colour: str, topleft: tuple):
        super(Box, self).__init__()
        self.rect = pygame.rect.Rect(topleft[0], topleft[1], size[0], size[1])
        self._Border = pygame.rect.Rect(topleft[0]-2, topleft[1]-2, size[0]+4, size[1]+4)
        self._Colour = colour
    
    def Draw(self):
        pygame.draw.rect(GAME.screen, BLACK, self._Border)
        pygame.draw.rect(GAME.screen, self._Colour, self.rect)
    
    def Update(self):
        return None

###############################################################################################################

class Dagger(pygame.sprite.Sprite):

    def __init__(self, origin: Country, destination: Country, startY: int, endY: int):
        super(Dagger, self).__init__()
        self.startX = origin.rect.centerx
        self.startY = startY
        self.endX = destination.rect.centerx
        self.endY = endY
        if self.startX > self.endX:
            self.left = True
        else:
            self.left = False
        self.right = not self.left
        self.distancex = self.endX - self.startX
        self.distancey = self.endY - self.startY
        image = pygame.image.load(resource_path("art/gun.png")).convert_alpha()
        self.image = pygame.transform.scale(image, (50, 50))
        if self.left:
            self.image = pygame.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
        self.rect.center = (self.startX, self.startY)
        self.vector = (self.distancex / 120, self.distancey / 120)
        self.travelled = 0
    
    def Update(self) -> bool:
        if self.left and self.rect.centerx < self.endX:
            return True
        elif self.right and self.rect.centerx > self.endX:
            return True
        self.rect.x += self.vector[0]
        self.travelled += 1
        self.rect.y = self.startY + (self.travelled * self.vector[1]) + 25*sin(self.travelled/10)
        self.Draw()
        return False
    
    def Draw(self):
        GAME.screen.blit(self.image, self.rect.topleft)

#################################################################################################################

class AttackTracker:

    def __init__(self):
        self.CurrentTurnAttacks = HashTable(10)
        self.Queue = AttackQueue()
    
    def AddAttackToQueue(self, attacker: Country, defender: Country):
        try:
            self.CurrentTurnAttacks.Add((hash(attacker), hash(defender)))
            return True
        except er.ActionNotUniqueError:
            return False
        
    def NewTurn(self, enemyAttacks: list, playerFirst: bool, playerCountries: list[Country], enemyCountries: list[Country]):
        playerattacks = self.GetAttacksThisTurn()
        for i in playerattacks:
            if i[0] == hash(playerCountries[0]):
                playerCountries[0].Opponent = i[1]
            elif i[0] == hash(playerCountries[1]):
                playerCountries[1].Opponent = i[1]
        for i in enemyAttacks:
            if i[0] == hash(enemyCountries[0]):
                enemyCountries[0].Opponent = i[1]
            elif i[0] == hash(enemyCountries[1]):
                enemyCountries[1].Opponent = i[1]
        playerOrderedAttacks = []
        enemyOrderedAttacks = []
        for i in playerCountries:
            if i.Opponent is not None:
                playerOrderedAttacks.append([hash(i), i.Opponent])
        for i in enemyCountries:
            if i.Opponent is not None:
                enemyOrderedAttacks.append([hash(i), i.Opponent])
        if playerFirst:
            self.Queue.AddAttacks(playerOrderedAttacks)
            self.Queue.AddAttacks(enemyOrderedAttacks)
        else:
            self.Queue.AddAttacks(enemyOrderedAttacks)
            self.Queue.AddAttacks(playerOrderedAttacks)
        self.CurrentTurnAttacks = HashTable(10)
    
    def GetAttacksThisTurn(self) -> list[tuple]:
        attacks = list(self.CurrentTurnAttacks)
        return attacks
    
    def CheckCountry(self, country: Country):
        return self.CurrentTurnAttacks.Search(country)
        
###################################################################################################################################

class HashTable(): #Hash table using chaining
    def __init__(self, size):
        self.values = [] #type: list[LinkedList]
        self.size = size
        for i in range(0, size):
            self.values.append(LinkedList())
    
    def Add(self, item: tuple):
        index = hash(item[0]) % self.size
        success = self.values[index].AddItem((item[0], item[1]))
        if not success:
            raise er.ActionNotUniqueError
    
    def Search(self, item: Country):
        index = hash(item) % self.size
        linkedlist = self.values[index]
        itemFound = False
        for obj in linkedlist:
            if obj[0] == item:
                itemFound = True
                break
        return itemFound
    
    def __iter__(self):
        for List in self.values:
            for item in List:
                if item == "Empty":
                    break
                else:
                    yield item

##################################################################################################################

class LinkedList:
    def __init__(self, items=[]):
        if items == []:
            self.root = None
        else:
            for i in items:
                self.AddItem(i)
        self.length = max(len(items), 1)
    
    def AddItem(self, item):
        if self.root is not None:
            if self.root.value == item:
                success = False
            else:
                success = self.root.Add(item)
        else:
            self.root = Node(item)
            success = True
        if success:
            self.length += 1
            return True
        else:
            return False
    
    def MoveRoot(self):
        if self.length < 1:
            return
        if self.root == None:
            self.length = 0
            return
        self.root = self.root.ptr
        self.length -= 1
    
    def __iter__(self):
        if self.root is None:
            yield "Empty"
        else:
            item = self.root
            while item is not None and item.value is not None:
                yield item.value
                item = item.ptr
    
    def __getitem__(self, index):
        if index >= self.length:
            raise IndexError
        currentItem = self.root
        for i in range(index):
            currentItem = currentItem.ptr
        if currentItem is None:
            return currentItem
        return currentItem.value
    
    def __len__(self):
        return self.length

class Node():
    def __init__(self, item):
        self.value = item
        self.ptr = None
    
    def Add(self, item):
        if self.value == item:
            return False
        if self.ptr is not None:
            self.ptr.Add(item)
        else:
            self.ptr = Node(item)
            return True

##################################################################################################################################

class AttackQueue:

    def __init__(self):
        self.attacks = LinkedList()

    def GetAttack(self) -> None or tuple:
        return self.Pop()
    
    def Pop(self):
        try:
            attack = self.attacks[0]
        except IndexError:
            return None
        self.attacks.MoveRoot()
        return attack
    
    def AddAttacks(self, attacks: list):
        for attack in attacks:
            self.attacks.AddItem(attack)
    
    def __len__(self):
        return len(self.attacks)
    
    def __repr__(self):
        for i in self.attacks:
            print(i)

##################################################################################################################################

class InputBox:
    def __init__(self, hint: str, font: pygame.font.Font, colour: str, left: int, top: int, width: int, height: int):
        self.rect = pygame.Rect(left, top, width, height)
        self.string = ""
        self.colour = colour
        self.hint = font.render(hint, True, self.colour)
        self.font = font
        self.border = pygame.Rect(left-2, top-2, width+4, height+4)

    def GetString(self) -> str:
        return self.string
    
    def AddToString(self, char: str):
        if len(self.string) == 15:
            return
        self.string += char
    
    def Delete(self):
        self.string = self.string[:-1]

    def Draw(self):
        pygame.draw.rect(GAME.screen, BLACK, self.border)
        pygame.draw.rect(GAME.screen, WHITE, self.rect)
        GAME.screen.blit(self.hint, (self.rect.x, self.rect.y-40))
        string = self.font.render(self.string, True, BLACK)
        GAME.screen.blit(string, (self.rect.x+5, self.rect.top+5))

####################################################################################################

class Thread(threading.Thread):
    def __init__(self, target: 'function', args: list):
        super(Thread, self).__init__(target=target, args=args + [self])
        self.running = True
        self.start()
    
    def quit(self):
        self.running = False
        
def MainLoop():
    GAME.screen.fill(BLACK)
    GAME.Update()
    global CONN
    CONN = Connection()
    if GAME.New:
        GetPlayerInfo()
        GAME.Save()
        Tutorial()
        MainMenu()
    else:
        success = CONN.Login()
        if not success:
            sys.exit() 
        else:
            MainMenu()
    GAME.Save()

def MainMenu():
    xOffset = GAME.SCREENWIDTH // 15
    PlayButton = Button("Play", BLACK, BLUE, ROYALBLUE, GAME.boldFont, 3*xOffset-100, 620, 100, 50)
    TutorialButton = Button("Tutorial", BLACK, BLUE, ROYALBLUE, GAME.boldFont, 6*xOffset-100, 620, 100, 50)
    InventoryButton = Button("Inventory", BLACK, BLUE, ROYALBLUE, GAME.smallBoldFont, 9*xOffset-100, 620, 100, 50)
    exitButton = Button("Exit", BLACK, BLUE, ROYALBLUE, GAME.boldFont, 12*xOffset-100, 620, 100, 50)
    buttons = [PlayButton, TutorialButton, InventoryButton, exitButton]
    card1 = PlayerAggressiveCountry(30, 50, "Angola")
    card1.UpdatePosition((100, 200))
    card2 = PlayerDefensiveCountry(30, 50, "Malta")
    card2.UpdatePosition((GAME.SCREENWIDTH-100, 200))
    cards = [card1, card2] #type: list[Card]
    for card in cards:
        card.SetDetails()
    if not GAME.New:
        welcomeText = GAME.smallBoldFont.render(f"Welcome back, {GAME.PLAYER.username}", True, BLACK)
    click = False
    run = True
    stage = "Moving"
    GAME.MusicPlayer.load(resource_path("music/Menu.ogg"))
    GAME.MusicPlayer.play(-1)
    while run:
        GAME.screen.blit(GAME.titlescreen, (0,0))
        GAME.screen.blit(welcomeText, (GAME.SCREENWIDTH/2-125, 550))
        mx, my = pygame.mouse.get_pos() 
        for card in cards:
            card.Update()
            card.Draw()
        if stage == "Moving":                              #Checks if game stage is moving
            inPos = True                                   #Sets flag
            for card in cards:                             #Iterates through every card
                if not card.inPos:                         #Checks if card is in position (set by Card)
                    inPos = False                          #Sets flag to false if card is not in position
            if inPos:                                      #If every card is in place, sets stage to Flipping
                stage = "Flipping"

        if stage == "Flipping":                            #Checks if flipping stage reached
            flipped = False
            for card in cards:                             #Iterates through every card
                if not card.flipping and not card.flipped: #Checks if card has begun to Flip
                    card.Flip()                            #Flips it if not
                elif not card.flipping and card.flipped:   #Checks if the card has been flipped
                    flipped = True                         #Sets the flag saying its no longer flipping
                    GAME.Shake(10)                         #Shakes the screen lightly
                else:
                    flipped = False
            if flipped:                                    #Checks the flipping flag
                stage = "Finished"                         #Moves the game stage to finished if no longer flipping            

        for button in buttons:
            button.Draw()
            if button.rect.collidepoint((mx, my)):
                button.Highlight()
                if click:
                    GAME.SFXPlayer.play(GAME.ClickSound)
                    if button.string == "Exit": #If exit button pressed, Save the game data and stop the game
                        run = False
                        GAME.Save()
                        CONN.Send("END")
                    elif button.string == "Tutorial": #Launches Tutorial
                        Tutorial()
                        GAME.MusicPlayer.unload()
                        GAME.MusicPlayer.load(resource_path("music/Menu.ogg"))
                        GAME.MusicPlayer.play(-1)
                    elif button.string == "Play": #Launches matchmaking
                        Play()
                    elif button.string == "Inventory":
                        Inventory()
                        GAME.MusicPlayer.unload()
                        GAME.MusicPlayer.load(resource_path("music/Menu.ogg"))
                        GAME.MusicPlayer.play(-1)
    
        for event in GAME.getevent(): #Iterates through and handles player input events

            if event.type == pygame.QUIT:
                run = False
                GAME.Save()
                CONN.Send("END")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True
            else:
                click = False

        GAME.Update()

def Tutorial():
    GAME.Reset()
    enemyCountries = [EnemyBalancedCountry(25, 40, "Italy"), EnemyAggressiveCountry(25, 40, "Hungary")]
    enemyBuffs = [MinorProductionBuff(False), MinorDefenseBuff(False)]
    playerCountries = [PlayerBalancedCountry(25, 40, "Angola"), PlayerAggressiveCountry(25, 40, "Canada")]
    playerBuffs = [MajorAttackBuff(True), MajorProductionBuff(True)]
    enemy = Player(username="EnemyBot", elo=1000)
    player = GAME.PLAYER
    if GAME.New:
        player.countries = playerCountries
        player.buffs = playerBuffs
        player.prioritycountries = playerCountries.copy()
        player.prioritybuffs = playerBuffs.copy()
        GAME.Save()
    else:
        playerCountries = player.prioritycountries
        if len(playerCountries) < 2:
            playerCountries = [player.countries[0], player.countries[1]]
        playerBuffs = player.prioritybuffs
        if len(playerBuffs) < 2:
            playerBuffs = [player.prioritybuffs[0], player.prioritybuffs[1]]
    Battle = TutorialBattle(player, playerCountries, playerBuffs, enemy, enemyCountries, enemyBuffs)
    Battle.Run()
    GAME.Reset()
    GAME.New = False

def Inventory():
    GAME.Reset()
    player = GAME.PLAYER
    countries = player.countries.copy()
    buffs = player.buffs.copy()
    InventoryText = GAME.bigBoldFont.render("INVENTORY", True, WHITE)
    HintText = GAME.smallBoldFont.render("Remember, the gold cards are your battle cards!", True, WHITE)
    SwitchButton = Button("Switch To: Buffs", WHITE, BLUE, ROYALBLUE, GAME.smallBoldFont, 790, 10, 260, 30)
    NextPage = Button("Next Page", WHITE, BLUE, ROYALBLUE, GAME.smallBoldFont, 930, 50, 115, 30)
    LastPage = Button("Last Page", WHITE, BLUE, ROYALBLUE, GAME.smallBoldFont, 800, 50, 115, 30)
    buttons = [SwitchButton, NextPage, LastPage]
    priorityButtons = [Button("Prioritise", WHITE, BLUE, ROYALBLUE, GAME.smallBoldFont, 5, 625, 170, 75)]
    countrypages = []
    buffpages = []
    GAME.MusicPlayer.unload()
    GAME.MusicPlayer.load(resource_path("music/Loading.ogg"))
    GAME.MusicPlayer.play(-1)
    while countries != []:
        page = pygame.Surface(GAME.screen.get_size())
        page.fill(BLUE)
        page.blit(InventoryText, (GAME.SCREENWIDTH/2-200, 10))
        page.blit(HintText, (10, 80))
        ypos = 250
        xpos = 100
        rows = []
        for i in range(2):
            row = countries[:6]
            if row == []:
                row += countries
            if row == []:
                break
            for i in row:
                i.Reset()
                i.UpdatePosition((xpos, ypos))
                i.SetDetails()
                if i in player.prioritycountries:
                    i.priority = True
                else:
                    i.priority = False
                xpos += 175
                countries.remove(i)
            ypos += 300
            rows += row
        countrypages.append((page, rows))

    while buffs != []:
        page = pygame.Surface(GAME.screen.get_size())
        page.fill(BLUE)
        page.blit(InventoryText, (GAME.SCREENWIDTH/2-200, 10))
        page.blit(HintText, (10, 80))
        ypos = 250
        xpos = 100
        rows = []
        for i in range(2):
            row = buffs[:6]
            if row == []:
                row += buffs
            if row == []:
                break
            for i in row:
                i.flipped = False
                i.image = i.cardBack
                i.Reset()
                i.UpdatePosition((xpos, ypos))
                i.SetDetails()
                if i in player.prioritybuffs:
                    i.priority = True
                else:
                    i.priority = False
                xpos += 175
                buffs.remove(i)
            ypos += 300
            rows += row
        buffpages.append((page, rows))
    pages = countrypages #type: list[tuple[pygame.Surface, Card]]
    pageNum = 1
    stage = "Move"
    ActionBox = Box((1080, 100), BLUE, (0, GAME.SCREENHEIGHT-100))
    cardSelected = None
    run = True
    click = False
    clicked = False
    while run:
        if click and not clicked: #Only lets one click occur instead of keeping the flag at true for the frames
            click = True          #where the left mouse button is pressed down
            clicked = True
        else:
            click = False
        GAME.screen.blit(pages[pageNum-1][0], (0, 0))

        if stage == "Move":
            inProgress = False
            for card in pages[pageNum-1][1]:
                if not card.inPos:
                    inProgress = True
                card.Update()

            if not inProgress:
                stage = "Flip"

        elif stage == "Flip":
            inProgress = False
            for card in pages[pageNum-1][1]:
                if not card.flipped:
                    inProgress = True
                    if not card.flipping:
                        card.Flip()
                card.Update()
            if not inProgress:
                stage = "Inventory"

        elif stage == "Options":
            ActionBox.Draw()
            for button in priorityButtons:
                button.Draw()
                if button.rect.collidepoint((mx, my)):
                    button.Highlight() 
                    if click:
                        player.SetPriority(cardSelected)
                        stage = "Inventory"
                        cardSelected.highlighted = False
                        cardSelected = None
            
        mx, my = pygame.mouse.get_pos()

        for card in pages[pageNum-1][1]:
            card.Draw()
            if card.rect.collidepoint((mx, my)) and click and (stage == "Options" or stage == "Inventory"):
                if cardSelected == card:
                    stage = "Inventory"
                    cardSelected = None
                    card.highlighted = False
                else:
                    if cardSelected is not None:
                        cardSelected.highlighted = False
                    stage = "Options"
                    cardSelected = card
                    card.highlighted = True
        
        for button in buttons:
            button.Draw()
            if button.rect.collidepoint(mx, my):
                button.Highlight()
                if click:
                    GAME.SFXPlayer.play(GAME.ClickSound)
                    if button.string == "Next Page":
                        if pageNum + 1 > len(pages):
                            continue
                        pageNum += 1
                    elif button.string == "Last Page":
                        if pageNum - 1 < 1:
                            continue
                        pageNum -= 1    
                    elif button.string == "Switch To: Buffs":
                        pages = buffpages
                        pageNum = 1
                        stage = "Move"
                        button.UpdateString("Switch To: Countries")
                    elif button.string == "Switch To: Countries":
                        pages = countrypages
                        pageNum = 1
                        stage = "Move" 
                        button.UpdateString("Switch To: Buffs")  
                    if cardSelected is not None:
                        cardSelected.highlighted = False 
                        cardSelected = None     
            
        for event in GAME.getevent():                       #Gets user input events, iterates through them
            if event.type == pygame.QUIT: 
                GAME.SFXPlayer.play(GAME.ClickSound)           #If cross in corner pressed, stop running this game loop
                run = False                                    #This will return you to the Main Menu
            elif event.type == pygame.MOUSEBUTTONDOWN:         #Checks for clicks
                if event.button == 1:                          #If left click
                    click = True                               #Set click flag
            elif event.type == pygame.MOUSEBUTTONUP:           #If stopped clicking
                clicked = False                                #Allow clicks to work again
        GAME.Update()
    
    GAME.Reset()
        
def GetPlayerInfo():
    run = True
    inputbox = InputBox("Enter Your Name:", GAME.smallBoldFont, WHITE, GAME.SCREENWIDTH/2-100, GAME.SCREENHEIGHT/2-20, 200, 40)
    while run:
        GAME.screen.fill(BLUE)
        inputbox.Draw()
        for event in GAME.getevent():                       #Gets user input events, iterates through them
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RETURN:
                    GAME.PLAYER.SetUsername(inputbox.string) 
                    run = False
                    break
                elif event.key == pygame.K_BACKSPACE:
                    inputbox.Delete()
                    continue
                try:
                    inputbox.AddToString(chr(event.key))
                except:
                    pass
        GAME.Update()
    inputbox = InputBox("Enter Your Password:", GAME.smallBoldFont, WHITE, GAME.SCREENWIDTH/2-100, GAME.SCREENHEIGHT/2-20, 200, 40)
    run = True
    while run:
        GAME.screen.fill(BLUE)
        inputbox.Draw()
        for event in GAME.getevent():                       #Gets user input events, iterates through them
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RETURN:
                    GAME.PLAYER.SetPassword(inputbox.string)
                    run = False
                    break
                elif event.key == pygame.K_BACKSPACE:
                    inputbox.Delete()
                    continue
                try:
                    inputbox.AddToString(chr(event.key))
                except:
                    pass
        GAME.Update()
    success = CONN.Login()
    if success:
        return
    error = GAME.smallBoldFont.render("Try a different username!", True, WHITE)
    timer = 0
    while timer < 180:
        GAME.screen.fill(BLUE)
        GAME.screen.blit(error, (GAME.SCREENWIDTH/2-100, GAME.SCREENHEIGHT/2-20))
        GAME.Update()
        timer += 1
    GetPlayerInfo()

def Play():
    t = Thread(target=LoadScreen, args=["Matchmaking..."])
    d1 = []
    d2 = []
    d3 = {"Player": [GAME.PLAYER.username, GAME.PLAYER.elo], "First": None}
    countries = GAME.PLAYER.prioritycountries.copy()
    for i in countries:
        d1.append(i.ToList())
    buffs = GAME.PLAYER.prioritybuffs.copy()
    for i in buffs:
        d2.append(str(i))
    CONN.Send("MATCHMAKE")
    data = CONN.Receive()
    while data["Command"] != "MATCHMADE":
        for event in GAME.getevent():
            if event.type == pygame.QUIT:
                t.quit()
                CONN.Send("UNMATCHMAKE")
                t.join()
                return
        data = CONN.Receive()
    CONN.SetBattleMode()
    t.quit()
    t.join()
    t = Thread(target=LoadScreen, args=["Initialising Battle..."])
    setupdata = CONN.Receive()
    while setupdata["Command"] != "IP":
        for event in GAME.getevent():
            pass
        setupdata = CONN.Receive()
    CONN.Send("RECEIVED")
    received = False
    while not received:
        try:
            key = CONN.SOCK.recv(2048)
            received = True
        except:
            pass
        for event in GAME.getevent():
            pass
    try:
        key = rsa.PublicKey.load_pkcs1(key, "PEM")
    except Exception as e:
        print(e)
    d3["First"] = setupdata["Args"][1]
    enemy = Player(ip=setupdata["Args"][0], key=key)
    CONN.SetBattlePlayerMode(setupdata["Args"][0], setupdata["Args"][1])
    if d3["First"]:
        data = CONN.Receive()
        while data["Command"] != "CLEAR":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
        CONN.SendToPlayer("BATTLE", enemy.key, d1)
        data = CONN.Receive()
        while data["Command"] != "RECEIVED":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
        CONN.SendToPlayer("BATTLE", enemy.key, d2)
        data = CONN.Receive()
        while data["Command"] != "RECEIVED":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
        CONN.SendToPlayer("BATTLE", enemy.key, d3)
        data = CONN.Receive()
        while data["Command"] != "RECEIVED":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
    CONN.Send("CLEAR")
    data = CONN.Receive()
    while data["Command"] != "BATTLE": #Expects Dict containing key "EnemyCountries"
        for event in GAME.getevent():
            pass
        data = CONN.Receive()
    battle = data["Args"][0]
    CONN.SendToPlayer("RECEIVED", enemy.key)
    data2 = CONN.Receive() 
    while data2["Command"] != "BATTLE": #Expects Dict containing key "EnemyBuffs"
        for event in GAME.getevent():
            pass
        data2 = CONN.Receive()
    battle2 = data2["Args"][0]
    CONN.SendToPlayer("RECEIVED", enemy.key)
    data3 = CONN.Receive() 
    while data3["Command"] != "BATTLE": #Expects Dict containing key "EnemyBuffs"
        for event in GAME.getevent():
            pass
        data3 = CONN.Receive()
    battle3 = data3["Args"][0]
    CONN.SendToPlayer("RECEIVED", enemy.key)
    if not d3["First"]:
        CONN.SendToPlayer("BATTLE", enemy.key, d1)
        data = CONN.Receive()
        while data["Command"] != "RECEIVED":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
        CONN.SendToPlayer("BATTLE", enemy.key, d2)
        data = CONN.Receive()
        while data["Command"] != "RECEIVED":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
        CONN.SendToPlayer("BATTLE", enemy.key, d3)
        data = CONN.Receive()
        while data["Command"] != "RECEIVED":
            for event in GAME.getevent():
                pass
            data = CONN.Receive()
    enemyCountries = battle
    enemyBuffs = battle2
    enemyCountryObjects = []
    enemyBuffObjects = []
    playerCountries = GAME.PLAYER.prioritycountries.copy()
    playerBuffs = GAME.PLAYER.prioritybuffs.copy()
    enemydata = battle3["Player"]
    enemy.username = enemydata[0]
    enemy.elo = enemydata[1]
    for country in enemyCountries:
        if country[2] == "AGG":
            c = EnemyAggressiveCountry(country[3], country[1], country[0])
        elif country[2] == "BAL":
            c = EnemyBalancedCountry(country[3], country[1], country[0])
        elif country[2] == "DEF":
            c = EnemyDefensiveCountry(country[3], country[1], country[0])
        enemyCountryObjects.append(c)
    for buff in enemyBuffs:
        enemyBuffObjects.append(eval(buff + "(False)"))
    battle = Battle(GAME.PLAYER, playerCountries, playerBuffs, enemy, enemyCountryObjects, enemyBuffObjects, battle3["First"])
    t.quit()
    t.join()
    battle.Run()
    CONN.SetNormalMode()
    GAME.Reset()

class LoadObject:
    def __init__(self, centre: tuple[int, int]):
        self.rect = pygame.Rect(centre[0], centre[1], 8, 8)
        self.centre = centre
        self.theta = 0
        self.SpiralFunc = lambda: 146*(self.theta**(1/6))-50

    def Draw(self):
        self.theta += 0.05
        radius = self.SpiralFunc()
        adj = radius * cos(self.theta)
        opp = radius * sin(self.theta)
        self.rect.x = self.centre[0]+adj
        self.rect.y = self.centre[1]+opp
        pygame.draw.rect(GAME.screen, ROYALBLUE, self.rect)

class Text:
    def __init__(self, text: str, x: int, y: int):
        self.text = GAME.smallBoldFont.render(text, True, BLACK)
        self.x = x
        self.y = y
        self.rect = self.text.get_rect()
        self.rect.x = x
        self.rect.y = y

    def Draw(self):
        GAME.screen.blit(self.text, (self.x, self.y))

def LoadScreen(string: str, thread: Thread):    
    text = GAME.boldFont.render(string, True, WHITE)
    rect = text.get_rect()
    x = (GAME.SCREENWIDTH//2) - (rect.width//2)
    y = (GAME.SCREENHEIGHT//2) - (rect.height//2)
    los = [LoadObject((GAME.SCREENWIDTH/2, GAME.SCREENHEIGHT/2))]
    counter = 0
    while thread.running:
        GAME.screen.fill(BLUE) 
        counter += 1
        if counter % 10 == 0:
            los.append(LoadObject((GAME.SCREENWIDTH/2, GAME.SCREENHEIGHT/2)))
        for lo in los:    
            lo.Draw()
        GAME.screen.blit(text, (x, y))
        GAME.Update()

def Main():
    global GAME 
    GAME = Game()
    GAME.LoadPlayer()
    MainLoop()

if __name__ == "__main__":
    Main()