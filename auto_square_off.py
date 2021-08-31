import logging
import json
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
    logging.basicConfig(filename='auto_square_off.log', level=logging.INFO)
    logging.info('*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')
    logging.info('Started Auto Square off @ '+datetime.now().strftime("%D-%H:%M:%S"))
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
            except Exception as e:
                print('Login failed Alice...retrying in 1 mins',e)
                logging.error('Login failed Alice...retrying in 1 mins',e)
                open('access_token.txt', 'w').close()
                sleep(60)
                pass

        while datetime.now().time()<time(15,29):
            print('Time 3.29pm not reached waiting for 1 more min')
            logging.info('Time 3.29pm not reached waiting for 1 more min')
            sleep(60)
        
        try:
            square_off(alice)
        except Exception as e:
            print('Some error occured in squreoff ->',e)
            logging.error('Some error occured in squreoff ->',e)
    except Exception as e:
        print("Some error occured ->",e)
        logging.error("Some error occured ->",e)
    logging.info('*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*')

if(__name__ == '__main__'):
    print('Started Auto Square off @ ',datetime.now().strftime("%D-%H:%M:%S"))
    if (date.today() in nse_holiday)|(date.today().weekday() in [5,6]) :
        print('Today is a market holiday')
        logging.info('Today is a market holiday')
        sys.exit()
    main()