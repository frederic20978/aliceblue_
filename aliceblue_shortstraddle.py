import logging
import requests
import datetime
import sys
import json
from time import sleep
import pickle
from alice_blue import *
from datetime import datetime,timedelta,date,time
from square_off import square_off
from bs4.builder import FAST
from protlib import CUChar


# Config

f = open('credentials/details.json',)
data = json.load(f)

username = data['username']
password = data['password']
api_secret = data['api_secret']
twoFA = data['twoFA']
app_id = data['app_id']

nse_holiday = [date(2021,7,21), date(2021,8,19), date(2021,9,10), date(2021,10,15), date(2021,11,5), date(2021,11,19)]

no_of_lots = 3
sl = [ 0.2, 0.3, 0.4, 0.4, 0.2, 0.05, 0.05]
curr_orders = []


ltp = 0
optionType = ''
socket_opened = False
alice = None
def event_handler_quote_update(message):
    global ltp
    global optionType
    if message['instrument'].symbol.find('CE')!=-1:
        optionType = "CE"
    elif message['instrument'].symbol.find('PE')!=-1:
        optionType = "PE"
    else:
        optionType = "NO"
    ltp = message['ltp']

def open_callback():
    global socket_opened
    socket_opened = True


def sell_ce_option(bn_call,ce_price):
    print('selling call option @ ',ltp)
    logging.info('selling call option @ '+str(ltp))

    quantity = no_of_lots*int(bn_call[5])
    sl_percentage = sl[date.today().weekday()]

    sell_order = alice.place_order(transaction_type = TransactionType.Sell,
                         instrument = bn_call,
                         quantity = quantity,
                         order_type = OrderType.Market,
                         product_type = ProductType.Delivery,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)

    trig = float(round((1 + sl_percentage)*ltp))
    curr_orders.append(sell_order['data']['oms_order_id'])

    if sell_order['status'] == 'success':
        sl_order = alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = bn_call,
                     quantity = quantity,
                     order_type = OrderType.StopLossLimit,
                     product_type = ProductType.Delivery,
                     price = trig+20,
                     trigger_price = trig,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
    curr_orders.append(sl_order['data']['oms_order_id'])


def sell_pe_option(bn_put,pe_price):
    print('selling put option @ ',ltp )
    logging.info('selling put option @ '+ str(ltp) )

    quantity = no_of_lots*int(bn_put[5])
    sl_percentage = sl[date.today().weekday()]

    sell_order = alice.place_order(transaction_type = TransactionType.Sell,
                         instrument = bn_put,
                         quantity = quantity,
                         order_type = OrderType.Market,
                         product_type = ProductType.Delivery,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)

    trig = float(round((1 + sl_percentage)*ltp))
    curr_orders.append(sell_order['data']['oms_order_id'])

    if sell_order['status'] == 'success':
        sl_order = alice.place_order(transaction_type = TransactionType.Buy,
                     instrument = bn_put,
                     quantity = quantity,
                     order_type = OrderType.StopLossLimit,
                     product_type = ProductType.Delivery,
                     price = trig + 20,
                     trigger_price = trig,
                     stop_loss = None,
                     square_off = None,
                     trailing_sl = None,
                     is_amo = False)
    curr_orders.append(sl_order['data']['oms_order_id'])

def get_date_curr_expiry(atm_ce):
    print('getting current expiry date')
    logging.info('getting current expiry date')
    global datecalc
    call = None

    datecalc = date.today()
    #get curretn week expiry date
    while call==None:
        try:
            call = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date = datecalc, is_fut = False, strike = atm_ce, is_CE = True)
            if call == None:
                datecalc = datecalc + timedelta(days=1)

        except:
            pass

def get_ce_curr_price(atm_ce):
    print('getting current atm_call price')
    logging.info('getting current atm_call price')
    global bn_call,token_ce,ce_order_placed,ce_sl_price

    bn_call = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date = datecalc, is_fut = False, strike = atm_ce, is_CE = True)
    alice.subscribe(bn_call, LiveFeedType.COMPACT)
    sleep(0.5)
    while optionType.find('CE')==-1:
        
        print('CE needed Not CE')
        logging.info('CE needed Not CE')
        print(optionType)
        sleep(1)
        pass
    ce_price = ltp
    sell_ce_option(bn_call,ce_price)
    alice.unsubscribe(bn_call,LiveFeedType.COMPACT)


def get_pe_curr_price(atm_pe):
    print('getting current atm_put price')
    logging.info('getting current atm_put price')
    global bn_put,token_pe,pe_order_placed,pe_sl_price

    bn_put = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date = datecalc, is_fut = False, strike = atm_pe, is_CE = False)
    alice.subscribe(bn_put, LiveFeedType.COMPACT)
    sleep(0.5)
    while optionType.find('PE')==-1:
        print('PE needed Not PE')
        logging.info('PE needed Not PE')
        print(optionType)
        sleep(1)
        pass
    pe_price = ltp
    sell_pe_option(bn_put,pe_price)
    alice.unsubscribe(bn_put,LiveFeedType.COMPACT)


