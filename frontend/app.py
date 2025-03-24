from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import requests
import base64
import os
import sys
import dotenv
dotenv.load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("SUPER_SECRET_KEY")
app.static_folder = 'static'

FASTAPI_URL = "http://localhost:8000"  # Update if your FastAPI app is running elsewhere

# Serve static files from the 'temp' directory
temp_dir = os.path.join(app.root_path, '..', 'temp')
@app.route('/temp/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(temp_dir, filename)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form_data = {"username": request.form["username"], "password": request.form["password"]}
        response = requests.post(f"{FASTAPI_URL}/token", data=form_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            session["token"] = token
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/")
def index():
    return redirect(url_for("upload"))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    token = session.get("token")
    if not token:
        return redirect(url_for("login"))
    # check if the token is still valid
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{FASTAPI_URL}/", headers=headers)
    if response.status_code == 401:
        return redirect(url_for("logout"))

    if request.method == "POST":
        file = request.files["file"]
        if file:
            headers = {"Authorization": f"Bearer {token}"}
            try:
                response = requests.post(f"{FASTAPI_URL}/process", files={"file": (file.filename, file.stream)}, headers=headers)
                if response.status_code == 401:
                    return redirect(url_for("logout"))
                response.raise_for_status()
                result = response.json()
                achat = result["data"]["achat"]
                client = result["data"]["client"]
                client[0]["birthdate"] = client[0]["birthdate"].split("T")[0]
                facture = result["data"]["facture"]
                produit = result["data"]["produit"]
                filename = file.filename
                return render_template("upload.html", achat=achat, client=client, facture=facture, produit=produit, image_filename=filename)
            except requests.exceptions.RequestException as e:
                return render_template("upload.html", error=str(e))

    return render_template("upload.html")


@app.route("/logout")
def logout():
    session.pop("token", None)
    return redirect(url_for("login"))

@app.route("/factures")
def factures():
    token = session.get("token")
    if not token:
        return redirect(url_for("login"))
    headers = {"Authorization": f"Bearer {token}"}
    sort = request.args.get("sort")
    order = request.args.get("order")
    params = {}
    if sort:
        params["sort"] = sort
    if order:
        params["order"] = order
    try:
        response = requests.get(f"{FASTAPI_URL}/factures", headers=headers, params=params)
        if response.status_code == 401:
            return redirect(url_for("logout"))
        response.raise_for_status()
        factures = response.json()
        return render_template("factures.html", factures=factures)
    except requests.exceptions.RequestException as e:
        return render_template("factures.html", error=str(e))
    
@app.route("/factures/<id_facture>")
def facture(id_facture):
    token = session.get("token")
    if not token:
        return redirect(url_for("login"))
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{FASTAPI_URL}/factures/{id_facture}", headers=headers)
        if response.status_code == 401:
            return redirect(url_for("logout"))
        response.raise_for_status()
        result = response.json()

        # Process response data
        facture = result["facture"]
        facture["date_facturation"] = facture["date_facturation"].split("T")[0]
        client = result["client"]
        client["birthdate"] = client["birthdate"].split("T")[0]
        products = [
            {
                "id_produit": p["product"]["id_produit"],
                "nom": p["product"]["nom"],
                "prix": p["product"]["prix"],
                "quantite": p["quantity"],
            }
            for p in result["products"]
        ]

        return render_template(
            "facture.html",
            facture=facture,
            client=client,
            produit=products,
        )
    except requests.exceptions.RequestException as e:
        return render_template("facture.html", error=str(e))

if __name__ == "__main__":
    app.run(debug=True)
