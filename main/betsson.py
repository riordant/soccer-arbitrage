#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('/Users/tadhgriordan/Documents/AutoArb/dependencies')

#from matches import *
from selenium import webdriver
from google import get_match_id
import main
from main import *
import urllib2
from functions import current_time, format_time,contains
from time import sleep
import time
try: import simplejson as json
except ImportError: import json
import requests  
import arrow

api="https://sbsitefacade.bpsgameserver.com/isa/v2/601/en/event?categoryIds=1&eventPhase=1,2&eventStartFrom=YYYY-MM-DDTHH:MM:SS&eventStartTo=YYYY-MM-DDTHH:MM:SS&onlyEvenLineMarkets=false"

ROOT = "el"
ID = "ei"
TIME = "sd"
LEAGUE = "scn"
TEAMS = "en"
TEAMS = "epl"
TEAM = "pn"
REGION = "rn"
BET_TYPES = "ml"
MATCH_WINNER = 0
MATCH_WINNER_BETS = "msl"
BET_TYPES = "ml"
HOME_BET = 0
DRAW_BET = 1
AWAY_BET = 2
HOME = 0
AWAY = 1
BET = "msp"
hours_back = 3
hours_forward = 24 

driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])

def process_query(home,away):
    '''
    Betsson layout (TBC): 
    Women:  contain "(women)" or "(Women)".
    ''' 
    if contains(home,"(women)"):
        home = home.replace("(women)","")
    if contains(away,"(women)"):
        away = away.replace("(women)","")
    if contains(home,"(Women)"):
        home = home.replace("(Women)","")
    if contains(away,"(Women)"):
        away = away.replace("(Women)","")
    
    return home + " vs. " + away          

    
class Betsson(object):
    def __init__(self):
        print("started")

    def extract(self):
        global api
        
        start_time = current_time()
        api=api.replace("eventStartFrom=YYYY-MM-DDTHH:MM:SS","eventStartFrom="+str(arrow.utcnow().replace(hours=-hours_back))[0:19])
        api=api.replace("eventStartTo=YYYY-MM-DDTHH:MM:SS", "eventStartTo="+str(arrow.utcnow().replace(hours=+hours_forward))[0:19])
        response = requests.get(api)
        json = response.json()
        print("time to get: " + str(current_time()-start_time))
        
        games = json.get(ROOT)        
        for game in games:
            id = game.get(ID) 
            time = format_time(BETSSON,game.get(TIME).replace("T"," ").replace("Z",""))
            region = game.get(REGION)
            league = game.get(LEAGUE)
            home = game.get(TEAMS)[HOME].get(TEAM)
            away = game.get(TEAMS)[AWAY].get(TEAM)
            print(home + " " + away)
            bets = game.get(BET_TYPES)[MATCH_WINNER].get(MATCH_WINNER_BETS)
            home_bet = bets[HOME_BET].get(BET)
            draw_bet = bets[DRAW_BET].get(BET)
            away_bet = bets[AWAY_BET].get(BET) 
            
            match_id_query = process_query(home,away)            
            match_id = get_match_id(driver,match_id_query,time,None).decode('utf-8')
            #print(match_id)
            print(str(id) + " " + time + " " + league + " " + home + " " + away + " " + str(home_bet) + " " + str(draw_bet) + " " + str(away_bet) + " " + match_id)       
        
if __name__ == '__main__':
    scraper = Betsson()
    scraper.extract()
        