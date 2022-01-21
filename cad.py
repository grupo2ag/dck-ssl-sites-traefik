from f_db import *
from f_token import *
from f_ufs import *
from modelos import *



from flask_restplus import Api, Resource
from flask_cors import CORS, cross_origin
from flask import request,Flask
#import unicodedata 
import datetime
import requests
import base64
import json
import time
#import os

class Flask_db(Flask):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.conexao_db = conecta_banco()
        self.token      = gera_token()
        self.lista_ufs  = recebe_lista_ufs(self.token)
        self.dic_cnaes  = recebe_lista_cnae(self.token)
        self.lista_if   = recebe_if(self.token)
        # self.nat_jur  = recebe_nat_jur(self.token)

class Server():
    def __init__(self,):
        self.app = Flask_db(__name__)
        CORS(self.app,  allow_headers='*', origins='*')
        self.app.config['CORS_HEADERS'] = 'Content-Type'
        self.api = Api(self.app,
                       version     = "1.0",
                       title       = "Cadastro de Clientes",
                       description = "API para cadastro de clientes",
                       doc         = "/docs"
                       )
    def run (self,):
        self.app.run(debug = True)

def verifica_cnpj(conexao,doc):

    select_query = '''SELECT  cpj.id, cpj.nr_doc_contrato as nr_doc, cpj.razao_social, cpj.nome_fantasia, cpj.ddd_fone, cpj.nr_fone, cpj.email, cpj.inscricao_estadual, cpj.inscricao_municipal, cpj.site, cpj.data_abertura, cpj.data_atualizacao_rfb, cpj.ek_natureza_juridica as natureza_juridica,
                              sts.STATUS_CRM as status_rfb, 
                              cne.ek_cnae_id as cnae_primario FROM tb_contratante_pj cpj
                      LEFT JOIN tb_status_crm   sts ON cpj.fk_status_crm_id     = sts.ID
                      LEFT JOIN tb_cnae_cliente cne ON cne.fk_contratante_pj_id = cpj.id
                      WHERE cpj.nr_doc_contrato = (%s) AND cne.flag_primario = 1'''

    param = tuple([doc])

    with conexao.cursor(dictionary=True) as cursor:                                                                                    
        try:                                
            cursor.execute(select_query,param)
            result = cursor.fetchone()
        except Exception as e:
            print ("\nFalha na query:",cursor.statement )
            print("Erro: ",e,"\n")
            return None,None,500
    if result:
        result["data_abertura"]        = result["data_abertura"].strftime("%Y-%m-%d")
        result["data_atualizacao_rfb"] = result["data_atualizacao_rfb"].strftime("%Y-%m-%d")
        result["natureza_juridica"] = str(result["natureza_juridica"]) # Provisório
        return True,result,200
    else:
        return False,None,200

def verifica_cpf(conexao,doc): 

    fk_status_ativo = 32
    select_query = '''SELECT pct.nome, pct.data_nascimento, pct.ddd_cel, pct.nr_cel, pct.ddd_fone, pct.nr_fone, pct.email, pct.profissao, pct.nr_rg, pct.Expedidor_rg,
                             cpf.nr_doc_contratante as nr_doc, cpf.data_atualizacao_rfb,
                             sts.STATUS_CRM as status_rfb, 
                             cls.CLASSE_CRM as estado_civil
                      FROM tb_contratante_pf cpf 
                      INNER JOIN tb_pessoa_contato pct ON cpf.fk_pessoa_contato_id = pct.id 
                      LEFT JOIN tb_status_crm      sts ON cpf.fk_status_crm_id     = sts.ID
                      LEFT JOIN tb_classe_crm      cls ON cpf.fk_classe_crm_id     = cls.ID
                      WHERE cpf.nr_doc_contratante = (%s) AND pct.fk_status_crm_id = (%s)'''

    param = tuple([doc,fk_status_ativo])

    with conexao.cursor(dictionary=True) as cursor:                                                                                    
        try:                                
            cursor.execute(select_query,param)
            result = cursor.fetchone()  
        except Exception as e:
            print ("\nFalha na query:",cursor.statement )
            print("Erro: ",e,"\n")
            return None,None,500
    if result:
        result["data_nascimento"]      = result["data_nascimento"].strftime("%Y-%m-%d")
        result["data_atualizacao_rfb"] = result["data_atualizacao_rfb"].strftime("%Y-%m-%d")
        return True,result,200 
    else:
        return False,None,200

