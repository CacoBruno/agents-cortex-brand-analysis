from langchain_core.tools import tool

from src.tools_agents.insights_tools.schemas import (
    CoverageOrchestratorInput,
)
from src.tools_agents.insights_tools.services import (
    build_initial_coverage_state,
)
from src.tools_agents.insights_tools.graph import (
    build_coverage_orchestrator_graph,
    build_coverage_orchestrator_graph_with_whatsapp,
    build_coverage_orchestrator_graph_with_meeting_insights
)

from services.output_configs.output_mspack import make_msgpack_safe
from langchain_core.tools import tool

from src.tools_agents.insights_tools.output_formatter import format_orchestrator_output

@tool(args_schema=CoverageOrchestratorInput)
def insights_orchestrator_analysis_media_tool(
    url_platform: str,
    end_date: str,
    analysis_start_date: str,
    client: str,
    client_display_name: str,
    produto_analisado: list[str],
    period: str = "mes",
    period_label: str | None = None,
    anchor_weekday: str = "segunda-feira",
    list_search: list[str] | None = None,
    status_classificacao: list[str] | None = None,
    tipos_de_impactos: list[str] | None = None,
    representa_empresa: str = "Sim",
    tier: list[str] | None = None,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    max_retries: int = 3,
):
    """
    Executa o orquestrador síncrono de insights para base de análise de mídia (clientes).

    Esta tool monta automaticamente o estado inicial da análise, executa o
    grafo LangGraph de cobertura de mídia e retorna os principais produtos
    analíticos gerados: insights finais, highlights executivos, contexto de
    notícias e contexto de negócios.

    Fluxo executado:
        1. Captura dados da plataforma.
        2. Gera indicadores de padrão de exposição.
        3. Gera contexto narrativo das notícias.
        4. Gera contexto de negócios da empresa.
        5. Gera highlights executivos.
        6. Consolida os insights finais.

    Regras automáticas:
        - O start_date usado na captura é calculado como end_date menos 1 ano.
        - analysis_start_date é usado apenas para recortar o período analisado
          no contexto das notícias.
        - year é extraído automaticamente de end_date.
        - data_ancora_semana é calculada a partir de end_date e anchor_weekday.
        - Se list_search vier None, usa [client, client_display_name].
        - company_name usado nos insights é client_display_name.

    Args:
        url_platform:
            URL da plataforma Cortex/PRData usada para exportar os dados.

        end_date:
            Data final da análise, no formato YYYY-MM-DD.
            Também serve como referência para calcular o start_date histórico
            de captura e o year.

        analysis_start_date:
            Data inicial do período efetivamente analisado no contexto das
            notícias, no formato YYYY-MM-DD.

        client:
            Nome normalizado da empresa na base de dados.
            Exemplo: "americanas sa".

        client_display_name:
            Nome amigável da empresa usado nos textos e nos insights.
            Exemplo: "Americanas".

        produto_analisado:
            Lista de produtos, marcas ou aliases usados no filtro da captura.

        period:
            Granularidade analítica usada nos indicadores.
            Valores esperados: "dia", "semana", "mes" ou "ano".
            Default: "mes".

        period_label:
            Rótulo textual do período analisado.
            Exemplo: "Março de 2026".

        anchor_weekday:
            Dia da semana usado para calcular data_ancora_semana.
            Exemplo: "segunda-feira", "domingo".
            Default: "segunda-feira".

        list_search:
            Lista de termos usados para extrair contexto das notícias.
            Se None, será gerada automaticamente com [client, client_display_name].

        status_classificacao:
            Filtro de status de classificação.
            Default: ["Classificado"].

        tipos_de_impactos:
            Filtro de tipos de impacto.
            Default: ["Promotores", "Detratores", "Inócuos"].

        representa_empresa:
            Filtro para publicações que representam a empresa.
            Default: "Sim".

        tier:
            Filtro de tiers da mídia.
            Default: ["Tier 1", "Tier 2"].

        model:
            Modelo LLM usado nas etapas generativas.
            Default: "gpt-4.1-mini".

        temperature:
            Temperatura do modelo LLM.
            Default: 0.2.

        max_retries:
            Número máximo de tentativas nas chamadas LLM.
            Default: 3.

    Returns:
        dict:
            Dicionário com:
                - status: status da execução.
                - insights: insights finais consolidados.
                - highlights: highlights executivos.
                - contexto_noticias: resumo/contexto narrativo das notícias.
                - contexto_negocios: contexto de negócio da empresa.
                - contexto_dia: contexto por principais dias.
                - contexto_veiculos: contexto por principais veículos.
                - contexto_assuntos: contexto por principais assuntos.
                - state: estado completo final do LangGraph.
    """

    initial_state = build_initial_coverage_state(
        url_platform=url_platform,
        end_date=end_date,
        analysis_start_date=analysis_start_date,
        client=client,
        client_display_name=client_display_name,
        produto_analisado=produto_analisado,
        period=period,
        period_label=period_label,
        anchor_weekday=anchor_weekday,
        list_search=list_search,
        status_classificacao=status_classificacao,
        tipos_de_impactos=tipos_de_impactos,
        representa_empresa=representa_empresa,
        tier=tier,
        model=model,
        temperature=temperature,
        max_retries=max_retries,
    )

    graph = build_coverage_orchestrator_graph()
    result = graph.invoke(initial_state)
    result = make_msgpack_safe(result)

    formatted = format_orchestrator_output(
        result=result,
        output_type="insights",
        return_debug=False,
    )
    return make_msgpack_safe(formatted["final_answer"])

