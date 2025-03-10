from sqlalchemy import create_engine, MetaData, Table, Column, String, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable not set")
engine = create_engine(database_url)

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
    Column("birthday", Date),
)

facture = Table(
    "facture",
    metadata,
    Column("id_facture", String(50), primary_key=True),
    Column("texte", String(1500)),
    Column("date_facturation", Date),
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

from sqlalchemy import text

def create_tables(engine):
    metadata.create_all(engine)

def add_data(engine, table_name, df):
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

create_tables(engine)

if __name__ == "__main__":
    create_tables(engine)