from oled_091 import SSD1306
from subprocess import check_output
from time import sleep
from datetime import datetime
from os import path
from tkinter import Tk

import os
import serial
import RPi.GPIO as GPIO

from guizero import App, Box, Text, TextBox, MenuBar, question, Window, ListBox, PushButton

import csv

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.OUT)

DIR_PATH = path.abspath(path.dirname(__file__))
DefaultFont = path.join(DIR_PATH, "Fonts/GothamLight.ttf")

class read_rfid:
    
    def __init__(self):
        self.ser = serial.Serial ("/dev/ttyS0") #Open named port
        self.ser.baudrate = 9600 #Set baud rate to 9600
    
    def read_rfid (self):
        RFidTAG=""
        serLength = self.ser.inWaiting()

        if (serLength >= 12):
            RFidBuffer = self.ser.read(serLength)
            RFidBuffer = RFidBuffer.decode("utf-8") 
            i = RFidNum = 0
            RFidSTR = RFidBuffer[3:10] #on récupère le morceau utile pour le code RFID
            n = len(RFidSTR) - 1
            #-------------------------------------------------
            #Conversion du Tag RFI Hexa en code RFID numérique
            #-------------------------------------------------
            while n>=0:
                if RFidSTR[n]>='0' and RFidSTR[n]<='9':
                    rem = int(RFidSTR[n])
                elif RFidSTR[n]>='A' and RFidSTR[n]<='F':
                    rem = ord(RFidSTR[n]) - 55
                RFidNum = RFidNum + (rem * (16 ** i))
                n = n - 1
                i = i + 1
            #-------------------------------------------------
            RFidTAG = str(RFidNum) #conversion du nombre en chaine
            RFidTAG = '0'*(10-len(RFidTAG)) + RFidTAG #on complète avec des  pour avoir  chiffre
            
            #--------
            #Sonnerie
            #--------
            GPIO.output(17,GPIO.HIGH)
            sleep(.05)
            GPIO.output(17,GPIO.LOW)
            #--------
            
        return RFidTAG

class Config:
    def __init__(self):
        self.projets = []
        self.nb_projets = -1
        
    def load(self):
        filename = path.join(DIR_PATH,"config.csv")
        if not path.exists(filename):
            file = open(filename,"w")
            file.close()
        else:
            with open(filename) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row["type"] == "1":
                        self.projets.append(Projet(row["nom"]))
                        self.nb_projets = self.nb_projets + 1
                    elif row["type"] == "2":
                        self.projets[self.nb_projets].equipes.append(row["nom"])
                    elif row["type"] == "3":
                        self.projets[self.nb_projets].roles.append(row["nom"])
                    
    def print_config(self):
        for projet in self.projets:
            print (projet.name)
            for role in projet.roles:
                print (role)
            for equipe in projet.equipes:
                print (equipe)
    
    def get_projet_byname(self,nom):
        for projet in self.projets:
            if projet.name==nom:
                return projet 
                
    def add_project(self,nom):
        self.projets.append(Projet(nom))
        self.nb_projets = self.nb_projets + 1

    def del_project(self,nom):
        self.projets.remove(self.get_projet_byname(nom))
        self.nb_projets = self.nb_projets - 1

    def save(self):
        filename = path.join(DIR_PATH,"config.csv")
        nom_colonnes =['type','nom']
        with open(filename, 'w') as csvfile:   
            obj = csv.DictWriter(csvfile, fieldnames=nom_colonnes)
            obj.writeheader()
            for projet in self.projets:
                obj.writerow({'type':'1','nom':projet.name})
                for equipe in projet.equipes:
                    obj.writerow({'type':'2','nom':equipe})
                for role in projet.roles:
                    obj.writerow({'type':'3','nom':role})
 
class Projet:
    def __init__(self,nom):
        self.name = nom
        self.equipes=[]
        self.roles=[]
    
