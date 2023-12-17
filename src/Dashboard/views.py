# api/views.py
from sqlite3 import Date
from datetime import datetime
from bson import json_util
from django.core.cache import cache
import json
from django.http import JsonResponse
from pymongo import MongoClient
from rest_framework.views import APIView
from rest_framework.response import Response
from operator import itemgetter
from . import settings
from .models import Customers
from .serializers import CustomerSerializer

try:
    client = MongoClient(settings.MONGO_DB_URI)
    db = client['sample_analytics']  # Nom de la base de données
except Exception as e:
    print("error during connection to database", e)


# Fonction de regroupement par code postal
def group_customers_by_postal_code():
    try:
        collection = db['customers']
        customers = list(collection.find())
        grouped_customers = {}

        for customer in customers:
            postal_code_prefix = customer['address'][-5:-5]  # Utilisez les deux premiers chiffres du code postal
            if postal_code_prefix not in grouped_customers:
                grouped_customers[postal_code_prefix] = []
            grouped_customers[postal_code_prefix].append(customer)

        return json.loads(json_util.dumps(grouped_customers))
    except Exception as excep:
        print("error during get customer informations", excep)
    grouped_customers = {}


def get_customer_data():
    try:
        collection = db['customers']
        users = list(collection.find())
        for user in users:
            user['_id'] = str(user['_id'])
        return users
    except Exception as excep:
        print("error during get customer informations", excep)


def get_account_data():
    try:
        collection = db['accounts']
        accounts = list(collection.find())
        for account in accounts:
            account['_id'] = str(account['_id'])
        return accounts
    except Exception as excep:
        print("error during get account informations", excep)


def get_transaction_data():
    try:
        collection = db['transactions']
        transactions = list(collection.aggregate([
            {"$unwind": "$transactions"}]))

        return json.loads(json_util.dumps(transactions))
    except Exception as excep:
        print("error during get transaction informations", excep)


def total_Avg_transactions():
    try:
        collection = db['transactions']

        # Calcul du montant total
        total_amount_cursor = collection.aggregate([
            {"$unwind": "$transactions"},
            {"$match": {"transactions.total": {"$type": "string"}}},  # Filtre pour exclure les valeurs non convertibles
            {"$addFields": {
                "total_amount": {"$toDouble": "$transactions.total"}
            }},
            {"$group": {
                "_id": None,
                "total_amount": {"$sum": "$total_amount"}
            }}
        ])
        total_amount_list = list(total_amount_cursor)

        total_amount = total_amount_list[0]['total_amount'] if total_amount_list else 0

        # Calcul du montant moyen
        average_amount_cursor = collection.aggregate([
            {"$unwind": "$transactions"},
            {"$match": {"transactions.total": {"$type": "string"}}},  # Filtre pour exclure les valeurs non convertibles
            {"$addFields": {
                "total_amount": {"$toDouble": "$transactions.total"}
            }},
            {"$group": {
                "_id": None,
                "average_amount": {"$avg": "$total_amount"}
            }}
        ])
        average_amount_list = list(average_amount_cursor)
        average_amount = average_amount_list[0]['average_amount'] if average_amount_list else None

        return {"total_amount": total_amount, "average_amount": round(average_amount, 2)}
    except Exception as excep:
        print("error during get transaction avg informations", excep)


def recent_transactions():
    collection = db['transactions']

    # Récupération des dernières transactions
    # recent_transactions = collection.transactions.find().sort([('$natural', -1)]).limit(5)

    # Utilisation de l'agrégation pour déplier le tableau 'transactions' et trier par date
    pipeline = [
        {
            '$unwind': '$transactions'
        },
        {
            '$sort': {'transactions.date': -1}
        },
        {
            '$limit': 10
        }
    ]

    # Exécutez la requête d'agrégation
    result = list(collection.aggregate(pipeline))

    return json.loads(json_util.dumps(result))


### Raouf
def display_users_by_tier(users, tier):
    try:
        # Filtrer les utilisateurs en fonction du niveau de compte spécifié
        filtered_users = [user for user in users if has_tier(user, tier)]

        # Afficher les utilisateurs filtrés
        print(f"Utilisateurs avec le niveau de compte '{tier}':")
        for user in filtered_users:
            user['_id'] = str(user['_id'])
        return filtered_users
    except Exception as excep:
        print("Erreur lors de l'affichage des utilisateurs par niveau de compte", excep)


