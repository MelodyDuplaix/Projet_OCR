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

def test_execute_query(engine, setup_database):
    # Add a test client to the database
    try:
        add_client(
            name="Test Client",
            mail="test@example.com",
            address="123 Test St",
            birthdate=datetime.date(1990, 1, 1),
            genre="M"
        )
    except:
        pass

    # Execute a query to retrieve the client
    df = execute_query("SELECT * FROM melody.client WHERE nom = 'Test Client'")

    # Assert that the DataFrame is not empty and contains the test client
    assert not df.empty
    assert df["nom"][0] == "Test Client"
    assert df["mail"][0] == "test@example.com"
    assert df["adresse"][0] == "123 Test St"
    assert df["birthdate"][0] == datetime.date(1990, 1, 1)
    assert df["genre"][0] == "M"
