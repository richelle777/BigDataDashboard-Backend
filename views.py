# api/views.py
from datetime import datetime,date
import calendar
from bson import json_util
import json
from django.http import JsonResponse
from pymongo import MongoClient
from rest_framework.views import APIView
from rest_framework.response import Response

from . import settings
from .models import Customers
from .serializers import CustomerSerializer

try:
    client = MongoClient(settings.MONGO_DB_URI)
    db = client['sample_analytics']  # Nom de la base de données
except Exception as e:
    print("error during connection to database", e)


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
        transactions = list(collection.find())
        for transaction in transactions:
            transaction['_id'] = str(transaction['_id'])
        return transactions
    except Exception as excep:
        print("error during get transaction informations", excep)


def total_Avg_transactions():
    try:
        collection = db['transactions']

        # Calcul du montant total
        total_amount_cursor = collection.aggregate([
            {"$unwind": "$transactions"},
            {"$group": {"_id": None, "total_amount": {"$sum": "$transactions.amount"}}}
        ])
        total_amount_list = list(total_amount_cursor)
        total_amount = total_amount_list[0]['total_amount'] if total_amount_list else 0

        # Calcul du montant moyen
        average_amount_cursor = collection.aggregate([
            {"$unwind": "$transactions"},
            {"$group": {"_id": None, "average_amount": {"$avg": "$transactions.amount"}}}
        ])
        average_amount_list = list(average_amount_cursor)
        average_amount = average_amount_list[0]['average_amount'] if average_amount_list else None

        return {"total_amount": total_amount, "average_amount": average_amount}
    except Exception as excep:
        print("error during get transaction avg informations", excep)


def recent_transactions():
    collection = db['transactions']

    # Récupération des dernières transactions
    recent_transactions = collection.find().sort([('$natural', -1)]).limit(5)

    return json.loads(json_util.dumps(recent_transactions))


def top_products():
    collection = db['transactions']

    # Calcul du top 5 des produits les plus achetés
    top_products = collection.aggregate([
        {"$unwind": "$transactions"},
        {"$group": {"_id": "$transactions.symbol", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 10}
    ])

    return json.loads(json_util.dumps(top_products))

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

class GestionClients:
    def __init__(self):
        self.clients = []

    def get_customer_data(self):
        try:
            collection = db['customers']
            users = list(collection.find())
            for user in users:
                user['_id'] = str(user['_id'])
                user['birthdate'] = self.convertir_timestamp_en_birthdate(user.get('birthdate', {"$date": 0}))
                user['age'] = self.calculer_age(user['birthdate'])
            return users
        except Exception as e:
            print(f"Erreur lors de la récupération des données des clients : {e}")
            return []

    def convertir_timestamp_en_birthdate(self, timestamp):
        birthdate_timestamp = timestamp["$date"] / 1000
        birthdate = datetime.utcfromtimestamp(birthdate_timestamp)
        return {"$date": int(birthdate.timestamp() * 1000)}

    def calculer_age(self, date_naissance):
        # Convertir la date de naissance en timestamp
        birthdate_timestamp = date_naissance["$date"] / 1000

        # Convertir le timestamp en datetime
        birthdate = datetime.utcfromtimestamp(birthdate_timestamp)

        # Calculer l'âge en années
        age = datetime.utcnow().year - birthdate.year - ((datetime.utcnow().month, datetime.utcnow().day) < (birthdate.month, birthdate.day))

        return age

    def kpi_clients_par_tranche_age(self):
        tranches_age = {"Jeune": (0, 18), "Adulte": (19, 65), "Senior": (66, 120)}
        compteurs = {tranche: 0 for tranche in tranches_age}

        for client in self.clients:
            age = client.get('age', 0)
            for tranche, (min_age, max_age) in tranches_age.items():
                if min_age <= age <= max_age:
                    compteurs[tranche] += 1

        return compteurs

# Exemple d'utilisation
gestion_clients = GestionClients()
gestion_clients.clients = gestion_clients.get_customer_data()

kpi_resultat = gestion_clients.kpi_clients_par_tranche_age()
print("KPI Clients par tranche d'âge:")
for tranche, nombre in kpi_resultat.items():
    print(f"{tranche}: {nombre} clients")