from sqlalchemy import create_engine, Column, String, Date, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import pandas as pd
from sqlalchemy import text

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "melody"}

    username = Column(String(50), primary_key=True)
    full_name = Column(String(50))
    email = Column(String(50))
    hashed_password = Column(String(200))
    disabled = Column(Boolean, default=False)

class Produit(Base):
    __tablename__ = "produit"
    __table_args__ = {"schema": "melody"}
    id_produit = Column(String(50), primary_key=True)
    nom = Column(String(50))
    prix = Column(Numeric)

class Client(Base):
    __tablename__ = "client"
    __table_args__ = {"schema": "melody"}

    id_client = Column(String(50), primary_key=True)
    nom = Column(String(50))
    mail = Column(String(50))
    adresse = Column(String(200))
    birthdate = Column(Date)
    genre = Column(String(50))

class Facture(Base):
    __tablename__ = "facture"
    __table_args__ = {"schema": "melody"}

    id_facture = Column(String(50), primary_key=True)
    texte = Column(String(1500))
    date_facturation = Column(DateTime)
    total = Column(Numeric)

class Achat(Base):
    __tablename__ = "achat"
    __table_args__ = {"schema": "melody"}

    id_produit = Column(String(50), ForeignKey("melody.produit.id_produit"), primary_key=True)
    id_client = Column(String(50), ForeignKey("melody.client.id_client"), primary_key=True)
    id_facture = Column(String(50), ForeignKey("melody.facture.id_facture"), primary_key=True)
    quantité = Column(Numeric(15, 2))

class Log(Base):
    __tablename__ = "log"
    __table_args__ = {"schema": "melody"}

    time = Column(DateTime, primary_key=True)
    fichier = Column(String(50))
    erreur = Column(String(5000))

def create_tables():
    """
    Create the tables in the database.
    """
    Base.metadata.create_all(engine)

def add_user(username, full_name, email, hashed_password, disabled=False):
    """
    Add a new user to the database.
    """
    user = User(username=username, full_name=full_name, email=email, hashed_password=hashed_password, disabled=disabled)
    with SessionLocal() as session:
        session.add(user)
        session.commit()

def add_data(engine, table_name, df):
    """
    Executes a SQL query and returns the result as a Pandas DataFrame.
    
    args:
        sql_query (str): The SQL query to execute.
    
    returns:
        pd.DataFrame: The result of the query as a Pandas DataFrame.
    """
    if not df.empty:
        if table_name == 'client':
            id_column = 'id_client'
            Model = Client
        elif table_name == 'produit':
            id_column = 'id_produit'
            Model = Produit
        elif table_name == 'facture':
            id_column = 'id_facture'
            Model = Facture
        elif table_name == 'achat':
            id_column = 'id_produit'
            Model = Achat
        elif table_name == 'log':
            id_column = 'time'
            Model = Log
        else:
            id_column = None
            Model = None

        if id_column and Model:
            existing_ids = set()
            with engine.connect() as connection:
                result = connection.execute(text(f"SELECT {id_column} FROM melody.\"{table_name}\""))
                for row in result:
                    existing_ids.add(row[0])

            df = df[~df[id_column].isin(existing_ids)]

            if not df.empty:
                with SessionLocal() as session:
                    for _, row in df.iterrows():
                        data = row.to_dict()
                        session.add(Model(**data))
                    session.commit()

def add_client(name, mail, address, birthdate, genre):
    """
    Add a new client to the database.
    
    args:
        name (str): The name of the client.
        mail (str): The email of the client.
        address (str): The address of the client.
        birthdate (str): The birthdate of the client.
        genre (str): The genre of the client.
    """
    client = Client(id_client=f"CLT_{name.replace(' ', '_')}", nom=name, mail=mail, adresse=address, birthdate=birthdate, genre=genre)
    with SessionLocal() as session:
        session.add(client)
        session.commit()

def add_product(name, price):
    """
    Add a new product to the database.
    
    args:
        name (str): The name of the product.
        price (float): The price of the product.
    """
    product = Produit(id_produit=f"PRD_{name.replace(' ', '_')}", nom=name, prix=price)
    with SessionLocal() as session:
        session.add(product)
        session.commit()

def add_invoice(invoice_id, text, date, total):
    """
    Add a new invoice to the database.
    
    args:
        invoice_id (str): The ID of the invoice.
        text (str): The text of the invoice.
        date (str): The date of the invoice.
        total (float): The total of the invoice.
    """
    invoice = Facture(id_facture=invoice_id, texte=text, date_facturation=date, total=total)
    with SessionLocal() as session:
        session.add(invoice)
        session.commit()

def add_purchase(product_id, client_id, invoice_id, quantity):
    """
    Add a new purchase to the database.
    
    args:
        product_id (str): The ID of the product.
        client_id (str): The ID of the client.
        invoice_id (str): The ID of the invoice.
        quantity (float): The quantity of the product.
    """
    purchase = Achat(id_produit=product_id, id_client=client_id, id_facture=invoice_id, quantité=quantity)
    with SessionLocal() as session:
        session.add(purchase)
        session.commit()
        
def add_log(time, file, error):
    """
    Add a new log to the database.
    
    args:
        time (str): The time of the log.
        file (str): The file of the log.
    """
    log = Log(time=time, fichier=file, erreur=error)
    with SessionLocal() as session:
        session.add(log)
        session.commit()


def execute_query(sql_query):
    """
    Executes a SQL query and returns the result as a Pandas DataFrame.
    
    args:
        sql_query (str): The SQL query to execute.
    
    returns:
        pd.DataFrame: The result of the query as a Pandas DataFrame.
    """
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    engine = create_engine(database_url)
    with engine.connect() as connection:
        result = connection.execute(text(sql_query))
        df = pd.DataFrame(result.fetchall(), columns=list(result.keys()))
    return df

if __name__ == "__main__":
    create_tables()
