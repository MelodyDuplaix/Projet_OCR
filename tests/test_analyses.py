import pytest
import pandas as pd
from src import analyses
from src.analyses import segment_customer

def test_get_age(mocker):
    # Mock the database session and query
    mock_session = mocker.MagicMock()
    mock_query_result = [(1, pd.Timestamp('1990-01-01')), (2, pd.Timestamp('1980-01-01')), (3, pd.Timestamp('2000-01-01'))]
    mock_query = mocker.MagicMock()
    mock_query.all.return_value = mock_query_result
    mock_session.query.return_value = mock_query
    analyses.SessionLocal = mocker.MagicMock(return_value=mock_session)
    mock_session.__enter__.return_value = mock_session
    mock_session.__exit__.return_value = None

    # Call the function
    df_age = analyses.get_age()

    # Assert the result
    assert isinstance(df_age, pd.DataFrame)
    assert len(df_age) == 3
    assert 'id_client' in df_age.columns
    assert 'age' in df_age.columns
    
def test_segment_customer():
    # Create a sample row
    row = pd.Series({
        'score_recence': 5,
        'score_frequence': 5,
        'score_depense': 5
    })

    # Call the function
    segment = segment_customer(row)

    # Assert the result
    assert segment == "Champions"
