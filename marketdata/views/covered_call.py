from django.shortcuts import render
from django.http import HttpRequest

from . import graph_utils

from pandas_datareader import yahoo as yahoo
from yahoo_fin import stock_info as yf

import datetime
import requests as rq
# from io import BytesIO
# import base64

sesh = None
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0'

def graph_view(request):

    global sesh

    if not sesh:
        sesh = rq.Session()
        sesh.headers.update({
            'User-Agent': USER_AGENT
        })

    product = request.GET.get('product', 'AMZN')
    strike = int(request.GET.get('strike', 130))
    expiry_str = request.GET.get('expiry', '2023-09-08')
    long = int(request.GET.get('long', 100))
    cover = int(request.GET.get('cover', 100))

    expiry = datetime.datetime.strptime(expiry_str, '%Y-%m-%d')

    context = {
        # 'graph_div': graph_div,
        'product': product,
        'strike': strike,
        'expiry': expiry_str,
        'long': long,
        'cover': cover,
    }

    try:
        tk = yahoo.options.Options(product, session=sesh)
        df = tk.get_call_data(expiry=expiry)
        df = df.reset_index()
        call = df[df['Strike'] == strike].iloc[0]

        U = round(yf.get_live_price(product), 2)
        K = strike
        P = call['Bid']

        # graph_div = get_payoff_graph(U, K, P, long, cover)

        op_list = [
            {'type': 'u',              'side': 'b', 'price': U, 'size': long},
            {'type': 'c', 'strike': K, 'side': 's', 'price': P, 'size': cover},
        ]

        x, (y_long, y_call), (label_long, label_call), combined = graph_utils.get_plots(U, op_list, spot_range=50)

        context.update({
            'spot': U,
            'x': x.tolist(),
            'y_long': y_long.tolist(),
            'y_call': y_call.tolist(),
            'label_long': label_long,
            'label_call': label_call,
            'y_combined': combined.tolist(),
        })

    except Exception as e:
        print(e)
        context.update({
            'spot': None,
            'x': [],
            'y_long': [],
            'y_call': [],
            'label_long': None,
            'label_call': None,
            'y_combined': [],
        })

    return render(request, 'marketdata/covered_call.html', context=context)


# def get_payoff_graph(U, K, P, long_q, cover_q):

#     op_list = [
#         {'type': 'u',              'side': 'b', 'price': U, 'size': long_q},
#         {'type': 'c', 'strike': K, 'side': 's', 'price': P, 'size': cover_q},
#     ]

#     fig = graph_utils.multi_plotter(spot=U,spot_range=25, op_list=op_list)
#     tmp = BytesIO()
#     fig.savefig(tmp, format='png')
#     encoded = base64.b64encode(tmp.getvalue()).decode('utf-8')

#     graph_div = f'<img src=\'data:image\png;base64,{encoded}\'>'

#     return graph_div