def insere_cnae(conexao,fks_cnae,id_ctpj,atual):

    template = [" (default,%s,%s,%s,%s)"]
    n = len(fks_cnae)
    template_completo = ",".join(template*n)

    
    insert_query = '''INSERT INTO tb_cnae_cliente (id, flag_primario, data_hora_insert , ek_cnae_id , fk_contratante_pj_id) 
                    VALUES '''
    
    insert_query = insert_query + template_completo      

    lista_cnae = [True,atual,fks_cnae[0],id_ctpj]
    
    for c in fks_cnae[1:]:
        lista_cnae.extend([False, atual, c, id_ctpj])

    param = tuple (lista_cnae)
    
    with conexao.cursor() as cursor:
        try:
            cursor.execute(insert_query,param)
            conexao.commit()
            ult_ids = ultimos_ids(conexao,"tb_cnae_cliente",n)
            return "Sucesso",200,ult_ids
        except Exception as e:
            print("Falha na query: ", cursor.statement )
            print("Erro:",e,"\n")
            msg,cod = cod_erro( str(e)[0:4] )
            return msg,cod,[]

def insere_pessoas_contato(conexao,pessoas_contato,id_ctr,atual):
    fk_status_registro_ativo = 32
    n = len(pessoas_contato)

    template = [" (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"]
    template_completo = ",".join(template*n)

    
    insert_query = '''INSERT INTO tb_pessoa_contato (id, nr_doc_pessoa, nome, data_nascimento, ddd_cel, nr_cel, ddd_fone, nr_fone, email, profissao, nr_rg, Expedidor_rg, data_hora_insert, fk_contrato_id, fk_classe_crm_id, fk_status_crm_id) 
                    VALUES '''
    
    insert_query = insert_query + template_completo      
    
    lista_pessoa = []
    for p in pessoas_contato:
        lista = [p["nr_doc"], p["nome"], p["data_nascimento"], p["ddd_cel"], p["nr_cel"], p["ddd_fone"], p["nr_fone"], p["email"], p["profissao"], p["nr_rg"], p["expedidor_rg"], atual,id_ctr, p["perfil"],fk_status_registro_ativo]
        lista_pessoa.extend(lista)

    param = tuple (lista_pessoa)

    with conexao.cursor() as cursor:
        try:
            cursor.execute(insert_query,param)
            conexao.commit()
            ult_ids = ultimos_ids(conexao,"tb_pessoa_contato",n)
            return "Sucesso",200,ult_ids
        except Exception as e:
            print("Falha na query: ", cursor.statement )
            print("Erro:",e,"\n")
            msg,cod = cod_erro( str(e)[0:4] )
            return msg,cod,[]

def insere_enderecos(conexao,endereco,id_ctr,atual):
    fk_status_registro_ativo = 32
    n = len(endereco)

    template = [" (default,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"]
    template_completo = ",".join(template*n)

    
    insert_query = '''INSERT INTO tb_endereco (ID, CEP, ENDERECO, BAIRRO, NUMERO, COMPLEMENTO, DATA_HORA_INSERT, EK_SIGLA_UF_ID, EK_MUNICIPIO_ID, FK_CONTRATO_ID, FK_CLASSE_CRM_ID, FK_STATUS_CRM_ID ) 
                    VALUES '''
    
    insert_query = insert_query + template_completo      
    
    linta_end = []
    for end in endereco:
        lista = [end["cep"], end["endereco"], end["bairro"], end["numero"], end["complemento"],atual, end["uf"], end["municipio"],id_ctr, end["classe"],fk_status_registro_ativo]
        linta_end.extend(lista)

    param = tuple (linta_end)

    with conexao.cursor() as cursor:
        try:
            cursor.execute(insert_query,param)
            conexao.commit()
            ult_ids = ultimos_ids(conexao,"tb_endereco",n)
            return "Sucesso",200,ult_ids
        except Exception as e:
            print("Falha na query: ", cursor.statement )
            print("Erro:",e,"\n")
            msg,cod = cod_erro( str(e)[0:4] )
            return msg,cod,[]

