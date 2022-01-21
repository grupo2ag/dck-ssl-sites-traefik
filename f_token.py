import os
import requests
import base64
import time
import json

def gera_token():
    GRANTTYPE = os.getenv('TOK_GRANTTYPE')
    LOGIN     = os.getenv('TOK_LOGIN')
    REALM     = os.getenv('TOK_REALM')
    SCOPE     = os.getenv('TOK_SCOPE')
    PASS      = os.getenv('TOK_PASS')
    URL       = os.getenv('TOK_URL')

    body = {                           
            "grantType":GRANTTYPE,
            "login":    LOGIN,    
            "realm":    REALM,     
            "scope":    SCOPE,     
            "senha":    PASS       
            }
    

    if URL is None: 
        URL = "https://auth.autocrivo.com.br:8443/api/auth"

    resposta = requests.post(URL,json=body)

    if resposta.status_code in [200,201]:
        return resposta.content
    else:
        print("conteudo:",resposta.content)
        print("Código:", resposta.status_code)
        return None

def valida_token(token):
    URL    = os.getenv('AUTH_URL')
    
    if URL is None: 
        URL = "https://auth.autocrivo.com.br:8443/api/auth"

    resposta = requests.get(URL, timeout = 15, headers={'Authorization': token})
    
    if resposta.status_code in [200,201]:
        return True
    else:
        return False

def verifica_validade(token):
    token = str(token)
    payload = token.split(".")[1]
    payload += "=" * ((4 - len(payload) % 4) % 4)
    payload = base64.b64decode(payload).decode("utf-8")
    exp     = json.loads(payload)["exp"]

    if exp > time.time():
        return True
    else:
        return False
