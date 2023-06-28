import requests
import json
import random
import math
from io import BytesIO
from urllib.request import urlopen
from PIL import ImageTk
import PIL.Image
from tkinter import *
import tkinter.ttk as ttk
import tkinter.font as font

class move():
    def __init__(self, name):
        api_url = "https://pokeapi.co/api/v2/move/" + name.lower()
        response_api = requests.get(api_url)
        data = response_api.text
        parse_data = json.loads(data)
        self.name = name[0].upper() + name[1:]
        self.name = self.name.replace("-", " ")
        self.power = parse_data['power']
        if type(self.power) != int:
            self.power = 30
        self.type = parse_data['type']['name']
    def __str__(self):
        return self.name + " " + self.type[0].upper() + self.type[1:] + " " + str(self.power)

class pokemon():
    def __init__(self, name, level):
        api_url = "https://pokeapi.co/api/v2/pokemon/" + name.lower()
        response_api = requests.get(api_url)
        data = response_api.text
        parse_data = json.loads(data)
        self.back_image_url = parse_data['sprites']['back_default']
        self.back_image = self.GetImage(self.back_image_url, 500)
        self.front_image_url = parse_data['sprites']['front_default']
        self.front_image = self.GetImage(self.front_image_url, 300)
        self.level = level
        self.hp, self.attack, self.defence, self.special_attack, self.special_defence, self.speed  = [self.RecalculateStat(x['base_stat']) for x in parse_data['stats']]
        self.hp += self.level+5
        self.maxhp = self.hp
        self.types = [x['type']['name'] for x in parse_data['types']]
        self.typesToDisplay = ", ".join([x[0].upper()+x[1:] for x in self.types])
        self.name = name[0].upper() + name[1:]
        self.moves = [[x['move']['name'], len(x['version_group_details'])] for x in parse_data['moves']]
        self.moves.sort(key = lambda x: x[1], reverse=True)
        self.moves = self.moves[0:4]
        self.moves = [move(x[0]) for x in self.moves]
    def RecalculateStat(self, value):
        return math.floor(((value+random.randint(0, 15))*2+math.floor(math.ceil(math.sqrt(30000*self.level/100))/4))*self.level/100)+5
    def ReceiveDamage(self, mve):
        PrintLog(self.name + " received " + str(mve[0]) + " damage!")
        if mve[1] > 1:
            PrintLog("It's critical hit!")
        if mve[2] > 1:
            PrintLog("It's super effective!")
        if mve[2] < 1:
            PrintLog("It's not really effective")
        self.hp -= int(mve[0])
        if partyPlayer.pokemons[partyPlayer.activePokemon] == self:
            hpBarPlayer['value'] = self.hp/self.maxhp*100
        else:
            hpBarOpponent['value'] = self.hp/self.maxhp*100
        if self.hp <= 0:
            PrintLog(self.name + " fainted!")
    def GetImage(self, image_url, x):
        img = PIL.Image.open(BytesIO(urlopen(image_url).read()))
        img.convert("RGBA")
        img = img.resize((x, x))
        return img

class party():
    def __init__(self, pokemons):
        self.pokemons = pokemons
        self.activePokemon = 0
    def __str__(self):
        return " ".join([x.name for x in self.pokemons])
    def switchTo(self, index):
        self.activePokemon = index
        if partyPlayer == self:
            fightButton['state'] = ACTIVE
            namePlayer.set(self.pokemons[self.activePokemon].name)
            hpPlayerText.set(str(self.pokemons[self.activePokemon].hp) + " / " + str(self.pokemons[self.activePokemon].maxhp))
            typesPlayer.set(partyPlayer.pokemons[partyPlayer.activePokemon].typesToDisplay)
            hpBarPlayer['value'] = partyPlayer.pokemons[partyPlayer.activePokemon].hp/partyPlayer.pokemons[partyPlayer.activePokemon].maxhp*100
            if random.randint(0, 1):
                UpdateBackground()
                logs.set("")
                TurnOpponent()
            else:
                UpdateBackground()
                DisplayFirstOptions()
        else:
            nameOpponent.set(self.pokemons[self.activePokemon].name)
            hpOpponentText.set(str(self.pokemons[self.activePokemon].hp) + " / " + str(self.pokemons[self.activePokemon].maxhp))
            typesOpponent.set(partyOpponent.pokemons[partyOpponent.activePokemon].typesToDisplay)
            hpBarOpponent['value'] = partyOpponent.pokemons[partyOpponent.activePokemon].hp/partyOpponent.pokemons[partyOpponent.activePokemon].maxhp*100
            UpdateBackground()
            DisplayFirstOptions()