@tool(args_schema=CoverageOrchestratorInput)
async def insights_orchestrator_analysis_media_tool_async(
    url_platform: str,
    end_date: str,
    analysis_start_date: str,
    client: str,
    client_display_name: str,
    produto_analisado: list[str],
    period: str = "mes",
    period_label: str | None = None,
    anchor_weekday: str = "segunda-feira",
    list_search: list[str] | None = None,
    status_classificacao: list[str] | None = None,
    tipos_de_impactos: list[str] | None = None,
    representa_empresa: str = "Sim",
    tier: list[str] | None = None,
    model: str = "gpt-4.1-mini",
    temperature: float = 0.2,
    max_retries: int = 3,
):
    """
    Executa o orquestrador assíncrono de análise de mídia.

    Esta versão usa graph.ainvoke(initial_state), permitindo que o LangGraph
    execute ramos independentes do fluxo em paralelo quando possível.

    Fluxo executado:
        1. Captura dados da plataforma.
        2. Gera padrão de exposição.
        3. Gera contexto narrativo das notícias.
        4. Gera contexto de negócios.
        5. Gera highlights executivos.
        6. Consolida insights finais.

    Paralelização:
        Após a captura de dados, o grafo pode executar em paralelo:
            - node_padrao_exposicao
            - node_contexto_negocios

        Depois de node_padrao_exposicao, pode executar em paralelo:
            - node_highlights
            - node_contexto_exposicao

        O node_insights roda somente após a conclusão de:
            - node_highlights
            - node_contexto_exposicao
            - node_contexto_negocios

    Regras automáticas:
        - start_date da captura = end_date menos 1 ano.
        - analysis_start_date é usado no contexto das notícias.
        - year é extraído de end_date.
        - data_ancora_semana é calculada a partir de end_date.
        - list_search usa [client, client_display_name] quando None.
        - company_name nos insights usa client_display_name.

    Args:
        url_platform:
            URL da plataforma de mídia.

        end_date:
            Data final da análise, no formato YYYY-MM-DD.

        analysis_start_date:
            Data inicial do recorte analisado, no formato YYYY-MM-DD.

        client:
            Nome normalizado da empresa na base.

        client_display_name:
            Nome amigável usado nos textos.

        produto_analisado:
            Lista de produtos, marcas ou aliases usados na captura.

        period:
            Granularidade analítica. Default: "mes".

        period_label:
            Rótulo textual do período analisado.

        anchor_weekday:
            Dia da semana usado para calcular a data âncora semanal.

        list_search:
            Termos usados para busca no contexto das notícias.

        status_classificacao:
            Status considerados na captura.

        tipos_de_impactos:
            Tipos de impacto considerados.

        representa_empresa:
            Filtro de representação da empresa.

        tier:
            Tiers de mídia considerados.

        model:
            Modelo LLM usado nas etapas generativas.

        temperature:
            Temperatura do modelo.

        max_retries:
            Número máximo de tentativas.

    Returns:
        dict:
            Dicionário com status, insights, highlights, contexto_noticias,
            contexto_negocios, detalhes intermediários e state final.
    """
    
    initial_state = build_initial_coverage_state(
        url_platform=url_platform,
        end_date=end_date,
        analysis_start_date=analysis_start_date,
        client=client,
        client_display_name=client_display_name,
        produto_analisado=produto_analisado,
        period=period,
        period_label=period_label,
        anchor_weekday=anchor_weekday,
        list_search=list_search,
        status_classificacao=status_classificacao,
        tipos_de_impactos=tipos_de_impactos,
        representa_empresa=representa_empresa,
        tier=tier,
        model=model,
        temperature=temperature,
        max_retries=max_retries,
    )

    graph = build_coverage_orchestrator_graph()
    result = await graph.ainvoke(initial_state)
    result = make_msgpack_safe(result)

    formatted = format_orchestrator_output(
        result=result,
        output_type="insights",
        return_debug=False,
    )

    return make_msgpack_safe(formatted["final_answer"])