def recebe_if(token):
    #URL = os.getenv("IF_URL")

    #if URL == None:
    #    URL = ""

    ##page_size = {"pageSize":"1000"}
    #resposta    = requests.get(URL, timeout = 15, headers={'Authorization':token}) #, params = page_size)
    #
    #conteudo = (resposta.content).decode()
    #cod      = resposta.status_code
    #    

    #if cod != 200:
    #    print (conteudo, cod)
    #    return "Erro interno",500,None
    #
    #lista_if = json.loads(conteudo)["content"]
    #for f in lista_if:
    #    f["indice"] = f.pop("indice_financeiro")
    #    # f.pop("outros")

    #return lista_if
    return [{"id":1, "indice":"IGP-M"}]

def recebe_id_cnae(lista_cod_cnae,dic_cnae):

    lista_fk_cnae = []
    
    for cod in lista_cod_cnae:
        for j in dic_cnae.keys():
            if dic_cnae[j]["cod"] == cod :
                lista_fk_cnae.append(j)

    if len(lista_fk_cnae)!=len(lista_cod_cnae):
        return 404,None
    
    return 200,lista_fk_cnae

def recebe_lista_cnae(token):
    URL = os.getenv("CNAE_URL")

    if URL == None:
        URL = "http://165.227.106.74:9117/api/v1/atividade-economica"

    page_size = {"pageSize":"1000"}
    resposta    = requests.get(URL, timeout = 15, headers={'Authorization':token}, params = page_size)
    
    conteudo = (resposta.content).decode()
    cod      = resposta.status_code
        

    if cod != 200:
        print (conteudo, cod)
        return "Erro interno",500,None
    
    lista_cnae = json.loads(conteudo)["content"]
    dic_cnae   = {}

    
    for c in lista_cnae:
        dic_cnae[ c["id"]  ] = {"cod": c["cdAtividadeEconomoca"], "desc":c["dsAtividadeEconomica"]}
    
    return dic_cnae

def cod_status_rfb(str_status):

    cod_status_rfb = {"ativo":15,"baixado":16, "inapto":17,"suspenso":18,"nulo":19}

    str_status = str_status.lower()

    cod_status = None

    for k in cod_status_rfb:
        if str_status[0] == k[0]:
            cod_status = cod_status_rfb[k]

    return cod_status


