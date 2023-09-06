from django.shortcuts import render
from django.http import HttpRequest

from . import graph_utils

from pandas_datareader import yahoo as yahoo
from yahoo_fin import stock_info as yf

import datetime
import requests as rq
import numpy as np
import pandas as pd

sesh = None
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0'

def strategy_ranker(request):

    global sesh

    if not sesh:
        sesh = rq.Session()
        sesh.headers.update({
            'User-Agent': USER_AGENT
        })

    context = {}

    symbols = request.GET.getlist('symbols', ['AAPL', 'AMZN', 'CRWD', 'GOOGL', 'KO'])
    expiry_str = request.GET.get('expiry', '2023-09-08')
    expiry = datetime.datetime.strptime(expiry_str, '%Y-%m-%d')

    Q = request.GET.get('quantity', 100)

    dfs = [get_covered_call_rankings(symbol, expiry, Q) for symbol in symbols]
    df = pd.concat(dfs)
    df = df.sort_values('PNL', ascending=False)
    df = df.round(4)

    data = df[['PNL', 'Underlying', 'Strike', 'Underlying_Price']].iloc[:50].values.tolist()

    context['data'] = data

    return render(request, 'marketdata/top_strategies.html', context=context)


def get_covered_call_rankings(symbol, expiry, Q, U=None):
    
    U = U or round(yf.get_live_price(symbol), 2)

    tk = yahoo.options.Options(symbol, session=sesh)
    df = tk.get_call_data(expiry=expiry)
    df = df.reset_index()

    df['PNL'] = df['Bid']*Q - np.maximum(U - df['Strike'], 0)*Q

    return df