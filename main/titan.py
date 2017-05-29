#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('/Users/tadhgriordan/Documents/AutoArb/dependencies')

from matches import *
import main
from main import *
import re
import urlparse
import requests
import thread
import atexit
import datetime
import urllib2
import xml.etree.cElementTree as ET
from datetime import date
from functions import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from time import sleep
import re

link = "http://sports.titanbet.co.uk/en/football"

matches = []
matches.append([])
matches.append([])

UPCOMING = 0
LIVE = 1 

#'threads' is a list of triples of (id,url,home). this is all the information needed to start a new thread.
threads = []
ID = 0
URL  = 1
HOME = 2

#'leagues' is a list of tuples of (id,league). leagues can only be gotten by running a thread for each game.
leagues = []
ID = 0
LEAGUE = 1

#this variable is used to keep the latest updated list of matches. it is updated when the main thread is refreshed.
current_match_ids = []

'''
The following function is threaded and is run at the start of the program.
basically what happens is the "Upcoming Events" table needs to be periodically refreshed to remove stale games.
the problem with this is that once the time comes to refresh the table (ie. a game having started), the game
can still be present in the table for quite some time, and so the page will continue to refresh until this time,
slowing down how quickly we can get the bets of the other games.
The solution to this is to run a separate "refresh" thread that is activated once a game is found to be out of date.
this thread continuously refreshes the page and compares the games on each update to the games in the regular thread.
Once they are different (ie. the game has been removed from the table and new games added), we deactivate the refresh thread, 
and send a signal to the regular thread to refresh the page. the refresh thread then waits for another stale game, and the 
process repeats.
'''
 
#Titan - special identification
#Teams - noisy data follows string.
#(-{1-10}): some indication of bets - just requires a removal.
#(W) - indicator of womans' game.
#(R) - indicator of reserves game.
#U20 - under 20 game.
#U19 - under 19 game.
#Youth - Underage game.
#B - also reserves.
def process_query(str):
    if contains(str," B "):
        str = str.replace(" B "," ")
    if str[len(str)-1] == "B":
        str = str[:-1] #removes the B.
    
    if str.count("Youth") == 2:
        str = str.replace("Youth","")
    
    return str
        
def refresh_state():
    global refresh_needed
    global current_match_ids
    global activate_refresh_state
    print("creating refresh driver..")
    refresh_state_driver= webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
    print("getting refresh link..")
    refresh_state_driver.get(link)
    print("refresh link acquired.")  
    
    while True:
        if activate_refresh_state == True: 
            print("refreshing refresh..")   
            refresh_state_driver.refresh()
            print("parsing refresh..") 
            doc = BeautifulSoup(refresh_state_driver.page_source,"lxml")
            print("parsed refresh.")
            games = doc.select("div[id=upcomingForSport-tab-FOOT] > div > div > div > table > tbody > tr")
            refresh_match_ids = []
            for game in games:
                refresh_match_ids.append(game["data-mkt_id"])  
            print refresh_match_ids
            print current_match_ids
            difference = set(refresh_match_ids).symmetric_difference(current_match_ids)
            if len(difference)>0:
                print("difference in games detected.")
                refresh_needed=True
                activate_refresh_state=False
      
''' start thread functions. 
    thread functions are not put into the 'functions' file as they must be separated per class to work correctly.
'''      
#returns: void. 
#stores the league for the game URL passed to it.
#threaded.
#tested - ok.
def get_league_from_url(id,url,home,state):    
        print("starting thread for id " + id)
        print("url: " + url)
        prev_time = current_time()        
        if state == UPCOMING:
            print("getting title..")
            league_doc = BeautifulSoup(urllib2.urlopen("http://sports.titanbet.co.uk"+url),"lxml")
            league = league_doc.title.string
        if state == LIVE:
            driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
            driver.get(url)
            doc = BeautifulSoup(driver.page_source, "lxml")
            quit_driver(driver)
            league = doc.select("div[id=node_main-wrap] > div > div[class*=breadcrumb] > div[class=menu] > div > ul > li > a > div > span")[3].text
        print("league: " + league)
        print("time to get title: " + str(current_time()-prev_time))
        print("title acquired.")
        league = league[11:league.index(home)-3]
        league = league[league.index(" - ")+3:]
        print("league for id " + id + " " + league)
        update_league_list(TITAN,id,league)

