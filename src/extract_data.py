import datetime
import numpy as np
import pandas as pd
from dotenv import load_dotenv # type: ignore
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.get_all_files import get_all_files
from dateparser import parse
import cv2
import pytesseract
import time
from sqlalchemy import create_engine
import re

def decode_qrcode(img_path):
    """
    Extract the text from the qrcode in the given image

    Args:
        img_path (str): the path of the image

    Returns:
        tupple: the genre, birthdate, datetime and name fac of the client in the qrcode
    """
    scale_factor = 3
    img = cv2.imread(img_path)
    (x, y, w, h) = (530, 5, 180, 180)
    top_left = (x, y)
    bottom_right = (x + w, y + h)
    roi = img[y:y+h, x:x+w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(10,10))
    enhanced = clahe.apply(gray)
    new_size = int(img.shape[1] * scale_factor), int(img.shape[0] * scale_factor)
    img_large = cv2.resize(enhanced, new_size, interpolation=cv2.INTER_LINEAR_EXACT)
    detector = cv2.QRCodeDetector()
    data, bbox, straight_qrcode = detector.detectAndDecode(img_large)
    if not data:
        roi = img[y:y+h, x:x+w]
        new_size = int(roi.shape[1] * scale_factor), int(roi.shape[0] * scale_factor)
        img_large = cv2.resize(img_large, new_size, interpolation=cv2.INTER_LINEAR_EXACT)
        data, bbox, straight_qrcode = detector.detectAndDecode(img_large)
    if data:
        data = data.split("\n")
        datetime = data[1].split("DATE:")[1]
        birthdate = parse(data[2].split(", birth ")[1], languages=["fr", "en"])
        genre = data[2].split(",")[0].split(":")[1]
        fac = data[0].replace("INVOICE:FAC/","").replace("/","-")
        return genre, birthdate, datetime, fac
    return None, None, None, None

def process_image(input_img_path, regions, scale_factor=2):
    """
    Extract the data from the differents region of the given image

    Args:
        input_img_path (str): the path of the image
        regions (dict): the regions of the image
        scale_factor (int): the scale factor of the image.

    Returns:
        dict: the extracted data from the image
    """
    img = cv2.imread(input_img_path)
    
    # Agrandir l'image pour améliorer la reconnaissance des caractères
    new_size = (int(img.shape[1] * scale_factor), int(img.shape[0] * scale_factor))
    img = cv2.resize(img, new_size, interpolation=cv2.INTER_LINEAR)
    
    extracted_texts = {}

    for region_name, (x, y, w, h) in regions.items():
        # Ajuster les coordonnées des régions à l'échelle
        x, y, w, h = int(x * scale_factor), int(y * scale_factor), int(w * scale_factor), int(h * scale_factor)
        
        roi = img[y:y+h, x:x+w]

        # Convertir en niveaux de gris
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Amélioration du contraste (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(10,10))
        enhanced = clahe.apply(gray)

        # Binarisation (Otsu)
        _, thresholded = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        if region_name == "Quantities_and_prices":
            text = pytesseract.image_to_string(thresholded, config="psm 6 --tessedit_char_whitelist 0123456789Eurox.")
        text = pytesseract.image_to_string(thresholded, config="--psm 6")
        extracted_texts[region_name] = text.strip()

    return extracted_texts

# Définition des blocs
predefined_regions = {
    "Products": (20, 180, 420, 900),
    "Quantities_and_prices": (510, 180, 280, 900),
    "Qrcode": (530, 5, 180, 180),
    "bloc": (10, 10, 520, 180)
}

def nettoyer_total(total):
    """
    Clean the total value from text

    Args:
        total (str): the total to clean

    Returns:
        str: the total cleaned
    """
    if "x" in total:
        return None
    return total.replace(" Euro", "")

