from __future__ import annotations

from langchain_core.tools import tool

from core.dataframe_store import save_dataframe
from src.tools_agents.communication_indexes.schemas import (
    GenDataviewsInput, GenDataviewsMeta, GenDataviewsOutput,
    CalcNPSScoreInput, CalcNPSScoreMeta, CalcNPSScoreOutput,
    NPSTotalAndContribInput, NPSTotalAndContribMeta, NPSTotalAndContribOutput,
    ProtagonismScoreInput, ProtagonismScoreMeta, ProtagonismScoreOutput,
    FreqScoreInput, FreqScoreMeta, FreqScoreOutput,
    ValorationScoreInput, ValorationScoreMeta, ValorationScoreOutput,
    JornalistaScoreInput, JornalistaScoreMeta, JornalistaScoreOutput,
    ActionScoreInput, ActionScoreMeta, ActionScoreOutput,
    ToolErrorOutput,
)
from src.tools_agents.communication_indexes.services import (gen_dataviews_service, calc_nps_score_service, 
                                                             nps_total_and_contrib_service, protagonism_score_service, 
                                                             freq_score_service, valoration_score_service, jornalista_score_service,
                                                            action_score_service )


@tool("generate_dataviews", args_schema=GenDataviewsInput)
def gen_dataviews_tool(
    dataframe_id: str,
    data_ancora_semana: str | None = None,
) -> dict:
    """
    Gera um dataview a partir de um DataFrame previamente armazenado.
    Permite configurar opcionalmente uma data âncora para definição da semana.
    """
    try:
        params = GenDataviewsInput(
            dataframe_id=dataframe_id,
            data_ancora_semana=data_ancora_semana,
        )

        result_df = gen_dataviews_service(params)

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="generate_dataviews",
            filters={
                "source_dataframe_id": dataframe_id,
                "data_ancora_semana": params.data_ancora_semana,
            },
        )

        output = GenDataviewsOutput(
            message="Dataview gerado com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=GenDataviewsMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="gen_dataviews",
                filters_applied={
                    "source_dataframe_id": dataframe_id,
                    "data_ancora_semana": params.data_ancora_semana,
                },
            ),
            preview=result_df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao gerar dataview.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    


@tool("calculate_nps_score", args_schema=CalcNPSScoreInput)
def calc_nps_score_tool(
    dataframe_id: str,
    value_col: str = "alcance",
    impacto_col: str = "Tipos de impactos",
    group_cols = None,
    sum_cols = None,
    dedupe_columns: bool = True,
) -> dict:
    """
    Calcula o NPS de um DataFrame previamente armazenado, com base nos tipos de impacto.
    """
    try:
        params = CalcNPSScoreInput(
            dataframe_id=dataframe_id,
            value_col=value_col,
            impacto_col=impacto_col,
            group_cols=group_cols if group_cols is not None else ["Data", "Empresa analisada"],
            sum_cols=sum_cols if sum_cols is not None else ["alcance", "valoracao", "count"],
            dedupe_columns=dedupe_columns,
        )

        result_df = calc_nps_score_service(params)

        applied_filters = {
            "source_dataframe_id": dataframe_id,
            "value_col": params.value_col,
            "impacto_col": params.impacto_col,
            "group_cols": params.group_cols,
            "sum_cols": params.sum_cols,
            "dedupe_columns": params.dedupe_columns,
        }

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="calculate_nps_score",
            filters=applied_filters,
        )

        output = CalcNPSScoreOutput(
            message="Cálculo de NPS executado com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=CalcNPSScoreMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="calc_nps_score",
                filters_applied=applied_filters,
            ),
            preview=result_df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao calcular NPS.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    

@tool("nps_total_and_contrib", args_schema=NPSTotalAndContribInput)
def nps_total_and_contrib_tool(
    dataframe_id: str,
    dim_col: str,
    value_col: str = "alcance",
    impacto_col: str = "Tipos de impactos",
    group_cols=None,
    impacts=None,
    contr_type: str = "Total",
    round_total: int = 2,
    round_contrib: int = 4,
) -> dict:
    """
    Calcula o NPS total e a contribuição por dimensão em um DataFrame previamente armazenado.
    """
    try:
        params = NPSTotalAndContribInput(
            dataframe_id=dataframe_id,
            dim_col=dim_col,
            value_col=value_col,
            impacto_col=impacto_col,
            group_cols=group_cols if group_cols is not None else ["Data", "Empresa analisada"],
            impacts=impacts if impacts is not None else ["Promotores", "Detratores", "Inócuos"],
            contr_type=contr_type,
            round_total=round_total,
            round_contrib=round_contrib,
        )

        result_df = nps_total_and_contrib_service(params)

        applied_filters = {
            "source_dataframe_id": dataframe_id,
            "dim_col": params.dim_col,
            "value_col": params.value_col,
            "impacto_col": params.impacto_col,
            "group_cols": params.group_cols,
            "impacts": params.impacts,
            "contr_type": params.contr_type,
            "round_total": params.round_total,
            "round_contrib": params.round_contrib,
        }

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="nps_total_and_contrib",
            filters=applied_filters,
        )

        output = NPSTotalAndContribOutput(
            message="Cálculo de NPS total e contribuição executado com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=NPSTotalAndContribMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="nps_total_and_contrib",
                filters_applied=applied_filters,
            ),
            preview=result_df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao calcular NPS total e contribuição.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    

