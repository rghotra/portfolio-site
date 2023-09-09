from django.shortcuts import render
from django.http import HttpRequest

from . import graph_utils

from pandas_datareader import yahoo as yahoo
from yahoo_fin import stock_info as yf

import datetime
import requests as rq
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit

sesh = None
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0'

r = 0.0426
T = 252

def historical_greeks(request):

    global sesh

    if not sesh:
        sesh = rq.Session()
        sesh.headers.update({
            'User-Agent': USER_AGENT
        })

    context = {}

    symbol = request.GET.get('symbol', 'AAPL')
    strike = float(request.GET.get('strike', 100.0))
    expiry_str = request.GET.get('expiry', '2023-09-15')
    expiry = datetime.datetime.strptime(expiry_str, '%Y-%m-%d').date()

    end = request.GET.get('end', None)
    if end:
        end = datetime.datetime.strptime(end, '%Y-%m-%d').date()
    else:
        end = datetime.date.today()
    start = request.GET.get('start', None)
    if start:
        start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
    else:
        start = end - datetime.timedelta(days=100)

    context.update({
        'symbol': symbol,
        'expiry': expiry_str,
        'start': start.strftime("%Y-%m-%d"),
        'end': end.strftime("%Y-%m-%d"),
        'strike': strike,
    })

    df = get_greeks_table(symbol, expiry, strike, start, end)
    df = df[::-1].reset_index()
    data = df[['underlying', 'call', 'IV', 'delta', 'gamma', 'theta', 'vega', 'RV', 'underlying_volume', 'call_volume']].iloc[:].to_numpy()
    data = np.round(data, 4)
    data = np.concatenate([np.expand_dims(df['index'].astype(str).to_numpy(), axis=1), data.astype(object)], axis=1)
    print(data.shape)

    context['data'] = data

    return render(request, 'marketdata/greeks.html', context=context)



def get_greeks_table(symbol, expiry, strike, start, end):
    t = (expiry - end).days/T

    option_symbol = f"{symbol}{expiry.strftime('%y%m%d')}C{fstrike(strike)}"

    asset = yf.get_data(symbol, start_date=start, end_date=end, interval='1d')
    option = yf.get_data(option_symbol, start_date=start, end_date=end, interval='1d')

    df = pd.DataFrame()
    df['underlying'] = asset['close']
    df['underlying_volume'] = asset['volume']
    df['call'] = option['close']
    df['call_volume'] = option['volume']

    call_nulls = ((df['call'].isnull()) | (df['call_volume'].isnull()))
    underlying_nulls = ((df['underlying'].isnull()) | (df['underlying_volume'].isnull()))
    nulls = ((call_nulls) | (underlying_nulls))
    # print(sum(nulls))
    df = df[~nulls]

    rvol = df['underlying'].rolling(21).apply(
        lambda window: np.std(window.rolling(2).apply(lambda x: np.log(x.iloc[1]/x.iloc[0]))) * np.sqrt(T)
    )
    df['RV'] = rvol

    df['B&S IV'] = vol = np.sqrt(2*np.pi/r)*df['call']/df['underlying']

    iv_calc = lambda S, *vol: iv_finder(S, strike, r, t, np.array(vol))
    vol, _ = curve_fit(iv_calc, df['underlying'], df['call'], p0=vol)
    df['IV'] = vol



    d1 = np.log(df['underlying']/strike) + (r + np.power(vol, 2)/2)*t
    df['d1'] = d1 = d1/(vol*np.sqrt(t))
    df['d2'] = d2 = d1 - vol*np.sqrt(t)

    rv = stats.norm()

    df['delta'] = rv.cdf(d1)

    df['gamma'] = rv.pdf(d1)/(df['underlying']*vol*np.sqrt(t))

    df['theta'] = -(df['underlying']*vol/2/np.sqrt(t)*rv.pdf(d1)) - r*strike*np.exp(-r*t)*rv.cdf(d2)
    df['theta'] = df['theta']/T

    df['vega'] = df['underlying']*np.sqrt(t)*rv.pdf(d1)/100

    return df


def fstrike(k):
    return f'{round(k, 3)*1000:0>8.0f}'

rv = stats.norm()

def black_scholes_price(vol, S, K, r, t):
    
    d1 = np.log(S/K) + (r + 0.5*np.power(vol, 2))*t
    d1 = d1/(vol*np.sqrt(t))
    d2 = d1 - vol*np.sqrt(t)
    
    p = rv.cdf(d1)*S - rv.cdf(d2)*K*np.exp(-r*t)
    
    return p

def iv_finder(S, K, r, t, vol):
    return black_scholes_price(vol, S, K, r, t)