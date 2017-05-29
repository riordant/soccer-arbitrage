#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('/Users/tadhgriordan/Documents/AutoArb/main')
import os
import requests
from inspect import currentframe
from datetime import datetime
from datetime import date
import time
import arrow
from selenium import webdriver
#import main
from main import *
#import intertops
#import willhill
#import titan
#import pinnacle
from signal import SIGTERM
from bs4 import BeautifulSoup
from time import sleep
import urllib2
import math
#from google import *
from itertools import tee, islice, chain, izip



''' this file contains a number of common functions across a number of (or all) bookies. '''
singleton = 0 # '.select' with BeautifulSoup always returns a list. most of my selectors return a list of size 1. this just makes it more readable.
ID = 0
LEAGUE = 1

XPATH = 0
TAG_NAME = 1
CLASS_NAME = 2

''' start misc. functions. '''
def contains(str,substr):
    if str.find(substr) != -1:
        return True
    return False

def linenumber():
    cf = currentframe()
    return cf.f_back.f_lineno

def find_between(s, first, last):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""
        
def get_page_load_time(link):
    start_time = current_time()
    r = requests.get(link)
    doc = BeautifulSoup(r.content,"lxml")
    print("time to get: " + str(current_time() - start_time))

def quit_driver(driver):
    driver.service.process.send_signal(SIGTERM)
    driver.quit() 

def set_blank_array(size):
    arr = []
    for i in range(1,size):
        arr.append([])
    return arr

def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

#takes the amount of bookieMatches for one Match as an argument,
#and returns a list of indexes for each potential arb.
#for example, 3 bookies= 3^3 - 3, 4 bookies=4^3 - 4
#essentially, the list counts from 0 to size^3 in the base number system equal to size.
def get_bet_indexes(size):
    list_size = pow(size,3)
    list = []
    for i in range(list_size):
        nums = []
        while i:
            i, r = divmod(i, size)
            nums.append(str(r))
        index = ''.join(reversed(nums))
        num_zeros_to_append = 3-len(index)
        for zero in range(num_zeros_to_append):
            index = "0"+index
        index = [int(index[0]),int(index[1]),int(index[2])]
        if index.count(index[0]) != len(index): #checks if all elements are identical (undesired as that would be the same bookie)
            list.append(index)
    return list

#gets the previous and next element in a list in a tuple
def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return izip(prevs, items, nexts)
''' end misc. functions. '''