class items():
    def __init__(self, potion, superPotion, hyperPotion, revive):
        self.potion = potion
        self.superPotion = superPotion
        self.hyperPotion = hyperPotion
        self.revive = revive
    def UsePotion(self, potionType, target):
        logs.set("")
        match potionType:
            case 1:
                num = 20
                self.potion -= 1
            case 2:
                num = 50
                self.superPotion -= 1
            case 3:
                num = 200
                self.hyperPotion -= 1
            case 4:
                num = int(math.floor(partyPlayer.pokemons[target].maxhp/2))
                self.revive -= 1
                PrintLog(partyPlayer.pokemons[target].name + " revived!")
        PrintLog(partyPlayer.pokemons[target].name + " got healed by " + str(num) + " HP!")
        partyPlayer.pokemons[target].hp += num
        if partyPlayer.pokemons[target].hp >= partyPlayer.pokemons[target].maxhp:
            partyPlayer.pokemons[target].hp = partyPlayer.pokemons[target].maxhp
        TurnOpponent()

def GetTypeEffectivness(type):
    api_url = "https://pokeapi.co/api/v2/type/" + type.lower()
    response_api = requests.get(api_url)
    data = response_api.text
    parse_data = json.loads(data)["damage_relations"]
    doubleDamageTo = [x['name'] for x in parse_data["double_damage_to"]]
    halfDamageTo = [x['name'] for x in parse_data["half_damage_to"]] + [x['name'] for x in parse_data["no_damage_to"]]
    return doubleDamageTo, halfDamageTo

def CalculateDamage(level, speed, attack, types, opponentDefence, opponentTypes, powerMove, typeMove):
    randNum = random.randint(0,255)
    if randNum < math.floor(speed/2):
        crit = 2
    else:
        crit = 1
    if typeMove in types:
        stab = 1.5
    else:
        stab = 1
    typeEffectivness = GetTypeEffectivness(typeMove)
    doubleDamageTo = typeEffectivness[0]
    halfDamageTo = typeEffectivness[1]
    if opponentTypes[0] in doubleDamageTo:
        type1 = 2
    elif opponentTypes[0] in halfDamageTo:
        type1 = 0.5
    else:
        type1 = 1
    if len(opponentTypes) > 1:
        if opponentTypes[1] in doubleDamageTo:
            type2 = 2
        elif opponentTypes[1] in halfDamageTo:
            type2 = 0.5
        else:
            type2 = 1
    else:
        type2 = 1
    randNum = random.randint(217,255)
    damage = ((2*level*crit/5+2)*powerMove*attack/opponentDefence/50+2)*stab*type1*type2*randNum//255
    return damage, crit, type1*type2

def TurnPlayer(movPlayer):
    logs.set("")
    pokemonPlayer = partyPlayer.pokemons[partyPlayer.activePokemon]
    pokemonOpponent = partyOpponent.pokemons[partyOpponent.activePokemon]
    pokemonOpponent.ReceiveDamage(CalculateDamage(pokemonPlayer.level, pokemonPlayer.speed, pokemonPlayer.attack, pokemonPlayer.types, pokemonOpponent.defence, pokemonOpponent.types, movPlayer.power, movPlayer.type))
    hpOpponentText.set(str(pokemonOpponent.hp)+ " / " + str(pokemonOpponent.maxhp))
    partyOpponent.pokemons[partyOpponent.activePokemon] = pokemonOpponent
    if pokemonOpponent.hp > 0:
        TurnOpponent()
    else:
        if len(partyOpponent.pokemons) - 1 <= partyOpponent.activePokemon:
            GameOver()
            return 0
        else:
            partyOpponent.pokemons[partyOpponent.activePokemon].hp = 0
            partyOpponent.switchTo(partyOpponent.activePokemon+1)

