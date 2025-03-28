import requests

def get_data_for_facture(headers, id_facture, FASTAPI_URL):
    response = requests.get(f"{FASTAPI_URL}/factures/{id_facture}", headers=headers)
    if response.status_code == 401:
        raise Exception("Unauthorized")
    response.raise_for_status()
    result = response.json()

    # Process response data
    facture = result["facture"]
    facture["date_facturation"] = facture["date_facturation"].split("T")[0]
    client = result["client"]
    client["birthdate"] = client["birthdate"].split("T")[0]
    products = [
        {
            "id_produit": p["product"]["id_produit"],
            "nom": p["product"]["nom"],
            "prix": p["product"]["prix"],
            "quantite": p["quantity"],
        }
        for p in result["products"]
    ]
    
    return facture, client, products