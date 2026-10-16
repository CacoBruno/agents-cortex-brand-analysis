from tools.authentication import get_auth_headers
from tools.download import get_ctx_cube
from tools.dates import get_date_range
from .index_function import generate_row_hash, map_mes_low
import pandas as pd
import os
import json
from tools.fields import *
from typing import List
# Load .env file


from dotenv import load_dotenv
load_dotenv()

# Access variables
PLATFORM_LOGIN = os.getenv('PLATFORM_LOGIN')
PLATFORM_PASSWORD = os.getenv('PLATFORM_PASSWORD')


def get_infos_brand(url_platform: str) -> pd.DataFrame:

    client_name = url_platform.replace("https://", "").split(".")[0]


    name = '[DataScience] Configuração de variações de menções para protagonismo'
    df_name = get_cube(client_name, name, PLATFORM_LOGIN, PLATFORM_PASSWORD, filters=[], fields=[])

    #empresas = list(set(df_name['Empresas citadas'].to_list()))
    #produtos = list(set(df_name['Produtos citados'].to_list()))

    return df_name


def get_cube(client_name, cube_name, login, senha, fields=[], filters=[]):    
    client_auth_endpoint = f'https://{client_name.lower()}.cortex-intelligence.com/service/integration-authorization-service.login'
    client_credentials =  {'login': login, 'password': senha}
    cubos_endpoint = f'https://{client_name.lower()}.cortex-intelligence.com/service/integration-cube-service.download?'
    resp = get_auth_headers(client_auth_endpoint, client_credentials)
    auth_headers = resp["auth_headers"]
    if resp["status_code"] != 200:
        raise (
        f"Não foi possível acessar a Plataforma. Erro: {resp['status_code']}")

    print(f"Get infos from {cube_name} ...")
    dataframe =  get_ctx_cube(
        cube_name,
        fields,
        filters,
        auth_headers,
        cubos_endpoint,
    )
    print('Data access completed successfully!\n')
    return dataframe



def check_urls_in_publicacoes(url_platform: str,  link_original=None, link=None) -> pd.DataFrame:

    # ------------------------------------------------------------------
    # Normaliza parâmetros
    # ------------------------------------------------------------------
    link_original     = _to_list(link_original)
    link              = _to_list(link)
    
    # ------------------------------------------------------------------
    # Autenticação na plataforma
    # ------------------------------------------------------------------

    cube_name = 'Publicações'
    client_platform = url_platform.replace('https://', '').replace('/','').split('.')[0]
    # Access variables
    PLATFORM_LOGIN = os.getenv('PLATFORM_LOGIN')
    PLATFORM_PASSWORD = os.getenv('PLATFORM_PASSWORD')
    client_auth_endpoint = f'https://{client_platform.lower()}.cortex-intelligence.com/service/integration-authorization-service.login'
    client_credentials =  {'login': PLATFORM_LOGIN, 'password': PLATFORM_PASSWORD}
    cubos_endpoint = f'https://{client_platform.lower()}.cortex-intelligence.com/service/integration-cube-service.download?'

    resp = get_auth_headers(client_auth_endpoint, client_credentials)
    auth_headers = resp["auth_headers"]
    if resp["status_code"] != 200:
        raise (
            f"Não foi possível acessar a Plataforma. Erro: {resp['status_code']}")



    dfs = []

    if link_original:

        filters =  [{'name': "Link original da publicação",
                'exact_match': False,
                'values': link_original}
                ]       

        df =  get_ctx_cube(
            cube_name,
            CHECK_FIELDS,
            filters,
            auth_headers,
            cubos_endpoint,
        )

        print('Links Originais: Original Shape = ', len(df))    
        
        dfs.append(df)


    if link:

        filters =  [
                {'name': "Link",
                'exact_match': False,
                'values': link}
                ]           


        df =  get_ctx_cube(
            cube_name,
            CHECK_FIELDS,
            filters,
            auth_headers,
            cubos_endpoint,
        )

        print('Links clipadora: Original Shape = ', len(df))    
        
        dfs.append(df)

    # ------------------------------------------------------------------
    # Concatena resultados
    # ------------------------------------------------------------------
    if not dfs:
        return "Nenhum registro encontrado com os filtros fornecidos."

    result = (
        pd.concat(dfs, ignore_index=True)
          .drop_duplicates(subset=["ID Cortex"])
          .reset_index(drop=True)
    )
    return result


