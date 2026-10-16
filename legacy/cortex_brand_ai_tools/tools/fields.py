DOWNLOAD_FIELDS  = ["Chave Análise de Mídia Hash", "Título", "Data", "Conteúdo", 
                "Mídia", "Fonte", "Alcance orgânico", "Tier", "Empresa analisada",
                "Produto analisado", "Status classificação", "Link", "Link original da publicação", "Sentimento automático",
                "Protagonismo automático", "Tópicos (automático)", "Assunto específico automático",
                "Ação (automático)", "Origem da Menção (automático)", "Jornalista", 
                "Índice Confiança - Tópicos DS", "Índice Confiança - Ação DS"    
                ]




CHECK_FIELDS  = ["ID Cortex", "Título", "Data", "Conteúdo", 
                "Mídia", "Fonte", "Alcance orgânico", "Tier", "Empresa analisada",
                "Produto analisado", "Status classificação", "Link", "Link original da publicação"
                ]

CHECK_FIELDS_PR_DATA  = ["titulo_da_publicacao", "nome_fonte_normalizado","Fornecedor", "data_da_publicacao",
                          "cliente", "original_link", "clipadora_link", "nome_fornecedor"]

UPLOAD_CHECK_FIELDS  = ["Título", "Data", "Conteúdo", 
                "Veículo (Default)", 'Mídia (Default)', "Fonte", "Jornalista","Alcance total", "Link", "Link original da publicação"
                ]


REVISION_FIELDS  = ["Chave Análise de Mídia Hash", "Título", "Data", "Conteúdo", 
                "Mídia", "Fonte", "Alcance orgânico", "Alcance total", "Tier", "Empresa analisada",
                "Produto analisado", "Status classificação", "Link", "Link original da publicação", "Sentimento",
                "Nível de Protagonismo", "Macro assunto", "Mensagem-chave","Nível de Protagonismo final", "Tópicos", "Assunto específico",
                "Ação", "Tipo da ação", "Jornalista", "Temas", "Origem da menção"
             
                ]


REVISION_FIELDS_TO_UPLOAD  = ["Chave Análise de Mídia Hash", "Alcance total", "Tier", "Status classificação", 
                "Nível de Protagonismo",  "Tópicos", "Assunto específico", "Sentimento",
                "Ação", "Jornalista", "Temas", "Origem da menção", "Tipo da ação"
             
                ]

DOWNLOAD_PUBLICACOES = ["ID Cortex", "Título", "Data", "Conteúdo", "Tier", "Cidade (MSS)", "Estado (MSS)", "País (MSS)",
                "Mídia", "Fonte", "Alcance orgânico", "Tier", "Status classificação", "Link", 
                "Link original da publicação", "Enviar no clipping?", 'Empresas citadas', 
                'Produtos citados', 'Porta Vozes', 'Estado (final)' 
                ]



DOWNLOAD_ANALISE_MIDIA  = ["Chave Análise de Mídia Hash", "Título", "Data", "Conteúdo", "Link", "Link original da publicação", 
                "Mídia", "Fonte", "Cidade (MSS)", "Estado (MSS)", "País (MSS)", "Alcance orgânico", "Alcance total", "Valoração", "Engajamento total", "Tier", "Empresa analisada",
                "Produto analisado", "Veículo (Default)",  'Mídia (Default)',"Tier","Status classificação",  "Sentimento", "Sentimento final", "Sentimento automático",  
                "Nível de Protagonismo", "Nível de Protagonismo final", "Protagonismo automático", "Jornalista", "Macro assunto", 
                "Macro-assunto", "Temas", "Mensagem-chave", "Tags", "Pilar", "Sub-pilar", "Subpilar (Crise)", "Subpilar (Geral)",
                 "Tópicos", "Pilares", "Assuntos monitorados", "Assunto específico", "Assunto específico automático", "Ação", "Ação de comunicação (classificadores)" , 
                 "Tipo da ação", "Tipos de impactos","Origem da menção", "Classificado por", "Representa empresa?"
                ]


