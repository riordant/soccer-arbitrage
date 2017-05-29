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
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException

from bs4 import BeautifulSoup
from time import sleep

link = "https://www.pinnaclesports.com/en/login"

class Pinnacle(object):
    def __init__(self):
          print("Pinnacle started")
      
    def extract(self):
        
        print("getting driver..")
        driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
        driver.set_window_size(1280, 1024) # set browser size.
        doc_captured = False
        while not(doc_captured):
            try:
                print("getting link..")
                driver.get(link)
                print("link acquired")

                print("entering details..")
                driver.find_element_by_name("CustomerId").send_keys("") 
                driver.find_element_by_name("Password").send_keys("") 

                print("logging in..")
                driver.find_element_by_name("loginSubmit").click()

                print("finding and clicking continue..")        

                driver.find_element_by_class_name("loginNext").click()

                #Click game link and wait for some time
                print("clicking Soccer..")
                driver.find_element_by_link_text("Soccer").click()

                #Click moneyline link and wait for some time
                print("clicking Moneyline..")
                driver.find_element_by_id("menuEventFilter_29_299").click()
                print("scrolling to the end of the page..")
                scroll_end_of_page(PINNACLE,driver)
                doc_captured = True
            except (ElementNotVisibleException, NoSuchElementException):
                print("failed this iteration.")
                doc_captured = False
        
        print("getting json..")
        driver.get("https://members.pinnaclesports.com/Sportsbook/Asia/GetUpdates/?marketType=Live&timeStamp=04/20/2016%2012:08:24&selectedEventFilterId=299&selectedPeriodNumber=null&selectedTime=null") 
        
        print("getting and printing cookies..")
        cookies = driver.get_cookies()
        print(cookies)
        
        print("setting up requests session..")
        import requests
        s = requests.Session()
        
        for cookie in cookies:
            s.cookies.set(cookie['name'], cookie['value'])
        
        print("printing result..")
        r = s.get("https://members.pinnaclesports.com/Sportsbook/Asia/GetUpdates/?marketType=Live&timeStamp=04/20/2016%2012:08:24&selectedEventFilterId=299&selectedPeriodNumber=null&selectedTime=null") 
        
        print(r.content)
        
        parse_area_id = driver.find_element_by_id("29") #root element for both live, upcoming and early games.
        parse_area_source = parse_area_id.get_attribute("innerHTML")
        doc = BeautifulSoup(parse_area_source, "lxml")    
         
        types = doc.select("table")
        types.pop() #removes Early type games.

        for type in types:        
            leagues = type.select("tbody") 
            print("leagues size: " + str(len(leagues)))                   
            for league in leagues:
                league_name = league.select("tr > th > span[class=dispName]")[singleton].text.strip()
                region = league_name.split(" - ")[0]
                print(league_name)
                games = league.select("tr[id*=_]")
                for game in games:
                    id = game.get("id").split("_")[1]                
                    time    = format_time(PINNACLE, game.select("td > span[class^=hTime]")[singleton].text.strip())	
                    home = game.select("td > span[class~=Home]")[singleton].text.strip()			    			    	
                    away = game.select("td > span[class~=Away]")[singleton].text.strip()                
                    home_bet = game.select("td[class*=Handicap] > a")[singleton].text.strip()
                    if home_bet == "": home_bet = 0            
                    draw_bet = game.select("td[class*=T1] > a")[singleton].text.strip()
                    if draw_bet == "": draw_bet = 0            
                    away_bet = game.select("td[class*=T2] > a")[singleton].text.strip()
                    if away_bet == "": away_bet = 0                
                    print(id + " " + time + " " + region + " " + league_name + " " + home + " " + away + " " + home_bet + " " + draw_bet + " " + away_bet)
            
            
if __name__ == '__main__':  
    print(linenumber())
    scraper = Pinnacle()
    scraper.extract()   
    