def check_urls_in_pr_data(link_original=None) -> pd.DataFrame:

    # ------------------------------------------------------------------
    # Normaliza parâmetros
    # ------------------------------------------------------------------
    link_original     = _to_list(link_original)
    print(link_original)
  
    # ------------------------------------------------------------------
    # Autenticação na plataforma
    # ------------------------------------------------------------------

    cube_name = '[Data Delivery] Publicações'
    client_platform = 'prdata'
    # Access variables
    PLATFORM_LOGIN = os.getenv('PLATFORM_LOGIN')
    PLATFORM_PASSWORD = os.getenv('PLATFORM_PASSWORD')
    client_auth_endpoint = f'https://{client_platform.lower()}.cortex-intelligence.com/service/integration-authorization-service.login'
    client_credentials =  {'login': PLATFORM_LOGIN, 'password': PLATFORM_PASSWORD}
    cubos_endpoint = f'https://{client_platform.lower()}.cortex-intelligence.com/service/integration-cube-service.download?'

    resp = get_auth_headers(client_auth_endpoint, client_credentials)
    auth_headers = resp["auth_headers"]
    if resp["status_code"] != 200:
        raise (
            f"Não foi possível acessar a Plataforma. Erro: {resp['status_code']}")



  

    filters =  [{'name': "original_link",
                'exact_match': False,
                'values': link_original}
                ]       

    df =  get_ctx_cube(
            cube_name,
            CHECK_FIELDS_PR_DATA,
            filters,
            auth_headers,
            cubos_endpoint,
        )

    print('Links Originais: Original Shape = ', len(df))    
        


    return df



import os
import pandas as pd

def _to_list(x):
    """Garante que x seja lista; None → [], escalar → [esc], lista → lista."""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]

def revision_media_analysis(
        url_platform: str,
        link_original=None,
        link=None,
        titulo=None,
        id_analise_midia=None,
        empresa_analisada=None,
        produto_analisado=None
    ) -> str | pd.DataFrame:

    # ------------------------------------------------------------------
    # 1. Normaliza parâmetros
    # ------------------------------------------------------------------
    link_original     = _to_list(link_original)
    link              = _to_list(link)
    titulo            = _to_list(titulo)
    id_analise_midia  = _to_list(id_analise_midia)
    empresa_analisada = _to_list(empresa_analisada)
    produto_analisado = _to_list(produto_analisado)

    if not any([link_original, link, titulo,
                id_analise_midia, empresa_analisada, produto_analisado]):
        return "Precisa inserir ao menos uma variável de filtro"

    # ------------------------------------------------------------------
    # 2. Autenticação na plataforma
    # ------------------------------------------------------------------
    cube_name   = "Análise de Mídia"
    client      = url_platform.replace("https://", "").split(".")[0]
    auth_url    = f"https://{client}.cortex-intelligence.com/service/integration-authorization-service.login"
    cubo_url    = f"https://{client}.cortex-intelligence.com/service/integration-cube-service.download?"

    resp = get_auth_headers(auth_url, {
        "login": os.getenv("PLATFORM_LOGIN"),
        "password": os.getenv("PLATFORM_PASSWORD")
    })
    if resp["status_code"] != 200:
        raise RuntimeError(f"Não foi possível autenticar (erro {resp['status_code']}).")

    auth_headers = resp["auth_headers"]

    # ------------------------------------------------------------------
    # 3. Faz as buscas e acumula resultados
    # ------------------------------------------------------------------
    dfs = []

    if id_analise_midia:
        filters = [{'name': "Chave Análise de Mídia Hash",
                    'exact_match': False,
                    'values': id_analise_midia}]
        df = get_ctx_cube(cube_name, REVISION_FIELDS, filters,
                          auth_headers, cubo_url)
        print("Shape – id_analise_midia:", len(df))
        dfs.append(df)

    if link_original and (empresa_analisada or produto_analisado):
        filters = [
            {'name': "Link original da publicação", 'exact_match': False, 'values': link_original},
            {'name': "Empresa analisada",            'exact_match': False, 'values': empresa_analisada},
            {'name': "Produto analisado",            'exact_match': False, 'values': produto_analisado},
        ]
        df = get_ctx_cube(cube_name, REVISION_FIELDS, filters,
                          auth_headers, cubo_url)
        print("Shape – link_original:", len(df))
        dfs.append(df)

    if link and (empresa_analisada or produto_analisado):
        filters = [
            {'name': "Link",               'exact_match': False, 'values': link},
            {'name': "Empresa analisada",  'exact_match': False, 'values': empresa_analisada},
            {'name': "Produto analisado",  'exact_match': False, 'values': produto_analisado},
        ]
        df = get_ctx_cube(cube_name, REVISION_FIELDS, filters,
                          auth_headers, cubo_url)
        print("Shape – link:", len(df))
        dfs.append(df)

    if titulo and (empresa_analisada or produto_analisado):
        filters = [
            {'name': "Título",             'exact_match': False, 'values': titulo},
            {'name': "Empresa analisada",  'exact_match': False, 'values': empresa_analisada},
            {'name': "Produto analisado",  'exact_match': False, 'values': produto_analisado},
        ]
        df = get_ctx_cube(cube_name, REVISION_FIELDS, filters,
                          auth_headers, cubo_url)
        print("Shape – titulo:", len(df))
        dfs.append(df)

    # ------------------------------------------------------------------
    # 4. Concatena resultados
    # ------------------------------------------------------------------
    if not dfs:
        return "Nenhum registro encontrado com os filtros fornecidos."

    result = (
        pd.concat(dfs, ignore_index=True)
          .drop_duplicates(subset=["Chave Análise de Mídia Hash"])
          .reset_index(drop=True)
    )
    return result


