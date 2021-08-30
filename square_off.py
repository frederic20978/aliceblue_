from time import sleep
from alice_blue import *
import logging
from datetime import datetime,time


def buy_signal(ins_scrip,quantity,product):

    if product=="MIS":
        p = ProductType.Intraday 
    else:
        p = ProductType.Delivery 

    alice.place_order(transaction_type = TransactionType.Buy,
                         instrument = ins_scrip,
                         quantity = quantity,
                         order_type = OrderType.Market,
                         product_type = p,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)

def sell_signal(ins_scrip,quantity,product):

    if product=="MIS":
        p = ProductType.Intraday 
    else:
        p = ProductType.Delivery 

    alice.place_order(transaction_type = TransactionType.Sell,
                         instrument = ins_scrip,
                         quantity = quantity,
                         order_type = OrderType.Market,
                         product_type = p,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)
    
def square_off(aliceObject):
    global alice
    alice=aliceObject

 
    pos_res = alice.get_daywise_positions()# get daywise positions
    positions = (pos_res['data']['positions'])
    orders = alice.get_order_history()
    pending_orders = orders['data']['pending_orders']    
    
    
    try:
        alice.cancel_all_orders()
        for pen_order in pending_orders:
            print('cancel order..symobl -> ',pen_order['trading_symbol'],'...quantity -> ',pen_order['quantity'],'...',pen_order['transaction_type'])
    except Exception as e:
        print('Some error occured in cancel orders:::->',e)

    for position in positions:
        try:
            print('Squaring off...', position['trading_symbol'],'...type -> ',position['product'],'...quantity -> ',position['net_quantity'])
            logging.info('Squaring off...'+position['trading_symbol']+'...type -> '+position['product']+'...quantity -> '+str(position['net_quantity']))
            if position['net_quantity']>0:
                ins_scr = alice.get_instrument_by_token(position['exchange'],position['instrument_token'])
                sell_signal(ins_scr,position['net_quantity'],position['product'])
            elif position['net_quantity']<0:
                ins_scr = alice.get_instrument_by_token(position['exchange'],position['instrument_token'])
                buy_signal(ins_scr,position['net_quantity']*-1,position['product'])
        except Exception as e:
           print('Some error occured in positions square off:::->',e)
    
