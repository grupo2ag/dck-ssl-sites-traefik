from flask_restplus import fields

class String_Null(fields.String):
    __schema_type__ = ['string', 'null']
    __schema_example__ = 'string_ou_null'

def cria_modelos(api): 

    m_ctr = api.model(
        "contrato",
        {
        "indice_financeiro":    fields.Integer(description=""),
        "perfil_contrato":      fields.Integer(description="")
        }
    )

    m_condcom = api.model(
        "condicao_comercial",
        {
        "dia_vencimento":           fields.Integer(description=""),
        "valor_manutencao":         fields.Float(description=""),
        "valor_adesao":             fields.Float(description=""),
        "flag_cobranca_integral":   fields.Boolean(description=""),
        "flag_taxa_extra_anual":    fields.Boolean(description=""),
        "carteira_id":              fields.Integer(description=""),
        "tabela_preco":             fields.Integer(description=""), 
        "classe_faturamento":       fields.Integer(description=""),
        "perfil_contrato":          fields.Integer(description="") 
        }
    )

    m_ctpf = api.model(
        "Contratante_pf",
        {
        "data_atualizacao_rfb": fields.Date(description=""),
        "estado_civil":         fields.Integer(description="") , 
        "status_cadastro_rfb":  fields.String (description="") 
        }

    )

    m_ctpj = api.model(
        "Contratante_pj",
        {
        "nr_doc":               fields.String (description=""),
        "razao_social":         fields.String (description=""),
        "nome_fantasia":        fields.String (description=""),
        "ddd_fone":             fields.String (description=""),
        "nr_fone":              fields.String (description=""),
        "email":                fields.String (description=""),
        "inscricao_estadual":   fields.String (description=""),
        "inscrição_municipal":  String_Null (description=""),
        "site":                 fields.String (description=""),
        "data_abertura":        fields.Date   (description=""),
        "data_atualizacao_rfb": fields.Date   (description=""),
        "natureza_juridica":    fields.String(description="") , 
        "cnae_primario":        fields.String (description=""),
        "cnaes_secundarios":    fields.List   (fields.String(),description=""), #testar
        "perfil":               fields.Integer(description="") , 
        "status_cadastro_rfb":  fields.String (description="")
        }

    )

    m_pesctt = api.model(
        "pessoa_contato",
        {
        "nr_doc":           fields.String (description=""),
        "nome":             fields.String (description=""),
        "data_nascimento":  fields.Date   (description=""),
        "ddd_fone":         fields.String (description=""),
        "nr_fone":          fields.String (description=""),
        "ddd_cel":          fields.String (description=""),
        "nr_cel":           fields.String (description=""),
        "email":            fields.String (description=""),
        "profissao":        fields.String (description=""),
        "nr_rg":            String_Null   (description=""),
        "expedidor_rg":     String_Null   (description=""),
        "perfil":           fields.Integer(description=""),
        "contato_principal":fields.Boolean(description="")
        }
    )
    m_end = api.model(
        "endereco",
        {
        "cep":          fields.Integer(description=""),
        "endereco":     fields.String (description=""),
        "bairro":       fields.String (description=""),
        "numero":       fields.String (description=""),
        "complemento":  fields.String (description=""),
        "uf":           fields.Integer(description=""),
        "municipio":    fields.Integer(description=""),
        "classe":       fields.Integer(description=""),
        }
    )

    m_completo_pf = api.model(
    "completo_pf", {
        "contrato":             fields.Nested(m_ctr, description=''),

        "condicao_comercial":   fields.Nested(m_condcom, description=''),

        "contrante_pf":         fields.List(fields.Nested(m_ctpf),description=""), 

        "pessoa_contato":       fields.List(fields.Nested(m_pesctt),description="" ), 
    

        "endereco":             fields.List(fields.Nested(m_end),description="" )
    }
    )

    m_completo_pj = api.model(
    "completo_pj", {
        "contrato":             fields.Nested(m_ctr, description=''),

        "condicao_comercial":   fields.Nested(m_condcom, description=''),

        "contrante_pj":         fields.List(fields.Nested(m_ctpj),description=""), 

        "pessoa_contato":       fields.List(fields.Nested(m_pesctt),description="" ),

        "endereco":             fields.List(fields.Nested(m_end),description="" )
    }
    )

    

    return m_completo_pf, m_completo_pj