def export_databate_publ(
        url_platform: str,
        start_date = None,
        end_date = None,
        empresa_citada=None,
        produto_citado=None,
        midia=None,
        tier=None,
        estado=None,
    ) -> pd.DataFrame:

    # ------------------------------------------------------------------
    # 1. Normaliza parâmetros
    # ------------------------------------------------------------------
    empresa_citada = _to_list(empresa_citada)
    produto_citado = _to_list(produto_citado)
    midia  = _to_list(midia)
    tier = _to_list(tier)
    estado = _to_list(estado)


    if empresa_citada == [] and produto_citado == []:
        ### aqui poderia printar os nomes que estão na plataforma
        empresas, produtos = get_infos_brand(url_platform)

        print(f"Precisa inserir o nome da Empresa ou do Produto que para fazer o download: \
            As empresas são: {empresas} \
            \
            Os produtos são: {produtos} \
        ")
        df = pd.DataFrame(columns=DOWNLOAD_PUBLICACOES)

        return df
    
    elif empresa_citada != [] or produto_citado != []:
        
        seven_days_ago, today = get_date_range()

        if start_date == None:
            start_date = seven_days_ago
            print(start_date)
        
        if end_date == None:    
            end_date = today
            print(end_date)


        if tier ==[]:
            tier = ['Tier 1', 'Tier 2', 'Outros']    


        # ------------------------------------------------------------------
        # 2. Autenticação na plataforma
        # ------------------------------------------------------------------
        cube_name = 'Publicações'
        client      = url_platform.replace("https://", "").split(".")[0]
        auth_url    = f"https://{client}.cortex-intelligence.com/service/integration-authorization-service.login"
        cubo_url    = f"https://{client}.cortex-intelligence.com/service/integration-cube-service.download?"

        resp = get_auth_headers(auth_url, {
            "login": os.getenv("PLATFORM_LOGIN"),
            "password": os.getenv("PLATFORM_PASSWORD")
        })
        if resp["status_code"] != 200:
            raise RuntimeError(f"Não foi possível autenticar (erro {resp['status_code']}).")

        auth_headers = resp["auth_headers"]




        step_filters = [
                {'name': 'Empresas citadas', 'exact_match': False, 'values': empresa_citada},
                {'name': 'Produtos citados', 'exact_match': False, 'values': produto_citado},            
                {'name': 'Estado (final)', 'exact_match': False, 'values': estado},
                {'name': 'Mídia', 'exact_match': False, 'values': midia},
                {'name': 'Tier', 'exact_match': False, 'values': tier},

            ]


        date_filter = [{"name": "Data",
                        "values": (start_date, end_date)}]

        filters = [f for f in [step_filters, date_filter] if f is not None]
        filters = [item for sublist in filters for item in sublist]

        df = get_ctx_cube(cube_name, DOWNLOAD_PUBLICACOES, filters, 
                            auth_headers, cubo_url) 
        print("Shape – link:", len(df))


        return df


