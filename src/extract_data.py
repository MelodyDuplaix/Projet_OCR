import pandas as pd
from dotenv import load_dotenv # type: ignore
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.get_all_files import get_all_files
from src.database import add_data, engine
from dateparser import parse
import cv2
import pytesseract
import time

load_dotenv()
blob_keys = os.getenv("AZURE_BLOB_KEYS")
all_files = get_all_files(blob_keys)

def decode_qrcode(img_path):
    img = cv2.imread(img_path)
    (x, y, w, h) = (540, 8, 150, 150)
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
    "Adresse": (10, 116, 400, 60),
    "Nom": (70, 70, 250, 30),
    "Mail": (50, 100, 250, 20),
    "Date": (105, 45, 250, 30),
    "Products": (20, 180, 400, 350),
    "Quantities_and_prices": (540, 180, 250, 350)
}


def nettoyer_total(total):
    if "x" in total:
        return None
    return total.replace(" Euro", "")

def extraire_donnees(file):
    chemin = f"data/files/{file.split('_')[1]}/{file}"

    try:
        extracted_texts = process_image(chemin, predefined_regions)
        genre, birthdate, datetime_qr, fac = decode_qrcode(chemin)

        adresse = extracted_texts["Adresse"].replace("\n", " ")
        nom_client = extracted_texts["Nom"]
        mail_client = extracted_texts["Mail"]
        date_facturation = parse(extracted_texts["Date"], languages=["fr", "en"])

        # Use QR code datetime if available, otherwise use extracted date
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
            print(f"Erreur dans le fichier {file} : {', '.join(erreurs)}")
            return None

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

        # Aggregate quantities for the same product
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

        add_data(engine, "client", df_client)
        add_data(engine, "facture", df_facture)
        add_data(engine, "produit", df_produit)
        add_data(engine, "achat", df_achat)

        return df_client, df_facture, df_produit, df_achat

    except Exception as e:
        print(f"Échec pour le fichier {file} : {str(e)}")
        return None
    
if __name__ == "__main__":
    start_time = time.time()

    for i, file in enumerate(all_files, start=1):
        data = extraire_donnees(file)

        if data:
            df_client, df_facture, df_produit, df_achat = data

        if i % 100 == 0:
            elapsed_time = time.time() - start_time
            print(f"{i} fichiers traités en {elapsed_time:.2f} secondes")

    print("\nTraitement terminé")
