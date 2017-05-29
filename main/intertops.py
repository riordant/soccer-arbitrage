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
import requests
import stopit
import xml.etree.cElementTree as ET
from datetime import date
from functions import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from time import sleep
from socket import *

games = []

#'threads' is a list of tuples of (id,url). this is the information needed to start a new thread.
threads = []
ID = 0
URL  = 1

#'leagues' is a list of tuples of (id,league). leagues can only be gotten by running a thread for each game.
leagues = []
ID = 0
LEAGUE = 1

link="https://sports.intertops.eu/en/Bets/Sport/12?page=0&type=next&partial=true"

UPCOMING = 0
LIVE = 1

drivers = []
#print("getting drivers..")
#drivers.append(webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true']))
#drivers.append(webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true']))

finished = []
finished.append(False)
finished.append(False)

sources = []
sources.append([])
sources.append("") #Upcoming is a list of pages, Live is a single page.



hours_forward = 3
time_forward_milli = hours_forward*60*60*1000

def refresher(driver):  
   #GET/CHECK ALL THE FOLLOWING CODE
   cookies = driver.get_cookies() 
  
   driver.find_element_by_css_selector("body").send_keys(Keys.COMMAND, "t") # GET CODE
   tabs = driver.window_handles # GET CODE
   driver.switch_to.window(tabs[0])
   driver.find_element_by_css_selector("body").send_keys(Keys.CONTROL, Keys.TAB)
   driver.find_element_by_css_selector("body").send_keys(Keys.COMMAND, "w")
   driver.get("https://sports.intertops.eu/en/Bets/Sport/12")
   for cookie in cookies:
       driver.add_cookie(cookie)

def find_live_source(driver):
    global finished
    global sources
    start_time = current_time()
    print("getting link")
    response = requests.get("https:/")
    print response.content
    return response.content
    
def find_upcoming_source(driver):
    '''
    A barebones html page can be accessed which contains most of the info (bar leagues) that are needed.
    it still only shows 20 games per page however, and this function only gets the number of games up to
    a page number that is defined by how many games into the future we want to get by time.
    '''
    global link
    global finished
    global sources
    page = 0
    full_source = []
    last_game_reached = False
    start_time = current_time()
    while last_game_reached==False:
        print("page num: " + str(page))
        page+=1
        link = link.replace("page="+str(page-1),"page="+str(page)) 
        print("link: " + link) 
        driver.get(link)
        print("got link")
        try:
            all_game_times = driver.find_elements_by_css_selector("li > div > div > span[class^=eventdatetime]")
            print(len(all_game_times))
            last_game_time = all_game_times[len(all_game_times)-1].get_attribute("title") 
            print(last_game_time)        
            last_game_time = last_game_time.replace("<br/>"," ") #replaces "<br/>" with a space.
            last_game_time = format_time(INTERTOPS,last_game_time)
            print("last game time: " + last_game_time)
            full_source.append(driver.page_source)
            if time_in_millis(last_game_time) > (current_time() + time_forward_milli):
                last_game_reached = True
        except NoSuchElementException:
            last_game_reached==True #exception is raised in the case of reaching end of all games.
            
    link="https://sports.intertops.eu/en/Bets/Sport/12?page=0&type=next&partial=true"
    print("time to get: " + str(current_time()-start_time))
    return full_source
    
def find_relevant_matches(driver):
   '''
   * Intertops matches are in groups of 20; every time "show more" is clicked another group of 20 show.
   * this can go on for ages as matches go as far as a week ahead, and loading is relatively show, so id like to get all matches for 6 hours ahead of current time.
   * so the best way to do this is get all matches in the current set of 20, and attempt to find a game which is greater than 6 hours ahead (doesn't have to be exact)
   * if no match is found which fit this criteria, we click "show more" and repeat the process for the next 20.
   * when criteria met, we stop clicking show more and just use the matches we have (the group of 20/40/60 etc.)
   ''' 
   last_relevant_match_found = False    
   element_found = False
   while last_relevant_match_found == False:
       doc = BeautifulSoup(driver.page_source, "html.parser")
       games = doc.select("div[class=panel-body] > ul[class*=nextbets] > li")
       games.pop() #last element is not a match so it is removed.
       print("games size: " + str(len(games)))
       for game in games:
           if last_relevant_match_found: break
           time = game.select("div[class^=market-options] > span > span")[singleton].get("data-original-title")
           if time == "": time = game.select("div[class^=market-options] > span > span")[singleton].get("title") #could be Nonetype
           time = time.replace("<br/>"," ") #replaces "<br/>" with a space.
           time = format_time(INTERTOPS,time)    
           if time_in_millis(time) > (current_time() + 24*60*60*1000): 
               last_relevant_match_found = True #if the game time is over 6 hours ahead of now, stop adding new games.

       if last_relevant_match_found == False:
           element_found = False
       scroll_end_of_page(INTERTOPS,driver)
       while True: 
           if element_found: break
           try:
               show_more = WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CLASS_NAME, "load-more-lnk")))
               show_more.click() 
               element_found = True
           except TimeoutException:
               print("finished this scroll.")
           except NoSuchElementException: # end of page - basically all the games possible for the table.
               last_relevant_match_found = True 
               print("finished scrolling")  
           except ElementNotVisibleException: 
               print("element not found. repeating.")
   
   return games

''' start thread functions. 
    thread functions are not put into the 'functions' file as they must be separated per class to work correctly. (i think-test).
'''      
#returns: void. 
#stores the league for the game URL passed to it.
#threaded.
#tested - problem where the league returns 'None'. i think it's cause the html file i was using is outdated.
def get_league_from_url(id,url):
    req = urllib2.Request("https://sports.intertops.eu"+url, headers={'User-Agent' : "Magic Browser"}) 
    response = urllib2.urlopen(req)
    league_doc = BeautifulSoup(response, "html.parser")
    league = league_doc.title.string
    league = league.encode('ascii','ignore')
    league = league[league.index('  ')+2:].strip() #
    update_league_list(INTERTOPS,id,league)
    