@tool("protagonism_score", args_schema=ProtagonismScoreInput)
def protagonism_score_tool(
    dataframe_id: str,
    value_col: str = "alcance",
    impacto_col: str = "Nível de Protagonismo final",
    group_cols=None,
    filter_column: str | None = None,
    filter_value=None,
) -> dict:
    """
    Calcula o protagonism_score em um DataFrame previamente armazenado.
    """
    try:
        params = ProtagonismScoreInput(
            dataframe_id=dataframe_id,
            value_col=value_col,
            impacto_col=impacto_col,
            group_cols=group_cols if group_cols is not None else ["Data", "Empresa analisada"],
            filter_column=filter_column,
            filter_value=filter_value,
        )

        result_df = protagonism_score_service(params)

        applied_filters = {
            "source_dataframe_id": dataframe_id,
            "value_col": params.value_col,
            "impacto_col": params.impacto_col,
            "group_cols": params.group_cols,
            "filter_column": params.filter_column,
            "filter_value": params.filter_value,
        }

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="protagonism_score",
            filters=applied_filters,
        )

        output = ProtagonismScoreOutput(
            message="Cálculo de protagonism_score executado com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=ProtagonismScoreMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="protagonism_score",
                filters_applied=applied_filters,
            ),
            preview=result_df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao calcular protagonism_score.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    
@tool("freq_score", args_schema=FreqScoreInput)
def freq_score_tool(
    dataframe_id: str,
    value_col: str = "count",
    impacto_col: str = "Tipos de impactos",
    group_cols=None,
) -> dict:
    """
    Calcula a frequência por agrupamento em um DataFrame previamente armazenado.
    """
    try:
        params = FreqScoreInput(
            dataframe_id=dataframe_id,
            value_col=value_col,
            impacto_col=impacto_col,
            group_cols=group_cols if group_cols is not None else ["Data", "Empresa analisada"],
        )

        result_df = freq_score_service(params)

        applied_filters = {
            "source_dataframe_id": dataframe_id,
            "value_col": params.value_col,
            "impacto_col": params.impacto_col,
            "group_cols": params.group_cols,
        }

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="freq_score",
            filters=applied_filters,
        )

        output = FreqScoreOutput(
            message="Cálculo de frequência executado com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=FreqScoreMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="freq_score",
                filters_applied=applied_filters,
            ),
            preview=result_df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao calcular frequência.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    

@tool("valoration_score", args_schema=ValorationScoreInput)
def valoration_score_tool(
    dataframe_id: str,
    value_col: str = "valoracao",
    group_cols=None,
) -> dict:
    """
    Calcula a valoração agregada por agrupamento em um DataFrame previamente armazenado.
    """
    try:
        params = ValorationScoreInput(
            dataframe_id=dataframe_id,
            value_col=value_col,
            group_cols=group_cols if group_cols is not None else ["Data", "Empresa analisada"],
        )

        result_df = valoration_score_service(params)

        applied_filters = {
            "source_dataframe_id": dataframe_id,
            "value_col": params.value_col,
            "group_cols": params.group_cols,
        }

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="valoration_score",
            filters=applied_filters,
        )

        output = ValorationScoreOutput(
            message="Cálculo de valoração executado com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=ValorationScoreMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="valoration_score",
                filters_applied=applied_filters,
            ),
            preview=result_df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao calcular valoração.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    

@tool("jornalista_score", args_schema=JornalistaScoreInput)
def jornalista_score_tool(
    dataframe_id: str,
    value_cols=None,
    group_cols=None,
) -> dict:
    """
    Soma métricas de jornalista por agrupamento em um DataFrame previamente armazenado.
    """
    try:
        params = JornalistaScoreInput(
            dataframe_id=dataframe_id,
            value_cols=value_cols if value_cols is not None else ["jornalista_count", "count"],
            group_cols=group_cols if group_cols is not None else ["Data", "Empresa analisada"],
        )

        result_df = jornalista_score_service(params)

        applied_filters = {
            "source_dataframe_id": dataframe_id,
            "value_cols": params.value_cols,
            "group_cols": params.group_cols,
        }

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="jornalista_score",
            filters=applied_filters,
        )

        output = JornalistaScoreOutput(
            message="Cálculo de jornalista_score executado com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=JornalistaScoreMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="jornalista_score",
                filters_applied=applied_filters,
            ),
            preview=result_df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao calcular jornalista_score.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()
    

@tool("action_score", args_schema=ActionScoreInput)
def action_score_tool(
    dataframe_id: str,
    value_cols=None,
    group_cols=None,
) -> dict:
    """
    Calcula o action_score por agrupamento em um DataFrame previamente armazenado.
    """
    try:
        params = ActionScoreInput(
            dataframe_id=dataframe_id,
            value_cols=value_cols if value_cols is not None else ["acao_count", "count"],
            group_cols=group_cols if group_cols is not None else ["Data", "Empresa analisada"],
        )

        result_df = action_score_service(params)

        applied_filters = {
            "source_dataframe_id": dataframe_id,
            "value_cols": params.value_cols,
            "group_cols": params.group_cols,
        }

        result_dataframe_id = save_dataframe(
            df=result_df,
            source="action_score",
            filters=applied_filters,
        )

        output = ActionScoreOutput(
            message="Cálculo de action_score executado com sucesso.",
            dataframe_id=result_dataframe_id,
            meta=ActionScoreMeta(
                source_dataframe_id=dataframe_id,
                result_rows=int(len(result_df)),
                result_columns_count=int(len(result_df.columns)),
                result_columns=list(result_df.columns),
                operation="action_score",
                filters_applied=applied_filters,
            ),
            preview=result_df.head(10).to_dict(orient="records"),
        )

        return output.model_dump()

    except Exception as e:
        error_output = ToolErrorOutput(
            message="Erro ao calcular action_score.",
            error_type=type(e).__name__,
            details=str(e),
        )
        return error_output.model_dump()