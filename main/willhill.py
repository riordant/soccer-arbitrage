#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('/Users/tadhgriordan/Documents/AutoArb/dependencies')

from matches import *
import main
from main import *
import re
import urlparse
import thread
import atexit
import datetime
import urllib2
import xml.etree.cElementTree as ET
from datetime import date
from functions import *
from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import time

#times is a list of tuples of (id,time). needed for live games.
times = []

matches = []
ID = 0
TIME = 1

count = 0

#driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])

link = 'http://sports.williamhill.com/bet/en-ie/betting/y/5/tm/Football.html' # current site
#link = 'file:///Users/tadhgriordan/Documents/scraper/WilliamHill/webpages/1_L/william_hill.html' # tests
        
def cleanup():
    print("program exit")
    #driver.close()
    #driver.quit()
    
atexit.register(cleanup)

#William Hill Noisy data correction
#Team:
#(Bra): a Brazilian team.
#League:
#Playoffs: remove this
#Promotion: remove this
def process_team(str):
    if contains(str,"(Bra)"):
        str = str.replace("(Bra)","Brazil")
    if contains(str,"(Ecu)"):
        str = str.replace("(Ecu)","Ecuador")
    if contains(str,"(RSA)"):
        str = str.replace("(RSA)","South Africa")
    if contains(str,"(Por)"):
        str = str.replace("(Por)","Portugal")
        
def add_time(id,time):
    times.append([])
    times[len(times)-1].append(id)
    times[len(times)-1].append(time)
           
def alter_times(id,time):
    for time in times:
        if time[ID]==id:
           time[TIME]=time
           
def check_time_present(id):
    for time in times:
        if time[ID]==id:
           return [True,time[TIME]]
    return [False,""]
    
def getTimeThroughURL(id,url):    
    global count
    if check_time_present(id)[0] == False:
       time_driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
       print("url in gettimethroughurl: " + url)
       time_driver.get(url)
       time_driver.get_screenshot_as_file("hello" + str(count) + ".png")
       count += 1
       doc = BeautifulSoup(time_driver.page_source, "html.parser")
       time = doc.select("span[id=eventDetailsHeader] > nobr > span")[0].text.strip()
       print("time in gettimethrough url for id " + id + ": " + time)
       time = time[time.index('-'):len(time)-2]
       time = formatDate(time)
       alter_times(id,time)

def getLiveGameTime(league_game):               
    gametime = league_game.select("td[class~=leftPad] > a[id~=ip_"+ id[7:] + "_start]")
    if int(gametime[:2]) < 45: # if the game is definitely first half 
        gametime_milli = (int(gametime[:2]) * 60 * 1000) + (int(gametime[3:]) * 1000)
        live_time = currentTime() - gametime_milli
        
    elif int(gametime[:2]) >= 50: #if the game is definitely second half 
        half_time = 15 * 60 * 1000
        gametime_milli = (int(gametime[:2]) * 60 * 1000) + (int(gametime[3:]) * 1000)
        live_time = currentTime() - gametime_milli - half_time
    
    return live_time


class WillHillScraper(object):
    def __init__(self):
        print("started")

    def extract(self):
            
        leagues = s.select('div[id~="ip_sport_0_types"] > *')
        leagues.pop()
        
        for league in leagues:
              id = league['id'][8:]
              script  = "document.site.ajax_unexpanded_type('ip', '" + id + "', '0', 'Match _betting')"
              driver.execute_script(script)
              #self.driver.execute_script("document.site.ajax_unexpanded_type('ip', '" + league['id'][8:] + "', '0', 'Match _betting')")

        print("sleeping waiting for JS to finish..")
        sleep(2) #replace this with a while loop until last element is not a blank string.
        print("done")

        #re-parse page after javascript execution.
        s = BeautifulSoup(driver.page_source, "html.parser")
        leagues = s.select('div[id~="ip_sport_0_types"] > *')
        leagues.pop()
        for league in leagues:
            league_name = league.select("h3 > a")[0].text
            region = league_name.split(" ")[0] #region is (99% of the time) the first word.. doesn't have to be spot on just for identification in unknown db
            print(league_name)
            league_games = league.select("div > div > div > table > tbody > tr")
            for league_game in league_games:
                id = league_game['id']
                url = "" 
                urls = league_game.select("td[class~=leftPad] > a")
                for atag in urls:
                    url = atag.get('href') #stores the last 'a' tags' url into the url variable.
                print("url: " + url)
                url = url.replace("%2d","-")
                print("new url: " + url)	
                          
                time = ""
                if check_time_present(id)[ID]:
                   time = check_time_present(id)[TIME]
                else:
                  add_time(id,"") #if no entry for this game, we need to add one initially.
                  time = league_game.select("td[class~=leftPad] > a[id~=ip_"+ id[7:] + "_score]") 
                  if not(time == []): #for "live at", live and x mins games. the result is a list that's not empty
                     time = time[0].text # we specify the first element to be the time. If neither of the conditions below are satisfied, "time" is just the "Live At" time.
                     if "-" in time: # for a live game. we must estimate the start time from the diff of the current time and the game elapsed time, provided it's NOT half time.
                        #time = getLiveGameTime(league_game)
                        gametime = league_game.select("td[class~=leftPad] > a[id~=ip_"+ id[7:] + "_start]")[0].text.strip()
                        print(gametime)
                        if int(gametime[:2]) < 45: # if the game is definitely first half 
                            gametime_milli = (int(gametime[:2]) * 60 * 1000) + (int(gametime[3:]) * 1000)
                            live_time = currentTime() - gametime_milli
                        elif int(gametime[:2]) >= 50: #if the game is definitely second half 
                             half_time = 15 * 60 * 1000
                             gametime_milli = (int(gametime[:2]) * 60 * 1000) + (int(gametime[3:]) * 1000)
                             live_time = currentTime() - gametime_milli - half_time  
                        print(live_time)
                        live_time = live_time % 86400000 # normalisation. that value is a single day in milliseconds
                        time = str(datetime.timedelta(milliseconds=live_time))
                        time = time[0:5]
                        print(time)
                                                 
                     elif "min" in time:  # for an "x mins" game.
                        time = ""
                        print("thread for id " + id + " started.")
                        thread.start_new_thread(getTimeThroughURL,(id,url))
                     
                     else:
                        time = time[0:5] # "Live At" game. here we are just removing the postfix information after the time.
                     
                  else: # for "Today" games
                      time = league_game.select("td[class~=leftPad] > span")[0].text
                  
                  # remember we will have to standardise the time across all bookies as well.

                  print(id + " " + time)
                  alter_times(id,time)
                  
                teams = league_game.select("td > a > span[id~=" + id[7:] + "_mkt_namespace]")[0].text.replace(u'\xa0', u' ').split("   v   ")
                print(teams)
                home = teams[0]
                away = teams[1]

                home_bet = league_game.select("td[scope~=col] > div > div[id^=ip_selection]")[0].text.strip()
                draw_bet = league_game.select("td[scope~=col] > div > div[id^=ip_selection]")[1].text.strip()
                away_bet = league_game.select("td[scope~=col] > div > div[id^=ip_selection]")[2].text.strip()
                
                print(home + " " + away + " " + homeBet + " " + drawBet + " " + away_bet)
                #sleep(.1)
                matches.append(BookieMatch(WILLIAM_HILL,id,region,league_name,time,home,away,home_bet,draw_bet,away_bet))

        
if __name__ == '__main__':
    print(linenumber())
    scraper = WillHillScraper()
    print("in main class")
    while True:
        scraper.extract()

            
            