def has_tier(user, target_tier):
    # Vérifier si l'utilisateur a un compte avec le niveau spécifié
    return any(
        detail.get('tier') == target_tier
        for detail in user.get('tier_and_details', {}).values()
    )


# raouf

def top_products():
    collection = db['transactions']

    # Calcul du top 5 des plateformes de paiement les plus utilisees
    top_products = collection.aggregate([
        {"$unwind": "$transactions"},
        {"$group": {"_id": "$transactions.symbol", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ])

    return json.loads(json_util.dumps(top_products))


def accounts_by_tier():
    collection = db['customers']

    pipeline = [
        {
            "$project": {
                "tier_and_details_array": {"$objectToArray": "$tier_and_details"}
            }
        },
        {
            "$unwind": "$tier_and_details_array"
        },
        {
            "$group": {
                "_id": "$tier_and_details_array.v.tier",
                "count": {"$sum": 1}
            }
        }
    ]

    result = collection.aggregate(pipeline)

    return json.loads(json_util.dumps(result))


# (buy, sell)
def code_by_transaction():
    collection = db['transactions']

    pipeline = [
        {"$unwind": "$transactions"},
        {"$group": {"_id": "$transactions.transaction_code", "total": {"$sum": 1}}},
    ]

    result = collection.aggregate(pipeline)

    return json.loads(json_util.dumps(result))


def best_bad_accounts():
    collection = db['transactions']

    # Récupération des données avec conversion de total_amount en nombre
    all_accounts = db.transactions.aggregate([
        {"$unwind": "$transactions"},
        {"$match": {"transactions.total": {"$type": "string"}}},  # Filtre pour exclure les valeurs non convertibles
        {"$addFields": {
            "total_amount": {"$toDouble": "$transactions.total"}
        }},
        {"$group": {
            "_id": "$account_id",
            "total_amount": {"$sum": "$total_amount"}
        }},
        {"$sort": {"total_amount": -1}}
    ])

    # Convertir le curseur en une liste de dictionnaires
    all_accounts_list = list(all_accounts)

    # Récupération des 10 comptes avec le montant total le plus élevé
    top_accounts = sorted(all_accounts_list, key=lambda x: x['total_amount'], reverse=True)[:10]

    # Récupération des 10 comptes avec le montant total le plus bas
    bottom_accounts = sorted(all_accounts_list, key=lambda x: x['total_amount'])[:10]

    print(top_accounts)
    print(bottom_accounts)

    return {"top_accounts": top_accounts, "bottom_accounts": bottom_accounts}


def customers_by_age():
    collection = db['customers']
    result = collection.aggregate(
        [{"$project": {"age": {"$floor": {"$divide": [{"$subtract": [datetime.now(), "$birthdate"]}, 31536000000]}}}},
         {
             "$group": {"_id": {"$switch": {
                 "branches": [{"case": {"$and": [{"$lt": ["$age", 21]}]}, "then": "<21"},
                              {"case": {"$and": [{"$gte": ["$age", 21]}, {"$lt": ["$age", 31]}]}, "then": "21-30"},
                              {"case": {"$and": [{"$gte": ["$age", 31]}, {"$lt": ["$age", 46]}]}, "then": "31-45"},
                              {"case": {"$and": [{"$gte": ["$age", 46]}, {"$lt": ["$age", 71]}]}, "then": "46-70"},
                              {"case": {"$and": [{"$gte": ["$age", 71]}, {"$lt": ["$age", 100]}]}, "then": "71-99"}
                              ],
                 "default": "Unknown"}},
                 "count": {"$sum": 1}
             }
         }
         ])
    # result = collection.aggregate([
    #     {
    #         "$project": {
    #             "age": {
    #                 "$floor": {
    #                     "$divide": [
    #                         {"$subtract": [datetime.now(), "$birthdate"]},
    #                         31536000000
    #                     ]
    #                 }
    #             }
    #         }
    #     },
    #     {
    #         "$facet": {
    #             "ageGroups": [
    #                 {
    #                     "$bucket": {
    #                         "groupBy": "$age",
    #                         "boundaries": [20,30,40,50,60,70,80,90, 100],
    #                         "default": "Unknown",
    #                         "output": {
    #                             "count": {"$sum": 1}
    #                         }
    #                     }
    #                 }
    #             ]
    #         }
    #     },
    #     {
    #         "$unwind": "$ageGroups"
    #     },
    #     {
    #         "$replaceRoot": {"newRoot": "$ageGroups"}
    #     }
    # ])

    # result = collection.aggregate([
    #     {
    #         "$project": {
    #             "age": {
    #                 "$floor": {
    #                     "$divide": [
    #                         {"$subtract": [datetime.now(), "$birthdate"]},
    #                         31536000000
    #                     ]
    #                 }
    #             }
    #         }
    #     }
    # ])
    #
    # # Convertir le résultat en une liste Python
    # ages_list = [doc["age"] for doc in result]
    #
    # # Afficher la liste des âges
    # print(ages_list)

    return json.loads(json_util.dumps(result))


# Affichage des transactions par periode et par code (sell or buy)
def transactions_by_period_and_code(startdate, enddate):
    collection = db['transactions']
    # Convertissez les chaînes de date en objets datetime
    start_date = datetime.strptime(startdate, '%Y-%m-%d')
    end_date = datetime.strptime(enddate, '%Y-%m-%d')

    # Convertissez les dates en format compatible avec la base de données
    start_date_db = datetime.combine(start_date, datetime.min.time())
    end_date_db = datetime.combine(end_date, datetime.max.time())

    print(start_date_db)
    print(end_date_db)

    # Requête MongoDB
    pipeline = [
        {
            '$unwind': '$transactions'
        },
        {
            '$match': {
                'transactions.date': {'$gte': start_date_db, '$lte': end_date_db}
            }
        },
        {
            "$addFields": {
                "month": {
                    "$month": "$transactions.date"
                },
                "total_amount": {"$toDouble": "$transactions.total"}
            }
        },
        {
            '$group': {
                '_id': {
                    'transaction_code': '$transactions.transaction_code',
                    'month': '$month'
                },
                'total_amount': {'$sum': '$total_amount'}
            }
        }
    ]

    result = list(collection.aggregate(pipeline))
    print(result)
    return result


class TransactionsByPeriodAndCodeView(APIView):
    def get(self, request, startdate, enddate):
        result = transactions_by_period_and_code(startdate, enddate)
        return JsonResponse(result, safe=False)


class GroupCustomersByCodeView(APIView):
    def get(self, request):
        result = group_customers_by_postal_code()
        return JsonResponse(result, safe=False)


class CodeByTransactionView(APIView):
    def get(self, request):
        result = code_by_transaction()
        return JsonResponse(result, safe=False)


class NbCustomersByAgeView(APIView):
    def get(self, request):
        result = customers_by_age()
        return JsonResponse(result, safe=False)


class NbAccountsByTierView(APIView):
    def get(self, request):
        result = accounts_by_tier()
        return JsonResponse(result, safe=False)


class CustomersListView(APIView):
    def get(self, request):
        users = get_customer_data()
        return JsonResponse(users, safe=False)


class TotalCustomersView(APIView):
    def get(self, request):
        users = get_customer_data()
        return JsonResponse(len(users), safe=False)


class TotalAccountsView(APIView):
    def get(self, request):
        accounts = get_account_data()
        return JsonResponse(len(accounts), safe=False)


class TotalTransactionsView(APIView):
    def get(self, request):
        transactions = get_transaction_data()
        return JsonResponse(len(transactions), safe=False)


class AllTotalView(APIView):
    def get(self, request):
        transactions = get_transaction_data()
        accounts = get_account_data()
        customers = get_customer_data()
        amount_transactions = total_Avg_transactions()

        return JsonResponse(
            {'total-customer': len(customers), 'total-transaction': len(transactions), 'total-account': len(accounts),
             'total-amount-transaction': amount_transactions['total_amount'],
             'average-amount-transaction': amount_transactions['average_amount']},
            safe=False)


class TotalAvgTransactionsView(APIView):
    def get(self, request):
        transactions = total_Avg_transactions()
        return JsonResponse(transactions, safe=False)


class RecentTransactionsView(APIView):
    def get(self, request):
        transactions = recent_transactions()
        return JsonResponse(transactions, safe=False)


class TopProductsView(APIView):
    def get(self, request):
        transactions = top_products()
        return JsonResponse(transactions, safe=False)


class UsersByTierView(APIView):
    def get(self, request, tier):
        users_data = get_customer_data()
        filtered_users = display_users_by_tier(users_data, tier)
        return JsonResponse(filtered_users, safe=False)


class BestBadAccountsView(APIView):
    def get(self, request):
        accounts = best_bad_accounts()
        return JsonResponse(accounts, safe=False)
