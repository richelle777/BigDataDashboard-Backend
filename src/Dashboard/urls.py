# api/urls.py
from django.urls import path
from .views import CustomersListView, TotalCustomersView, TotalAccountsView, TotalTransactionsView, \
    TotalAvgTransactionsView, RecentTransactionsView, TopProductsView, AllTotalView, NbAccountsByTierView, \
    NbCustomersByAgeView, CodeByTransactionView, GroupCustomersByCodeView

urlpatterns = [
    path('customers/', CustomersListView.as_view(), name='customers-list'),
    path('all-total/', AllTotalView.as_view(), name='all-total-list'),
    path('total-customers/', TotalCustomersView.as_view(), name='customers-total'),
    path('total-accounts/', TotalAccountsView.as_view(), name='accounts-total'),
    path('total-transactions/', TotalTransactionsView.as_view(), name='transactions-total'),
    path('total-avg-transactions/', TotalAvgTransactionsView.as_view(), name='transactions-total'),
    path('recent-transactions/', RecentTransactionsView.as_view(), name='transactions-total'),
    path('top-products/', TopProductsView.as_view(), name='transactions-total'),
    # representation des niveaux(tier) auxquels les differents comptes ont droit
    path('accounts-by-tier/', NbAccountsByTierView.as_view(), name='transactions-total'),
    # nombre de clinets par tranches d'ages
    path('customers-by-age/', NbCustomersByAgeView.as_view(), name='transactions-total'),
    # code avec le plus grand nombre de transactions
    path('code_by_transaction/', CodeByTransactionView.as_view(), name='transactions-total'),
    path('group_by_code/', GroupCustomersByCodeView.as_view(), name='transactions-total')
]