def TurnOpponent():
    pokemonPlayer = partyPlayer.pokemons[partyPlayer.activePokemon]
    pokemonOpponent = partyOpponent.pokemons[partyOpponent.activePokemon]
    movOpponent = pokemonOpponent.moves[random.randint(0, 3)]
    pokemonPlayer.ReceiveDamage(CalculateDamage(pokemonOpponent.level, pokemonOpponent.speed, pokemonOpponent.attack, pokemonOpponent.types, pokemonPlayer.defence, pokemonPlayer.types, movOpponent.power, movOpponent.type))
    hpPlayerText.set(str(pokemonPlayer.hp) + " / " + str(pokemonPlayer.maxhp))
    partyPlayer.pokemons[partyPlayer.activePokemon] = pokemonPlayer
    if sum([x.hp for x in partyPlayer.pokemons]) <= 0:
        GameOver()
    elif pokemonPlayer.hp <= 0:
        backButton['state'] = DISABLED
        partyPlayer.pokemons[partyPlayer.activePokemon].hp = 0
        DisplayFirstOptions()
        DisplayPokemons()
    else:
        DisplayFirstOptions()

def GameOver():
    hpBarPlayer['value'] = partyPlayer.pokemons[partyPlayer.activePokemon].hp/partyPlayer.pokemons[partyPlayer.activePokemon].maxhp*100
    hpBarOpponent['value'] = partyOpponent.pokemons[partyOpponent.activePokemon].hp/partyOpponent.pokemons[partyOpponent.activePokemon].maxhp*100
    DisplayFirstOptions()
    backButton['state'] = DISABLED
    fightButton['state'] = DISABLED
    pokemonButton['state'] = DISABLED
    itemsButton['state'] = DISABLED
    if sum([x.hp for x in partyPlayer.pokemons]) > 0:
        PrintLog("You've won!")
    else:
        PrintLog("You've lost!")
    PrintLog("Game over!")

def HandleInput():
    while True:
        try:
            pokName = input("Enter pokemon's name: ").lower()
            if pokName not in dataList:
                print("Pokemon not found")
            else:
                break
        except:
            print("Invalid name")
    while True:
        lvl = input("Enter pokemon's level: ")
        try:
            if int(lvl) > 0 and int(lvl) <= 100:
                break
            else:
                print("Number out of range (1-100)")
        except:
            print("Invalid number")
    print("Downloading data...")
    return pokemon(pokName, int(lvl))

def PrintLog(text):
    logs.set(logs.get()+"\n"+text)

