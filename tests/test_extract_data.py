import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from src.extract_data import extraire_donnees


def test_file1():
    extract = extraire_donnees("data/test_files/FAC_2018_0001-654.png")
    assert extract["status"] == "success"
    print(extract["erreur"])
    df_client, df_facture, df_produit, df_achat = extract["data"]
    assert len(df_client) == 1
    assert len(df_facture) == 1
    assert len(df_produit) == 4
    assert len(df_achat) == 4
    assert df_client["Nom"].tolist() == ["Carol Potter"]

def test_tests_facture():
    dossier = "data/test_files"
    for racine, dossiers, fichiers_dans_dossier in os.walk(dossier):
        for fichier in fichiers_dans_dossier:
            if "2018" not in fichier:
                chemin_complet = os.path.join(racine, fichier)
                extract = extraire_donnees(chemin_complet)
                if "OK" in fichier:
                    assert extract["status"] == "success"
                    df_client, df_facture, df_produit, df_achat = extract["data"]
                    assert len(df_client) == 1
                    assert len(df_facture) == 1
                else:
                    assert extract["status"] == "error"
                   
def test_invoice0():
    invoice = extraire_donnees("data/test_files/FAC0_XXX.png")
    assert invoice['status']!="success"

def test_invoice1():
    invoice = extraire_donnees("data/test_files/FAC1_OK.png")
    assert invoice['status']=="success"
    df_client, df_facture, df_produit, df_achat = invoice["data"]
    assert df_facture['Total'][0]==500.88

def test_invoice2():
    invoice = extraire_donnees("data/test_files/FAC2_OK.png")
    assert invoice['status']=="success"
    df_client, df_facture, df_produit, df_achat = invoice["data"]
    assert df_facture['Total'][0]==91.62
    assert df_client['Nom'][0]=='Ryan Whitaker'

def test_invoice3():
    invoice = extraire_donnees("data/test_files/FAC3_OK.png")
    assert invoice['status']=="success"
    df_client, df_facture, df_produit, df_achat = invoice["data"]
    assert df_facture['Total'][0]==330.58
    assert df_client['mail'][0]=='yblack@example.org'

# def test_invoice4():
#     invoice = extraire_donnees("data/test_files/FAC4_OK.png")
#     assert invoice['status']=="success"
#     df_client, df_facture, df_produit, df_achat = invoice["data"]
#     assert df_facture['Total'][0]==500.88
#     assert df_facture['id_facture'][0]=='2018-0019'

def test_invoice5():
    invoice = extraire_donnees("data/test_files/FAC5_OK.png")
    assert invoice['status']!="success"

def test_invoice6():
    invoice = extraire_donnees("data/test_files/FAC6_BAD.png")
    assert invoice['status']!="success"

def test_invoice7():
    invoice = extraire_donnees("data/test_files/FAC7_OK.png")
    assert invoice['status']=="success"
    df_client, df_facture, df_produit, df_achat = invoice["data"]
    assert df_facture['Total'][0]==91.62

def test_invoice8():
    invoice = extraire_donnees("data/test_files/FAC8_OK.png")
    assert invoice['status']=="success"
    df_client, df_facture, df_produit, df_achat = invoice["data"]
    assert df_facture['Total'][0]==91.62

def test_invoice9():
    invoice = extraire_donnees("data/test_files/FAC9_OK.png")
    assert invoice['status']=="success"
    df_client, df_facture, df_produit, df_achat = invoice["data"]
    assert df_facture['Total'][0]==330.58

def test_invoice10():
    invoice = extraire_donnees("data/test_files/FAC10_OK.png")
    assert invoice['status']=="success"
    df_client, df_facture, df_produit, df_achat = invoice["data"]
    assert df_facture['Total'][0]==330.58

def test_invoice11():
    invoice = extraire_donnees("data/test_files/FAC11_BAD.png")
    assert invoice['status']!="success"