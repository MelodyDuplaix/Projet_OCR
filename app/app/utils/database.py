from matplotlib import table
from sqlalchemy import create_engine, Column, String, Date, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import pandas as pd
from sqlalchemy import text

load_dotenv()

try:
    database_url = os.getenv("DATABASE_URL")
    if database_url is None:
        raise ValueError("DATABASE_URL environment variable is not set.")
    engine = create_engine(database_url)
except ValueError as e:
    print(f"Error: {e}")
    exit(1) # Exit with an error code

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
    Add data to the specified table in the database.

    Args:
        engine (engine): the engine to connect to the database
        table_name (str): the name of the table to add the data to
        df (pd.DataFrame): the dataframe to add to the database
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
        elif table_name == 'log':
            id_column = 'time'
            Model = Log
        else:
            id_column = None
            Model = None
            
        if table_name == 'achat':
            with SessionLocal() as session:
                for _, row in df.iterrows():
                    data = row.to_dict()
                    # Check if the record already exists
                    existing_record = session.query(Achat).filter_by(
                        id_produit=data['id_produit'],
                        id_client=data['id_client'],
                        id_facture=data['id_facture']
                    ).first()
                    if not existing_record:
                        try:
                            session.add(Achat(**data))
                            session.commit()
                        except:
                            session.rollback()
                            pass
                    else:
                        session.rollback()
                        pass
        elif id_column and Model:
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
        error (str): The error of the log.
    """
    file = file.split("-")[0].split("_")[1:].join("-")
    log = Log(time=time, fichier=file, erreur=error)
    with SessionLocal() as session:
        session.add(log)
        session.commit()

def get_all_factures():
    with SessionLocal() as session:
        return session.query(Facture).all()

def get_facture_by_id(id_facture: str):
    """
    Get facture by id.

    Args:
        id_facture (str): The id of the facture.

    Returns:
        dict: The facture data.
    """
    with SessionLocal() as session:
        facture = session.query(Facture).filter(Facture.id_facture == id_facture).first()
        if facture:
            purchases = session.query(Achat).filter(Achat.id_facture == id_facture).all()
            products_data = []
            client = None
            for purchase in purchases:
                client = session.query(Client).filter(Client.id_client == purchase.id_client).first()
                product = session.query(Produit).filter(Produit.id_produit == purchase.id_produit).first()
                products_data.append({
                    "product": product,
                    "quantity": purchase.quantité
                })
            facture_data = {
                "facture": facture,
                "client": client,
                "products": products_data
            }
            return facture_data
        return None

def get_all_clients():
    with SessionLocal() as session:
        return session.query(Client).all()

def get_client_by_id(id_client: str):
    """
    Get client by id.

    Args:
        id_client (str): The id of the client.

    Returns:
        dict: The client data.
    """
    with SessionLocal() as session:
        client = session.query(Client).filter(Client.id_client == id_client).first()
        if client:
            purchases = session.query(Achat).filter(Achat.id_client == id_client).all()
            factures_data = []
            for purchase in purchases:
                facture = session.query(Facture).filter(Facture.id_facture == purchase.id_facture).first()
                products_data = []
                products = session.query(Achat).filter(Achat.id_facture == purchase.id_facture).all()
                for prod in products:
                    product = session.query(Produit).filter(Produit.id_produit == prod.id_produit).first()
                    products_data.append({
                        "product": product,
                        "quantity": prod.quantité
                    })
                factures_data.append({
                    "facture": facture,
                    "products": products_data
                })
            client_data = {
                "client": client,
                "factures": factures_data
            }
            return client_data
        return None

def get_all_achats():
    with SessionLocal() as session:
        return session.query(Achat).all()

def get_achat_by_id(id_produit: str, id_client: str, id_facture: str):
    with SessionLocal() as session:
        return session.query(Achat).filter(Achat.id_produit == id_produit, Achat.id_client == id_client, Achat.id_facture == id_facture).first()

def get_all_produits():
    with SessionLocal() as session:
        return session.query(Produit).all()

def get_produit_by_id(id_produit: str):
    """
    Get produit by id.

    Args:
        id_produit (str): The id of the produit.

    Returns:
        dict: The produit data.
    """
    with SessionLocal() as session:
        produit = session.query(Produit).filter(Produit.id_produit == id_produit).first()
        if produit:
            purchases = session.query(Achat).filter(Achat.id_produit == id_produit).all()
            purchases_data = []
            for purchase in purchases:
                client = session.query(Client).filter(Client.id_client == purchase.id_client).first()
                facture = session.query(Facture).filter(Facture.id_facture == purchase.id_facture).first()
                purchases_data.append({
                    "purchase": purchase,
                    "client": client,
                    "facture": facture
                })
            produit_data = {
                "produit": produit,
                "purchases": purchases_data
            }
            return produit_data
        return None


def get_factures_summary_data():
    """
    Get factures summary data.

    Returns:
    dict: The factures summary data (chiffre d'affaire total, nombre de factures, nombre de clients, nombre de produits vendus, vente par mois).
    """
    with SessionLocal() as session:
        factures = session.query(Facture).all()
        clients = session.query(Client).all()
        produits = session.query(Produit).all()
        achats = session.query(Achat).all()

        # Calculate sales per month
        vente_par_mois = {}
        for facture in factures:
            month = facture.date_facturation.strftime("%Y-%m")
            if month not in vente_par_mois:
                vente_par_mois[month] = 0
            vente_par_mois[month] += float(facture.total)
        return {
            "ca_total": sum(facture.total for facture in factures),
            "nb_factures": len(factures),
            "nb_clients": len(clients),
            "nb_produits": len(produits),
            "nb_produits_vendus": len(achats),
            "vente_par_mois": vente_par_mois
        }
        
def execute_query(sql_query):
    """
    Executes a SQL query and returns the result as a Pandas DataFrame.
    
    Args:
        sql_query (str): The SQL query to execute.
    
    Returns:
        pd.DataFrame: The result of the query as a Pandas DataFrame.
    """
    load_dotenv()
    try:
        database_url = os.getenv("DATABASE_URL")
        if database_url is None:
            raise ValueError("DATABASE_URL environment variable is not set.")
        engine = create_engine(database_url)
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            df = pd.DataFrame(result.fetchall(), columns=list(result.keys()))
        return df
    except Exception as e:
        print(f"Database query failed: {e}")
        return pd.DataFrame() # Return an empty DataFrame on error



if __name__ == "__main__":
    create_tables()
