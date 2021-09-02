import logging
import json
import pickle
from datetime import date,datetime,time
from time import sleep
from alice_blue import *
from square_off import square_off
import sys

# Config
f = open('credentials/details.json',)
data = json.load(f)

username = data['username']
password = data['password']
api_secret = data['api_secret']
twoFA = data['twoFA']
app_id = data['app_id']

nse_holiday = [date(2021,7,21), date(2021,8,19), date(2021,9,10), date(2021,10,15), date(2021,11,5), date(2021,11,19)]
    
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
        try:
            with open('credentials/file.pkl', 'rb') as file:
                saved_details = pickle.load(file)
            expiryDate = saved_details['date']
        except Exception as e:
            expiryDate = date.today()
            print('Error occured in opening file')

        till_time = time(15,00)
        if ((date.today().weekday() in [3]) & (date.today().weekday() in [expiryDate.weekday()])):
            print('Expiry day')
            till_time = time(13,58)

        while datetime.now().time()<till_time:
            
            pos_res = alice.get_daywise_positions()# get daywise positions
            positions = (pos_res['data']['positions'])

            totalm2m = float(0)
            orders = alice.get_order_history()
            
            try:
                for order_ in orders['data']['completed_orders']:
                    if order_['order_status']=='rejected':
                        square_off(alice)
                        print('Rej')
            except Exception as e:
                print('orders[data][completed_orders] cannot be fetched')

            for position in positions:
                print(position['trading_symbol'],'...m2m -> ',position['m2m'],'...unrealizedPnL -> ',position['unrealised_pnl'])
                logging.info(position['trading_symbol']+'...m2m -> '+position['m2m']+'...unrealizedPnL -> '+str(position['unrealised_pnl']))
                totalm2m += float(position['m2m'].replace(',', ''))

            print('Total PnL -> ',totalm2m)
            logging.info('Total PnL -> '+ str(totalm2m))
            is_squared_off = False
        
            if totalm2m<-9000:
                while is_squared_off==False:
                    try:
                        square_off(alice)
                        is_squared_off = True
                        sys.exit()
                    except Exception as e:
                        pass
                        print('Some error occured in squreoff ->',e)
                        logging.error('Some error occured in squreoff ->' + str(e))
            else:
                print('m2m not less than -9000 trying again in 1 mins')
                logging.info('m2m not less than -9000 trying again in 1 mins '+ datetime.now().strftime("%D-%H:%M:%S"))
                sleep(60)

        if datetime.now().time()>=till_time:
            try:
                square_off(alice)
            except Exception as e:
                print('Some error occured in squreoff ->',e)
                logging.error('Some error occured in squreoff ->' + str(e))
    except Exception as e:
        print('Some error occured -> ',e)
        logging.error('Some error occured -> ' + str(e))
    
if(__name__ == '__main__'):
    print('Started StopLoss Square off @ ',datetime.now().strftime("%D-%H:%M:%S"))
    logging.basicConfig(filename='stoploss_squareoff.log', level=logging.INFO)
    logging.info('*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
    logging.info('Started StopLoss Square off @ '+datetime.now().strftime("%D-%H:%M:%S"))
    if (date.today() in nse_holiday)|(date.today().weekday() in [5,6]) :
        print('Today is a market holiday')
        logging.info('Today is a market holiday')
        sys.exit()
    main()
    logging.info('*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')