@tool(args_schema=CoverageOrchestratorInput)
def insights_orchestrator_with_whatsapp_tool(**kwargs):
    """
    Executa o orquestrador completo dos insights de análise de cobertura de mídia
    e gera, além dos insights estratégicos, uma mensagem executiva pronta
    para envio via WhatsApp.

    Esta tool integra múltiplas etapas analíticas em um único fluxo:
        1. Captura de dados de mídia na plataforma.
        2. Construção do padrão de exposição (métricas, NPS, protagonismo, etc.).
        3. Extração de contexto narrativo das notícias (por dia, veículo e assunto).
        4. Geração de contexto de negócios da empresa.
        5. Geração de highlights executivos.
        6. Consolidação de insights estratégicos.
        7. Geração de mensagem executiva no formato WhatsApp.

    O fluxo é executado via LangGraph com paralelização automática
    entre etapas independentes.

    Regras automáticas aplicadas:
        - O período de captura de dados considera 1 ano anterior ao end_date.
        - O analysis_start_date é utilizado apenas no contexto das notícias.
        - O ano (year) é derivado automaticamente do end_date.
        - A data âncora semanal é calculada a partir do end_date e do dia da semana informado.
        - Se list_search não for fornecido, utiliza [client, client_display_name].
        - O nome da empresa nos insights e no WhatsApp usa client_display_name.

    Args:
        kwargs:
            Parâmetros definidos no schema CoverageOrchestratorInput, incluindo:
                - url_platform
                - end_date
                - analysis_start_date
                - client
                - client_display_name
                - produto_analisado
                - period
                - period_label
                - anchor_weekday
                - list_search
                - status_classificacao
                - tipos_de_impactos
                - representa_empresa
                - tier
                - model
                - temperature
                - max_retries

    Returns:
        dict:
            Estrutura com os principais outputs do pipeline:

                status:
                    Status da execução ("success" ou "error").

                insights:
                    Insights estratégicos consolidados da análise.

                whatsapp_message:
                    Mensagem executiva otimizada para envio via WhatsApp,
                    construída a partir de big numbers, contexto de cobertura
                    e insights.

                highlights:
                    Highlights executivos derivados das métricas, veículos,
                    dias e assuntos.

                contexto_noticias:
                    Contexto narrativo estruturado da cobertura de mídia.

                contexto_negocios:
                    Contexto estratégico da empresa (mercado, riscos,
                    oportunidades e objetivos).

                state:
                    Estado completo final do LangGraph, contendo todos os
                    dados intermediários e outputs gerados ao longo do fluxo.
    """    
    initial_state = make_msgpack_safe(build_initial_coverage_state(**kwargs))

    graph = build_coverage_orchestrator_graph_with_whatsapp()
    result = graph.invoke(initial_state)
    result = make_msgpack_safe(result)
    formatted = format_orchestrator_output(
        result=result,
        output_type="whatsapp",
        return_debug=False,
        )

    return make_msgpack_safe(formatted["final_answer"])