#########################################
####### BASE ANALISE DE MIDIA ###########
#########################################

def export_database_ma(
        url_platform: str,
        start_date = None,
        end_date = None,
        empresa_analisada=None,
        produto_analisado=None,
        midia=None,
        tier=None,
        estado=None,
        tipos_de_impactos=None,
        sentimento  = None,        
        protagonismo  = None,
        topico  = None,
        assuntos_especifico  = None,
        acao_comunicacao  = None,
        origem_mencao  = None,
        jornalista  = None,
        temas  = None,
        macro_assunto  = None,
        representa_empresa=None,
        status_classificacao  = None
    ) -> pd.DataFrame:

    # ------------------------------------------------------------------
    # 1. Normaliza parâmetros
    # ------------------------------------------------------------------
    empresa_analisada = _to_list(empresa_analisada)
    produto_analisado = _to_list(produto_analisado)
    midia  = _to_list(midia)
    tier = _to_list(tier)
    estado = _to_list(estado)
    tipos_de_impactos = _to_list(tipos_de_impactos)
    sentimento  = _to_list(sentimento)
    protagonismo  = _to_list(protagonismo)
    topico  = _to_list(topico)
    assuntos_especifico  = _to_list(assuntos_especifico)
    acao_comunicacao  = _to_list(acao_comunicacao)
    origem_mencao  = _to_list(origem_mencao)
    jornalista  = _to_list(jornalista)
    temas  = _to_list(temas)
    macro_assunto  = _to_list(macro_assunto)
    representa_empresa = _to_list(representa_empresa)
    status_classificacao = _to_list(status_classificacao)




    if empresa_analisada == [] and produto_analisado == []:
        ### aqui poderia printar os nomes que estão na plataforma
        empresas, produtos = get_infos_brand(url_platform)

        print(f"Precisa inserir o nome da Empresa ou do Produto que para fazer o download: \
            As empresas são: {empresas} \
            \
            Os produtos são: {produtos} \
        ")
        df = pd.DataFrame(columns=DOWNLOAD_ANALISE_MIDIA)

        return df
    
    elif empresa_analisada != [] or produto_analisado != []:
        
        seven_days_ago, today = get_date_range()

        if start_date == None:
            start_date = seven_days_ago
            print(start_date)
        
        if end_date == None:    
            end_date = today
            print(end_date)


        if tier ==[]:
            tier = ['Tier 1', 'Tier 2', 'Outros']    

        if status_classificacao ==[]:
            status_classificacao = ['Classificado', 'Pendente']    



        # ------------------------------------------------------------------
        # 2. Autenticação na plataforma
        # ------------------------------------------------------------------
        cube_name   = "Análise de Mídia"
        client      = url_platform.replace("https://", "").split(".")[0]
        auth_url    = f"https://{client}.cortex-intelligence.com/service/integration-authorization-service.login"
        cubo_url    = f"https://{client}.cortex-intelligence.com/service/integration-cube-service.download?"

        resp = get_auth_headers(auth_url, {
            "login": os.getenv("PLATFORM_LOGIN"),
            "password": os.getenv("PLATFORM_PASSWORD")
        })
        if resp["status_code"] != 200:
            raise RuntimeError(f"Não foi possível autenticar (erro {resp['status_code']}).")

        auth_headers = resp["auth_headers"]



        step_filters = [
                {'name': 'Empresa analisada', 'exact_match': False, 'values': empresa_analisada},
                {'name': 'Produto analisado', 'exact_match': False, 'values': produto_analisado},            
                {'name': 'Estado (final)', 'exact_match': False, 'values': estado},
                {'name': 'Mídia', 'exact_match': False, 'values': midia},
                {'name': 'Tier', 'exact_match': False, 'values': tier},
               {'name': 'Sentimento', 'exact_match': False, 'values': sentimento},
               {'name': 'Status classificação', 'exact_match': False, 'values': status_classificacao},
               {'name': 'Nível de Protagonismo', 'exact_match': False, 'values': protagonismo},
               {'name': 'Macro assunto', 'exact_match': False, 'values': macro_assunto},
               {'name': 'Tópicos', 'exact_match': False, 'values': topico},
               {'name': 'Assunto específico', 'exact_match': False, 'values': assuntos_especifico },           
               {'name': 'Ação', 'exact_match': False, 'values': acao_comunicacao},           
               {'name': 'Origem da menção', 'exact_match': False, 'values': origem_mencao},
               {'name': 'Jornalista', 'exact_match': False, 'values': jornalista},                          
               {'name': 'Temas', 'exact_match': False, 'values': temas},        
               {'name': 'Representa empresa?', 'exact_match': False, 'values': representa_empresa},                   
               {'name': 'Tipos de impactos', 'exact_match': False, 'values': tipos_de_impactos},                          
            
            ]


        date_filter = [{"name": "Data",
                        "values": (start_date, end_date)}]

        filters = [f for f in [step_filters, date_filter] if f is not None]
        filters = [item for sublist in filters for item in sublist]

        df = get_ctx_cube(cube_name, DOWNLOAD_ANALISE_MIDIA, filters, 
                            auth_headers, cubo_url) 
        print("Shape – link:", len(df))


        return df



