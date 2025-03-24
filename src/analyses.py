from sqlalchemy import func, cast, Integer
from sqlalchemy.orm import sessionmaker
import pandas as pd
from src.database import Facture, Achat, Produit, Client, Log, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Date, Numeric, DateTime, ForeignKey, func, cast, Integer
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from datetime import datetime
import pandas as pd

def get_montant_score():
    with SessionLocal() as session:
        query = (
            session.query(
                Client.id_client,
                func.sum(Facture.total).label('total_depense')
            )
            .join(Achat, Achat.id_facture == Facture.id_facture)
            .join(Client, Client.id_client == Achat.id_client)
            .group_by(Client.id_client)
        )
        result = query.all()
        df_montant = pd.DataFrame(result, columns=['id_client', 'total_depense'])
    df_montant['total_depense'] = pd.to_numeric(df_montant['total_depense'], errors='coerce')
    df_montant['score_depense'] = pd.qcut(
        df_montant['total_depense'].dropna(), 
        q=5, 
        labels=[5, 4, 3, 2, 1]
    )
    return df_montant

def get_frequence_score():
    with SessionLocal() as session:
        query = (
            session.query(
                Client.id_client,
                func.count(Achat.id_facture.distinct())
            )
            .join(Client, Client.id_client == Achat.id_client)
            .group_by(Client.id_client)
        )
        result = query.all()
        df_frequence = pd.DataFrame(result, columns=['id_client', 'nombre_de_commande'])
    bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.1]
    labels = [1, 2, 3, 4, 5]
    df_frequence['score_frequence'] = pd.cut(df_frequence['nombre_de_commande'].rank(method='min', pct=True), 
                                            bins=bins, 
                                            labels=labels, 
                                            include_lowest=True, 
                                            right=False)
    df_frequence['score_frequence'] = df_frequence['score_frequence'].astype(int, errors='ignore')
    df_frequence.sort_values("nombre_de_commande")
    return df_frequence

def get_recence_score():
    with SessionLocal() as session:
        now = datetime.now().date()
        query = (
            session.query(
                Achat.id_client,
                cast(func.date_part('day', now - func.max(Facture.date_facturation)), Integer).label("jours_depuis_derniere_facture")
            )
            .join(Facture, Facture.id_facture == Achat.id_facture)
            .join(Client, Client.id_client == Achat.id_client)
            .group_by(Achat.id_client)
        )
        result = query.all()
        df_recence = pd.DataFrame(result, columns=['id_client', 'jours_depuis_derniere_facture'])
    df_recence['score_recence'] = pd.qcut(
        df_recence['jours_depuis_derniere_facture'], 
        q=5, 
        labels=[5, 4, 3, 2, 1]
    )
    df_recence.sort_values("score_recence")
    return df_recence

def get_age():
    with SessionLocal() as session:
        query = (
            session.query(
                Client.id_client,
                Client.birthdate
            )
        )
        result = query.all()
        df_age = pd.DataFrame(result, columns=['id_client', 'birthdate'])

    now = datetime.now()
    df_age['age'] = df_age['birthdate'].apply(lambda x: now.year - x.year - ((now.month, now.day) < (x.month, x.day)))

    df_age = df_age.drop('birthdate', axis=1)
    return df_age

def segment_customer(row):
    recency = row['score_recence']
    frequency_monetary = row['score_frequence'] * row["score_depense"]

    if recency <= 2:
        if frequency_monetary >= 4:
            return "Cannot Lose Them"
        elif frequency_monetary <= 2:
            return "Lost"
        else:
            return "At Risk"
    elif recency >= 4:
        if frequency_monetary >= 4:
            return "Champions"
        elif frequency_monetary == 1:
            return "New"
        else:
            return "Loyal"
    else:  # recency = 3
        if frequency_monetary >= 4:
            return "Loyal"
        elif frequency_monetary == 3:
            return "Need Attention"
        elif frequency_monetary == 2:
            return "About to Sleep"
        else:
            return "Promising"
