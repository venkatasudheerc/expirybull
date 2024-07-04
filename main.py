# This is a sample Python script.
import datetime
import logging
import time

from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import pandas as pd
import optionchain_stream

import auth
import instruments
from credentials_zerodha import USERNAME, PASSWORD, API_KEY, API_SECRET, TOTP_TOKEN, ACCESS_TOKEN

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

'''
pyotp usage: https://tradewithpython.com/totp-login-zerodha-kiteconnect
'''


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    kite = KiteConnect(api_key=API_KEY)

    if ACCESS_TOKEN == '':
        kite_login = auth.Auth()
        kite = kite_login.login(mfa_key="859857")
        # kite = kite_login.login_http(mfa_key="168090")
        print("Update credentials_zerodha.py file with ACCESS_TOKEN")
        exit()
    else:
        kite.set_access_token(ACCESS_TOKEN)

    '''
    Create Instruments for an underlying
    Capture expiry date specific option chain
    '''
    instruments = instruments.Instruments(underlying="NIFTY")
    expiry_df = instruments.option_contracts(kite, expiry=True)

    # Create Kite Ticker object and register for tick data

    kws = KiteTicker(kite.api_key, kite.access_token)
    rows_list = []


    def on_ticks(ws, ticks):
        # Callback to receive ticks.
        """
        https://kite.trade/forum/discussion/8019/faqs-on-pykiteconnect-specific-to-python-client#websocket-streaming
        """
        instruments.feed_data(ticks, kite)
        # print(ticks)
        # pd.DataFrame(ticks).to_csv("rows.csv", index=False)


    def on_connect(ws, response):
        # Callback on successful connect.
        # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
        ws.subscribe(expiry_df['instrument_token'].tolist())

        # Set RELIANCE to tick in `full` mode.
        ws.set_mode(ws.MODE_FULL, expiry_df['instrument_token'].tolist())


    def on_close(ws, code, reason):
        # On connection close stop the main loop
        # Reconnection will not happen after executing `ws.stop()`
        # ws.stop()
        print("on_close() : ", code)
        print("on_close() : ", reason)


    # Assign the callbacks.
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close

    kws.connect(threaded=True)

    # Block main thread
    count = 0
    while True:
        count += 1
        if count % 2 == 0:
            if kws.is_connected():
                kws.set_mode(kws.MODE_FULL, expiry_df['instrument_token'].tolist())
        else:
            if kws.is_connected():
                kws.set_mode(kws.MODE_QUOTE, expiry_df['instrument_token'].tolist())
        time.sleep(30)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