class rfid_info:
    
    SB = read_rfid()
    
    def __init__(self):
        self.read = False
        self.find = False
        self.tagid = ""
        self.oldtagid = ""
        self.nom = ""
        self.prenom = ""
        self.classe = ""
        self.projet = ""
        self.equipe = ""
        self.role = ""
        self.instruction = ""
        self.etape=1
        
    def reset(self):
        self.read = False
        self.find = False
        self.tagid = ""
        self.nom = ""
        self.prenom = ""
        self.classe = ""
        self.projet = ""
        self.equipe = ""
        self.role = ""
        self.instruction = ""
    #-------------------------------------------------
    #Vérifie si le tag RFID est dans le fichier CSV
    #-------------------------------------------------
    def findRFidTag(self):
        self.read = False
        tagid = self.SB.read_rfid()
        if(tagid != ""):
            if(tagid != self.oldtagid):
                self.reset()
                self.tagid = tagid
                self.oldtagid = self.tagid
                self.read = True
                filename = path.join(DIR_PATH,"users.csv")
                with open(filename) as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if row["tagid"] == self.tagid:
                            self.find = True
                            self.nom = row["nom"]
                            self.prenom = row["prenom"]
                            self.classe = row["classe"]
                            self.projet = config.projets[int(row["projet"])-1].name
                            self.equipe = config.projets[int(row["projet"])-1].equipes[int(row["equipe"])-1]
                            self.role = config.projets[int(row["projet"])-1].roles[int(row["role"])-1]
                            
                csvfile.close()
                self.findInfo()
            
    def findInfo(self):
        if (self.projet !=""):
            myPath = path.join(DIR_PATH, self.projet)
            if (not path.exists(myPath)):
                os.mkdir(myPath)
            if (self.equipe !=""):   
                myPath = path.join(DIR_PATH, self.projet + "/" + self.equipe)
                if (not path.exists(myPath)):
                    os.mkdir(myPath)
                filename = path.join(myPath, "collectif" + str(self.etape) + ".txt")
                if path.exists(filename):
                    file = open(filename,"r")
                    self.instruction = "Séance " + str(self.etape) + "\n\n" + file.read() + "\n\n"
                else:
                    file = open(filename,"w")
                file.close()
                if (self.role !=""):   
                    filename = path.join(myPath,self.role + str(self.etape) + ".txt")
                    if path.exists(filename):
                        file = open(filename,"r")
                        self.instruction = self.instruction + file.read()
                    else:
                        file = open(filename,"w")
                    file.close()
       
    def etapeSuivante(self):
        self.etape = self.etape + 1
        self.findInfo()
        
    def etapePrecedente(self):
        if (self.etape > 1):
           self.etape = self.etape - 1
           self.findInfo()
        
def info_print():
    # Affichage de lécran de démarrage sur le Module OLED
    display.DirImage(path.join(DIR_PATH, "Images/SB.png"))
    display.DrawRect()
    display.ShowImage()
    sleep(4)
    print_Tag("","") #affichage des instructions 

#-------------------------------------------------
#Affichage des instructions sur l'écran OLED
# 1 Nom et N° de carte
# 2 carte inconnue et N° de carte
# 3 Scanner carte
#-------------------------------------------------
def print_Tag(tagid,nom):
    if(tagid != ""):
        if(nom != ""):
            display.PrintText(nom, FontSize=14, cords=(0, 2))
        else:
            display.PrintText("Carte inconnue", FontSize=14, cords=(0, 2))
        display.PrintText(tagid, FontSize=16, cords=(0, 20))
    else:
        display.PrintText("Scanner carte", FontSize=14, cords=(0, 2))
    display.ShowImage()

#-------------------------------------------------
#Vérifie si le tag RFID est dans le fichier CSV
#-------------------------------------------------
def checkRFidTag():
    myCard.findRFidTag()
    if(myCard.read):
        print(myCard.tagid)
        rfidNom.value = myCard.tagid
        if(myCard.find):
            rfidNom.value = myCard.tagid + " : " + myCard.prenom + " " + myCard.nom + " " + myCard.classe
            rfidInfo.value = myCard.equipe + " : " + myCard.role 
            print_Tag(myCard.tagid,myCard.prenom + " " + myCard.nom)
        else:
            print_Tag(myCard.tagid,"")
            rfidNom.value = "Carte inconnue"
        
        showInfo()
    rfidNom.after(50, checkRFidTag)

def showInfo():
    if(myCard.find):
        instruct.value = myCard.instruction
    else:
        rfidInfo.value = ""
        instruct.value = ""

def etapeSuivante():
    myCard.etapeSuivante()
    showInfo()
    
def etapePrecedente():
    myCard.etapePrecedente()
    showInfo()
    
