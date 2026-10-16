from __future__ import annotations

from langchain_core.tools import tool

from src.tools_agents.platform.schemas import (
    ExportDatabaseMAInput, ExportDatabaseMAOutput, ExportDatabaseMAMeta, 
    ExportActionDatabaseInput,  ExportActionDatabaseMeta, ExportActionDatabaseOutput,
    ExportDatabasePublInput, ExportDatabasePublMeta, ExportDatabasePublOutput, 
    GetInfosBrandInput, GetInfosBrandMeta, GetInfosBrandOutput,
    GetPRDataDataFrameInput, GetPRDataDataFrameMeta, GetPRDataDataFrameOutput, GetPRDataOpenSourceDataFrameInput,
    GetMSSDataFrameInput, GetMSSDataFrameMeta, GetMSSDataFrameOutput,
    ToolErrorOutput )

from src.tools_agents.platform.services import (export_media_analysis_database, export_action_database_service, 
                                                export_publications_database_service, get_infos_brand_service, 
                                                get_prdata_dataframe_service, get_prdata_open_source_service,
                                                get_mss_dataframe_service)

from core.dataframe_store import save_dataframe, get_dataframe


#################################################
#################################################

@tool("get_dataframe")
def get_dataframe_tool(dataframe_id: str) -> dict:
    """
    Recupera um DataFrame previamente armazenado.
    use a tool quando for necesserário ler do dataframe
    """

    df = get_dataframe(dataframe_id)

    return {
        "status": "success",
        "rows": len(df),
        "columns": list(df.columns),
        "df": df
    }


@tool("export_media_analysis_database", args_schema=ExportDatabaseMAInput)
def export_media_analysis_database_tool(
    url_platform: str,
    start_date: str | None = None,
    end_date: str | None = None,
    empresa_analisada=None,
    produto_analisado=None,
    midia=None,
    tier=None,
    estado=None,
    tipos_de_impactos=None,
    sentimento=None,
    protagonismo=None,
    topico=None,
    assuntos_especifico=None,
    acao_comunicacao=None,
    origem_mencao=None,
    jornalista=None,
    temas=None,
    macro_assunto=None,
    representa_empresa=None,
    status_classificacao=None,
) -> dict:
    """
    Exporta a base de análise de mídia da plataforma Cortex.
    Use a tool quando for necessário fazer download dos dados da base de anállise de mídia da plataforma.
    """

    try:
        params = ExportDatabaseMAInput(
            url_platform=url_platform,
            start_date=start_date,
            end_date=end_date,
            empresa_analisada=empresa_analisada,
            produto_analisado=produto_analisado,
            midia=midia,
            tier=tier,
            estado=estado,
            tipos_de_impactos=tipos_de_impactos,
            sentimento=sentimento,
            protagonismo=protagonismo,
            topico=topico,
            assuntos_especifico=assuntos_especifico,
            acao_comunicacao=acao_comunicacao,
            origem_mencao=origem_mencao,
            jornalista=jornalista,
            temas=temas,
            macro_assunto=macro_assunto,
            representa_empresa=representa_empresa,
            status_classificacao=status_classificacao,
        )

        df = export_media_analysis_database(params)
        df_id = save_dataframe(
        df=df,
        source="export_media_analysis",
        filters=params.to_service_kwargs(),
        )

        output = ExportDatabaseMAOutput(
        message="Base exportada com sucesso.",
        dataframe_id=df_id,
        meta=ExportDatabaseMAMeta(
            rows=int(len(df)),
            columns_count=int(len(df.columns)),
            columns=list(df.columns),
            filters_applied=params.to_service_kwargs(),
        ),
        preview=df.head(10).to_dict(orient="records"),
            )
        
        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao executar exportação da base.",
            error_type=type(e).__name__,
            details=str(e),
        )

        return error_output.model_dump()
    

