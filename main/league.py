'''
import mysql.connector
from fuzzywuzzy import fuzz
from db_indexes import *
from collections import Counter
from operator import itemgetter, attrgetter
'''

import sys
sys.path.append('/Users/tadhgriordan/Documents/AutoArb/dependencies')
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from fake_useragent import UserAgent
#from functions import quit_driver

def quit_driver(driver):
    driver.service.process.send_signal(SIGTERM)
    driver.quit() 

def current_time():
    millis = int(round(time.time() * 1000))
    return millis
    
def is_league_present_in_db(bookie_match):
    query_base = "SELECT * FROM IDENTIFIER WHERE BOOKIE_ID = %"
    query = query_base.replace("%",str(bookie_match.bookie_id))
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        if bookie_match.league == row[Identifier().STRING]:
            return True
    
    return False    
    
'''
gets the league id for the league passed to it, provided "is_league_present_in_db"
returns true for the same arguments.
'''
def get_league_id_from_db(bookie_match):
    query = query_base.replace("%",str(bookie_match.bookie_id))
    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        if bookie_match.league == row[Identifier().STRING]:
            return row[Identifier().LEAGUE_ID]


def add_to_identifier_table(bookie_match):
    '''the first query is used to find whether or not there is already an entry for this bookie id and league id.
       if the query returns 0 rows, we insert a new row.
       otherwise at least 1 does exist - so we add a new row with the same credentials and an incremented quantity value.'''
    
    query = "SELECT * FROM IDENTIFIER WHERE LEAGUE_ID = %d AND BOOKIE_ID = %d" % (bookie_match.league_id,bookie_match.bookie_id)
    cursor.execute(query)
    rows = cursor.fetchall()
    
    if len(rows) == 0: #no entries for this league and bookie id. so we add a new entry with quantity 1
        query = "INSERT into IDENTIFIER (STRING,LEAGUE_ID,BOOKIE_ID,QUANTITY,CHECKED) values (%s, %s, %s,%d,%s)" % (bookie_match.league, bookie_match.league_id, bookie_match.bookie_id,1,"N")
        cursor.execute(query)
  
    else: #multiple entries found. we add a new entry with the highest current quantity + 1
        max_quantity_query = "select max(quantity) from identifier where league_id = %d and bookie_id = %d" % (298,2)
        cursor.execute(max_quantity_query)
        quantity = cursor.fetchall()[0][0] + 1
        query = "INSERT into IDENTIFIER (STRING,LEAGUE_ID,BOOKIE_ID,QUANTITY,CHECKED) values (%s, %s, %s, %d, %s)" % (bookie_match.league, bookie_match.league_id, bookie_match.bookie_id, quantity, "N")
        cursor.execute(query)
    
    db.commit()
    # Commit your changes in the database
    
    
def add_to_unknown_table(bookie_match):
    query = "INSERT into IDENTIFIER (REGION,LEAGUE,EXAMPLE_MATCH,BOOKIE_ID) values (%s, %s, %s, %d)" % (bookie_match.region, bookie_match.league, bookie_match.home + " vs. " + bookie_match.away,bookie_match.bookie_id)
    cursor.execute(query)
    
    

    

            
'''
the following function is called in the case that the "is_league_present_in_db"
returns false.
the process is as follows:
    - match against each identifier in the db
    - take each match that has a value thats greater than 90.
    - divide into league groups
    - take the group that has the most identifiers.
    - if no one group has an equal number of entries: take the top groups.
    - add the values of the identifiers of the top groups and select the highest
advantages of this method: it takes precedence over league groups that have a higher number
of identifiers, but in the case that a number of groups are identified, it takes the most identified
group out of them by the total value of the identifiers. hopefully this would be an extreme edge case
however.
'''     
    
