# Importez MongoClient à partir de pymongo
from pymongo import MongoClient

# Initialisez la connexion MongoDB
client = MongoClient("mongodb+srv://default:default@cluster0.pnqgs3z.mongodb.net/?retryWrites=true&w=majority")

# Sélectionnez la base de données
db = client['sample_analytics']

# Sélectionnez la collection
collection = db['customers']

# Récupérez toutes les données de la collection
result = collection.find()

# Affichez les données
for document in result:
    print(document)