def start_threads():
    #global threads
    for thread_vals in titan.threads:
        print("starting thread for id " + thread_vals[ID])
        thread.start_new_thread(get_league_from_url,(thread_vals[ID],thread_vals[URL],thread_vals[HOME],thread_vals[STATE]))
        print("finished thread for id " + thread_vals[ID])
        sleep(.75)
    titan.threads = [] #clear 'threads' on finish.
''' end thread functions. '''
  
def get_upcoming_games(doc):
    #global matches
    games = doc.select("div[id=upcomingForSport-tab-FOOT] > div > div > div > table > tbody > tr")
    '''
    if update_match_ids is True:
        print("in update match ids")
        current_match_ids = []
        for game in games:
            current_match_ids.append(game["data-mkt_id"])
        games = doc.select("div[id=upcomingForSport-tab-FOOT] > div > div > div > table > tbody > tr")
        update_match_ids = False
        in_refresh_state = False
    '''
    for game in games:
        id = game["data-mkt_id"] 
                                
        time = game.select("td > div > span[class~=date]")[0].text + " " + game.select("td > div > span[class~=time]")[0].text
        time = format_time(TITAN,time)
        '''
        if check_game_started(time) is True and in_refresh_state is False: 
            print("game started.")
            activate_refresh_state = True
            in_refresh_state = True # we need 2 signals here, one is turned off in the thread and the other here. necessary for correctly ordering events.
        teams = game.select('td[class^=seln] > div > button')
        print(len(teams))
        #print(teams)
        home = game.select('td[class^=seln] > div > button')[0].get("title").strip()
        print(home) 
        away = game.select('td[class^=seln] > div > button')[2].get("title").strip()
        '''
        
        league = ""
        if check_league_present(TITAN,id) is True:
            league = get_league_from_list(TITAN,id)
        else:
            url = game.select("td[class=mkt-count] > a")[singleton].get("href")
            add_league(TITAN,id,"")
            add_thread_for_league(TITAN,id,url,home,UPCOMING)

        home_bet = game.select("td[class^=seln] > div > button > span > span[class^=price]")[1].text.strip()
        draw_bet = game.select("td[class^=seln] > div > button > span > span[class^=price]")[4].text.strip()
        away_bet = game.select("td[class^=seln] > div > button > span > span[class^=price]")[7].text.strip()

        print(id + " " + league + " " + time + " " + home + " " + away + " " + home_bet + " " + draw_bet + " " + away_bet)
        
        #matches[UPCOMING].append(BookieMatch(TITAN,id,league,time,home,away,home_bet,draw_bet,away_bet))
    
    return matches


def get_live_games(doc):
    games = doc.select("div[id=inplayForSport-tab-FOOT] > div > table > tbody > tr")
    for game in games:
        if len(game.select("td[class^=seln]")) > 0:
            id = game["data-mkt_id"] 
            #time = format_timestamp(game.select("td > div > span[class~=clock]")[singleton].get("data-zero-point"))
            #TODO: get time from "datetime" on league page, and add an hour to it as it is always an hour behind.
            home = process_team(game.select('td[class^=seln] > div > button')[0].get("title").strip())
            away = process_team(game.select('td[class^=seln] > div > button')[2].get("title").strip())
            
            league = ""
            if check_league_present(TITAN,id) is True:
                league = get_league_from_list(TITAN,id)
            else:
                if game.select("td[class=stats] > a")!=None:
                    url = game.select("td[class=stats] > a")[singleton].get("href")
                    add_league(TITAN,id,"")
                    add_thread_for_league(TITAN,id,url,home,LIVE)
            
            if game.select("td > div > button")[0].get("disabled")==None: #if bets are not disabled, set them correctly.
                bets = game.select("td[class^=seln] > div > button > span > span[class^=dec]")
                home_bet = game.select("td[class^=seln] > div > button > span > span[class*=dec]")[0].text.strip()
                draw_bet = game.select("td[class^=seln] > div > button > span > span[class*=dec]")[1].text.strip()
                away_bet = game.select("td[class^=seln] > div > button > span > span[class*=dec]")[2].text.strip()
            else:
                home_bet = "0"
                draw_bet = "0"
                away_bet = "0"
            print(id + " " + league + " " + time + " " + home + " " + away + " " + home_bet + " " + draw_bet + " " + away_bet)
        
        #matches[LIVE].append(BookieMatch(TITAN,id,league,time,home,away,home_bet,draw_bet,away_bet))
        