def extract_data_raw(file):
    """
    Extract the raw data from the image.

    Args:
        file (str): the path of the file to extract the data from.

    Returns:
        dict: the data extracted from the image, including status, filename, error, and a dictionary of extracted variables.
    """
    erreurs = []

    try:
        extracted_texts = process_image(file, predefined_regions)
        genre, birthdate, datetime_qr, fac = decode_qrcode(file)
        bloc = extracted_texts["bloc"]
        invoice_line = next((line for line in bloc.split('\n') if line.strip().startswith('INVOICE FAC')), '') if bloc else ''
        file_date = '-'.join(part.strip() for part in invoice_line.split('/')[-2:]).replace(" ","") if invoice_line else None
        date_facturation = re.search(r'Issue date (\d{4}-\d{2}-\d{2})', bloc) if bloc else None
        date_facturation = parse(date_facturation.group(1), languages=["fr", "en"]) if date_facturation else None
        nom_client = re.search(r'Bill to (.+)', bloc) if bloc else None
        nom_client = nom_client.group(1).strip() if nom_client else None
        mail_client = re.search(r'Email (.+@.+\..+)', bloc) if bloc else None
        mail_client = mail_client.group(1) if mail_client else None
        adresse = bloc.split("Address ")[1].replace("\n", " ").strip() if bloc else None

        if datetime_qr and date_facturation:
            if parse(datetime_qr, languages=["fr", "en"]).date() == date_facturation.date(): # type: ignore
                date_facturation = parse(datetime_qr, languages=["fr", "en"])
            else:
                erreurs.append("Dates non correspondantes")

        products = [product for product in extracted_texts["Products"].split('\n') if product != "TOTAL"]
        quantities = [quantity.split("x")[0].strip() for quantity in extracted_texts["Quantities_and_prices"].split('\n')[:-1]]
        prices = [price.split("x")[1].strip().replace(" Euro", "") for price in extracted_texts["Quantities_and_prices"].replace("\n\n", "\n").split('\n')[:-1]]
        total = extracted_texts["Quantities_and_prices"].split('\n')[-1].replace(" Euro", "").replace("Furo", "")

        if not file_date == fac and fac: erreurs.append("Identifiants de fichiers non correspondants")
        if not nom_client: erreurs.append("Nom non détecté")
        if not mail_client: erreurs.append("Mail non détecté")
        if not date_facturation: erreurs.append("Date non détectée")
        if not products: erreurs.append("Produits non détectés")
        if not quantities: erreurs.append("Quantités non détectées")
        if not prices: erreurs.append("Prix non détectés")
        if not birthdate: erreurs.append("Date de naissance non détectée")
        if not genre: erreurs.append("Genre non détecté")
        if not adresse: erreurs.append("Adresse non détectée")
        if total is None: erreurs.append("Total mal détecté")

        try:
            total_calcule = sum(float(price) * int(quantity) for price, quantity in zip(prices, quantities))
            total_calcule = round(total_calcule, 2)
            total_from_invoice = round(float(total.replace(',', '.')), 2)
            if total_from_invoice != total_calcule:
                erreurs.append("Total non correct")
        except Exception as e:
            erreurs.append(f"Erreur lors du calcul du total : {str(e)}")
        
        if erreurs:
            return {"status": "error", "fichier": file, "data": None,"erreur": ', '.join(erreurs), "variables": None}

        variables = {
            "nom_client": nom_client,
            "mail_client": mail_client,
            "adresse": adresse,
            "birthdate": birthdate,
            "genre": genre,
            "date_facturation": date_facturation,
            "total": total,
            "products": products,
            "quantities": quantities,
            "prices": prices,
            "fac": fac,
            "file_date": file_date,
            "extracted_texts": extracted_texts
        }

        return {"status": "success", "fichier": file, "data": None, "erreur": None, "variables": variables}

    except Exception as e:
        return {"status": "error", "fichier": file,"data": None, "erreur": str(e), "variables": None}

