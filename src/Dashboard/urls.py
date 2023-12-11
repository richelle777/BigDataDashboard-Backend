# api/urls.py
from django.urls import path
from .views import CustomersListView, TotalCustomersView, TotalAccountsView, TotalTransactionsView, \
    TotalAvgTransactionsView, RecentTransactionsView, TopProductsView

urlpatterns = [
    path('customers/', CustomersListView.as_view(), name='customers-list'),
    path('total-customers/', TotalCustomersView.as_view(), name='customers-total'),
    path('total-accounts/', TotalAccountsView.as_view(), name='accounts-total'),
    path('total-transactions/', TotalTransactionsView.as_view(), name='transactions-total'),
    path('total-avg-transactions/', TotalAvgTransactionsView.as_view(), name='transactions-total'),
    path('recent-transactions/', RecentTransactionsView.as_view(), name='transactions-total'),
    path('top-products/', TopProductsView.as_view(), name='transactions-total'),

]