def resized():
    instruct.height = (app.height/17)-7
    rfidNom.width=int((app.width-90)/9)
    rfidInfo.width=int((app.width-90)/9)
    
def center_window(width, height, myApp):
    # get screen width and height
    screen_width = myApp.tk.winfo_screenwidth()
    screen_height = myApp.tk.winfo_screenheight()

    # calculate position x and y coordinates
    x = (screen_width/2) - (width/2)
    y = (screen_height/2) - (height/2)
    myApp.tk.geometry('%dx%d+%d+%d' % (width, height, x, y))
    
       
def new_project():
    a=1
    
def edit_projects():
    win_project.show(wait = True)
    
def inline_help():
    a=1
    
def about():
    a=1

def select_project():
    selection=projet_list.children[0].tk.curselection()
    selected_index = selection[0]
    equipe_list.clear()
    for equipe in config.projets[selected_index].equipes:
        equipe_list.append(equipe)
    role_list.clear()
    for role in config.projets[selected_index].roles:
        role_list.append(role)

def create_projet():
    new_name = win_project.question("Nouveau projet", "Nom")
    if new_name:
        projet_list.append(new_name)
        config.add_project(new_name)
        #config.print_config()
        
def edit_projet_name():
    selection=projet_list.children[0].tk.curselection()
    if selection:
        selected_index = selection[0]
        new_name = win_project.question("modifier projet", "nouveau nom", initial_value=projet_list.value)
        if new_name:
            if new_name != projet_list.value:
                projet_list.children[0].tk.delete(selected_index)
                projet_list.children[0].tk.insert(selected_index, new_name)
                config.projets[selected_index].name=new_name
                #config.print_config()
                
def del_projet():
    project_name = projet_list.value
    if (project_name != "default"):
        projet_list.remove(project_name)
        config.del_project(project_name)
        #config.print_config()
        
def create_equipe():
    project_name = projet_list.value
    if (project_name != "default"):
        new_name = win_project.question("Nouvelle equipe", "Nom")
        if new_name:
            equipe_list.append(new_name)
            config.get_projet_byname(project_name).equipes.append(new_name)
            #config.print_config()
            
def edit_equipe_name():
    selection=equipe_list.children[0].tk.curselection()
    if selection:
        selected_index = selection[0]
        new_name = win_project.question("modifier equipe", "nouveau nom", initial_value=equipe_list.value)
        if new_name:
            if new_name != equipe_list.value:
                project_name = projet_list.value
                if (project_name != "default"):
                    equipe_list.children[0].tk.delete(selected_index)
                    equipe_list.children[0].tk.insert(selected_index, new_name)
                    config.get_projet_byname(project_name).equipes[selected_index]=new_name
                    #config.print_config()

def del_equipe():
    equipe_name = equipe_list.value
    if (equipe_name != ""):
        project_name = projet_list.value
        if (project_name != "default"):
            config.get_projet_byname(project_name).equipes.remove(equipe_name)
            equipe_list.remove(equipe_name)
            #config.print_config()
            
def create_role():
    project_name = projet_list.value
    if (project_name != "default"):
        new_name = win_project.question("Nouveau role", "Nom")
        if new_name:
            role_list.append(new_name)
            config.get_projet_byname(project_name).roles.append(new_name)
            #config.print_config()
            
def edit_role_name():
    selection=role_list.children[0].tk.curselection()
    if selection:
        selected_index = selection[0]
        new_name = win_project.question("modifier role", "nouveau nom", initial_value=role_list.value)
        if new_name:
            if new_name != role_list.value:
                project_name = projet_list.value
                if (project_name != "default"):
                    role_list.children[0].tk.delete(selected_index)
                    role_list.children[0].tk.insert(selected_index, new_name)
                    config.get_projet_byname(project_name).roles[selected_index]=new_name
                    #config.print_config()
def del_role():
    role_name = role_list.value
    if (role_name != ""):
        project_name = projet_list.value
        if (project_name != "default"):
            config.get_projet_byname(project_name).roles.remove(role_name)
            role_list.remove(role_name)
            #config.print_config()

def save_config():
    config.save()
    win_project.hide()

def dummy():
    print("dummy")
    
    
display = SSD1306()
config = Config()
config.load()
#config.print_config()
myCard = rfid_info()

info_print()