@tool(args_schema=CoverageOrchestratorInput)
async def insights_orchestrator_with_whatsapp_tool_async(**kwargs):
    """
    Executa o orquestrador completo dos insights de análise de cobertura de mídia de forma assíncrona,
    incluindo a geração de insights estratégicos e uma mensagem executiva para WhatsApp.

    Esta versão utiliza execução assíncrona (`graph.ainvoke`), permitindo paralelização
    eficiente entre etapas independentes do pipeline, reduzindo o tempo total de execução
    em cenários com múltiplas chamadas de I/O ou LLM.

    Fluxo executado:
        1. Captura de dados de mídia.
        2. Construção do padrão de exposição.
        3. Extração de contexto narrativo das notícias.
        4. Geração de contexto de negócios.
        5. Geração de highlights executivos.
        6. Consolidação de insights estratégicos.
        7. Geração de mensagem executiva para WhatsApp.

    Paralelização:
        - Após a captura, são executados em paralelo:
            • padrão de exposição
            • contexto de negócios

        - Após o padrão de exposição:
            • highlights
            • contexto da exposição

        - O node de insights aguarda:
            • highlights
            • contexto da exposição
            • contexto de negócios

        - O node de WhatsApp é executado após os insights.

    Regras automáticas:
        - start_date da captura = end_date - 1 ano
        - analysis_start_date usado apenas no contexto de notícias
        - year derivado automaticamente de end_date
        - data_ancora_semana calculada via anchor_weekday
        - list_search default = [client, client_display_name]
        - company_name = client_display_name nos insights e WhatsApp

    Args:
        kwargs:
            Parâmetros definidos no CoverageOrchestratorInput, incluindo:

                url_platform:
                    URL da plataforma de dados de mídia.

                end_date:
                    Data final da análise (YYYY-MM-DD).

                analysis_start_date:
                    Data inicial do período analisado no contexto de notícias.

                client:
                    Nome normalizado da empresa na base.

                client_display_name:
                    Nome amigável da empresa.

                produto_analisado:
                    Lista de produtos/marcas utilizados na captura.

                period:
                    Granularidade analítica ("dia", "semana", "mes", "ano").

                period_label:
                    Rótulo textual do período (ex: "Março de 2026").

                anchor_weekday:
                    Dia da semana usado para cálculo da data âncora.

                list_search:
                    Termos usados para extração de contexto das notícias.

                status_classificacao:
                    Filtro de classificação dos conteúdos.

                tipos_de_impactos:
                    Tipos de impacto considerados.

                representa_empresa:
                    Filtro de representatividade da empresa.

                tier:
                    Níveis de mídia considerados.

                model:
                    Modelo LLM utilizado.

                temperature:
                    Temperatura do modelo.

                max_retries:
                    Número máximo de tentativas para chamadas LLM.

    Returns:
        dict:
            Dicionário contendo:

                status:
                    Status da execução.

                insights:
                    Insights estratégicos consolidados.

                whatsapp_message:
                    Mensagem executiva pronta para WhatsApp.

                highlights:
                    Highlights executivos.

                contexto_noticias:
                    Contexto narrativo da cobertura.

                contexto_negocios:
                    Contexto estratégico da empresa.

                state:
                    Estado completo do grafo com todos os dados intermediários.
    """
    
    initial_state = make_msgpack_safe(build_initial_coverage_state(**kwargs))
    
    graph = build_coverage_orchestrator_graph_with_whatsapp()

    result = await graph.ainvoke(initial_state)
    result = make_msgpack_safe(result)

    formatted = format_orchestrator_output(
        result=result,
        output_type="whatsapp",
        return_debug=False,
        )

    return make_msgpack_safe(formatted["final_answer"])