class Titan(object):
      def __init__(self):
          print("titan started")
      
      def extract(self):
          '''
          global refresh_needed
          global current_match_ids
          global activate_refresh_state
          update_match_ids = True
          in_refresh_state = False
          print("creating driver..")
          #driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
          print("getting link..")
          #driver.get(link)
          print("link acquired.")
          
          
          uncomment this when finished testing. takes too long/unnecessary for testing
          print("selecting timezone..")
          driver.find_element_by_name('tz_offset').find_element_by_class_name("styled-select").click()
          driver.find_element_by_xpath(".//*[@id='header-area']/div[2]/div[2]/div[2]/form[1]/div/ul/li[14]").click()
          print("timezone selected.")   
            
          print("selecting decimal odds..")     
          driver.find_element_by_xpath(".//*[@id='header-area']/div[2]/div[2]/div[2]/div/div").click()       
          driver.find_element_by_xpath(".//*[@id='header-area']/div[2]/div[2]/div[2]/div/ul/li[2]").click()
          print("decimal odds selected.")
          '''
                    
          while True:
            '''
            if refresh_needed == True:
                print("refreshing current..")
                driver.refresh() #for some reason this is really slow when it happens. possibly do the same as I did with intertops
                print("current refreshed.")
                refresh_needed = False
                update_match_ids = True
            '''
              
            for i in range(UPCOMING,LIVE): matches[i] = []
            print("getting source..")
            response = requests.get(link)
            print("parsing..")             
            doc = BeautifulSoup(response.content, 'lxml')
            print("parsed.")
            
            print("getting upcoming games..")
            matches[UPCOMING] = get_upcoming_games(doc)           
            print("getting live games..")
            matches[LIVE] = get_live_games(doc)
                               
            if len(titan.threads) > 0: 
                start_threads() 
            
            print("sleeping 5 sec..")
            sleep(5)
                        
            
if __name__ == '__main__':
    '''
    print(linenumber())
    scraper = Titan()
    scraper.extract()
    '''
    
    print("started")
    start_time = current_time()
    r = requests.get("http://stats.betradar.com/s4/?clientid=159&language=en#2_1,3_4,22_4,5_10331,9_headtohead,7_4758,178_4785")
    doc = BeautifulSoup(r.content, "lxml")
    spans = doc.select("div[id=node_main-wrap] > div > div[class*=breadcrumb] > div[class=menu] > div > ul > li > a > div > span")
    for span in spans:
        print(span.text)
    '''
    driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
    driver.get("http://stats.betradar.com/s4/?clientid=159&language=en#2_1,3_4,22_4,5_10331,9_headtohead,7_4758,178_4785")
    
    doc = BeautifulSoup(driver.page_source, "lxml")
    spans = doc.select("div[id=node_main-wrap] > div > div[class*=breadcrumb] > div[class=menu] > div > ul > li > a > div > span")
    for span in spans:
        print(span.text)
    #print(len(doc.select("div[id=node_main-wrap] > div > div[class*=breadcrumb] > div[class=menu] > div > ul > li > a > div > span")))
    #print(len(doc.select("a[class=atopelem]")))
    
    while doc.select("a[class=atopelem] > div > span")[singleton].text == "": 
        print("regetting source..")
        doc = BeautifulSoup(driver.page_source, "lxml")
    
    print(doc.select("a[class=atopelem] > div > span")[singleton].text)
    print("time to get: " + str(current_time()-start_time))
    '''
    
    