#Création de l'interface
appWidth = 900
appHeight = 700
app = App(title="scanner votre carte RFid", width=appWidth, height=appHeight, visible=False, layout="auto", bg=(224,231,242))
center_window(appWidth, appHeight, app)

menubar = MenuBar(app,
                  toplevel=["Projet", "Aide"],
                  options=[
                      [["Editer", edit_projects]],
                      [["Aide", inline_help], ["A propos", about]]
                  ])

#empty1 = Text(app, text="",height=1)

title_grid = Box(app, width="fill" ,height=60, layout="grid")
bt_time_before = PushButton(title_grid, text="<", grid=(0,0), align="left",height=2, width=2,command=etapePrecedente)
title_grid2 = Box(title_grid, width="fill" ,height=60, layout="grid",grid=(1,0))
rfidNom = Text(title_grid2,height=1,width=int((appWidth-90)/9),grid=(0,0))
rfidNom.bg = (177,187,200)
rfidInfo = Text(title_grid2,height=1,width=int((appWidth-90)/9),grid=(0,1))
rfidInfo.bg = (177,187,200)
bt_time_after = PushButton(title_grid, text=">", grid=(2,0), align="right",height=2, width=2,command=etapeSuivante)


instruct = TextBox(app,width="fill",multiline=True,scrollbar=True)
instruct.bg = "white"

designBy = Text(app, text="Technologie - Collège Val de Rance", align="bottom",width="fill")
designBy.bg = (177,187,200)
app.show()


#design de la fenêtre de projet
winWidth = 420
winHeight = 520

win_project = Window(app, title = "projets", width=winWidth, height=winHeight, visible=False, bg=(224,231,242))
center_window(winWidth, winHeight, win_project)

main_grid = Box(win_project, width=winWidth-30 ,height=winHeight-10, layout="grid")

txt_projet = Text(main_grid, text="Liste des projets : ", grid=(0,0), align="left")
projet_list = ListBox(main_grid, width=250, height=130, grid=(0,1), align="left", command=select_project)
projet_list.bg="white"
for projet in config.projets:
    projet_list.append(projet.name)
box_projet = Box(main_grid, width=100 ,height=200, layout="grid", border=True, grid=(1,1))
bt_new_projet =   PushButton(box_projet, text="Ajouter projet", grid=(0,0), align="left", width=12, command=create_projet)
bt_edit_projet =  PushButton(box_projet, text="Modifier projet", grid=(0,1), align="left", width=12, command=edit_projet_name)
bt_suppr_projet = PushButton(box_projet, text="Supprimer", grid=(0,2), align="left", width=12, command=del_projet)

txt_equipe = Text(main_grid, text="Lste des équipes : ", grid=(0,2), align="left")
equipe_list = ListBox(main_grid, width=250, height=130, grid=(0,3), align="left")
equipe_list.bg="white"
box_equipe = Box(main_grid, width=100 ,height=200, layout="grid", border=True, grid=(1,3))
bt_new_equipe =   PushButton(box_equipe, text="Ajouter équipes", grid=(0,0), align="left", width=12, command=create_equipe)
bt_edit_equipe =  PushButton(box_equipe, text="Modifier équipe", grid=(0,1), align="left", width=12, command=edit_equipe_name)
bt_suppr_equipe = PushButton(box_equipe, text="Supprimer", grid=(0,2), align="left", width=12,command=del_equipe)

txt_role = Text(main_grid, text="Lste des rôles : ", grid=(0,4), align="left")
role_list = ListBox(main_grid, width=250, height=130, grid=(0,5), align="left")
role_list.bg="white"
box_role = Box(main_grid, width=100 ,height=200, layout="grid", border=True, grid=(1,5))
bt_new_role =     PushButton(box_role, text="Ajouter rôle", grid=(0,0), align="left", width=12, command=create_role)
bt_edit_role =    PushButton(box_role, text="Modifier rôle", grid=(0,1), align="left", width=12, command=edit_role_name)
bt_suppr_role =   PushButton(box_role, text="Supprimer", grid=(0,2), align="left", width=12, command=del_role)

bt_save_config = PushButton(main_grid, text="enregistrer", grid=(1,6), align="right", width=12,command=save_config)
bt_save_config.bg = "red"

#Lancement du scan rfid sans arréter l'affichage
rfidNom.after(50, checkRFidTag)
instruct.after(100, resized)

app.when_resized = resized


app.display()
   