@tool(args_schema=CoverageOrchestratorInput)
def insights_orchestrator_with_meeting_insights_tool(**kwargs):
    """
    Executa o orquestrador completo de análise de mídia e gera um
    script executivo de reunião baseado nos insights estratégicos da cobertura.

    Esta tool executa um pipeline analítico completo utilizando LangGraph,
    consolidando métricas quantitativas, contexto narrativo das notícias,
    highlights executivos e contexto de negócios da empresa para gerar
    um material estruturado de apoio para reuniões executivas.

    O fluxo inclui:
        1. Captura e preparação da base de mídia.
        2. Construção dos indicadores de exposição.
        3. Geração de contexto narrativo da cobertura.
        4. Geração de contexto estratégico de negócios.
        5. Geração de highlights executivos.
        6. Consolidação dos insights finais.
        7. Construção do script executivo de reunião.
        8. Salvamento automático dos arquivos gerados.

    Fluxo executado:
        node_captura_dados
            ↓
        ├── node_padrao_exposicao
        │       ├── node_highlights
        │       └── node_contexto_exposicao
        │
        └── node_contexto_negocios
                    ↓
              node_insights
                    ↓
         node_meeting_insights
                    ↓
                   END

    Paralelização:
        Após a captura de dados:
            - node_padrao_exposicao
            - node_contexto_negocios

        Após node_padrao_exposicao:
            - node_highlights
            - node_contexto_exposicao

        O node_insights aguarda:
            - node_highlights
            - node_contexto_exposicao
            - node_contexto_negocios

        O node_meeting_insights é executado somente após a geração
        consolidada dos insights estratégicos.

    Objetivo do script gerado:
        O material final é pensado para:
            - reuniões executivas com clientes;
            - apresentações estratégicas;
            - alinhamentos internos;
            - preparação de porta-vozes;
            - planejamento de comunicação;
            - storytelling executivo;
            - reuniões de acompanhamento reputacional.

    Conteúdos utilizados na geração:
        - Big Numbers da cobertura
        - Indicadores de reputação/NPS
        - Highlights executivos
        - Principais temas
        - Principais veículos
        - Principais dias da cobertura
        - Contexto estratégico da empresa
        - Contexto narrativo da imprensa
        - Insights consolidados

    Regras automáticas:
        - O período de captura considera 1 ano anterior ao end_date.
        - analysis_start_date é usado apenas no contexto da exposição.
        - year é derivado automaticamente de end_date.
        - data_ancora_semana é calculada automaticamente.
        - list_search usa [client, client_display_name] quando None.
        - company_name assume client_display_name.
        - O script é salvo automaticamente em JSON e Markdown.
        - output_dir e base_filename podem ser customizados via state.

    Args:
        kwargs:
            Parâmetros definidos no schema CoverageOrchestratorInput.

            Principais parâmetros:

            url_platform:
                URL da plataforma de mídia.

            end_date:
                Data final da análise no formato YYYY-MM-DD.

            analysis_start_date:
                Data inicial do período analisado.

            client:
                Nome normalizado da empresa na base.

            client_display_name:
                Nome amigável da empresa usado nos textos.

            produto_analisado:
                Lista de produtos, marcas ou aliases usados na captura.

            period:
                Granularidade analítica.
                Ex: "dia", "semana", "mes", "ano".

            period_label:
                Label textual do período analisado.

            anchor_weekday:
                Dia usado como referência para fechamento semanal.

            list_search:
                Lista de termos usados no contexto da exposição.

            status_classificacao:
                Status considerados na captura.

            tipos_de_impactos:
                Tipos de impacto utilizados.

            representa_empresa:
                Filtro de representatividade da empresa.

            tier:
                Tiers de mídia considerados.

            model:
                Modelo LLM utilizado nas etapas generativas.

            temperature:
                Temperatura do modelo.

            max_retries:
                Número máximo de retries para chamadas LLM.

    Returns:
        dict:
            Estrutura contendo:

                status:
                    Status da execução.

                insights:
                    Insights estratégicos consolidados.

                meeting_insights:
                    Resultado bruto do node de reunião.

                meeting_script:
                    Estrutura final do script executivo.

                files:
                    Caminhos dos arquivos salvos.

                highlights:
                    Highlights executivos gerados.

                contexto_noticias:
                    Contexto narrativo da cobertura.

                contexto_negocios:
                    Contexto estratégico da empresa.

                state:
                    Estado completo final do LangGraph.
    """

    initial_state = make_msgpack_safe(build_initial_coverage_state(**kwargs))

    graph = build_coverage_orchestrator_graph_with_meeting_insights()

    result = graph.invoke(initial_state)
    result = make_msgpack_safe(result)

    formatted = format_orchestrator_output(
        result=result,
        output_type="meeting_script",
        return_debug=False,
    )

    return make_msgpack_safe(formatted["final_answer"])