############################################
## UPLOADS FUNCTIONS
############################################

from tools.load_manager import CortexUploadAPI

def upload_missing_news_publicacoes(df: pd.DataFrame, url_plataform: str):

    try:
        publicacoes_id = '9e99f5db6efe43bebaa66142834d7a9d'
        api = CortexUploadAPI()
        client_platform = url_plataform.replace('https://', '').replace('/','').split('.')[0]

        api.upload_to_ctx(df=df,
                        cube_id=publicacoes_id,
                        client=client_platform,
                        credentials= {"login": PLATFORM_LOGIN, "password": PLATFORM_PASSWORD},
                        filename='subject')
        
        return f'upload na plafaforma: {df}'
    
    except NameError as e:
        return e
    

def upload_review_classification(df: pd.DataFrame, url_plataform: str):

    try:
        analise_midia_id = '01f6057b711545708703eec79e5426fd'
        api = CortexUploadAPI()
        client_platform = url_plataform.replace('https://', '').replace('/','').split('.')[0]

        api.upload_to_ctx(df=df,
                        cube_id=analise_midia_id,
                        client=client_platform,
                        credentials= {"login": PLATFORM_LOGIN, "password": PLATFORM_PASSWORD},
                        filename='subject')
        
        print(f'upload na plafaforma: {df}')
        return f'upload na plafaforma: {df}'
    
    except NameError as e:
        return e   
    

def export_action_database(url_platform, start_date, end_date): 
    
    cube_name = 'Cadastro de ações'
    client_platform = url_platform.replace('https://', '').replace('/','').split('.')[0]
        # Access variables
    PLATFORM_LOGIN = os.getenv('PLATFORM_LOGIN')
    PLATFORM_PASSWORD = os.getenv('PLATFORM_PASSWORD')

        
    step_filters =  [
                ]       


    date_filter = [{"name": "Data da ação",
                        "values": (start_date, end_date)}]

    filters = [f for f in [step_filters, date_filter] if f is not None]
    filters = [item for sublist in filters for item in sublist]

        
        ################################################################################
        # Define Plataform Info
        ################################################################################
    client_auth_endpoint = f'https://{client_platform.lower()}.cortex-intelligence.com/service/integration-authorization-service.login'
    client_credentials =  {'login': PLATFORM_LOGIN, 'password': PLATFORM_PASSWORD}
    cubos_endpoint = f'https://{client_platform.lower()}.cortex-intelligence.com/service/integration-cube-service.download?'

    print(client_auth_endpoint)

        ################################################################################
        #  Cortex Authentication 
        ################################################################################
    resp = get_auth_headers(client_auth_endpoint, client_credentials)
    auth_headers = resp["auth_headers"]
    if resp["status_code"] != 200:
            raise (
                f"Não foi possível acessar a Plataforma. Erro: {resp['status_code']}")


        ################################################################################
        # Data Access
        ################################################################################
    print(f"Get news from {cube_name} ...")
    print(f'fields downloads: {ACTION_FIELDS}')
    am_df =  get_ctx_cube(
            cube_name,
            ACTION_FIELDS,
            filters,
            auth_headers,
            cubos_endpoint,
        )
    
    
    am_df['Data da ação'] = pd.to_datetime(am_df['Data da ação'])
    am_df["ano"] = am_df["Data da ação"].dt.year
    am_df["mes_num"] = am_df["Data da ação"].dt.month
    am_df
    am_df["mes"] = am_df["Data da ação"].dt.strftime("%m/%Y")
    am_df

    am_df['mes_nome'] = am_df['mes_num'].apply(lambda x : map_mes_low[x])
    am_df['Mês'] = am_df.apply(lambda x : x['mes_nome'] + '/' + str((x['ano'])), axis=1)

    cols_hash = [
            'Data da ação', 'Título da ação', 'Origem da ação',
       'Ação de comunicação', 'Tipo da ação', 'Texto da ação'
        ]

    am_df = generate_row_hash(am_df, columns=cols_hash, hash_col='Chave Análise de Mídia Hash')

    return am_df


