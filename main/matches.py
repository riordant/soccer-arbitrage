#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from main import TOTAL_BOOKIES,PINNACLE
from main import *
from functions import set_blank_array

class BookieMatch(object):  
    id = ""
    bookie_id = 0
    region = ""
    league = ""
    league_id = 0
    time = "" 
    home = ""
    away = ""
    home_bet = 0
    draw_bet = 0
    away_bet = 0 
    
    def __init__(self, bookie_id, id, region, league, league_id, time, home, away, home_bet, draw_bet, away_bet):
        self.bookie_id = bookie_id
        self.id = id
        self.league_id = league_id
        self.region = region
        self.league = league
        self.time = time
        self.home = home
        self.away = away
        self.home_bet = home_bet
        self.draw_bet = draw_bet
        self.away_bet = away_bet

    def __init__(self):
        #empty constructor for initialisation.
        pass
    

class Match(object): 
    ids       = set_blank_array(TOTAL_BOOKIES)
    regions   = set_blank_array(TOTAL_BOOKIES)
    leagues   = set_blank_array(TOTAL_BOOKIES)
    times     = set_blank_array(TOTAL_BOOKIES)
    homes     = set_blank_array(TOTAL_BOOKIES)
    aways     = set_blank_array(TOTAL_BOOKIES)
    home_bets = set_blank_array(TOTAL_BOOKIES)
    draw_bets = set_blank_array(TOTAL_BOOKIES)
    away_bets = set_blank_array(TOTAL_BOOKIES)
    bookie_ids_added = set_blank_array(TOTAL_BOOKIES)
    
    def __init__(self,bookie_match):
        set_bookie_match(bookie_match)
    
    def set_bookie_match(bookie_match):
        ids[bookie_match.bookie_id] = bookie_match.id
        regions[bookie_match.bookie_id] = bookie_match.regions
        leagues[bookie_match.bookie_id] = bookie_match.league
        times[bookie_match.bookie_id] = bookie_match.time
        homes[bookie_match.bookie_id] = bookie_match.home
        aways[bookie_match.bookie_id] = bookie_match.away
        home_bets[bookie_match.bookie_id] = bookie_match.home_bet
        draw_bets[bookie_match.bookie_id] = bookie_match.draw_bet
        away_bets[bookie_match.bookie_id] = bookie_match.away_bet
        bookie_ids_added[bookie_match.bookie_id] = True         