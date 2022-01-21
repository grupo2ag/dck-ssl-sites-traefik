import os
import json
import requests

def recebe_lista_ufs(token):

    URL = os.getenv("UF_URL")

    if URL == None:
        URL = "http://165.227.106.74:9117/api/v1/uf"

 
    resposta    = requests.get(URL, timeout = 15, headers={'Authorization':token})
    str_content = (resposta.content).decode()
    ufs = json.loads(str_content)
    

    if resposta.status_code != 200 or ufs == []:
        print("Erro:",resposta.status_code)
        print("Resposta:", resposta)
        return None
    
    for uf in ufs: [uf.pop(key) for key in ["id","codIbge"]]
    
    return ufs


def recebe_lista_municipios(token,sigla):
    URL = os.getenv("UF_LISTA_MCP")

    if URL == None:
        URL = "http://165.227.106.74:9117/api/v1/municipio"
    

    URL = URL+"/"+sigla
    page_size = {"pageSize":"1000"}
    resposta    = requests.get(URL, timeout = 15, headers={'Authorization':token}, params = page_size)

    conteudo = (resposta.content).decode()
    cod      = resposta.status_code
    
    if cod != 200:
        print (conteudo, cod)
        return None,500

    municipios = json.loads(conteudo)["content"]
    return municipios,cod

def recebe_municipio_cod_denatran(cod_denatran,token):
   
    URL = os.getenv("UF_MCP_COD")

    if URL == None:
        URL = "http://165.227.106.74:9117/api/v1/municipio/cod-denatran"

    if isinstance(cod_denatran,int):
        URL = URL+"/"+str(cod_denatran)
    else: 
        return None

    resposta    = requests.get(URL, timeout = 15, headers={'Authorization':token})
    
    conteudo = (resposta.content).decode()
    cod      = resposta.status_code
    
    if cod != 200:
        print (conteudo, cod)
        return None

    municipio = json.loads(conteudo)["nomeMunicipio"]

    return municipio

def nome_cod_uf(cod,lista):  
    for uf in lista:
        if uf["codDenatran"] == cod:
            return uf["nome"]
    
    return None
