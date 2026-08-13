#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Flask pour MoussaConsulting / appeloffres.net
- Authentification par identifiant + mot de passe (JWT)
- Extraction des annonces BOAMP filtrées par secteur et par période
Déployé sur Vercel en tant que fonction Python unique (api/index.py),
toutes les routes /api/* sont routées ici (voir vercel.json).
"""

import os
import sys
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime, timedelta, timezone
from functools import wraps

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

APP_USERNAME = os.environ.get("APP_USERNAME", "admin")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "changeme")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me-in-production")
TOKEN_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", "28800"))  # 8h

SOURCE_ID_BOAMP = 1674
BOAMP_PDF_BASE_URL_PIAMP = "https://www.boamp.fr/telechargements/FILES/PDF"
BOAMP_PDF_BASE_URL_LEGACY = "https://www.boamp.fr/telechargements/PDF"
AVIS_ID_APPEL_OFFRES = 1
AVIS_ID_AVIS_ATTRIBUTION = 8
COUNTRY_ID_FRANCE = 70
BOAMP_API_URL = "https://www.boamp.fr/api/explore/v2.1/catalog/datasets/boamp/records"

# Secteurs proposés dans l'interface -> mots-clés de filtrage
# (le dataset BOAMP n'expose pas un champ "secteur" unique et fiable,
# on filtre donc sur l'objet + les descripteurs)
SECTEURS = {
    "tous": {"label": "Tous secteurs", "keywords": []},
    "btp": {
        "label": "BTP / Travaux",
        "keywords": ["travaux", "batiment", "bâtiment", "construction", "voirie",
                     "reseaux", "réseaux", "genie civil", "génie civil", "rénovation",
                     "renovation", "chantier"],
    },
    "informatique": {
        "label": "Informatique / Télécom",
        "keywords": ["informatique", "logiciel", "numerique", "numérique",
                     "reseau informatique", "telecom", "télécom", "cybersecurite",
                     "cybersécurité", "systeme d'information", "système d'information",
                     "developpement", "développement", "cloud"],
    },
    "services": {
        "label": "Services",
        "keywords": ["prestation de services", "service", "nettoyage", "gardiennage",
                     "conseil", "formation", "maintenance"],
    },
    "fournitures": {
        "label": "Fournitures",
        "keywords": ["fourniture", "achat de materiel", "achat de matériel",
                     "equipement", "équipement", "mobilier"],
    },
    "sante": {
        "label": "Santé",
        "keywords": ["sante", "santé", "hopital", "hôpital", "medical", "médical",
                     "pharmaceutique", "soins"],
    },
    "transport": {
        "label": "Transport",
        "keywords": ["transport", "logistique", "vehicule", "véhicule", "flotte"],
    },
    "environnement": {
        "label": "Environnement / Énergie",
        "keywords": ["environnement", "energie", "énergie", "dechet", "déchet",
                     "eau", "assainissement", "recyclage"],
    },
}


# ============================================================
# AUTH (JWT maison, sans dépendance externe)
# ============================================================

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(username: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_token(token: str):
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(signature_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentification requise"}), 401
        token = auth_header[len("Bearer "):]
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Session invalide ou expirée"}), 401
        request.user = payload.get("sub")
        return f(*args, **kwargs)
    return wrapper


# ============================================================
# TRANSFORMATION BOAMP -> APPELOFFRES.NET  (logique d'origine conservée)
# ============================================================

def format_date(date_str):
    if not date_str:
        return None
    try:
        if "T" in str(date_str):
            return date_str
        return f"{date_str}T00:00:00.000Z"
    except Exception:
        return None


def format_date_with_time(date_str):
    if not date_str:
        return None
    try:
        date_str = str(date_str)
        if "T" in date_str:
            return date_str
        return f"{date_str}T12:00:00.000Z"
    except Exception:
        return None


def get_date_limite(record):
    date_limite_fields = [
        "datelimitereponse",
        "datelimitereponsemapa",
        "datefindiffusion",
        "datelimiteremisecandidatures",
        "datelimiteremiseoffres",
    ]
    for field in date_limite_fields:
        if record.get(field):
            return record.get(field)
    return None


def record_matches_secteur(record, secteur_key):
    if secteur_key not in SECTEURS or secteur_key == "tous":
        return True
    keywords = SECTEURS[secteur_key]["keywords"]
    if not keywords:
        return True
    haystack = " ".join([
        str(record.get("objet", "")),
        str(record.get("descripteurslibelles", "")),
    ]).lower()
    return any(kw in haystack for kw in keywords)


def transform_to_offre(record):
    nature_boamp = record.get("nature", "")
    offre_type = "international" if "international" in str(nature_boamp).lower() else "national"

    type_marche = record.get("typemarche", "")
    offre_nature = "prive" if "prive" in str(type_marche).lower() else "public"

    objet = record.get("objet", "") or "Sans titre"
    title = objet[:250] if len(objet) > 250 else objet

    batches = [{
        "title": title,
        "deposit": "0",
        "activitiesIds": [461],
    }]

    addresses = [{"countryId": str(COUNTRY_ID_FRANCE)}]
    images = ["default.jpg"]

    publication_date = format_date(record.get("dateparution"))
    date_limite = get_date_limite(record)
    expiration_date = format_date_with_time(date_limite)
    avis_id = AVIS_ID_APPEL_OFFRES if date_limite else AVIS_ID_AVIS_ATTRIBUTION

    id_web = record.get("idweb", "")
    url_detail = f"https://www.boamp.fr/avis/detail/{id_web}" if id_web else ""
    source_id = str(id_web) if id_web else str(int(datetime.now().timestamp()))

    pdf_url = None
    if id_web:
        source_schema = record.get("source_schema", "")
        date_parution = record.get("dateparution", "")
        if date_parution:
            parts = date_parution.split("-")
            year = parts[0] if len(parts) >= 1 else ""
            month = parts[1] if len(parts) >= 2 else ""
            if year:
                if source_schema and source_schema.startswith("3"):
                    if month:
                        pdf_url = f"{BOAMP_PDF_BASE_URL_PIAMP}/{year}/{month}/{id_web}.pdf"
                else:
                    filename = record.get("filename", "")
                    if filename:
                        pdf_url = f"{BOAMP_PDF_BASE_URL_LEGACY}/{year}/{filename}/{id_web}.pdf"

    return {
        "source_id": source_id,
        "source_type": "BOAMP",
        "avis_id": avis_id,
        "api_source_id": SOURCE_ID_BOAMP,
        "title": title,
        "description": record.get("descripteurslibelles", "") or objet,
        "publication_date": publication_date,
        "start_bidding_date": publication_date,
        "expiration_date": expiration_date,
        "opening_bids_date": expiration_date,
        "type": offre_type,
        "nature": offre_nature,
        "is_enabled": True,
        "is_multi_currency": False,
        "specifications_price": "0",
        "specifications_receiving_address": "En ligne",
        "offer_validity_periode": 30,
        "funding_source_type": "national",
        "funding_source": record.get("nomacheteur", "") or "Budget national",
        "images": images,
        "batches": batches,
        "addresses": addresses,
        "url": url_detail,
        "pdf_url": pdf_url,
        "promoter_name": record.get("nomacheteur", "") or "Acheteur BOAMP",
    }


def scrape_boamp(date_debut, date_fin, secteur_key="tous", max_pages=20):
    all_results = []
    seen_source_ids = set()
    offset = 0
    limit = 100
    pages = 0

    while pages < max_pages:
        params = {
            "where": f"dateparution >= '{date_debut}' AND dateparution <= '{date_fin}'",
            "limit": limit,
            "offset": offset,
        }
        response = requests.get(BOAMP_API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            break

        for record in results:
            if not record_matches_secteur(record, secteur_key):
                continue
            offre = transform_to_offre(record)
            if offre["source_id"] not in seen_source_ids:
                seen_source_ids.add(offre["source_id"])
                all_results.append(offre)

        if len(results) < limit:
            break

        offset += limit
        pages += 1

    return {
        "date_debut": date_debut,
        "date_fin": date_fin,
        "secteur": secteur_key,
        "total": len(all_results),
        "results": all_results,
    }


# ============================================================
# ROUTES
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/secteurs", methods=["GET"])
def list_secteurs():
    return jsonify([
        {"key": key, "label": value["label"]} for key, value in SECTEURS.items()
    ])


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    if not hmac.compare_digest(username, APP_USERNAME) or not hmac.compare_digest(password, APP_PASSWORD):
        return jsonify({"error": "Identifiant ou mot de passe incorrect"}), 401

    token = create_token(username)
    return jsonify({"token": token, "username": username, "expires_in": TOKEN_TTL_SECONDS})


@app.route("/api/scrape", methods=["POST"])
@require_auth
def scrape():
    data = request.get_json(silent=True) or {}
    date_debut = data.get("date_debut")
    date_fin = data.get("date_fin")
    secteur_key = data.get("secteur", "tous")
    # Pagination params (optional)
    try:
        page = int(data.get("page", 1))
    except Exception:
        page = 1
    try:
        per_page = int(data.get("per_page", 50))
    except Exception:
        per_page = 50

    if not date_debut or not date_fin:
        return jsonify({"error": "date_debut et date_fin sont requis (format YYYY-MM-DD)"}), 400

    if secteur_key not in SECTEURS:
        return jsonify({"error": f"Secteur inconnu: {secteur_key}"}), 400

    try:
        result = scrape_boamp(date_debut, date_fin, secteur_key)
        # Apply simple pagination to results
        total = result.get("total", 0)
        results = result.get("results", [])
        # Ensure sane values
        if per_page <= 0:
            per_page = 50
        if page <= 0:
            page = 1
        start = (page - 1) * per_page
        end = start + per_page
        paged = results[start:end]
        total_pages = (total + per_page - 1) // per_page if per_page else 1

        return jsonify({
            "date_debut": result.get("date_debut"),
            "date_fin": result.get("date_fin"),
            "secteur": result.get("secteur"),
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "results": paged,
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Erreur lors de l'appel à l'API BOAMP: {e}"}), 502


# Point d'entrée local (non utilisé par Vercel, utile pour tester en local)
if __name__ == "__main__":
    app.run(port=5000, debug=True)
