import pandas as pd
import sys
import os
import pickle
from sklearn.cluster import KMeans
from sklearn.discriminant_analysis import StandardScaler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import Facture, Achat, Produit, Client, Log, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Date, Numeric, DateTime, ForeignKey, func, cast, Integer
import os
import pandas as pd
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
import pandas as pd
from src.analyses import get_montant_score, get_frequence_score, get_recence_score, segment_customer, get_age

class RFMClustering():
    
    def __init__(self):
        pass
    
    def classify(self):
        df_montant = get_montant_score()
        df_frequence = get_frequence_score()
        df_recence = get_recence_score()
        df = pd.merge(df_montant, df_frequence, on='id_client', how='inner')
        df = pd.merge(df, df_recence, on='id_client', how='inner')
        df['segment'] = df.apply(segment_customer, axis=1)
        self.df = df
        return df
        
    def get_cluster(self, id_client):
        if not hasattr(self, 'df'):
            self.classify()
        category = self.df[self.df['id_client'] == id_client]["segment"].values[0]
        return category
        

class KmeansClustering():
    
    def __init__(self):
        self.n_clusters = 5
        self.scaler = StandardScaler()
        self.kmean_model = KMeans(n_clusters=self.n_clusters, 
                                init='k-means++', 
                                max_iter=300, 
                                n_init=10, 
                                random_state=0) 

    def classify(self):
        df_montant = get_montant_score()
        df_frequence = get_frequence_score()
        df_recence = get_recence_score()
        df_age = get_age()
        df = pd.merge(df_montant, df_frequence, on='id_client', how='inner')
        df = pd.merge(df, df_recence, on='id_client', how='inner')
        df = pd.merge(df, df_age, on='id_client', how='inner')
        self.df = df
        X = df[['total_depense', 'nombre_de_commande', 'jours_depuis_derniere_facture', 'age']]
        X = X.dropna()
        X_scaled = self.scaler.fit_transform(X)
        self.kmean_model.fit(X_scaled)
        df['cluster'] = self.kmean_model.labels_
        return df
    
    def get_cluster(self, id_client):
        if not hasattr(self, 'df'):
            self.classify()
        category = self.df[self.df['id_client'] == id_client]["cluster"].values[0]
        return category
    
    def save_model(self):
        with open('models/kmean_model.pkl', 'wb') as f:
            pickle.dump((self.kmean_model, self.scaler, self.df), f)

    def load_model(self):
        with open('models/kmean_model.pkl', 'rb') as f:
            self.kmean_model, self.scaler, self.df = pickle.load(f)



if __name__ == "__main__":
    kmean = KmeansClustering()
    df = kmean.classify()
    kmean.save_model()
    print("model saved")
    suite = input("Enter yes to continue with the tests")
    if suite != "yes":
        exit()
    rfm = RFMClustering()
    df = rfm.classify()
    print(df)
    print("affichage des lignes avec valeurs nan")
    print(df[df.isna().any(axis=1)])
    id_client = input("Enter the id_client: ")
    print(rfm.get_cluster(id_client))
    
    kmean = KmeansClustering()
    df = kmean.classify()
    print(df)
    id_client = input("Enter the id_client: ")
    print(kmean.get_cluster(id_client))
    kmean.save_model()
    kmean2 = KmeansClustering()
    kmean2.load_model()
    print(kmean2.get_cluster(id_client))