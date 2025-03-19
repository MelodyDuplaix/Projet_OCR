import datetime
import os
from typing import Annotated
from fastapi.responses import JSONResponse
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sys
import sys
import os
import json
from datetime import timedelta
from typing import Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import create_tables, add_user, add_data, engine, add_log
from src.extract_data import extraire_donnees
from app.auth import auth
from app.auth.auth import authenticate_user, create_access_token, get_current_active_user, get_current_user
from app.auth.models import User
from app.auth.models import Token
from app.helpers.helpers import save_uploaded_file, extract_data_from_file, add_data_to_database, convert_dataframes_to_json

app = FastAPI()

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

@app.get("/")
def read_root():
    return {"message": "Welcome to my FastAPI User Authentication!"}

@app.post("/process")
async def create_item(
    file: UploadFile = File(...),
    current_user: bool = Depends(get_current_user)  # Using the dependency
):
    try:
        file_location = await save_uploaded_file(file)
        extract_result = extract_data_from_file(file_location)

        add_data_to_database(engine, extract_result)
        data = convert_dataframes_to_json(extract_result)

        if data is None:
            add_log(datetime.datetime.now(), file_location, extract_result["erreur"])
            return JSONResponse(content={"status": "error", "erreur": extract_result["erreur"], "data": None})
        else:
            return JSONResponse(content={"status": "success", "erreur": None, "data": data})

    except HTTPException as http_exception:
        add_log(datetime.datetime.now(), file.filename, http_exception.detail)
        return JSONResponse(content={"status": "error", "erreur": http_exception.detail, "data": None})
    except Exception as e:
        add_log(datetime.datetime.now(), file.filename, str(e))
        return JSONResponse(content={"status": "error", "erreur": str(e), "data": None})
