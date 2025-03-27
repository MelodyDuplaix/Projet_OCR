import pytest
import pandas as pd
from src import clustering
from src.clustering import RFMClustering, KmeansClustering

def test_rfm_clustering_classify(mocker):
    # Mock the dependencies
    data = {'id_client': [1, 2], 'total_depense': [100, 200], 'score_depense': [5, 4]}
    df_montant = pd.DataFrame(data)
    clustering.get_montant_score = mocker.MagicMock(return_value=df_montant)
    
    data = {'id_client': [1, 2], 'nombre_de_commande': [10, 20], 'score_frequence': [5, 4]}
    df_frequence = pd.DataFrame(data)
    clustering.get_frequence_score = mocker.MagicMock(return_value=df_frequence)
    
    data = {'id_client': [1, 2], 'jours_depuis_derniere_facture': [10, 20], 'score_recence': [5, 4]}
    df_recence = pd.DataFrame(data)
    clustering.get_recence_score = mocker.MagicMock(return_value=df_recence)

    # Create an instance of the class
    rfm_clustering = RFMClustering()

    # Call the function
    df = rfm_clustering.classify()

    # Assert the result
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert 'id_client' in df.columns
    assert 'segment' in df.columns

def test_rfm_clustering_get_cluster(mocker):
    # Mock the classify function
    rfm_clustering = RFMClustering()
    rfm_clustering.classify = mocker.MagicMock(return_value=pd.DataFrame({'id_client': [1, 2], 'segment': ['Champions', 'Loyal']}))
    rfm_clustering.df = pd.DataFrame({'id_client': [1, 2], 'segment': ['Champions', 'Loyal']})

    # Call the function
    category = rfm_clustering.get_cluster(1)

    # Assert the result
    assert category == 'Champions'

def test_kmeans_clustering_classify(mocker):
    # Mock the dependencies
    clustering.get_montant_score = mocker.MagicMock(return_value=pd.DataFrame({'id_client': [1, 2], 'total_depense': [100, 200]}))
    clustering.get_frequence_score = mocker.MagicMock(return_value=pd.DataFrame({'id_client': [1, 2], 'nombre_de_commande': [10, 20]}))
    clustering.get_recence_score = mocker.MagicMock(return_value=pd.DataFrame({'id_client': [1, 2], 'jours_depuis_derniere_facture': [10, 20]}))
    clustering.get_age = mocker.MagicMock(return_value=pd.DataFrame({'id_client': [1, 2], 'age': [30, 40]}))

    # Create an instance of the class
    kmeans_clustering = KmeansClustering()
    kmeans_clustering.scaler = mocker.MagicMock()
    kmeans_clustering.kmean_model = mocker.MagicMock()
    kmeans_clustering.scaler.fit_transform.return_value = [[0, 0, 0, 0], [0, 0, 0, 0]]
    kmeans_clustering.kmean_model.labels_ = [0, 1]

    # Call the function
    df = kmeans_clustering.classify()

    # Assert the result
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert 'id_client' in df.columns
    assert 'cluster' in df.columns

def test_kmeans_clustering_get_cluster(mocker):
    # Mock the classify function
    kmeans_clustering = KmeansClustering()
    kmeans_clustering.classify = mocker.MagicMock(return_value=pd.DataFrame({'id_client': [1, 2], 'cluster': [0, 1]}))
    kmeans_clustering.df = pd.DataFrame({'id_client': [1, 2], 'cluster': [0, 1]})

    # Call the function
    category = kmeans_clustering.get_cluster(1)

    # Assert the result
    assert category == 0

def test_kmeans_clustering_load_model(mocker):
    mock_load = mocker.patch('pickle.load')
    kmeans_clustering = KmeansClustering()
    mock_load.return_value = (mocker.MagicMock(), mocker.MagicMock(), pd.DataFrame())
    kmeans_clustering.load_model()
    mock_load.assert_called()