def add_to_database(bookie_match):
    ID = 0
    QUANTITY = 1
    TOTAL = 1
    query = "SELECT * FROM IDENTIFIER"
    strong_identifiers = []
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        fuzzy_match = fuzzymatch(bookie_match.league,row[Identifier().STRING])
        if result >= 90:
            row.append(fuzzy_match)
            strong_identifiers.append(row)
    
    if len(rows) > 0:
        strong_league_ids = [row[Identifier().LEAGUE_ID] for row in rows] #get league ids of strong identifiers.
    
        ordered_strong_league_ids = Counter(strong_league_ids).most_common() #organises league ids by most common in ascending order.
    
        if len(ordered_strong_league_ids) == 1:
            return ordered_strong_league_ids[0][ID]
        
        #the length of the ordered list is greater than 1 and so we potentially have a number of leagues.
        #the way in which this will be done is to get the league id of the highest matching league ids,
        #get the fuzzy match results for those league ids from the rows, and add them together.
        #the league id with the highest value is the match.
        
        quantity_of_highest_ordered_strong_league_id = ordered_strong_league_ids[0][QUANTITY]
        
        fuzzy_totals = [] #position 0: league id, position 1: fuzzy total
        
        #ok you've to go back to rows and apply for the league ids you have that are high
        for ordered_strong_league_id in ordered_strong_league_ids:        
            if ordered_strong_league_id[QUANTITY] == quantity_of_highest_ordered_strong_league_id:
                fuzzy_totals.append(ordered_strong_league_id[ID],0)
                for row in rows:
                    if row[Identifier().LEAGUE_ID] == ordered_strong_league_id[ID]:
                        fuzzy_totals[len(fuzzy_totals)-1][TOTAL] += row[Identifier().FUZZY_MATCH]
        
        #orders the list by fuzzy total. the end bit reverses it as it is in descending order by default
        fuzzy_totals = (sorted(fuzzy_totals, key=itemgetter(TOTAL)))[::-1] 
        
        if fuzzy_totals[0][TOTAL] > fuzzy_totals[1][TOTAL]:
            #add new identifier row with checked false
            add_to_identifier_table(bookie_match,fuzzy_totals[0][ID])
        else:
            #add unidentified league to the unknown table in the database.
            add_to_unknown_table(bookie_match)
    
    else:
        #add new league and identifier for the league - with checked set to false.
        add_to_unknown_table(bookie_match)
        return None
            
    
def fuzzymatch(fst,snd):
    partial = fuzz.partial_ratio(fst,snd)
    print(partial)
    normal = fuzz.ratio(fst,snd)
    print(normal)
    token_sort = fuzz.token_sort_ratio(fst,snd)
    print(token_sort)
    token_set = fuzz.token_set_ratio(fst,snd)
    print(token_set)
    result = (partial + normal + token_sort + token_set)/4   
    return result

if __name__ == '__main__': 
    '''
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36"
    
    #team = "man utd"
    url = "https://www.google.ie/search?hl=en&q=chelsea+soccer+football&btnG=Google+Search&inurl=https&gws_rd=ssl"
    #url = "https://www.google.ie/#q=man+utd+soccer+football"
    #url = url.replace("team",team)
    print(url)
    #headers = {'User-Agent': user_agent}
    response = requests.get(url,headers={'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36"})
    #print(response.text)
    doc = BeautifulSoup(response.content,"lxml")
    
    #list = doc.select("div[class=_B5d]")
    #print(len(list))
    print(response.content)
    '''
    
    start_time = current_time()
    print("setting up driver..")
    driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'])
    driver.set_window_size(1280, 1024)
    
    print("getting link..")
    driver.get("https://www.google.ie/#q=chelsea+soccer+football")
    driver.get_screenshot_as_file("google.png")
    
    #print(driver.page_source)
    
    doc = BeautifulSoup(driver.page_source,"lxml")
    
    xpdopen = doc.select("div[class=_B5d]")[0].text
    
    print(xpdopen)
    
    print("time to get: " + str(current_time()-start_time))
    #quit_driver(driver)
    
       
    
    
    
    
    