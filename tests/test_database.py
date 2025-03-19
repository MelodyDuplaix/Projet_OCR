import datetime
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.database import (
    Base,
    add_client,
    add_data,
    add_invoice,
    add_log,
    add_product,
    add_purchase,
    execute_query,
)
from src.extract_data import extraire_donnees, extract_data_raw
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL environment variable not set")

@pytest.fixture(scope="session")
def engine():
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    engine = create_engine(database_url)
    yield engine

@pytest.fixture(scope="function")
def setup_database(engine):
    Base.metadata.create_all(engine)

def test_add_client(engine, setup_database):
    add_client(
        name="Test Client",
        mail="test@example.com",
        address="123 Test St",
        birthdate=datetime.date(1990, 1, 1),
        genre="M",
    )
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT * FROM melody.client WHERE nom = 'Test Client'")
        )
        client = result.fetchone()
        assert client is not None
        assert client.nom == "Test Client"
        assert client.mail == "test@example.com"
        assert client.adresse == "123 Test St"
        assert client.birthdate == datetime.date(1990, 1, 1)
        assert client.genre == "M"


def test_add_product(engine, setup_database):
    add_product(name="Test Product", price=9.99)
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT * FROM melody.produit WHERE nom = 'Test Product'")
        )
        product = result.fetchone()
        assert product is not None
        assert product.nom == "Test Product"
        assert float(product.prix) == 9.99


def test_add_invoice(engine, setup_database):
    add_invoice(
        invoice_id="INV-2019-0001",
        text="Invoice text",
        date=datetime.datetime(2023, 1, 1, 12, 0, 0),
        total=100.00,
    )
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT * FROM melody.facture WHERE id_facture = 'INV-2019-0001'")
        )
        invoice = result.fetchone()
        assert invoice is not None
        assert invoice.id_facture == "INV-2019-0001"
        assert invoice.texte == "Invoice text"
        assert invoice.date_facturation == datetime.datetime(2023, 1, 1, 12, 0, 0)
        assert invoice.total == 100.00


def test_add_purchase(engine, setup_database):
    add_client(
        name="Test Client",
        mail="test@example.com",
        address="123 Test St",
        birthdate=datetime.date(1990, 1, 1),
        genre="M",
    )
    add_product(name="Test Product", price=9.99)
    add_invoice(
        invoice_id="INV-2019-0001",
        text="Invoice text",
        date=datetime.datetime(2023, 1, 1, 12, 0, 0),
        total=100.00,
    )
    add_purchase(
        product_id="PRD_Test_Product", client_id="CLT_Test_Client", invoice_id="INV-2019-0001", quantity=1
    )
    with engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT * FROM melody.achat WHERE id_produit = 'PRD_Test_Product' AND id_client = 'CLT_Test_Client' AND id_facture = 'INV-2019-0001'"
            )
        )
        purchase = result.fetchone()
        assert purchase is not None
        assert purchase.id_produit == "PRD_Test_Product"
        assert purchase.id_client == "CLT_Test_Client"
        assert purchase.id_facture == "INV-2019-0001"
        assert purchase.quantité == 1


def test_add_log(engine, setup_database):
    log_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    add_log(
        time=log_time, file="test_file.py", error="Test error message"
    )
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT * FROM melody.log WHERE time = :log_time")
        ,{"log_time": log_time})
        log = result.fetchone()
        assert log is not None
        assert log.time == log_time
        assert log.fichier == "test_file.py"
        assert log.erreur == "Test error message"


def test_execute_query(engine, setup_database):
    # Add a test client to the database
    add_client(
        name="Test Client",
        mail="test@example.com",
        address="123 Test St",
        birthdate=datetime.date(1990, 1, 1),
        genre="Male"
    )

    # Execute a query to retrieve the client
    df = execute_query("SELECT * FROM melody.client WHERE nom = 'Test Client'")

    # Assert that the DataFrame is not empty and contains the test client
    assert not df.empty
    assert df["nom"][0] == "Test Client"
    assert df["mail"][0] == "test@example.com"
    assert df["adresse"][0] == "123 Test St"
    assert df["birthdate"][0] == datetime.date(1990, 1, 1)
    assert df["genre"][0] == "Male"


def test_add_data(engine, setup_database):
    # Create a DataFrame with client data
    data = {
        "id_client": ["CLT-002"],
        "nom": ["Test Client 2"],
        "mail": ["test2@example.com"],
        "adresse": ["456 Test St"],
        "birthdate": [datetime.date(1995, 2, 2)],
        "genre": ["Female"],
    }
    df = pd.DataFrame(data)

    # Add the data to the client table
    add_data(engine, "client", df)

    # Execute a query to retrieve the client
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT * FROM melody.client WHERE nom = 'Test Client 2'")
        )
        client = result.fetchone()
        assert client is not None
        assert client.nom == "Test Client 2"
        assert client.mail == "test2@example.com"
        assert client.adresse == "456 Test St"
        assert client.birthdate == datetime.date(1995, 2, 2)
        assert client.genre == "Female"
