#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from functions import contains,format_match_id_date_url, find_nth
#from main import Special
import requests
import arrow
import pycurl
from StringIO import StringIO
import random
from random import randint
import re
    
singleton = 0

def get_match_id(teams,date,time):
    teams = process_teams(teams)
    
    #date = format_match_id_date_url(date)
    
    url = create_google_url(teams,date)
        
    results = get_results(url)
    
    for result in results:       
        result_url = result.select("h3 > a")[singleton].get("href")[7:]
        print("result_url: " + result_url)
        if contains(result_url,"soccerway.com"): #first result from soccerway with " vs. " in the string, after the title is split by " - ".
            result_url = create_soccerway_url(result_url)
            result_doc = get_soccerway(result_url)
            if time == get_time(result_doc):
                title = get_title(result_doc)
                if contains(title," - "): #string can be eg 11 April 2016 or 11 april 2016
                    title_list = title.split(" - ")
                    for title_list_elem in title_list:
                        if contains(title_list_elem,"vs."):
                            return title_list_elem
    return ""


def process_teams(teams):
    #General query entries that just have to be removed with no special cases.
    #anything particularly difficult will be processed client-side
    undesirable_query_entries = ["&"," FC","FC ","CD "," CD","SC "," SC"," PI", "PI ","JK "," JK", #Misc.
                                 "U20","U19", #General
                                 "(women)","(Women)", #Betsson
                                 "(W)","(R)", #Titan
                                 "(Bra)","(Ecu)","(RSA)","(Por)", #William Hill 
                                 "(n)", #Pinnacle
                                 "(A)" #Intertops                                              
                                 ]
    for undesirable_query_entry in undesirable_query_entries:
        if contains(teams,undesirable_query_entry):
            teams.replace(undesirable_query_entry,"")
       
    return teams
    
#here we jumble the search query up in different ways to avoid having the same query format constantly -
#but the result should be the same regardless of the string.
#either of "home vs. away|home away|home v. away|other way around", "inurl:YYYY/MM/DD|YYYY-MM-DD|YYYY~MM~DD" and "Soccerway|soccerway" etc.,
#will be set in order 1-3.
#the url will also be changed randomly as we know 2 parameter strings that work, and also adding/not adding filter=0.
def create_google_url(teams,date):
    
    teams_list = teams.split(" vs. ")  
    indexes = random.sample(range(0,len(teams_list)),len(teams_list))
    string = teams_list[indexes[0]].lower() + rand_string_split() + teams_list[indexes[1]].lower()
    string = string.replace(" ","+")
    
    date_list = date.split(" ")
    inurl = '"inurl:' + date_list[0] + rand_inurl_delimiter() + date_list[1] + rand_inurl_delimiter() + date_list[2] + '"'
    
    web_id = rand_web_id()
    
    url_type = rand_url_type()
    
    filter = rand_param_filter()
     
    query = [string,inurl,web_id]
    indexes = random.sample(range(0,len(query)),len(query))
    
    url = url_type + query[indexes[0]] + "+" + query[indexes[1]] + "+" + query[indexes[2]] + filter
    
    print("url: " + url)
    return url

def create_soccerway_url(url):
    if not contains(url,"http://") or not contains(url,"https://"):
        url = "http://" + url
    url = url[0:find_nth(url,"/",12)+1] #removes noise after the '/' character which follows the event id
    print("url after extra removal: " + url)
    url = re.sub("http://.*.soccerway",'http://int.soccerway',url) #changes soccerway location to international (consistent string and maybe time)
    print("url after location change: " + url)
    return url
    
def rand_inurl_delimiter():
    rand = randint(0,3)
    if rand == 0:
        return "/"
    if rand == 1:
        return "-"
    if rand == 2:
        return "~"
    if rand == 3:
        return "`"

def rand_string_split():
    rand = randint(0,2)
    if rand == 0:
        return " vs. "
    if rand == 1:
        return " v. "
    if rand == 2:
        return " "

def rand_web_id():
    rand = randint(0,1)
    if rand == 0:
        return "soccerway"
    if rand == 1:
        return "Soccerway"

def rand_url_type():
    rand = randint(0,1)
    if rand == 0:
        return "http://www.google.com/search?hl=en&tbo=d&site=&source=hp&q="
    if rand == 1:
        return "https://www.google.com/search?hl=en&q="

def rand_param_filter():
     rand = randint(0,1)
     if rand == 0:
        return "&filter=0"
     if rand == 1:
        return ""
       

def get_results(url):
    
    buffer = StringIO()
    c = pycurl.Curl()
    #useragent = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    useragent = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
    c.setopt(pycurl.USERAGENT,useragent)
    c.setopt(c.URL, url)
    c.setopt(pycurl.FOLLOWLOCATION, True)   
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    body = buffer.getvalue()
    #print(body)
    
    #body = open('google_test.html', 'r').read()
    #open('google_test.html', 'r').write()

    doc = BeautifulSoup(body,"lxml")
    results = doc.select("div[class=g]")
    
    print("number results: " + str(len(results)))
    return results

def get_soccerway(url):
    response = requests.get(url)
    doc = BeautifulSoup(response.content,"lxml")
    return doc

def get_title(doc):
    return doc.select("title")[singleton] 
      
def get_time(doc):
    #gets the soccerway event url and fetches the time.
    #Part 1: if time in top section
    print("get time called")
    scoretime = doc.select(".scoretime")
    if len(scoretime)>0: 
        time = scoretime[0].text.strip()[0:5] #removes potential 'span' class on time
        if not contains(time,"-"):
            print("time: " + time)
            return str(arrow.get(time,"HH:mm").replace(hours=-1))[11:16]
            
    #part 2: if time in box
    box_dt = doc.select("div[class^=details] > dl > dt")
    if len(box_dt)>0:
        index = -1
        for i,dt in enumerate(box_dt):
            if dt.text.strip() == "Kick-off":
                index = i
                break
        if index != -1:
            box_dd = doc.select("div[class^=details] > dl > dd")
            time = box_dd[index].text.strip()[0:5] 
            print("time: " + time)
            return str(arrow.get(time,"HH:mm").replace(hours=-1))[11:16] #time difference from requests returned value. WATCH OUT FOR THIS       
    #No suitable string found. return nothing
    
    print("return no time")
    return ""
    
if __name__ == '__main__':
    print(get_match_id("Juventus vs. Palermo","2016 04 17","14:00")) #SOCCERWAY IS ACCURATE
    #2016/04/16/brazil/paranaense-1/clube-atletico-paranaense/parana-clube
    
    #response = requests.get("http://int.soccerway.com/matches/2016/04/17/italy/serie-a/juventus-fc/us-citta-di-palermo/2120702/")
    #("Juventus vs. Palermo","2016 04 17","14:00")
    #doc = BeautifulSoup(response.content,"lxml")
    
    print(get_time(doc))
    #print(get_time("http://au.soccerway.com/matches/2016/04/17/england/premier-league/afc-bournemouth/liverpool-fc/2043549/"))
    
