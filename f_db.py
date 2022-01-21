import os
from mysql.connector import connect, Error

def conecta_banco():
    try:
        USER     = os.getenv('DB_USER')
        PASS     = os.getenv('DB_PASS')
        HOST     = os.getenv('AC_HOST')
        DATABASE = os.getenv('DB_DATABASE')
        
        conexao = connect(
            host     = HOST,
            user     = USER,
            password = PASS,
            database = DATABASE
        )   
        return conexao

    except Error as e:
        print(e)
        print("Não foi possível estabelecer conexão com o Banco")

        return None

def cod_erro(erro):
    if erro == "1452":
        return "Não encontrado",404
    elif erro == "1406":
        return "Pedido mal formulado",400
    elif erro == "1062":
        return "Entrada duplicada", 400
    else:
        return "Erro interno",500
        
def select_all(conexao,tabela,colunas="*"):
    if type(colunas) is list:
        colunas = ', '.join(colunas)

    select_query = 'SELECT {colunas} FROM {tabela}'.format(colunas=colunas, tabela=tabela)

    with conexao.cursor(dictionary=True) as cursor:
        try:
            cursor.execute(select_query)
            result = cursor.fetchall()   
            return result,200
        except Exception as e:
            print ("\nFalha na query:",cursor.statement )
            print("Erro: ",e,"\n")
            print("Falha na query: ", cursor.statement )
            print("Erro:",e,"\n")
            msg,cod = cod_erro( str(e)[0:4] )

        return msg,cod

def insere(conexao,tabela,campos,param):    
    if type(campos) is list and type(param) is list:
        campos = ", ".join(campos)
        num_s = ",".join(["%s"]*len(param))
        param = tuple(param)

    elif type(campos) is str and type(param) is str:
        param = tuple([param])
        num_s = "%s"

    else :
        print("tipo de dado incorreto")
        return None
    
    insert_query = "INSERT INTO {tabela} ({campos})  VALUES ({num_s})".format(tabela = tabela,campos = campos,num_s = num_s)
    

    with conexao.cursor() as cursor:
        try:
            cursor.execute(insert_query,param)
            conexao.commit()
            msg  = "Registro salvo"
            id_r = ultimo_id(conexao)
            return msg,200,id_r
        except Exception as e:
            print("Falha na query: ", cursor.statement )
            print("Erro:",e,"\n")
            msg,cod = cod_erro( str(e)[0:4] )
            return msg,cod,None

def pesquisa(conexao,tabela,campos,param,colunas = "*",ordem = ""): # adicionar função para where x in [y,z] e de alias 
    if type(colunas) is list:
        colunas = ', '.join(colunas)        

    if type(campos) is list:                         # Adicionar exceção para NULL (IS NULL)
        campos = " = %s AND ".join(campos)
        param = tuple(param)

    elif type(campos) is str:
        param = tuple([param])

    else :
        print("tipo de dado incorreto")
        return None
    
    select_query = "SELECT {colunas} FROM  {tabela} WHERE {campos} = %s".format(colunas = colunas, tabela = tabela,campos = campos)
    
    if ordem != "":
        select_query += " ORDER BY {ordem} ASC".format(ordem = ordem)

    with conexao.cursor(dictionary=True) as cursor:                                                                                    
        try:                                
            cursor.execute(select_query,param)
            result = cursor.fetchall()     
        except Exception as e:
            print ("\nFalha na query:",cursor.statement )
            print("Erro: ",e,"\n")
            msg,cod = cod_erro( str(e)[0:4] )
            print(msg,cod) 
            return None
    
    return result

def deleta(conexao,tabela,reg_id): # Melhorar para ter a possibilidade de listas
    
    if isinstance(reg_id,int):
        reg_id = [reg_id]    
    
    if reg_id == []:
        return "Erro",500
        
    num_s = ",".join( ["%s" for s in range (len(reg_id))]  )

    delete_query = 'DELETE FROM {tabela} WHERE ID IN ({num_s})'.format(tabela=tabela,num_s=num_s)

    param =  tuple(reg_id)  

    with conexao.cursor() as cursor:                                                                                    
        try:                                
            cursor.execute(delete_query,param)
            conexao.commit()   
            msg = "O registro foi deletado com sucesso"
            cod = 200
        except Exception as e:
            print("Falha na query: ", cursor.statement )
            print("Erro:",e,"\n")
            msg,cod = cod_erro( str(e)[0:4] )
    
    return msg,cod

def update(conexao,tabela,campos,param,id_update): # Melhorar essa função (torná-la mais geral)

    if type(campos) is list and type(param) is list:
        campos = " = %s ,".join(campos)

    elif type(campos) is str and (type(param) is str or type(param) is int):
        param = [param]
        campos = campos + " = %s"

    else :
        print("tipo de dado incorreto")
        return None

    if type(id_update) is list:
        formato_s = "IN "+"(" + ",".join(["%s"]*len(id_update)) + ")"
        param.extend(id_update)
    else:
        formato_s = "= %s" 
        param.append(id_update)
    
    param = tuple(param)

    update_query = "UPDATE {tabela} SET {campos} WHERE ID {formato_s}".format(tabela = tabela, campos = campos,formato_s = formato_s)               

    with conexao.cursor() as cursor:                                                                                    
        try:                                
            cursor.execute(update_query,param)
            conexao.commit()   
            if cursor.rowcount>0:
                msg = "Registro atualizado"
                return msg,200   
            else:
                msg = "Não foi realizada nenhuma atualização"
                print(msg)
                return msg,200
            return True                                  
        except Exception as e:
            print("Falha na query: ", cursor.statement )
            print("Erro:",e,"\n")
            msg,cod = cod_erro( str(e)[0:4] )
            return msg,cod

def ultimo_id(conexao):
    select_query = "SELECT LAST_INSERT_ID()"
    
    with conexao.cursor(dictionary=True) as cursor:
        try:
            cursor.execute(select_query)
            ult_id = cursor.fetchall()
            ult_id = ult_id[0]["LAST_INSERT_ID()"]   
            return ult_id
        except Exception as e:
            print ("\nFalha na query:",cursor.statement )
            print("Erro: ",e,"\n")
            return None

def ultimos_ids(conexao,tabela,n):
    select_query = "SELECT id FROM {tabela} ORDER BY id DESC LIMIT %s".format(tabela=tabela)
    
    param = tuple([n])

    with conexao.cursor(dictionary=True) as cursor:
        try:
            cursor.execute(select_query,param)
            result = cursor.fetchall()
            ult_ids = []
            for r in result:
                ult_ids.append(r["id"])
            return ult_ids
        except Exception as e:
            print ("\nFalha na query:",cursor.statement )
            print("Erro: ",e,"\n")
            return None

def verifica_conexao(conexao):
    try:
        if not conexao.is_connected():
            conexao = conecta_banco()
    except:
        conexao = conecta_banco()

    return conexao
