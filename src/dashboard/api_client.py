import requests

API_BASE_URL = "http://127.0.0.1:8000/api/v1"


def get_company(company_id):
    url = f"{API_BASE_URL}/companies/{company_id}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def get_company_pl(company_id):
    url = f"{API_BASE_URL}/companies/{company_id}/pl"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def get_company_bs(company_id):
    url = f"{API_BASE_URL}/companies/{company_id}/bs"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def get_company_cashflow(company_id):
    url = f"{API_BASE_URL}/companies/{company_id}/cashflow"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def get_company_ratios(company_id):
    url = f"{API_BASE_URL}/companies/{company_id}/ratios"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def get_company_sector(company_id):
    url = f"{API_BASE_URL}/companies/{company_id}/sector"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def get_company_peers(company_id):
    url = f"{API_BASE_URL}/companies/{company_id}/peers"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def get_company_pros_cons(company_id):
    url = f"{API_BASE_URL}/companies/{company_id}/pros-cons"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()