def main ():
    server = Server()
    app = server.app
    api = server.api

    m_completo_pf,m_completo_pj = cria_modelos(api)

    @app.before_request
    def verifica():
        if request.method == 'OPTIONS':
            return {}, 200
        
        token = request.headers.get('Authorization')

        if not valida_token(token):
            return {"message":"Não autorizado"},401
        else:
            payload_b64 = token.split(".")[1]
            payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
            payload_str = base64.b64decode(payload_b64).decode("utf-8")
            payload     = json.loads(payload_str)
            
            if "ctr_id" not in payload:
                return {"message":"Token inválido"},400
            
            app.ctr_id  = payload["ctr_id"] 
            app.matriz  = payload["matriz"]

        app.conexao_db = verifica_conexao(app.conexao_db)
        if app.conexao_db is None:
            return {"message":"Erro interno"},500
        

    @cross_origin
    @api.route('/verifica_cnpj') 
    class Verifica_CNPJ(Resource):
        def get(self,):
            parametros = request.args
            doc        = parametros.get('doc')

            cadastrado,dados,cod = verifica_cnpj(app.conexao_db,doc) 
            
            if dados:
                id_cpj = dados.pop("id")

                dados["cnaes_secundarios"] = pesquisa(app.conexao_db,"tb_cnae_cliente",["fk_contratante_pj_id","flag_primario"],[id_cpj,False],"ek_cnae_id")
                
                dados["cnae_primario"] = app.dic_cnaes[dados["cnae_primario"]]["cod"] + " " + app.dic_cnaes[dados["cnae_primario"]]["desc"]


                for i in range(len(dados["cnaes_secundarios"])):
                    dados["cnaes_secundarios"][i] = app.dic_cnaes[ dados["cnaes_secundarios"][i]["ek_cnae_id"] ]["cod"] + " " + app.dic_cnaes[ dados["cnaes_secundarios"][i]["ek_cnae_id"] ]["desc"] 
                            

            if cod != 200:
                return "Erro interno", 500

            return {"cadastrado":cadastrado,"dados":dados },cod
    
    @cross_origin
    @api.route('/verifica_cpf') 
    class Verifica_CPF(Resource):
        def get(self,):
            parametros = request.args
            doc        = parametros.get('doc')

            cadastrado,dados,cod = verifica_cpf(app.conexao_db,doc) 
            
            if cod != 200:
                return "Erro interno", 500

            return {"cadastrado":cadastrado,"dados":dados },cod

    @cross_origin
    @api.route('/cadastro_pj')   
    class Cadastro_Pj(Resource):

        def get(self,):

            grupo_perfil_contrato     = 15
            grupo_perfil_pesctt       = 2
            grupo_perfil_ctpj         = 17
            grupo_endereco            = 4
            
            dic_param = {}

            perfis_contrato =       pesquisa(app.conexao_db,"tb_classe_crm","FK_GRUPO_CRM_ID",grupo_perfil_contrato,["id","classe_crm"])
            pessoas_contato =       pesquisa(app.conexao_db,"tb_classe_crm","FK_GRUPO_CRM_ID",grupo_perfil_pesctt,["id","classe_crm"])
            perfis_contratante_pj = pesquisa(app.conexao_db,"tb_classe_crm","FK_GRUPO_CRM_ID",grupo_perfil_ctpj,["id","classe_crm"])
            classe_endereco       = pesquisa(app.conexao_db,"tb_classe_crm","FK_GRUPO_CRM_ID",grupo_endereco,["id","classe_crm"])

            dic_param["indices_financeiros"]      = app.lista_if
            dic_param["perfis_contrato"]          = perfis_contrato
            dic_param["perfis_contratante_pj"]    = perfis_contratante_pj 
            dic_param["perfis_pessoa_contato"]    = pessoas_contato
            dic_param["classes_endereco"]         = classe_endereco

            for dic in perfis_contrato:
                 dic["perfil"] = dic.pop("classe_crm")
            for dic in pessoas_contato:
                dic["perfil"] = dic.pop("classe_crm")
            for dic in perfis_contratante_pj:
                dic["perfil"] = dic.pop("classe_crm")
            for dic in classe_endereco:
                dic["classe"] = dic.pop("classe_crm")


            return dic_param

        @api.expect(m_completo_pj,validate=True)  
        def post(self,):

            if not verifica_validade(app.token):
                app.token = gera_token()

            registro  = api.payload
            dic_cnaes = app.dic_cnaes
            lista_ufs = app.lista_ufs
            lista_ufs = [x["codDenatran"] for x in lista_ufs]

            fk_status_contrato_ativo = 1
            fk_status_registro_ativo = 32

            contrato        = registro["contrato"]
            cond_comercial  = registro["condicao_comercial"]
            contratante_pj  = registro["contratante_pj"]
            pessoas_contato = registro["pessoa_contato"]
            enderecos       = registro["endereco"]

            # Validações
            for end in enderecos:
                if recebe_municipio_cod_denatran(end["municipio"],app.token) == None:
                    return "Código de município não encontrado",404
                
                if end["uf"] not in lista_ufs: 
                    return "Código de UF não encontrado",404
    
            atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
            

            contratante_pj["status_cadastro_rfb"] = cod_status_rfb(contratante_pj["status_cadastro_rfb"])

            if not contratante_pj["status_cadastro_rfb"]:
                return "Status de cadastro na receita federal inválido",400

            # Cod CNAE para EK
            lista_cod_cnae = [contratante_pj["cnae_primario"]]           
            lista_cod_cnae.extend(contratante_pj["cnaes_secundarios"])  
            
            cod,fks_cnae  = recebe_id_cnae(lista_cod_cnae,dic_cnaes) 
            if cod != 200:
                return "Códigos de CNAE informados inválidos",cod

            # Contrato
            msg,cod,id_ctr = insere(app.conexao_db,"tb_contrato", ["ek_indice_financeiro_id" ,    "data_hora_insert", "fk_classe_crm_id" ,         "fk_status_crm_id"],
                                                                  [ contrato["indice_financeiro"], atual,              contrato["perfil_contrato"], fk_status_contrato_ativo  ] )
            if cod != 200:
                return msg,cod

            # Condição Comercial
            msg,cod,id_condcom = insere(app.conexao_db,"tb_condicao_comercial", ["dia_vencimento" ,                "valor_adesao" ,                "flag_cobranca_integral" ,                "flag_taxa_extra_anual" ,                "data_hora_insert",  "ek_carteira_id",              "ek_pacote_venda_id",           "fk_contrato_id" , "fk_status_crm_id"        ],
                                                                                [ cond_comercial["dia_vencimento"], cond_comercial["valor_adesao"], cond_comercial["flag_cobranca_integral"], cond_comercial["flag_taxa_extra_anual"], atual,               cond_comercial["carteira_id"], cond_comercial["pacote_venda"], id_ctr,            fk_status_registro_ativo ] )
            if cod != 200:
                deleta(app.conexao_db,"tb_contrato",id_ctr)
                return msg,cod
            
            # Contratante_pj
            msg,cod,id_ctpj = insere(app.conexao_db,"tb_contratante_pj",["nr_doc_contrato" ,     "razao_social" ,                 "nome_fantasia" ,                "ddd_fone" ,                "nr_fone" ,                "email" ,                "inscricao_estadual" ,                "inscricao_municipal" ,                "site" ,                "data_abertura",                 "data_hora_insert" , "data_atualizacao_rfb" ,                "ek_natureza_juridica" ,             "fk_contrato_id" ,"fk_classe_crm_id" ,      "fk_status_crm_id"                      ], 
                                                                        [contratante_pj["nr_doc"], contratante_pj["razao_social"], contratante_pj["nome_fantasia"], contratante_pj["ddd_fone"], contratante_pj["nr_fone"], contratante_pj["email"], contratante_pj["inscricao_estadual"], contratante_pj["inscricao_municipal"], contratante_pj["site"], contratante_pj["data_abertura"], atual,               contratante_pj["data_atualizacao_rfb"], contratante_pj["natureza_juridica"], id_ctr,           contratante_pj["perfil"], contratante_pj["status_cadastro_rfb" ] ] )
            if cod != 200:
                deleta(app.conexao_db,"tb_condicao_comercial",id_condcom) 
                deleta(app.conexao_db,"tb_contrato",id_ctr) 
                return msg,cod
            
            # Endereço
            msg,cod,ids_end  = insere_enderecos(app.conexao_db,enderecos,id_ctr,atual)

            if cod != 200:
                deleta(app.conexao_db,"tb_contratante_pj",id_ctpj) 
                deleta(app.conexao_db,"tb_condicao_comercial",id_condcom)
                deleta(app.conexao_db,"tb_contrato",id_ctr) 
                return msg,cod
            
            # Pessoa de contato 
            if pessoas_contato:
                msg,cod,ids_pesctt= insere_pessoas_contato(app.conexao_db,pessoas_contato,id_ctr,atual)
                if cod != 200:
                    deleta(app.conexao_db,"tb_endereco",ids_end)  
                    deleta(app.conexao_db,"tb_condicao_comercial",id_condcom) 
                    deleta(app.conexao_db,"tb_contratante_pj",id_ctpj) 
                    deleta(app.conexao_db,"tb_contrato",id_ctr) 
                    return msg,cod

            # CNAE
            msg,cod,_ = insere_cnae(app.conexao_db,fks_cnae,id_ctpj,atual) 
            if cod != 200:
                deleta(app.conexao_db,"tb_pessoa_contato",ids_pesctt)
                deleta(app.conexao_db,"tb_endereco",ids_end)          
                deleta(app.conexao_db,"tb_condicao_comercial",id_condcom) 
                deleta(app.conexao_db,"tb_contratante_pj",id_ctpj) 
                deleta(app.conexao_db,"tb_contrato",id_ctr) 
                

                return msg,cod
                
            return msg,cod

    @cross_origin
    @api.route('/cadastro_pf')   
    class Cadastro_Pj(Resource):

        def get(self,):

            grupo_perfil_contrato     = 15
            grupo_perfil_pesctt       = 2
            grupo_status_cadastro_rfb = 8
            grupo_estado_civil        = 16
            grupo_endereco            = 4
            
            dic_param = {}

            estados_civis =       pesquisa(app.conexao_db,"tb_classe_crm","FK_GRUPO_CRM_ID",grupo_estado_civil,["id","classe_crm"])
            perfis_contrato =     pesquisa(app.conexao_db,"tb_classe_crm","FK_GRUPO_CRM_ID",grupo_perfil_contrato,["id","classe_crm"])
            pessoas_contato =     pesquisa(app.conexao_db,"tb_classe_crm","FK_GRUPO_CRM_ID",grupo_perfil_pesctt,["id","classe_crm"])
            status_cadastro_rfb = pesquisa(app.conexao_db,"tb_status_crm","FK_GRUPO_CRM_ID",grupo_status_cadastro_rfb,["id","status_crm"])
            classe_endereco     = pesquisa(app.conexao_db,"tb_classe_crm","FK_GRUPO_CRM_ID",grupo_endereco,["id","classe_crm"])

            dic_param["indices_financeiros"]   = app.lista_if
            dic_param["perfis_contrato"]       = perfis_contrato
            dic_param["status_cadastro_rfb"]   = status_cadastro_rfb 
            dic_param["perfis_pessoa_contato"] = pessoas_contato
            dic_param["estados_civis"]         = estados_civis
            dic_param["classes_endereco"]      = classe_endereco

            for dic in perfis_contrato:
                dic["perfil"] = dic.pop("classe_crm")
            for dic in pessoas_contato:
                dic["perfil"] = dic.pop("classe_crm")
            for dic in status_cadastro_rfb:
                dic["status"] = dic.pop("status_crm")
            for dic in estados_civis:
                dic["estado_civil"] = dic.pop("classe_crm")
            for dic in classe_endereco:
                dic["classe"] = dic.pop("classe_crm")

            for i in range(len(pessoas_contato)):
                if pessoas_contato[i]["perfil"]=="Representante Legal":
                    pessoas_contato.pop(i)

            return dic_param

        @api.expect(m_completo_pf,validate=True)  
        def post(self,):

            if not verifica_validade(app.token):
                app.token = gera_token()

            registro        = api.payload
            lista_ufs       = app.lista_ufs
            lista_ufs       = [x["codDenatran"] for x in lista_ufs]
            
            fk_rep_legal    = 7
            fk_status_contrato_ativo = 1
            fk_status_registro_ativo = 32
            
            flag_ctt_principal  = False

            contrato        = registro["contrato"]
            cond_comercial  = registro["condicao_comercial"]
            contratante_pf  = registro["contratante_pf"]
            pessoas_contato = registro["pessoa_contato"]
            enderecos       = registro["endereco"]

            for end in enderecos:
                if recebe_municipio_cod_denatran(end["municipio"],app.token) == None:
                    return "Código de município não encontrado",404
                
                if end["uf"] not in lista_ufs: 
                    return "Código de UF não encontrado",404

            atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
            
            contratante_pf["status_cadastro_rfb"] = cod_status_rfb(contratante_pf["status_cadastro_rfb"])

            if not contratante_pf["status_cadastro_rfb"]:
                return "Status de cadastro na receita federal inválido",400

            # Contrato
            msg,cod,id_ctr = insere(app.conexao_db,"tb_contrato", ["ek_indice_financeiro_id" ,    "data_hora_insert", "fk_classe_crm_id" ,         "fk_status_crm_id"],
                                                                    [ contrato["indice_financeiro"], atual,              contrato["perfil_contrato"], fk_status_contrato_ativo  ] )
            if cod != 200:
                return msg,cod

            # Condição Comercial
            msg,cod,id_condcom = insere(app.conexao_db,"tb_condicao_comercial", ["dia_vencimento" ,                "valor_adesao" ,                "flag_cobranca_integral" ,                "flag_taxa_extra_anual" ,                "data_hora_insert" , "ek_carteira_id",               "ek_pacote_venda_id",             "fk_contrato_id" , "fk_status_crm_id"       ],
                                                                                [ cond_comercial["dia_vencimento"], cond_comercial["valor_adesao"], cond_comercial["flag_cobranca_integral"], cond_comercial["flag_taxa_extra_anual"], atual,               cond_comercial["carteira_id"],  cond_comercial["pacote_venda"],     id_ctr,           fk_status_registro_ativo ] )
            if cod != 200:
                deleta(app.conexao_db,"tb_contrato",id_ctr)
                return msg,cod
            
            # Representante legal
            for i in range (len(pessoas_contato)):
                if (pessoas_contato[i]["perfil"] == fk_rep_legal) and (pessoas_contato[i]["contato_principal"] == True):
                    flag_ctt_principal = True
                    cpf = pessoas_contato[i]["nr_doc"]
                    msg,cod,ctt_principal_id = insere_pessoas_contato(app.conexao_db,[ pessoas_contato[i] ],id_ctr,atual) # Alterar                     
                    pessoas_contato.pop(i)
                    break
                            
            if (not flag_ctt_principal) or (ctt_principal_id == []):
                deleta(app.conexao_db,"tb_condicao_comercial",id_condcom) 
                deleta(app.conexao_db,"tb_contrato",id_ctr) 
                return "É necessário que exista um contato principal e que ele seja representante legal",400
            else:
                ctt_principal_id = ctt_principal_id[0]
                
            if cod != 200:
                deleta(app.conexao_db,"tb_condicao_comercial",id_condcom) 
                deleta(app.conexao_db,"tb_contrato",id_ctr) 
                return msg,cod
            
            

            # Contratante_pf
            msg,cod,id_ctpf = insere(app.conexao_db,"tb_contratante_pf",["nr_doc_contratante", "data_atualizacao_rfb",                 "data_hora_insert", "fk_contrato_id", "fk_pessoa_contato_id", "fk_classe_crm_id",             "fk_status_crm_id"                     ], 
                                                                        [ cpf,                  contratante_pf["data_atualizacao_rfb"], atual,              id_ctr,           ctt_principal_id,           contratante_pf["estado_civil"], contratante_pf["status_cadastro_rfb"] ] )
            if cod != 200:
                deleta(app.conexao_db,"tb_pessoa_contato",ctt_principal_id)
                deleta(app.conexao_db,"tb_condicao_comercial",id_condcom) 
                deleta(app.conexao_db,"tb_contrato",id_ctr) 
                return msg,cod
            
            # Endereço
            msg,cod,ids_end  =insere_enderecos(app.conexao_db,enderecos,id_ctr,atual)
            if cod != 200:
                deleta(app.conexao_db,"tb_contratante_pf",id_ctpf) 
                deleta(app.conexao_db,"tb_condicao_comercial",id_condcom)
                deleta(app.conexao_db,"tb_contrato",id_ctr) 
                return msg,cod
            
            # Pessoa de contato 
            if pessoas_contato:
                msg,cod,_= insere_pessoas_contato(app.conexao_db,pessoas_contato,id_ctr,atual)
                if cod != 200:
                    deleta(app.conexao_db,"tb_endereco",ids_end)  
                    deleta(app.conexao_db,"tb_condicao_comercial",id_condcom) 
                    deleta(app.conexao_db,"tb_contratante_pf",id_ctpf) 
                    deleta(app.conexao_db,"tb_pessoa_contato",ctt_principal_id)
                    deleta(app.conexao_db,"tb_contrato",id_ctr) 
                    return msg,cod
                

            
            

            return msg,cod
    

    app.run(host="0.0.0.0",threaded=True)
    # threaded não será a solução definitiva, é necessário utilizar uma opção de deploy para a API 

    if app.conexao_db:
        app.conexao_db.close()
        print("conexão com o banco de dados terminada")

if __name__=="__main__":
	main()
