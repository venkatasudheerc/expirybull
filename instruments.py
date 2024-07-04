from datetime import datetime, date, timedelta
from pytz import timezone
from kiteconnect import KiteConnect
import pandas as pd
import mibian
import scipy


def calc_greeks(underlying_price, strike, ir, time_to_expiry, instrument_type, option_price):
    implied_volatility = float(0.0)
    delta = float(0.0)
    theta = float(0.0)
    rho = float(0.0)
    gamma = float(0.0)
    vega = float(0.0)

    if instrument_type == "CE":
        mbo = mibian.BS([underlying_price, strike, ir, time_to_expiry], callPrice=option_price)
        implied_volatility = mbo.impliedVolatility
        mbo = mibian.BS([underlying_price, strike, ir, time_to_expiry], volatility=implied_volatility)
        delta = mbo.callDelta
        theta = mbo.callTheta
        rho = mbo.callRho
        gamma = mbo.gamma
        vega = mbo.vega

    else:
        mbo = mibian.BS([underlying_price, strike, ir, time_to_expiry], putPrice=option_price)
        implied_volatility = mbo.impliedVolatility
        mbo = mibian.BS([underlying_price, strike, ir, time_to_expiry], volatility=implied_volatility)
        delta = mbo.putDelta
        theta = mbo.putTheta
        rho = mbo.putRho
        gamma = mbo.gamma
        vega = mbo.vega

    return implied_volatility, delta, theta, rho, gamma, vega


class Instruments:
    def __init__(self, underlying="NIFTY"):
        self.exchange = "NSE"
        self.segment = "NFO-OPT"
        self.underlying = underlying
        self.trading_symbol = ""
        self.underlying_map = [
            {'name': 'NIFTY', 'trading_symbol': 'NSE:NIFTY 50', 'exchange': 'NFO', 'segment': 'NFO-OPT'},
            {'name': 'BANKNIFTY', 'trading_symbol': 'NSE:NIFTY BANK', 'exchange': 'NFO', 'segment': 'NFO-OPT'},
            {'name': 'SENSEX', 'trading_symbol': 'BSE:SENSEX', 'exchange': 'BFO', 'segment': 'BFO-OPT'}]
        for ticker in self.underlying_map:
            if ticker['name'] == underlying:
                self.trading_symbol = ticker['trading_symbol']
                self.exchange = ticker['exchange']
                self.segment = ticker['segment']
        self.instruments_list = []
        self.target_symbols = []
        self.target_symbols_df = pd.DataFrame(None)
        self.option_chain_data = []

    def instruments(self, kite: KiteConnect = "kite"):
        self.instruments_list = kite.instruments(self.exchange)
        return self.instruments_list

    def option_contracts(self, kite: KiteConnect, instrument_type="", expiry=True):
        underlying_ltp = kite.quote(self.trading_symbol)[self.trading_symbol]['last_price']

        self.instruments_list = self.instruments(kite)
        for instrument in self.instruments_list:
            if instrument['name'] == self.underlying and instrument['segment'] == self.segment:
                if expiry:
                    if instrument['expiry'] == date.today() + timedelta(days=0) and \
                            underlying_ltp * 0.98 < instrument['strike'] < underlying_ltp * 1.02:
                        self.target_symbols.append(instrument)
                else:
                    if instrument_type == "":
                        self.target_symbols.append(instrument)
                    elif instrument['instrument_type'] == instrument_type:
                        self.target_symbols.append(instrument)

        self.target_symbols_df = pd.DataFrame(self.target_symbols)
        self.target_symbols_df.to_csv("option_contracts.csv", index=False)
        return self.target_symbols_df

    def feed_data(self, ticks, kite: KiteConnect, option_chain_data=None):
        print("inside feed_data()")
        tick_dict = None
        option_data = []
        for tick in ticks:
            if tick['mode'] != "full":
                continue
            print(tick)
            [symbol, instrument_type, strike] = [[x['tradingsymbol'], x['instrument_type'], x['strike']]
                                                 for x in self.target_symbols
                                                 if x['instrument_token'] == tick['instrument_token']][0]

            # calculate greeks
            # https://github.com/yassinemaaroufi/MibianLib

            underlying_ltp = kite.quote(self.trading_symbol)[self.trading_symbol]['last_price']

            t = datetime.now(timezone('Asia/Kolkata')).time().strftime("%H%M")
            # calculating time to expiry in days
            tt_expiry = (int(1530) - int(t))/615
            print("time to expiry : ", tt_expiry)

            [implied_volatility, delta, theta, rho, gamma, vega] = calc_greeks(underlying_price=underlying_ltp,
                                                                               strike=strike,
                                                                               ir=7,
                                                                               time_to_expiry=tt_expiry,
                                                                               instrument_type=instrument_type,
                                                                               option_price=tick['last_price'])
            print(symbol, instrument_type)
            tick_dict = {
                'instrument_token': tick['instrument_token'],
                'tradingsymbol': symbol,
                'instrument_type': instrument_type,
                'strike': strike,
                'datetime': datetime.now(timezone('Asia/Kolkata')).strftime("%Y%m%d_%H%M%S"),
                'ltp': tick['last_price'],
                'avg_traded_price': tick['average_traded_price'],
                'volume': tick['volume_traded'],
                'open_interest': tick['oi'],
                'implied_volatility': implied_volatility,
                'delta': delta,
                'theta': theta,
                'rho': rho,
                'gamma': gamma,
                'vega': vega
            }
            option_data.append(tick_dict)

        if len(self.option_chain_data) == 0:
            self.option_chain_data = pd.DataFrame(option_data)
        else:
            self.option_chain_data = pd.concat([self.option_chain_data, pd.DataFrame(option_data)])
        self.option_chain_data.to_csv("option_chain.csv", index=False)
        return option_chain_data
