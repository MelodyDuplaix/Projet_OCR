# Nom de l'application

## Description

Cette application a pour objectif d'automatiser la gestion et l'analyse des factures, en utilisant de l'ocr pour y extraire des données, les stocker dans une base de données, puis les analyser et les présenter dans une interface web. Elle intègre une démonstration d'extraction sur un fichier, un dashboard d'analyse des données de facturations avec un système de recommandation de produits pour les clients et un système de clustering des clients, ainsi qu'une dashboard de monitoring de l'application.


## Fonctionnalités

* Extraction des données des factures via OCR.
* Stockage des données extraites dans une base de données.
* Analyse des données de facturation.
* Système de recommandation de produits pour les clients.
* Clustering des clients.
* Dashboard de monitoring de l'application.


## Technologies utilisées

* FastAPI
* Tesseract pour l'ocr, avec OpenCV pour la manipulation des images
* Base de données PostGreSQL Azure

## Installation

préparation de l'environnement:

```bash
python -m venv venv
venv\Scripts\activate (ou source venv\Scripts\activate sur linux)
pip install -r requirements.txt
```

## Utilisation