def DisplayMoves():
    global firstMoveButton, secondMoveButton, thirdMoveButton, fourthMoveButton
    fightButton.grid_remove()
    pokemonButton.grid_remove()
    itemsButton.grid_remove()
    firstMoveButton = Button(root, text=partyPlayer.pokemons[partyPlayer.activePokemon].moves[0].name + "\n" + partyPlayer.pokemons[partyPlayer.activePokemon].moves[0].type[0].upper() + partyPlayer.pokemons[partyPlayer.activePokemon].moves[0].type[1:] + " " + str(partyPlayer.pokemons[partyPlayer.activePokemon].moves[0].power), command=(lambda: TurnPlayer(partyPlayer.pokemons[partyPlayer.activePokemon].moves[0])), width=12, height=2)
    secondMoveButton = Button(root, text=partyPlayer.pokemons[partyPlayer.activePokemon].moves[1].name + "\n" + partyPlayer.pokemons[partyPlayer.activePokemon].moves[1].type[0].upper() + partyPlayer.pokemons[partyPlayer.activePokemon].moves[1].type[1:] + " " + str(partyPlayer.pokemons[partyPlayer.activePokemon].moves[1].power), command=(lambda: TurnPlayer(partyPlayer.pokemons[partyPlayer.activePokemon].moves[1])), width=12, height=2)
    thirdMoveButton = Button(root, text=partyPlayer.pokemons[partyPlayer.activePokemon].moves[2].name + "\n" + partyPlayer.pokemons[partyPlayer.activePokemon].moves[2].type[0].upper() + partyPlayer.pokemons[partyPlayer.activePokemon].moves[2].type[1:] + " " + str(partyPlayer.pokemons[partyPlayer.activePokemon].moves[2].power), command=(lambda: TurnPlayer(partyPlayer.pokemons[partyPlayer.activePokemon].moves[2])), width=12, height=2)
    fourthMoveButton = Button(root, text=partyPlayer.pokemons[partyPlayer.activePokemon].moves[3].name + "\n" + partyPlayer.pokemons[partyPlayer.activePokemon].moves[3].type[0].upper() + partyPlayer.pokemons[partyPlayer.activePokemon].moves[3].type[1:] + " " + str(partyPlayer.pokemons[partyPlayer.activePokemon].moves[3].power), command=(lambda: TurnPlayer(partyPlayer.pokemons[partyPlayer.activePokemon].moves[3])), width=12, height=2)
    firstMoveButton.grid(row = 5, column=2)
    secondMoveButton.grid(row = 5, column=3)
    thirdMoveButton.grid(row = 6, column=2)
    fourthMoveButton.grid(row = 6, column=3)
    backButton['state'] = NORMAL

def DisplayFirstOptions():
    global fightButton, pokemonButton, itemsButton
    try:
        firstMoveButton.grid_remove()
        secondMoveButton.grid_remove()
        thirdMoveButton.grid_remove()
        fourthMoveButton.grid_remove()
    except:
        pass
    try:
        for i in range(len(partyPlayer.pokemons)):
            partyButtons[i].grid_remove()
    except:
        pass
    try:
        potionButton.grid_remove()
        superPotionButton.grid_remove()
        hyperPotionButton.grid_remove()
        reviveButton.grid_remove()
    except:
        pass
    fightButton = Button(root, text="Fight", command=DisplayMoves, width=12, height=2)
    pokemonButton = Button(root, text="Pokemon", command=DisplayPokemons, width=12, height=2)
    itemsButton = Button(root, text="Items", command=DisplayItems, width=12, height=2)
    fightButton.grid(row = 6, column = 2)
    pokemonButton.grid(row = 6, column = 3)
    itemsButton.grid(row = 7, column = 2)
    backButton['state'] = DISABLED

def DisplayItems():
    global potionButton, superPotionButton, hyperPotionButton, reviveButton
    NewView()
    potionButton = Button(root, text="Potion" + "\n" + str(itemsPlayer.potion) + " left", command=(lambda x=1: DisplayPokemonsForItems(x)), width=12, height=2)
    if itemsPlayer.potion <= 0: potionButton['state'] = DISABLED
    superPotionButton = Button(root, text="Super Potion" + "\n" + str(itemsPlayer.superPotion) + " left", command=(lambda x=2: DisplayPokemonsForItems(x)), width=12, height=2)
    if itemsPlayer.superPotion <= 0: superPotionButton['state'] = DISABLED
    hyperPotionButton = Button(root, text="Hyper Potion" + "\n" + str(itemsPlayer.hyperPotion) + " left", command=(lambda x=3: DisplayPokemonsForItems(x)), width=12, height=2)
    if itemsPlayer.hyperPotion <= 0: hyperPotionButton['state'] = DISABLED
    reviveButton = Button(root, text="Revive" + "\n" + str(itemsPlayer.revive) + " left", command=(lambda x=4: DisplayPokemonsForItems(x)), width=12, height=2)
    if itemsPlayer.revive <= 0: reviveButton['state'] = DISABLED
    potionButton.grid(row = 5, column=2)
    superPotionButton.grid(row = 5, column=3)
    hyperPotionButton.grid(row = 6, column=2)
    reviveButton.grid(row = 6, column=3)