@tool(args_schema=CoverageOrchestratorInput)
async def insights_orchestrator_with_meeting_insights_tool_async(**kwargs):
    """
    Executa o orquestrador assíncrono completo de análise de mídia
    com geração automatizada de script executivo de reunião.

    Esta versão utiliza execução assíncrona via graph.ainvoke(),
    permitindo que o LangGraph execute ramos independentes do fluxo
    em paralelo quando possível.

    O pipeline combina:
        - captura de mídia;
        - indicadores quantitativos;
        - contexto narrativo;
        - contexto estratégico;
        - highlights executivos;
        - insights consolidados;
        - geração de material executivo para reuniões.

    Fluxo executado:
        1. Captura dados da plataforma.
        2. Gera padrão de exposição.
        3. Gera contexto narrativo das notícias.
        4. Gera contexto de negócios.
        5. Gera highlights executivos.
        6. Consolida insights finais.
        7. Gera o script executivo de reunião.
        8. Salva os arquivos finais automaticamente.

    Estrutura do grafo:
        node_captura_dados
            ↓
        ├── node_padrao_exposicao
        │       ├── node_highlights
        │       └── node_contexto_exposicao
        │
        └── node_contexto_negocios
                    ↓
              node_insights
                    ↓
         node_meeting_insights
                    ↓
                   END

    Paralelização:
        Após a captura de dados:
            - node_padrao_exposicao
            - node_contexto_negocios

        Após node_padrao_exposicao:
            - node_highlights
            - node_contexto_exposicao

        node_insights aguarda:
            - node_highlights
            - node_contexto_exposicao
            - node_contexto_negocios

        node_meeting_insights roda somente após os insights consolidados.

    Objetivos do material gerado:
        - suporte a reuniões executivas;
        - construção de storytelling estratégico;
        - preparação de porta-vozes;
        - alinhamento de comunicação;
        - apoio comercial;
        - apresentações reputacionais;
        - análises de performance institucional.

    Dados utilizados:
        - métricas quantitativas;
        - NPS reputacional;
        - protagonismo;
        - principais temas;
        - principais veículos;
        - principais dias;
        - contexto da imprensa;
        - contexto estratégico;
        - insights finais consolidados.

    Regras automáticas:
        - start_date da captura = end_date menos 1 ano.
        - analysis_start_date é usado no contexto das notícias.
        - year é extraído automaticamente de end_date.
        - data_ancora_semana é calculada automaticamente.
        - list_search usa [client, client_display_name] quando None.
        - company_name assume client_display_name.
        - Os arquivos finais são salvos automaticamente.

    Args:
        kwargs:
            Parâmetros definidos no schema CoverageOrchestratorInput.

            Inclui:
                - url_platform
                - end_date
                - analysis_start_date
                - client
                - client_display_name
                - produto_analisado
                - period
                - period_label
                - anchor_weekday
                - list_search
                - status_classificacao
                - tipos_de_impactos
                - representa_empresa
                - tier
                - model
                - temperature
                - max_retries

    Returns:
        dict:
            Estrutura contendo:

                status:
                    Status da execução.

                insights:
                    Insights estratégicos consolidados.

                meeting_insights:
                    Resultado bruto do node de reunião.

                meeting_script:
                    Estrutura executiva final gerada.

                files:
                    Caminhos dos arquivos salvos.

                highlights:
                    Highlights executivos.

                contexto_noticias:
                    Contexto narrativo da cobertura.

                contexto_negocios:
                    Contexto estratégico da empresa.

                state:
                    Estado completo final do LangGraph.
    """

    initial_state = make_msgpack_safe(build_initial_coverage_state(**kwargs))

    graph = build_coverage_orchestrator_graph_with_meeting_insights()

    result = await graph.ainvoke(initial_state)
    result = make_msgpack_safe(result)
    
    formatted = format_orchestrator_output(
        result=result,
        output_type="meeting_script",
        return_debug=False,
    )

    return make_msgpack_safe(formatted["final_answer"])