def start_threads():
    #global threads
    for thread_vals in intertops.threads:
        #print("starting thread for id: " + thread_vals[ID])
        thread.start_new_thread(get_league_from_url,(thread_vals[ID],thread_vals[URL]))
        #print("finished thread for id: " + thread_vals[ID])
        sleep(.75)
    intertops.threads = [] #clear 'threads' on finish.
''' end thread functions. '''

class Intertops(object):
      def __init__(self):
          print("intertops started")
      
      def extract(self):
          
          while True:
              
              print("parsing..")
              '''
              thread.start_new_thread(find_upcoming_source,(drivers[UPCOMING],))
              sleep(.75)
              thread.start_new_thread(find_live_source,(drivers[LIVE],))
              '''
              
              sources[UPCOMING] = find_upcoming_source(drivers[UPCOMING])
              sources[LIVE] = find_live_source(drivers[LIVE])
              '''
              print("waiting for games to be gathered..")
              while not finished[UPCOMING] and not finished[LIVE]: pass #wait for games to be gathered
              print("gathered.")
              
              finished[UPCOMING] = False
              finished[LIVE] = False
              '''
              
              #Upcoming
              for upcoming_page_source in sources[UPCOMING]:
                  doc = BeautifulSoup(upcoming_page_source, "lxml")
                  print("file successfuly parsed.")
                  games = doc.select("body > li")
                  games.pop()
                  print("games size:  " + str(len(games)))
                  for game in games:
                      data = game.select("div[class=row] > div[class^=col-xs-4]")
                      id = data[0].select("a")[singleton].get("data-o-id") + data[1].select("a")[singleton].get("data-o-id") + data[2].select("a")[singleton].get("data-o-id")
                      home = data[0].select("div")[singleton].get("title").strip()
                      away = data[2].select("div")[singleton].get("title").strip()
                      home_bet = data[0].select("a")[singleton].get("data-o-inv").strip()
                      draw_bet = data[1].select("a")[singleton].get("data-o-inv").strip()
                      away_bet = data[2].select("a")[singleton].get("data-o-inv").strip()
                      print(home_bet + " " + draw_bet + " " + away_bet)
                      time = game.select("div[class^=market-options] > span > span")[singleton].get("title")
                      if time == "": time = game.select("div[class^=market-options] > span > span")[singleton].get("title")
                      time = time.replace("<br/>"," ") #replaces "<br/>" with a space.
                      time = format_time(INTERTOPS,time)
              
                      league = ""
                      region = ""
                      if check_league_present(INTERTOPS,id) == True:
                            league = get_league_from_list(INTERTOPS,id)
                            region = league.split(" ")[0] # the region is the first word of the league.

                      else:
                            url = game.select("div > div > a")[singleton].get("href").strip()
                            print(url)
                            add_league(INTERTOPS,id,"")
                            add_thread_for_league(INTERTOPS,id,url,None)
      
                      print(id + " " +  time + " " + league + " " + home + " " + away + " " + home_bet + " " + draw_bet + " " + away_bet)
              
              #Live
              doc = BeautifulSoup(sources[LIVE], "lxml")
              all_sports = doc.select("ul > li[class^=li-sport]")
              print("all sports len: " + str(len(all_sports)))
              soccer_index = 0
              for i,sport in enumerate(all_sports):
                  if sport.select("a > span")[singleton].text.strip() == "Soccer":
                     soccer_index = i
                     print("soccer index: " + soccer_index)
              games = all_sports[soccer_index].select("ul > li")
              print(str(len(games)))
              for game in games:
                  if len(game.select("div[class^=market]")) > 0: 
                      id_list = game.select("div[class=option] > a")
                      print(len(id_list))
                      id = game.select("div[class=option] > a")[0].get("data-o") + game.select("div[class=option] > a")[1].get("data-o") + game.select("div[class=option] > a")[2].get("data-o")
                      data = game.select("div > div > a")[singleton].get("data-original-title").text.strip()
                      data = data.split("•")
                      region = data[1].strip()
                      data = data[2].split("<br/>")
                      league = data[0].strip()
                      teams = data[1].strip()
                      time = data[2].strip()                      
                      home_bet = game.select("div[class=option] > a > span")[0].get("data-odds-value")
                      draw_bet = game.select("div[class=option] > a > span")[1].get("data-odds-value")
                      away_bet = game.select("div[class=option] > a > span")[2].get("data-odds-value")  
                      print(id + " " + data + " " + region + " " + league + " " + teams + " " + time + " " + home_bet + " " + draw_bet + " " + away_bet)          
                  
              if len(intertops.threads) > 0:
                  print("starting threads..")
                  start_threads()
              
              print("sleeping 5 secs..")
              sleep(5)  
              print("refreshed.")
                    
if __name__ == '__main__': 
    '''       
    scraper = Intertops()
    scraper.extract()
    '''
    
    start_time = current_time()    
    response = requests.get("http://liveweb.intertops.eu/")
    doc = BeautifulSoup(response.content,"lxml")
    sports = doc.select("a[class=name] > span[class=sport]")
    for sport in sports:
        print(sport.text)
    print("time to get: " + str(current_time()-start_time))
    '''
    start_time = current_time()    
    response = driver.get("https://sports.intertops.eu/en/Bets/Sport/12")
    doc = BeautifulSoup(driver.page_source,"lxml")
    print("time to get: " + str(current_time()-start_time))
    '''
    