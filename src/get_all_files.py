
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

def request_get(url):
  """
  Performs a GET request to the given URL and displays the response information.

  Args:
    str: url of the request
  """
  try:
    response = requests.get(url)
    response.raise_for_status()
    return response.text
  except requests.exceptions.RequestException as e:
    return f"Erreur lors de la requête: {e}"
  except ValueError as e:
    return f"Erreur lors du décodage JSON {e}"


def get_list_from_date(year, blob_keys):
    """
    Get the list of files from a given year.

    Args:
        year (int): Year of the files.
        blob_keys (str): all the url secure keys

    Returns:
        list: List of all the files from the given year.
    """
    url = f"https://projetocrstorageacc.blob.core.windows.net/invoices-{year}?restype=container&comp=list{blob_keys}"
    content = request_get(url)
    tree = BeautifulSoup(content, features="xml")
    liste = [name.get_text() for name in tree.find_all("Name")]
    return liste

def get_all_files(blob_keys):
    """
    Get all the files from all the years.

    Args:
        blob_keys (str): all the url secure keys

    Returns:
        list: List of all the files.
    """
    all_files = []
    for year in range(2018, 2026):
        year_files = get_list_from_date(year, blob_keys)
        all_files.extend(year_files)
    return all_files


def download_file_requests_os(url, filename):
    """
    Download a file from the url

    Args:
        url(str): Url of the file.
        filename(str): Name of the file. 
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement du fichier (méthode 3) : {e}")
    except IOError as e:
        print(f"Erreur lors de l'enregistrement du fichier (méthode 3): {e}")
    except Exception as e:
      print(f"Erreur (méthode 3): {e}")


if __name__ == "__main__":
    load_dotenv()
    blob_keys = os.getenv("AZURE_BLOB_KEYS")
    count = 0
    for file in get_all_files(blob_keys):
        year = file.split("_")[1]
        folder_path = f"../data/files/{year}"
        os.makedirs(folder_path, exist_ok=True)
        url = f"https://projetocrstorageacc.blob.core.windows.net/invoices-{year}/{file}?{blob_keys}"
        download_file_requests_os(url, f"{folder_path}/{file}")
        count += 1
        if count % 100 == 0:
            print(count)