#######################################
###### PR DATA
######################################

def get_prdata_dataframe(start_date: str, end_date:str, therms_values: List, media_outlets=None) -> pd.DataFrame:

  
    therms_values = _to_list(therms_values)
    
    url_platform = 'https://prdata.cortex-intelligence.com/'
    cube_name = '[Data Delivery] Publicações'
    client_platform = url_platform.replace('https://', '').replace('/','').split('.')[0]



    step_filters = [
        {
            "name": "conteudo",
            "exact_match": False,
            "values": therms_values,
        }
    ]

    if media_outlets:
        step_filters.append(
            {
                "name": "nome_fonte_normalizado",
                "exact_match": True,
                "values": media_outlets,
            }
        )

    date_filter = [
        {
            "name": "data_da_publicacao",
            "values": (start_date, end_date),
        }
    ]

    filters = step_filters + date_filter

    client_auth_endpoint = (
        f"https://{client_platform.lower()}.cortex-intelligence.com/"
        "service/integration-authorization-service.login"
    )
    client_credentials = {
        "login": PLATFORM_LOGIN,
        "password": PLATFORM_PASSWORD,
    }
    cubos_endpoint = (
        f"https://{client_platform.lower()}.cortex-intelligence.com/"
        "service/integration-cube-service.download?"
    )

    print(client_auth_endpoint)

    resp = get_auth_headers(client_auth_endpoint, client_credentials)
    auth_headers = resp["auth_headers"]

    if resp["status_code"] != 200:
        raise RuntimeError(
            f"Não foi possível acessar a Plataforma. Erro: {resp['status_code']}"
        )

    print(f"Get news from {cube_name} ...")
    print(f"fields downloads: {PR_DATA}")

    am_df = get_ctx_cube(
        cube_name,
        PR_DATA,
        filters,
        auth_headers,
        cubos_endpoint,
    )

    return am_df


#######################################
###### MAR ABERTO (OPEN SOURCE)
######################################

from typing import List, Optional
import pandas as pd