def extraire_donnees(file):
    """
    Extract the data from the image and return it in dataframes.

    Args:
        file (str): the path of the file to extract the data from.

    Returns:
        dict: the data extracted from the image, in dataframes: client, facture, produit, achat , the status, the errors and the file name.
    """
    raw_data = extract_data_raw(file)
    if raw_data["status"] == "error":
        return raw_data

    variables = raw_data["variables"]
    nom_client = variables["nom_client"]
    mail_client = variables["mail_client"]
    adresse = variables["adresse"]
    birthdate = variables["birthdate"]
    genre = variables["genre"]
    date_facturation = variables["date_facturation"]
    total = variables["total"]
    products = variables["products"]
    quantities = variables["quantities"]
    prices = variables["prices"]
    fac = variables["fac"]
    file_date = variables["file_date"]
    extracted_texts = variables["extracted_texts"]

    # Génération d'identifiants uniques
    id_client = f"CLT_{nom_client.replace(' ', '_')}" if nom_client else None
    id_facture = fac if fac else file_date

    df_client = pd.DataFrame([{
        "id_client": id_client,
        "nom": nom_client,
        "mail": mail_client.replace("| ", "") if mail_client else None,
        "adresse": adresse,
        "birthdate": birthdate,
        "genre": genre
    }])

    df_facture = pd.DataFrame({
        "id_facture": [id_facture],
        "texte": " ".join("".join(valeurs) for valeurs in extracted_texts.values()),
        "date_facturation": [date_facturation],
        "total": total
    })
    df_facture["total"] = df_facture["total"].astype(float, errors='ignore')

    products_filtre = [product for product in products if product.strip()]
    unique_products = {}
    for product, price in zip(products_filtre, prices):
        product_cleaned = product.strip().lower()
        if product_cleaned not in unique_products:
            unique_products[product_cleaned] = price

    df_produit = pd.DataFrame({
        "id_produit": [f"PROD_{'_'.join(n.split(' ')[:3])}" for n in unique_products.keys()],
        "nom": list(unique_products.keys()),
        "prix": list(unique_products.values())
    })

    # Agrégation des quantités si plusieurs fois le même produit dans une facture
    product_quantities = {}
    for product, quantity in zip(products_filtre, quantities):
        product_cleaned = product.strip().lower()
        if product_cleaned in product_quantities:
            product_quantities[product_cleaned] += int(quantity)
        else:
            product_quantities[product_cleaned] = int(quantity)

    df_achat = pd.DataFrame({
        "id_produit": [f"PROD_{'_'.join(n.split(' ')[:3])}" for n in unique_products.keys()],
        "id_client": [id_client] * len(product_quantities),
        "id_facture": [id_facture] * len(product_quantities),
        "quantité": list(product_quantities.values())
    })

    retour =  df_client, df_facture, df_produit, df_achat
    return {"status": "success", "fichier": file, "data": retour, "erreur": None}


if __name__ == "__main__":
    from src.database import add_data
    load_dotenv()
    blob_keys = os.getenv("AZURE_BLOB_KEYS")
    all_files = get_all_files(blob_keys)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    engine = create_engine(database_url)
    start_time = time.time()
    all_errors = []
    
    print("Début du traitement")

    for i, filename in enumerate(all_files, start=1):
        chemin = f"data/files/{filename.split('_')[1]}/{filename}"
        extract = extraire_donnees(chemin)
        status = extract["status"]
        file = extract["fichier"]
        erreur = extract["erreur"]
        data = extract["data"]
        if erreur:
            print(f"Echec du fichier : {file}, erreur : {erreur}")
            all_errors.append({
                "time": datetime.datetime.now(),
                "fichier": filename,
                "erreur": erreur
            })
        if data:
            df_client, df_facture, df_produit, df_achat = data
            add_data(engine, "client", df_client)
            add_data(engine, "facture", df_facture)
            add_data(engine, "produit", df_produit)
            add_data(engine,  "achat", df_achat)
            
        if i % 100 == 0:
            elapsed_time = time.time() - start_time
            print(f"{i} fichiers traités en {elapsed_time:.2f} secondes")

    print("\nTraitement terminé")
    if all_errors:
        df_errors = pd.DataFrame(all_errors)
        add_data(engine, "log", df_errors)
        print(f"Nombre d'erreurs : {len(df_errors)}")
