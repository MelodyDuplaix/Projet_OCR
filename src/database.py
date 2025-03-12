from sqlalchemy import DateTime, column, create_engine, MetaData, Table, Column, String, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import pandas as pd
from dotenv import load_dotenv
import os
from sqlalchemy import text

metadata = MetaData(schema="melody")

produit = Table(
    "produit",
    metadata,
    Column("id_produit", String(50), primary_key=True),
    Column("Nom", String(50)),
    Column("Prix", Numeric),
)

client = Table(
    "client",
    metadata,
    Column("id_client", String(50), primary_key=True),
    Column("Nom", String(50)),
    Column("mail", String(50)),
    Column("Adresse", String(200)),
    Column("Birthdate", Date),
    Column("Genre", String(50))
)

facture = Table(
    "facture",
    metadata,
    Column("id_facture", String(50), primary_key=True),
    Column("texte", String(1500)),
    Column("date_facturation", DateTime),
    Column("Total", Numeric)
)

achat = Table(
    "achat",
    metadata,
    Column("id_produit", String(50), ForeignKey("melody.produit.id_produit"), primary_key=True),
    Column("id_client", String(50), ForeignKey("melody.client.id_client"), primary_key=True),
    Column("id_facture", String(50), ForeignKey("melody.facture.id_facture"), primary_key=True),
    Column("quantité", Numeric(15, 2)),
)

log = Table(
    "log",
    metadata,
    Column("datetime", DateTime),
    Column("fichier", String(50)),
    Column("erreur", String(5000))
)

def create_tables():
    """
    Create the tables in the database.
    """
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    engine = create_engine(database_url)
    metadata.create_all(engine)

def add_data(table_name, df):
    create_tables()
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    engine = create_engine(database_url)
    if not df.empty:
        if table_name == 'client':
            id_column = 'id_client'
        elif table_name == 'produit':
            id_column = 'id_produit'
        elif table_name == 'facture':
            id_column = 'id_facture'
        elif table_name == 'achat':
            id_column = 'id_produit'
        else:
            id_column = None

        if id_column:
            existing_ids = set()
            with engine.connect() as connection:
                result = connection.execute(text(f"SELECT {id_column} FROM melody.\"{table_name}\""))
                for row in result:
                    existing_ids.add(row[0])

            df = df[~df[id_column].isin(existing_ids)]

        if not df.empty:
            df.to_sql(table_name, engine, schema='melody', if_exists='append', index=False)

if __name__ == "__main__":
    create_tables()