def get_prdata_open_source(
    start_date: str,
    end_date: str,
    therms_values: List,
    media_outlets: Optional[List] = None,
    midia_publicada: Optional[List] = None
) -> pd.DataFrame:

    therms_values = _to_list(therms_values)
    media_outlets = _to_list(media_outlets)
    midia_publicada = _to_list(midia_publicada)

    url_platform = "https://prdata.cortex-intelligence.com/"
    cube_name = "[Data Delivery] Twingly e Redes Sociais"
    client_platform = url_platform.replace("https://", "").replace("/", "").split(".")[0]

    # =========================
    # STEP FILTERS BASE
    # =========================
    step_filters = [
        {
            "name": "conteudo",
            "exact_match": False,
            "values": therms_values,
        }
    ]

    # =========================
    # OPTIONAL: media_outlets
    # =========================
    if media_outlets:
        step_filters.append(
            {
                "name": "nome_fonte_normalizado",
                "exact_match": True,
                "values": media_outlets,
            }
        )

    # =========================
    # OPTIONAL: midia_publicada
    # =========================
    if midia_publicada:
        step_filters.append(
            {
                "name": "midia_publicada",
                "exact_match": True,
                "values": midia_publicada,
            }
        )

    # =========================
    # DATE FILTER
    # =========================
    date_filter = [
        {
            "name": "data_da_publicacao",
            "values": (start_date, end_date),
        }
    ]

    filters = step_filters + date_filter

    # =========================
    # AUTH
    # =========================
    client_auth_endpoint = (
        f"https://{client_platform.lower()}.cortex-intelligence.com/"
        "service/integration-authorization-service.login"
    )

    client_credentials = {
        "login": PLATFORM_LOGIN,
        "password": PLATFORM_PASSWORD,
    }

    cubos_endpoint = (
        f"https://{client_platform.lower()}.cortex-intelligence.com/"
        "service/integration-cube-service.download?"
    )

    resp = get_auth_headers(client_auth_endpoint, client_credentials)
    auth_headers = resp["auth_headers"]

    if resp["status_code"] != 200:
        raise RuntimeError(
            f"Não foi possível acessar a Plataforma. Erro: {resp['status_code']}"
        )

    # =========================
    # DATA ACCESS
    # =========================
    am_df = get_ctx_cube(
        cube_name,
        PR_DATA,
        filters,
        auth_headers,
        cubos_endpoint,
    )

    return am_df

#######################################
###### MSS
######################################
def get_mss_dataframe(
    veiculos_mss=None,
    veiculos_fornecedor=None,
    fornecedores=None,
    tier=None,
    tipo_publico=None,
    estados=None,
    cidades=None,
    pais=None
) -> pd.DataFrame:

    url_platform = 'https://prdata.cortex-intelligence.com/'
    cube_name = '[Data Delivery] MSS'
    client_platform = url_platform.replace('https://', '').replace('/', '').split('.')[0]

    veiculos_mss = _to_list(veiculos_mss)
    veiculos_fornecedor = _to_list(veiculos_fornecedor)
    fornecedores = _to_list(fornecedores)
    tier = _to_list(tier)
    tipo_publico = _to_list(tipo_publico)
    estados = _to_list(estados)
    cidades = _to_list(cidades)
    pais = _to_list(pais)

    step_filters = [
        {'name': 'ms_name', 'exact_match': False, 'values': veiculos_mss},
        {'name': 'dp_name', 'exact_match': False, 'values': veiculos_fornecedor},
        {'name': 'dp_data_partner', 'exact_match': False, 'values': fornecedores},
        {'name': 'tier_cortex', 'exact_match': False, 'values': tier},
        {'name': 'tipo_de_publico', 'exact_match': False, 'values': tipo_publico},
        {'name': 'ms_state', 'exact_match': False, 'values': estados},
        {'name': 'ms_city', 'exact_match': False, 'values': cidades},
        {'name': 'ms_country', 'exact_match': False, 'values': pais},
    ]

    # remove filtros vazios
    filters = [
        f for f in step_filters
        if f.get("values") not in (None, [], "")
    ]

    client_auth_endpoint = (
        f'https://{client_platform.lower()}.cortex-intelligence.com/'
        'service/integration-authorization-service.login'
    )
    client_credentials = {
        'login': PLATFORM_LOGIN,
        'password': PLATFORM_PASSWORD
    }
    cubos_endpoint = (
        f'https://{client_platform.lower()}.cortex-intelligence.com/'
        'service/integration-cube-service.download?'
    )

    print(client_auth_endpoint)

    resp = get_auth_headers(client_auth_endpoint, client_credentials)
    auth_headers = resp["auth_headers"]

    if resp["status_code"] != 200:
        raise RuntimeError(
            f"Não foi possível acessar a Plataforma. Erro: {resp['status_code']}"
        )

    print(f"Get news from {cube_name} ...")
    print(f"fields downloads: {MSS_FIELDS}")

    am_df = get_ctx_cube(
        cube_name,
        MSS_FIELDS,
        filters,
        auth_headers,
        cubos_endpoint,
    )

    return am_df