ACTION_FIELDS = [
                "Data",
            "Data da ação",
            "Título da ação",
            "Origem da ação",
            "Ação de comunicação",
            "Tipo da ação",
            "Texto da ação",
            "Assessoria",
            "Imagens da ação",
            "Mensagens-chave",
            "Objetivo de negócio",
            "Local da ação",
            "Nº de convidados",
            "Nº de presentes",
            "Status da ação",
            "Publicado por",
            "Data de publicação",
            "Última atualização",
            "Pilar da Ação",
            "Unidade da ação",
            "Veículo(s)",
            "Protagonismo na ação",
            "Arquivo da Ação",
            "Vertical",
            "Pilares"
            ]

ACTION_FIELDS = [
                "Data",
            "Data da ação",
            "Título da ação",
            "Origem da ação",
            "Ação de comunicação",
            "Tipo da ação",
            "Texto da ação",
            "Assessoria",
            "Imagens da ação",
            "Mensagens-chave",
            "Objetivo de negócio",
            "Local da ação",
            "Nº de convidados",
            "Nº de presentes",
            "Status da ação",
            "Publicado por",
            "Data de publicação",
            "Última atualização",
            "Pilar da Ação",
            "Unidade da ação",
            "Veículo(s)",
            "Protagonismo na ação",
            "Arquivo da Ação",
            "Vertical",
            "Pilares"
            ]


PR_DATA = [
    "cortex_id",
"midia_publicada",
"alcance_organico_normalizado",
"alcance_total_default",
"alcance_total_normalizado",
"valoracao",
"autor_da_publicacao",
"cidade_do_publicador",
"titulo_da_publicacao",
"conteudo",
"data_da_publicacao",
"data_hora_numero",
"data_hora_texto",
"data_minuto_numero",
"data_minuto_texto",
"estado_do_publicador",
"id_da_fonte_cortex",
"clipadora_link",
"original_link",
"nome_fonte_default",
"nome_fonte_normalizado",
"numero_de_angry",
"numero_de_comentarios",
"numero_de_compartilhamento",
"numero_de_dislikes",
"numero_de_haha",
"numero_de_likes",
"numero_de_love",
"numero_de_reacoes",
"numero_de_sad",
"numero_de_seguidores",
"numero_de_thankful",
"numero_de_wow",
"numero_duracao_video",
"numero_interacoes_total",
"numero_seguindo",
"numero_visitantes_default",
"numero_visualizacoes",
"pais_do_publicador",
"tipo_midia",
"tipo_de_publico",
"tipo_postagem_redes_socias",
"tier_cortex"
]


MSS_FIELDS = ['dp_id', 'dp_create_date', 'dp_create_date_string',
       'dp_create_date_millis', 'dp_name', 'dp_update_date',
       'dp_update_date_string', 'dp_update_date_millis', 'dp_data_partner',
       'dp_id_media_on_partner', 'dp_media_type', 'dp_variation',
       'dp_media_source_id', 'dp_inactive', 'ms_id', 'ms_create_date',
       'ms_create_date_string', 'ms_create_date_millis', 'ms_name',
       'ms_update_date', 'ms_update_date_string', 'ms_update_date_millis',
       'ms_address', 'ms_city', 'ms_country', 'ms_group', 'ms_ibge_city_id',
       'ms_latitude', 'ms_longitude', 'ms_media_type', 'ms_periodicity',
       'ms_state', 'ms_valuation', 'ms_web_address_link', 'ms_inactive',
       'ms_reach_online', 'ms_reach_tv', 'ms_reach_print',
      'ms_reach_online_supplier', 'ms_reach_radio',
       'tipo_de_publico', 'tier_cortex', 'latitude_estado', 'longitude_estado',
       'nm_scope', 'nm_editorial', 'gov_id_hash_media_source', 'ms_reach_tv_show', 'in_great_portal',
       'gov_nm_media_source', 'ms_reach_average']