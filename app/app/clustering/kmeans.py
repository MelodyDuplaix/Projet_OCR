from sqlalchemy.orm import sessionmaker
import pandas as pd
from app.app.utils.database import Client, engine
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from datetime import datetime
import pandas as pd

def get_age():
    with SessionLocal() as session:
        query = (
            session.query(
                Client.id_client,
                Client.birthdate
            )
        )
        result = query.all()
        df_age = pd.DataFrame(result, columns=['id_client', 'birthdate'])

    now = datetime.now()
    df_age['age'] = df_age['birthdate'].apply(lambda x: now.year - x.year - ((now.month, now.day) < (x.month, x.day)))

    df_age = df_age.drop('birthdate', axis=1)
    return df_age