'''start webpage/html related functions. '''        
def write_page_to_file(bookie):
    if bookie == TITAN:
        link = "http://sports.titanbet.co.uk/en/football"
        print("creating driver..")
        driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
        print("getting link..")
        driver.get(link)
        print("link acquired.")
        print("writing file..")
        filename = arrow.utcnow().format("ddd MMM DD HH-mm-ss a YYYY") #create filename: the current date
        file_path = os.path.join("/Users/tadhgriordan/Documents/AutoArb/webpages/Titan", filename+".html") #create and store empty html file
        html_file= open(file_path,"w") #open from directory
        html_file.write(driver.page_source.encode('utf-8','ignore')) 
        html_file.close() 
        print("file written.")
        
    if bookie == WILLIAM_HILL:
        link = "http://sports.williamhill.com/bet/en-ie/betting/y/5/tm/Football.html"
        print("creating driver..")
        driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
        print("getting link..")
        driver.get(link)
        print("link acquired.")
        print("executing scripts..")
        print("parsing doc..")
        s = BeautifulSoup(driver.page_source, "html.parser")
        print("doc parsed.")
        leagues = s.select('div[id~="ip_sport_0_types"] > *')
        leagues.pop() 
        for league in leagues:
              id = league['id'][8:]
              script  = "document.site.ajax_unexpanded_type('ip', '" + id + "', '0', 'Match Betting')"
              driver.execute_script(script)
        print("sleeping waiting for JS to finish..")
        sleep(2) #replace this with a while loop until last element is not a blank string.
        print("done")

        print("writing file..")
        filename = arrow.utcnow().format("ddd MMM DD HH-mm-ss a YYYY") #create filename: the current date
        file_path = os.path.join("/Users/tadhgriordan/Documents/AutoArb/webpages/WilliamHill", filename+".html") #create and store empty html file
        html_file= open(file_path,"w") #open from directory
        html_file.write(driver.page_source.encode('utf-8','ignore')) 
        print("file written.")
    
    if bookie == INTERTOPS:
        link = "https://sports.intertops.eu/en/Bets/Sport/12"
        print("creating driver..")
        driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
        print("getting link..")
        driver.get(link)
        print("link acquired.")
        print("writing file..")
        filename = arrow.utcnow().format("ddd MMM DD HH-mm-ss a YYYY") #create filename: the current date
        file_path = os.path.join("/Users/tadhgriordan/Documents/AutoArb/webpages/Intertops", filename+".html") #create and store empty html file
        html_file= open(file_path,"w") #open from directory
        html_file.write(driver.page_source.encode('utf-8','ignore')) 
        html_file.close() 
        print("file written.")
    
    if bookie == PINNACLE:
        print("getting driver..")
        driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
        driver.set_window_size(1280, 1024) # set browser size.
        print("getting link..")
        driver.get("https://www.pinnaclesports.com/en/login")
        print("link acquired.")
        print("logging in..")
        driver.find_element_by_name("CustomerId").send_keys("TR790474")
        driver.find_element_by_name("Password").send_keys("lub9_H0y5") 
        driver.find_element_by_name("loginSubmit").click()

        driver.find_element_by_class_name("loginNext").click()
        
        #Click game link and wait for some time
        print("clicking Soccer..")
        driver.find_element_by_link_text("Soccer").click()

        #Click moneyline link and wait for some time
        print("clicking Moneyline..")
        driver.find_element_by_id("menuEventFilter_29_299").click()
    
        print("scrolling to the end of the page..")
        pinnacle.scroll_end_of_page(driver)
        print("done")
        
        driver.get_screenshot_as_file("pinnacle_end.png")
        
        print("writing file..")
        filename = arrow.utcnow().format("ddd MMM DD HH-mm-ss a YYYY") #create filename: the current date
        file_path = os.path.join("/Users/tadhgriordan/Documents/AutoArb/webpages/Pinnacle", filename+".html") #create and store empty html file
        html_file= open(file_path,"w") #open from directory
        html_file.write(driver.page_source.encode('utf-8','ignore')) 
        html_file.close() 
        print("file written.")

def scroll_end_of_page(bookie,driver):
    if bookie == PINNACLE:
        for x in range(0,1000): driver.execute_script("window.scrollBy(0,250)", "") #the 650 is arbitrary, the higher the number the more scrolling takes place, but when it reaches the end it gets slow.
        driver.execute_script("window.scrollTo(Math.max(document.documentElement.scrollHeight,document.body.scrollHeight,document.documentElement.clientHeight),0);") #return to top.
    if bookie == INTERTOPS:
        for x in range(0,65): driver.execute_script("window.scrollBy(0,250)", "")

'''test both functions below. consider passing a value to each for a timeout.'''
def get_lagged_element(driver, type, path):
    element_found = False
    if type==XPATH:
        while True:
            try:
                element = driver.find_element_by_xpath(path)
                return element
            except (ElementNotVisibleException, NoSuchElementException):
                print("element not yet visible or not yet present.")
    if type==TAG_NAME:
        while True:
            try:
                element = driver.find_element_by_tag_name(path)
                return element
            except (ElementNotVisibleException, NoSuchElementException):
                print("element not yet visible or not yet present.")  
    if type==CLASS_NAME:
        while True:
            try:
                element = driver.find_element_by_class_name(path)
                return element
            except (ElementNotVisibleException, NoSuchElementException):
                print("element not yet visible or not yet present.")

def wait_for_page_loaded(driver):
        page_loaded = False       
        while not(page_loaded):
            is_page_loaded= driver.execute_script("return document.readyState")
            if is_page_loaded=="complete":
                page_loaded=True
                
'''end webpage/html related functions. '''        
              
    
    
''' start 'get league' functions. '''       
#returns: boolean - True provided the league is present in leagues for that bookie, False otherwise.
def check_league_present(bookie,id):
    if bookie == TITAN:     leagues = titan.leagues
    if bookie == INTERTOPS: leagues = intertops.leagues  
    for league in leagues:
        if league[ID] == id:
            return True
    return False

#returns: void.
#adds a new entry to the league list for that bookie.
#each element is referenced by the game id.
def add_league(bookie,id,league):
    if bookie==TITAN:
        titan.leagues.append([])
        titan.leagues[len(titan.leagues)-1].append(id)
        titan.leagues[len(titan.leagues)-1].append(league)
    if bookie==INTERTOPS:
        intertops.leagues.append([])
        intertops.leagues[len(intertops.leagues)-1].append(id)
        intertops.leagues[len(intertops.leagues)-1].append(league) 
        
