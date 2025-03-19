import os
from typing import Annotated
from fastapi.responses import JSONResponse
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sys
import sys
import os
from datetime import timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import create_tables, add_user
from src.extract_data import extract_data_raw
from app.auth import auth
from app.auth.auth import authenticate_user, create_access_token, get_current_active_user, get_current_user
from app.auth.models import User
from app.auth.models import Token

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
    os.makedirs("temp", exist_ok=True)
    file_location = f"temp/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())

    if not os.path.exists(file_location):
        return JSONResponse(content={"status": "error", "erreur": "file not saved correctly"})

    print(f"File saved at {file_location}")
    extract = extract_data_raw(file_location)
    # TODO: ajouter le post traitement des donnnées pour les ajouter en base de données
    return JSONResponse(content=extract)
