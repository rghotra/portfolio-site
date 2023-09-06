from django.urls import path
from django.shortcuts import redirect

from .views import covered_call
from .views import meta

urlpatterns = [
    path('', lambda _: redirect('covered_call_viewer')),
    
    path('payoff/covered-call', covered_call.graph_view, name='covered_call_viewer'),
    path('meta', meta.strategy_ranker, name='strategy_rankings'),
]
