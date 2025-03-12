import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from src.extract_data import extraire_donnees


def test_file1():
    extract = extraire_donnees("data/test_files/FAC_2018_0001-654.png")
    assert extract["status"] == "success"
    df_client, df_facture, df_produit, df_achat = extract["data"]
    assert len(df_client) == 1
    assert len(df_facture) == 1
    assert len(df_produit) == 4
    assert len(df_achat) == 4
    assert df_client["Nom"].tolist() == ["Carol Potter"]