def DisplayPokemons():
    global partyButtons
    NewView()
    partyButtons = []
    for i in range(len(partyPlayer.pokemons)):
        partyButtons.append(Button(root, text=partyPlayer.pokemons[i].name + "\n" + str(partyPlayer.pokemons[i].hp) + "/" + str(partyPlayer.pokemons[i].maxhp), command=(lambda x=i: partyPlayer.switchTo(x)), width=12, height=2))
        if partyPlayer.pokemons[i].hp <= 0:
            partyButtons[i]['state'] = DISABLED
        partyButtons[i].grid(row = i//2+6, column = i%2+2)

def DisplayPokemonsForItems(PotionType):
    global partyButtons
    potionButton.grid_remove()
    superPotionButton.grid_remove()
    hyperPotionButton.grid_remove()
    reviveButton.grid_remove()
    partyButtons = []
    for i in range(len(partyPlayer.pokemons)):
        partyButtons.append(Button(root, text=partyPlayer.pokemons[i].name + "\n" + str(partyPlayer.pokemons[i].hp) + "/" + str(partyPlayer.pokemons[i].maxhp), command=(lambda x=i: itemsPlayer.UsePotion(PotionType, x)), width=12, height=2))
        if partyPlayer.pokemons[i].hp <= 0 and PotionType != 4:
            partyButtons[i]['state'] = DISABLED
        partyButtons[i].grid(row = i//2+6, column = i%2+2)

def NewView():
    fightButton.grid_remove()
    pokemonButton.grid_remove()
    itemsButton.grid_remove()
    backButton['state'] = NORMAL

def UpdateBackground():
    try:
        bgimageCanvas.grid_remove()
    except:
        pass
    root.imgPlayer = imgPlayer = ImageTk.PhotoImage(partyPlayer.pokemons[partyPlayer.activePokemon].back_image)
    root.imgOpponent = imgOpponent = ImageTk.PhotoImage(partyOpponent.pokemons[partyOpponent.activePokemon].front_image)
    bgimageCanvas = Canvas(root, width=800, height=451)
    bgimageCanvas.create_image(0,0,anchor=NW,image=img)
    bgimageCanvas.create_image(-30,65,anchor=NW,image=imgPlayer)
    bgimageCanvas.create_image(450,45,anchor=NW,image=imgOpponent)
    bgimageCanvas.grid(row=2, column=0, rowspan=3, columnspan=4)

pokemonListUrl = "https://pokeapi.co/api/v2/pokemon?limit=151&offset=0"
response = requests.get(pokemonListUrl)
dataTemp = response.text
dataList = json.loads(dataTemp)
dataList = [x['name'] for x in dataList['results']]
ListPartyPlayer = []
ListPartyOpponent = []

print("Choose your pokemons:")
for x in range(6):
    ListPartyPlayer.append(HandleInput())
    if x < 5:
        dec = input("Do you want to add another pokemon? y/n ")
        if dec.lower() == 'n':
            break
partyPlayer = party(ListPartyPlayer)

print("Choose oponnent's pokemons:")
for x in range(6):
    ListPartyOpponent.append(HandleInput())
    if x < 5:
        dec = input("Do you want to add another pokemon? y/n ")
        if dec.lower() == 'n':
            break
partyOpponent = party(ListPartyOpponent)

print("Choose your items:")
while True:
    fi = input("Potions: ")
    se = input("Super Potions: ")
    th = input("Hyper Potions: ")
    fo = input("Revives: ")
    try:
        fi = int(fi)
        se = int(se)
        th = int(th)
        fo = int(fo)
        if fi >= 0 and se >= 0 and th >= 0 and fo >= 0:
            break
        else:
            print("Items can't be negative!")
    except:
        print("Wrong input!")
itemsPlayer = items(fi, se, th, fo)

#partyPlayer = party([pokemon('bulbasaur', 30), pokemon('pikachu', 30), pokemon('charmander', 30)])
#partyOpponent = party([pokemon('charizard', 30), pokemon('snorlax', 30)])
#itemsPlayer = items(1, 2, 3, 2)

root = Tk()

root.option_add("*Font", "montserrat 20")
defaultFont = font.Font(size=25)
img = PIL.Image.open("sprites/bgimage.png")
img = ImageTk.PhotoImage(img)
root.imgPlayer = imgPlayer = ImageTk.PhotoImage(partyPlayer.pokemons[partyPlayer.activePokemon].back_image)
root.imgOpponent = imgOpponent = ImageTk.PhotoImage(partyOpponent.pokemons[partyOpponent.activePokemon].front_image)
bgimageCanvas = Canvas(root, width=800, height=451)
bgimageCanvas.create_image(0,0,anchor=NW,image=img)
bgimageCanvas.create_image(-30,65,anchor=NW,image=imgPlayer)
bgimageCanvas.create_image(450,45,anchor=NW,image=imgOpponent)
namePlayer = StringVar(root, partyPlayer.pokemons[partyPlayer.activePokemon].name)
nameOpponent = StringVar(root, partyOpponent.pokemons[partyOpponent.activePokemon].name)
typesPlayer = StringVar(root, partyPlayer.pokemons[partyOpponent.activePokemon].typesToDisplay)
typesOpponent = StringVar(root, partyOpponent.pokemons[partyOpponent.activePokemon].typesToDisplay)
hpPlayerText = StringVar(root, str(partyPlayer.pokemons[partyPlayer.activePokemon].hp) + " / " + str(partyPlayer.pokemons[partyPlayer.activePokemon].maxhp))
hpOpponentText = StringVar(root, str(partyOpponent.pokemons[partyOpponent.activePokemon].hp) + " / " + str(partyOpponent.pokemons[partyOpponent.activePokemon].maxhp))
logs = StringVar(root, "")
pokemonPlayerLabel = Label(root, textvariable = namePlayer)
pokemonOpponentLabel = Label(root, textvariable = nameOpponent)
typesPlayerLabel = Label(root, textvariable = typesPlayer)
typesOpponentLabel = Label(root, textvariable = typesOpponent)
logLabel = Label(root, textvariable=logs, wraplength=400, justify=LEFT, font="montserrat 15")
hpBarPlayer = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode = 'determinate')
hpBarPlayer['value'] = partyPlayer.pokemons[partyPlayer.activePokemon].hp/partyPlayer.pokemons[partyPlayer.activePokemon].maxhp*100
hpBarOpponent = ttk.Progressbar(root, orient=HORIZONTAL, length=150, mode = 'determinate')
hpBarOpponent['value'] = partyOpponent.pokemons[partyOpponent.activePokemon].hp/partyOpponent.pokemons[partyOpponent.activePokemon].maxhp*100
hpPlayerLabel = Label(root, textvariable = hpPlayerText)
hpOpponentLabel = Label(root, textvariable = hpOpponentText)
backButton = Button(root, text="⤺", command=DisplayFirstOptions, height=1, state=DISABLED)
pokemonPlayerLabel.grid(row = 0, column = 0)
pokemonOpponentLabel.grid(row = 0, column = 2)
typesPlayerLabel.grid(row = 0, column = 1)
typesOpponentLabel.grid(row = 0, column = 3)
hpBarPlayer.grid(row=1, column=0)
hpBarOpponent.grid(row=1, column=2)
hpPlayerLabel.grid(row=1, column=1)
hpOpponentLabel.grid(row=1, column=3)
backButton.grid(row=0, column=5, rowspan=2)
bgimageCanvas.grid(row=2, column=0, rowspan=3, columnspan=4)
logLabel.grid(row=6, column=0, rowspan=2, columnspan=2)
DisplayFirstOptions()

root.mainloop()