@tool("export_action_database", args_schema=ExportActionDatabaseInput)
def export_action_database_tool(
    url_platform: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Exporta a base de ações de comunicação da plataforma Cortex para um período específico.
    Use esta tool quando for necessário obter a base de ações cadastradas na plataforma.
    """
    try:
        params = ExportActionDatabaseInput(
            url_platform=url_platform,
            start_date=start_date,
            end_date=end_date,
        )

        df = export_action_database_service(params)

        dataframe_id = save_dataframe(
            df=df,
            source="export_action_database",
            filters=params.to_service_kwargs(),
        )

        output = ExportActionDatabaseOutput(
            message="Base de ações exportada com sucesso.",
            dataframe_id=dataframe_id,
            meta=ExportActionDatabaseMeta(
                rows=int(len(df)),
                columns_count=int(len(df.columns)),
                columns=list(df.columns),
                filters_applied=params.to_service_kwargs(),
            ),
            preview=df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao executar exportação da base de ações.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    

@tool("export_publications_database", args_schema=ExportDatabasePublInput)
def export_publications_database_tool(
    url_platform: str,
    start_date: str | None = None,
    end_date: str | None = None,
    empresa_citada=None,
    produto_citado=None,
    midia=None,
    tier=None,
    estado=None,
) -> dict:
    """
    Exporta a base de publicações da plataforma Cortex com filtros de período,
    empresa citada, produto citado, mídia, tier e estado.
    """
    try:
        params = ExportDatabasePublInput(
            url_platform=url_platform,
            start_date=start_date,
            end_date=end_date,
            empresa_citada=empresa_citada,
            produto_citado=produto_citado,
            midia=midia,
            tier=tier,
            estado=estado,
        )

        df = export_publications_database_service(params)

        dataframe_id = save_dataframe(
            df=df,
            source="export_publications_database",
            filters=params.to_service_kwargs(),
        )

        output = ExportDatabasePublOutput(
            message="Base de publicações exportada com sucesso.",
            dataframe_id=dataframe_id,
            meta=ExportDatabasePublMeta(
                rows=int(len(df)),
                columns_count=int(len(df.columns)),
                columns=list(df.columns),
                filters_applied=params.to_service_kwargs(),
            ),
            preview=df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao executar exportação da base de publicações.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()   
    

@tool("get_brand_info", args_schema=GetInfosBrandInput)
def get_brand_info_tool(url_platform: str) -> dict:
    """
    Obtém as informações  sobre as marcas e produtos do cliente cadastradas na plataforma Cortex.
    Use esta tool quando for necessário recuperar dados institucionais ou metadados da marca na plataforma.
    """
    try:
        params = GetInfosBrandInput(
            url_platform=url_platform,
        )

        df = get_infos_brand_service(params)

        dataframe_id = save_dataframe(
            df=df,
            source="get_brand_info",
            filters=params.to_service_kwargs(),
        )

        output = GetInfosBrandOutput(
            message="Informações da marca obtidas com sucesso.",
            dataframe_id=dataframe_id,
            meta=GetInfosBrandMeta(
                rows=int(len(df)),
                columns_count=int(len(df.columns)),
                columns=list(df.columns),
                filters_applied=params.to_service_kwargs(),
            ),
            preview=df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao obter informações da marca.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    
@tool("get_prdata_dataframe", args_schema=GetPRDataDataFrameInput)
def get_prdata_dataframe_tool(
    start_date: str,
    end_date: str,
    therms_values,
    media_outlets=None,
) -> dict:
    """
    Obtém dados do PRData, com todas as notícias capturadas pelo fornecedores da Cortex, a partir de um período, uma lista de termos e,
    opcionalmente, uma lista de veículos de mídia.
    """
    try:
        params = GetPRDataDataFrameInput(
            start_date=start_date,
            end_date=end_date,
            therms_values=therms_values,
            media_outlets=media_outlets,
        )

        df = get_prdata_dataframe_service(params)

        dataframe_id = save_dataframe(
            df=df,
            source="get_prdata_dataframe",
            filters=params.to_service_kwargs(),
        )

        output = GetPRDataDataFrameOutput(
            message="DataFrame do PRData obtido com sucesso.",
            dataframe_id=dataframe_id,
            meta=GetPRDataDataFrameMeta(
                rows=int(len(df)),
                columns_count=int(len(df.columns)),
                columns=list(df.columns),
                filters_applied=params.to_service_kwargs(),
            ),
            preview=df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao obter DataFrame do PRData.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()

@tool("get_prdata_dataframe", args_schema=GetPRDataOpenSourceDataFrameInput)
def get_prdata_opensource_tool(
    start_date: str,
    end_date: str,
    therms_values,
    media_outlets=None,
    midia_publicada=None,
) -> dict:
    """
    Obtém dados do PRData Twingly e Redes Sociais com base no período, termos e,
    opcionalmente, veículos de mídia e mídias publicadas.
    """
    try:
        params = GetPRDataOpenSourceDataFrameInput(
            start_date=start_date,
            end_date=end_date,
            therms_values=therms_values,
            media_outlets=media_outlets,
            midia_publicada=midia_publicada,
        )

        df = get_prdata_open_source_service(params)

        dataframe_id = save_dataframe(
            df=df,
            source="get_prdata_dataframe",
            filters=params.to_service_kwargs(),
        )

        output = GetPRDataDataFrameOutput(
            message="DataFrame do PRData obtido com sucesso.",
            dataframe_id=dataframe_id,
            meta=GetPRDataDataFrameMeta(
                rows=int(len(df)),
                columns_count=int(len(df.columns)),
                columns=list(df.columns),
                filters_applied=params.to_service_kwargs(),
            ),
            preview=df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao obter DataFrame do PRData.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()


@tool("get_mss_dataframe", args_schema=GetMSSDataFrameInput)
def get_mss_dataframe_tool(
    veiculos_mss=None,
    veiculos_fornecedor=None,
    fornecedores=None,
    tier=None,
    tipo_publico=None,
    estados=None,
    cidades=None,
    pais=None,
) -> dict:
    """
    Obtém um DataFrame sobre os veículos monitorados pela Cortex. A base é MSS é pode ser filtradas por veículos, fornecedores,
    tier, público, estados, cidades e país. Nesta base, pode ser chegado o alcance dos veículos, fornecedores, cidade, estado, país
    """
    try:
        params = GetMSSDataFrameInput(
            veiculos_mss=veiculos_mss,
            veiculos_fornecedor=veiculos_fornecedor,
            fornecedores=fornecedores,
            tier=tier,
            tipo_publico=tipo_publico,
            estados=estados,
            cidades=cidades,
            pais=pais,
        )

        df = get_mss_dataframe_service(params)

        dataframe_id = save_dataframe(
            df=df,
            source="get_mss_dataframe",
            filters=params.to_service_kwargs(),
        )

        output = GetMSSDataFrameOutput(
            message="DataFrame MSS obtido com sucesso.",
            dataframe_id=dataframe_id,
            meta=GetMSSDataFrameMeta(
                rows=int(len(df)),
                columns_count=int(len(df.columns)),
                columns=list(df.columns),
                filters_applied=params.to_service_kwargs(),
            ),
            preview=df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao obter DataFrame MSS.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    


