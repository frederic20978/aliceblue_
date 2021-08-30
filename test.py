import logging
import requests
import datetime
import sys
from time import sleep
from alice_blue import *
from datetime import datetime,timedelta,date,time
from square_off import square_off

username = '313008'
password = 'Joel@2001'
api_secret = 'G9wMhSURQUbHJyFa7nrhRCiLiVmOKUO6nJ7FwjuNQh5P82ORcfxQmLMS4u3ZBjK0'
twoFA = 'sheeja'
app_id = 'Ja8cd2b8sD'

def event_handler_quote_update(message):
    global ltp
    # if message['instrument'].symbol:
    if message['instrument'].symbol.find('CE')==-1:
        print(message['instrument'].symbol)
        print("PE")
    else:
        print(message['instrument'].symbol)
        print('CE')
    ltp = message['ltp']

def open_callback():
    global socket_opened
    socket_opened = True

file = open('access_token.txt','r')
access_token = file.read()
alice = AliceBlue(username=username, password=password, access_token=access_token, master_contracts_to_download=['NSE','NFO'])

socket_opened = False
alice.start_websocket(subscribe_callback=event_handler_quote_update,
                    socket_open_callback=open_callback,
                    run_in_background=True)
while(socket_opened==False):    # wait till socket open & then subscribe
    pass
sleep(1)

bn_call = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date = date(2021,8,26), is_fut = False, strike = 35500, is_CE = True)
alice.subscribe(bn_call, LiveFeedType.COMPACT)
sleep(10)
alice.unsubscribe(bn_call, LiveFeedType.COMPACT)
    
bn_put = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date = date(2021,8,26), is_fut = False, strike = 35500, is_CE = False)
alice.subscribe(bn_put, LiveFeedType.COMPACT)
sleep(10)
alice.unsubscribe(bn_put,LiveFeedType.COMPACT)