def get_BankNIftyIndexPrice():
    try:
        url = "https://rest.yahoofinanceapi.com/v6/finance/quote"
        querystring = {"symbols":"^NSEBANK"}
        headers = {
            'x-api-key': "m040TyoGhW9Kx9HDdaKC93Bkpx3vQL3v6ey1BTtV"
            }
        response = requests.request("GET", url, headers=headers, params=querystring)
        data = response.json()
        return data['quoteResponse']['result'][0]['regularMarketPrice']

    except Exception as e:
        print('Some error occured in fecthing data from fast api-> ',e)
        logging.error('Some error occured in fecthing data from fast api -> '+ str(e))
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/market/v2/get-quotes"
        querystring = {"region":"IN","symbols":"^NSEBANK"}
        headers = {
            'x-rapidapi-key': "69c50e42d6msh396c817a7ce5fa2p1a79f9jsnb12a2d70723f",
            'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com"
            }
        response = requests.request("GET", url, headers=headers, params=querystring)
        data = response.json()
        return data['quoteResponse']['result'][0]['regularMarketPrice']
    
def main():
    try:
        global socket_opened
        global alice
        global username
        global password
        global twoFA
        global api_secret
        global EMA_CROSS_SCRIP
        alice=None

        while alice is None:
            print('logging in alice blue')
            logging.info('logging in alice blue')
            try:
                file = open('access_token.txt','r')
                access_token = file.read()
                if access_token=='':
                    access_token =  AliceBlue.login_and_get_access_token(username=username, password=password, twoFA=twoFA,  api_secret=api_secret, app_id=app_id)
                    open('access_token.txt','w').write(access_token)
                    alice = AliceBlue(username=username, password=password, access_token=access_token, master_contracts_to_download=['NSE','NFO'])
                else:
                    print('using existing token')
                    logging.info('using existing token')
                    alice = AliceBlue(username=username, password=password, access_token=access_token, master_contracts_to_download=['NSE','NFO'])
            except:
                print('Login failed Alice...retrying in 1 mins')
                logging.info('Login failed Alice...retrying in 1 mins')
                open('access_token.txt', 'w').close()
                sleep(60)
                pass
        
        socket_opened = False
        alice.start_websocket(subscribe_callback=event_handler_quote_update,
                            socket_open_callback=open_callback,
                            run_in_background=True)
        while(socket_opened==False):    # wait till socket open & then subscribe
            pass
        sleep(1)

        order_placed = False
        try:
            while datetime.now().time()<=time(10,00):
                print('Time not 10.00pm waiting for 1min')
                logging.info('Time not 10.00pm waiting for 1min')
                sleep(60)

            if datetime.now().time()<=time(10,10):
                try:
                    while order_placed==False:
                        curr_ltp = get_BankNIftyIndexPrice()
                        print('Current BN_INDEX price -> ',curr_ltp)
                        atm_ce = round(curr_ltp/100)*100
                        atm_pe = round(curr_ltp/100)*100
                        print('atm_ce',atm_ce,'..atm_pe',atm_pe)
                        logging.info('atm_ce' + str(atm_ce) + '..atm_pe'+ str(atm_pe))
                        get_date_curr_expiry(atm_ce)
                        get_ce_curr_price(atm_ce)
                        get_pe_curr_price(atm_pe)
                        sleep(2)
                        for order_ in curr_orders:
                            x = alice.get_order_history(order_)
                            print(x['data'][0])
                            if x['data'][0]['order_status'] == 'rejected':
                                print("Rej")
                                logging.info("Rej")
                                square_off(alice)
                            
                        order_placed = True
                        saveDetails = {'date': datecalc,'orders':curr_orders}
                        try:
                            with open('credentials/file.pkl', 'wb') as file:
                                pickle.dump(saveDetails, file)
                        except Exception as e:
                            print("Some error in oprnign file for writing")
                            logging.info("Some error in oprnign file for writing")
                except Exception as e:
                    print('Some error occured in main so existing the position:::->',e)
                    square_off(alice)
                    logging.error('Some error occured in main:::->'+str(e))
            else:
                print("Time is past 10.10. So exiting the program")
                logging.info("Time is past 10.10. So exiting the program")
        except Exception as e:
            print('Some error occured so existing the positions -> ',e)
            square_off(alice)
    except Exception as e:
        print('Some error occured -> ',e)
        logging.error('Some error occured -> '+ str(e))

    
if(__name__ == '__main__'):
    logging.basicConfig(filename='short_straddle.log', level=logging.INFO)
    logging.info('*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
    logging.info('Started Short Straddle @ '+datetime.now().strftime("%D-%H:%M:%S"))
    print('Started Straddle @ ',datetime.now().strftime("%D-%H:%M:%S"))
    if (date.today() in nse_holiday)|(date.today().weekday() in [5,6]) :
        print('Today is a market holiday')
        logging.info('Today is a market holiday')
        sys.exit()
    main()
    logging.info('*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')