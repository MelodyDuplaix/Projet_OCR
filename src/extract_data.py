import pandas as pd
from dotenv import load_dotenv # type: ignore
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.get_all_files import get_all_files
from src.database import add_data
from dateparser import parse
import cv2
import pytesseract
import time
from sqlalchemy import create_engine



def decode_qrcode(img_path):
    """
    Extract the text from the qrcode in the given image

    Args:
        img_path (str): the path of the image

    Returns:
        tupple: the genre, birthdate, datetime and name fac of the client in the qrcode
    """
    img = cv2.imread(img_path)
    (x, y, w, h) = (530, 5, 160, 160)
    top_left = (x, y)
    bottom_right = (x + w, y + h)
    cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)
    roi = img[y:y+h, x:x+w]
    detector = cv2.QRCodeDetector()
    data, bbox, straight_qrcode = detector.detectAndDecode(roi)
    if data:
        data = data.split("\n")
        datetime = data[1].split("DATE:")[1]
        birthdate = data[2].split(", birth ")[1]
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
        scale_factor (int, optional): the scale factor of the image. Defaults to 2.

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
    "Adresse": (10, 116, 500, 60),
    "Nom": (70, 70, 450, 30),
    "Mail": (50, 100, 460, 20),
    "Date": (105, 45, 420, 30),
    "Products": (20, 180, 420, 350),
    "Quantities_and_prices": (510, 180, 280, 350),
    "Qrcode": (540, 8, 150, 150)
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

def extraire_donnees(file):
    """
    Extract the data from the image

    Args:
        file (str): the path of the file to extract the data from

    Returns:
        dict: the data extracted from the image, in dataframes: client, facture, produit, achat , the status, the errors and the file name
    """
    erreurs = []

    try:
        extracted_texts = process_image(file, predefined_regions)
        genre, birthdate, datetime_qr, fac = decode_qrcode(file)

        adresse = extracted_texts["Adresse"].replace("\n", " ").replace("Address ", "")
        nom_client = extracted_texts["Nom"]
        mail_client = extracted_texts["Mail"]
        date_facturation = parse(extracted_texts["Date"], languages=["fr", "en"])

        if datetime_qr:
            date_facturation = parse(datetime_qr, languages=["fr", "en"])

        products = [product for product in extracted_texts["Products"].split('\n') if product != "TOTAL"]
        quantities = [quantity.split("x")[0].strip() for quantity in extracted_texts["Quantities_and_prices"].split('\n')[:-1]]
        prices = [price.split("x")[1].strip().replace(" Euro", "") for price in extracted_texts["Quantities_and_prices"].replace("\n\n", "\n").split('\n')[:-1]]
        total = extracted_texts["Quantities_and_prices"].split('\n')[-1].replace(" Euro", "")

        erreurs = []
        if not nom_client: erreurs.append("Nom non détecté")
        if not mail_client: erreurs.append("Mail non détecté")
        if not date_facturation: erreurs.append("Date non détectée")
        if not products: erreurs.append("Produits non détectés")
        if not quantities: erreurs.append("Quantités non détectées")
        if not prices: erreurs.append("Prix non détectés")
        if total is None: erreurs.append("Total mal détecté")
        
        if erreurs:
            return {"status": "error", "fichier": file, "data": None,"erreur": ', '.join(erreurs)}

        # Génération d'identifiants uniques
        id_client = f"CLT_{hash(nom_client + mail_client) % 10**6}"
        id_facture = fac

        df_client = pd.DataFrame([{
            "id_client": id_client,
            "Nom": nom_client,
            "mail": mail_client.replace("| ", ""),
            "Adresse": adresse,
            "Birthdate": birthdate,
            "Genre": genre
        }])

        df_facture = pd.DataFrame({
            "id_facture": [id_facture],
            "texte": " ".join("".join(valeurs) for valeurs in extracted_texts.values()),
            "date_facturation": [date_facturation],
            "Total": total
        })

        products_filtre = [product for product in products if product.strip()]
        unique_products = {}
        for product, price in zip(products_filtre, prices):
            product_cleaned = product.strip().lower()
            if product_cleaned not in unique_products:
                unique_products[product_cleaned] = price

        df_produit = pd.DataFrame({
            "id_produit": [f"PROD_{hash(p) % 10**6}" for p in unique_products.keys()],
            "Nom": list(unique_products.keys()),
            "Prix": list(unique_products.values())
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
            "id_produit": [f"PROD_{hash(p) % 10**6}" for p in product_quantities.keys()],
            "id_client": [id_client] * len(product_quantities),
            "id_facture": [id_facture] * len(product_quantities),
            "quantité": list(product_quantities.values())
        })

        retour =  df_client, df_facture, df_produit, df_achat
        return {"status": "success", "fichier": file, "data": retour, "erreur": None}

    except Exception as e:
        return {"status": "error", "fichier": file,"data": None, "erreur": str(e)}
        

if __name__ == "__main__":
    load_dotenv()
    blob_keys = os.getenv("AZURE_BLOB_KEYS")
    all_files = get_all_files(blob_keys)
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    engine = create_engine(database_url)
    start_time = time.time()
    all_errors = []
    print(len(all_files))

    for i, file in enumerate(all_files, start=1):
        chemin = f"data/files/{file.split('_')[1]}/{file}"
        extract = extraire_donnees(chemin)
        status = extract["status"]
        file = extract["fichier"]
        erreur = extract["erreur"]
        data = extract["data"]
        if erreur:
            all_errors.append(extract)
        if data:
            df_client, df_facture, df_produit, df_achat = data
            add_data( "client", df_client)
            add_data( "facture", df_facture)
            add_data( "produit", df_produit)
            add_data( "achat", df_achat)
            
        if i % 100 == 0:
            elapsed_time = time.time() - start_time
            print(f"{i} fichiers traités en {elapsed_time:.2f} secondes")

    print("\nTraitement terminé")
    if all_errors:
        df_errors = pd.DataFrame(all_errors)
        df_errors.to_csv("data/log_errors.csv", index=False)
        print(f"Nombre d'erreurs : {len(df_errors)}")
        for _, row in df_errors.iterrows():
            print(f"Echec du fichier : {row['fichier']}")
            print(f"Erreur : {row['erreur']}")