# returns: String - the league from the list given the game id.
# is only called if 'check_league_present' returns True
def get_league_from_list(bookie,id):
    if bookie == TITAN: leagues = titan.leagues
    if bookie == INTERTOPS: leagues = intertops.leagues  
    for league in leagues:
        if league[ID] == id:
            return league[LEAGUE] 

#returns: void.
#updates the league list by adding the new league found in the thread for that bookie.
#game in list is found by id.
def update_league_list(bookie,id,league):
    if bookie == TITAN:
        for league_index in titan.leagues:
            if league_index[ID] == id:
                league_index[LEAGUE] = str(league)
                
    if bookie == INTERTOPS:
        for league_index in intertops.leagues:
            if league_index[ID] == id:
                league_index[LEAGUE] = str(league)

#returns: void.
#adds a new thread to the list for that bookie, to be started later in extracting the league.
#'extra' is for any extra arguments necessary for extracting the league. it will be a list if >1 args
def add_thread_for_league(bookie,id,url,extra):
    if bookie == TITAN: #'extra' is the string for the home team.
        titan.threads.append([])
        titan.threads[len(titan.threads)-1].append(id)
        titan.threads[len(titan.threads)-1].append(url)
        titan.threads[len(titan.threads)-1].append(extra)
           
    if bookie == INTERTOPS: #no extra here.
        intertops.threads.append([])
        intertops.threads[len(intertops.threads)-1].append(id)
        intertops.threads[len(intertops.threads)-1].append(url) 
''' end 'get league' functions.'''


''' start time functions. '''

def is_time_within_five_mins(bookie_time,match_time):
    five_before_millis = time_in_millis(match_time)-(5*60*1000)
    five_after_millis  = time_in_millis(match_time)+(5*60*1000)
    bookie_time_millis = time_in_millis(bookie_time)

    if((five_before_millis < bookie_time_millis)==(bookie_time_millis<five_after_millis)): return True

    return False
	
	
def current_time():
    millis = int(round(time.time() * 1000))
    return millis

def time_in_millis(formatted_time):
    parsed = arrow.get(formatted_time[4:], "MMM DD HH:mm:ss a YYYY")
    return parsed.timestamp*1000

def format_timestamp(millis):
    parsed = arrow.get(millis)
    formatted = parsed.format("ddd MMM DD HH:mm:ss a YYYY")
    return formatted

def format_match_id_date_title(formatted_time):
    parsed = arrow.get(formatted_time[4:], "MMM DD HH:mm:ss a YYYY")
    formatted = parsed.format("DD MMMM YYYY")
    return formatted

def format_match_id_date_url(formatted_time):
    parsed = arrow.get(formatted_time[4:], "MMM DD HH:mm:ss a YYYY")
    formatted = parsed.format("YYYY MM DD")
    print(formatted)
    return formatted
            
def format_time(bookie,unformatted_time):
    if bookie == TITAN:     
        parsed = arrow.get(unformatted_time + " " + str(arrow.utcnow().year), 'DD MMM HH:mm YYYY') # Example: "03 Feb 00:00 2016"
    if bookie == INTERTOPS:      
        parsed = arrow.get(unformatted_time, 'M/D/YYYY h:mm A') #example: "1/31/2016 5:15 PM"
    if bookie == PINNACLE:
        parsed = arrow.get(unformatted_time, 'M/D/YYYY h:mm A') #example: "2/10/2016 1:00 AM"
    if bookie == BETSSON:
        parsed = arrow.get(unformatted_time, 'YYYY-MM-DD HH:mm:ss') # example: 2016-04-11 18:45:00
    formatted = parsed.format("ddd MMM DD HH:mm:ss a YYYY")
    return formatted   

def check_game_started(formatted_time):  #takes the output after the date has been formatted.
    parsed = arrow.get(formatted_time[4:], "MMM DD HH:mm:ss a YYYY") # '.get' doesn't parse anything except the symbols here, so 'ddd' has to be removed.
    game_time_milli = parsed.timestamp*1000 # 'timestamp' is in seconds.
    if(game_time_milli<current_time()):
         return True 
    return False
''' end time functions. '''  
