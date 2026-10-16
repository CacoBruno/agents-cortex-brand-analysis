from __future__ import annotations

from typing import Dict, Any, Optional, List
import pandas as pd


def _normalize_date_value(value: Any) -> Optional[str]:
    """
    Normaliza um valor de data para string no formato YYYY-MM-DD.
    """
    if pd.isna(value):
        return None

    try:
        dt = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def _normalize_date_series(series: pd.Series) -> pd.Series:
    """
    Normaliza uma série de datas para YYYY-MM-DD.
    """
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d")


def _top_days(
    df: pd.DataFrame,
    *,
    date_col: str,
    metric_col: str,
    n: int,
    ascending: bool,
    only_positive: bool = False,
    only_negative: bool = False,
) -> List[str]:
    """
    Retorna os top N dias únicos com base em uma métrica.
    """
    if metric_col not in df.columns or n <= 0:
        return []

    tmp = df[[date_col, metric_col]].copy()
    tmp[metric_col] = pd.to_numeric(tmp[metric_col], errors="coerce")
    tmp = tmp.dropna(subset=[date_col, metric_col]).copy()

    if only_positive:
        tmp = tmp[tmp[metric_col] > 0]

    if only_negative:
        tmp = tmp[tmp[metric_col] < 0]

    if tmp.empty:
        return []

    tmp = (
        tmp.sort_values(by=metric_col, ascending=ascending)
           .drop_duplicates(subset=[date_col], keep="first")
           .head(n)
    )

    return tmp[date_col].tolist()


def _tier_rank(tier: Any) -> int:
    """
    Converte tier em rank numérico para ordenação.
    Menor número = maior prioridade.
    """
    if pd.isna(tier):
        return 999

    t = str(tier).strip().lower()

    if "tier 1" in t or t == "1" or "t1" in t:
        return 1
    if "tier 2" in t or t == "2" or "t2" in t:
        return 2
    if "tier 3" in t or t == "3" or "t3" in t:
        return 3
    if "tier 4" in t or t == "4" or "t4" in t:
        return 4

    return 999

def select_key_days_from_daily_nps_contrib(
    daily_df: pd.DataFrame,
    *,
    date_col: str = "Data",
    contrib_col: str = "contr_nps_score",
    promoter_col: str = "Promotores",
    detractor_col: str = "Detratores",
    zscore_col: str = "z_score_contr_nps",
    top_n_extra_positive: int = 0,
    top_n_extra_negative: int = 0,
    n_top_contrib: int = 1,
    n_top_negative_contrib: int = 1,
    n_top_promoter: int = 1,
    n_top_detractor: int = 1,
    n_top_zscore: int = 1,
    keep_only_positive_for_contrib: bool = True,
    keep_only_negative_for_negative_contrib: bool = True,
) -> Dict[str, Any]:
    """
    Seleciona os principais dias do período com base em um dataframe diário
    de contribuição para NPS.

    Modos suportados:
    1. Modo antigo:
       - top_n_extra_positive
       - top_n_extra_negative

    2. Modo novo:
       - n_top_contrib
       - n_top_negative_contrib
       - n_top_promoter
       - n_top_detractor
       - n_top_zscore
    """

    df = daily_df.copy()

    required_cols = [date_col, contrib_col, promoter_col, detractor_col, zscore_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes em daily_df: {missing}")

    df[date_col] = _normalize_date_series(df[date_col])

    for col in [contrib_col, promoter_col, detractor_col, zscore_col]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=[date_col]).copy()

    if df.empty:
        return {
            "selected_days": [],
            "rules": {},
            "summary": {},
            "reverse_rules": {},
        }

    # -------------------------
    # modo novo: top N por critério
    # -------------------------
    use_new_mode = any([
        n_top_contrib != 1,
        n_top_negative_contrib != 1,
        n_top_promoter != 1,
        n_top_detractor != 1,
        n_top_zscore != 1,
    ])

    if use_new_mode:
        rules = {
            "dias_maior_contribuicao_nps": _top_days(
                df,
                date_col=date_col,
                metric_col=contrib_col,
                n=n_top_contrib,
                ascending=False,
                only_positive=keep_only_positive_for_contrib,
            ),
            "dias_maior_detracao_nps": _top_days(
                df,
                date_col=date_col,
                metric_col=contrib_col,
                n=n_top_negative_contrib,
                ascending=True,
                only_negative=keep_only_negative_for_negative_contrib,
            ),
            "dias_maior_promotor": _top_days(
                df,
                date_col=date_col,
                metric_col=promoter_col,
                n=n_top_promoter,
                ascending=False,
            ),
            "dias_maior_detrator": _top_days(
                df,
                date_col=date_col,
                metric_col=detractor_col,
                n=n_top_detractor,
                ascending=False,
            ),
            "dias_maior_zscore": _top_days(
                df,
                date_col=date_col,
                metric_col=zscore_col,
                n=n_top_zscore,
                ascending=False,
            ),
        }

        selected_days = list(dict.fromkeys(
            day
            for days in rules.values()
            for day in days
            if day is not None
        ))

    else:
        # -------------------------
        # modo antigo
        # -------------------------
        rules = {}

        valid_contrib = df.dropna(subset=[contrib_col])
        if not valid_contrib.empty:
            idx_max_contrib = valid_contrib[contrib_col].idxmax()
            rules["dia_maior_contribuicao_nps"] = df.loc[idx_max_contrib, date_col]

            idx_min_contrib = valid_contrib[contrib_col].idxmin()
            rules["dia_maior_detracao_nps"] = df.loc[idx_min_contrib, date_col]
        else:
            rules["dia_maior_contribuicao_nps"] = None
            rules["dia_maior_detracao_nps"] = None

        valid_prom = df.dropna(subset=[promoter_col])
        if not valid_prom.empty:
            idx_max_prom = valid_prom[promoter_col].idxmax()
            rules["dia_maior_promotor"] = df.loc[idx_max_prom, date_col]
        else:
            rules["dia_maior_promotor"] = None

        valid_det = df.dropna(subset=[detractor_col])
        if not valid_det.empty:
            idx_max_det = valid_det[detractor_col].idxmax()
            rules["dia_maior_detrator"] = df.loc[idx_max_det, date_col]
        else:
            rules["dia_maior_detrator"] = None

        valid_z = df.dropna(subset=[zscore_col])
        if not valid_z.empty:
            idx_max_z = valid_z[zscore_col].idxmax()
            rules["dia_maior_zscore"] = df.loc[idx_max_z, date_col]
        else:
            rules["dia_maior_zscore"] = None

        extra_positive_days = []
        if top_n_extra_positive > 0:
            positive_df = df.dropna(subset=[contrib_col]).copy()
            positive_df = positive_df[positive_df[contrib_col] > 0]

            if not positive_df.empty:
                extra_positive_days = (
                    positive_df.sort_values(by=contrib_col, ascending=False)
                    .head(top_n_extra_positive)[date_col]
                    .tolist()
                )

        extra_negative_days = []
        if top_n_extra_negative > 0:
            negative_df = df.dropna(subset=[contrib_col]).copy()
            negative_df = negative_df[negative_df[contrib_col] < 0]

            if not negative_df.empty:
                extra_negative_days = (
                    negative_df.sort_values(by=contrib_col, ascending=True)
                    .head(top_n_extra_negative)[date_col]
                    .tolist()
                )

        base_days = [v for v in rules.values() if v is not None]
        selected_days = list(dict.fromkeys(
            base_days + extra_positive_days + extra_negative_days
        ))

    # resumo
    summary = {}
    selected_df = (
        df[df[date_col].isin(selected_days)]
        .drop_duplicates(subset=[date_col])
        .copy()
    )

    for _, row in selected_df.iterrows():
        day = row[date_col]
        summary[day] = {
            "contribuicao_nps": row.get(contrib_col),
            "promotores": row.get(promoter_col),
            "detratores": row.get(detractor_col),
            "z_score": row.get(zscore_col),
        }

    reverse_rules: Dict[str, List[str]] = {}

    if use_new_mode:
        for rule_name, days in rules.items():
            for day in days:
                reverse_rules.setdefault(day, []).append(rule_name)
    else:
        for rule_name, day in rules.items():
            if day is not None:
                reverse_rules.setdefault(day, []).append(rule_name)

    return {
        "selected_days": selected_days,
        "rules": rules,
        "summary": summary,
        "reverse_rules": reverse_rules,
    }

def filter_coverage_dict_by_selected_days(
    coverage_dict: Dict[str, Dict[str, Any]],
    selected_days: List[str],
) -> Dict[str, Dict[str, Any]]:
    """
    Filtra o dicionário de cobertura mantendo apenas os dias selecionados.
    """
    if not coverage_dict:
        return {}

    normalized_selected_days = []
    for day in selected_days:
        nd = _normalize_date_value(day)
        if nd is not None:
            normalized_selected_days.append(nd)

    normalized_selected_days = set(normalized_selected_days)

    normalized_coverage = {}
    for raw_day, payload in coverage_dict.items():
        nd = _normalize_date_value(raw_day)
        if nd is not None:
            normalized_coverage[nd] = payload

    return {
        day: normalized_coverage[day]
        for day in normalized_selected_days
        if day in normalized_coverage
    }

def build_main_days_from_nps_daily_contrib_and_coverage_dict(
    daily_contrib_df: pd.DataFrame,
    coverage_dict: Dict[str, Dict[str, Any]],
    *,
    daily_date_col: str = "Data",
    contrib_col: str = "contr_nps_score",
    promoter_col: str = "Promotores",
    detractor_col: str = "Detratores",
    zscore_col: str = "z_score_contr_nps",
    top_n_extra_positive: int = 0,
    top_n_extra_negative: int = 0,
) -> Dict[str, Any]:
    """
    Seleciona os dias mais relevantes com base no dataframe diário
    e retorna a cobertura correspondente no dicionário.
    """

    selected = select_key_days_from_daily_nps_contrib(
        daily_df=daily_contrib_df,
        date_col=daily_date_col,
        contrib_col=contrib_col,
        promoter_col=promoter_col,
        detractor_col=detractor_col,
        zscore_col=zscore_col,
        top_n_extra_positive=top_n_extra_positive,
        top_n_extra_negative=top_n_extra_negative,
    )

    filtered_coverage = filter_coverage_dict_by_selected_days(
        coverage_dict=coverage_dict,
        selected_days=selected["selected_days"],
    )

    dias_com_cobertura = list(filtered_coverage.keys())
    dias_sem_cobertura = [
        d for d in selected["selected_days"]
        if d not in dias_com_cobertura
    ]

    return {
        "criterios_dias": selected["rules"],
        "dias_selecionados": selected["selected_days"],
        "resumo_dias": selected["summary"],
        "dias_com_cobertura": dias_com_cobertura,
        "dias_sem_cobertura": dias_sem_cobertura,
        "cobertura_por_dia": filtered_coverage,
    }

def build_main_days_coverage_compact_dict(
    daily_contrib_df: pd.DataFrame,
    coverage_dict: Dict[str, Dict[str, Any]],
    *,
    daily_date_col: str = "Data",
    contrib_col: str = "contr_nps_score",
    promoter_col: str = "Promotores",
    detractor_col: str = "Detratores",
    zscore_col: str = "z_score_contr_nps",
    n_top_contrib: int = 1,
    n_top_negative_contrib: int = 1,
    n_top_promoter: int = 1,
    n_top_detractor: int = 1,
    n_top_zscore: int = 1,
    keep_only_positive_for_contrib: bool = True,
    keep_only_negative_for_negative_contrib: bool = True,
) -> Dict[str, Any]:
    """
    Retorna um dicionário compacto por dia, incluindo:
    - critérios que selecionaram o dia
    - métricas do dia
    - cobertura do dia
    """

    selected = select_key_days_from_daily_nps_contrib(
        daily_df=daily_contrib_df,
        date_col=daily_date_col,
        contrib_col=contrib_col,
        promoter_col=promoter_col,
        detractor_col=detractor_col,
        zscore_col=zscore_col,
        n_top_contrib=n_top_contrib,
        n_top_negative_contrib=n_top_negative_contrib,
        n_top_promoter=n_top_promoter,
        n_top_detractor=n_top_detractor,
        n_top_zscore=n_top_zscore,
        keep_only_positive_for_contrib=keep_only_positive_for_contrib,
        keep_only_negative_for_negative_contrib=keep_only_negative_for_negative_contrib,
    )

    filtered_coverage = filter_coverage_dict_by_selected_days(
        coverage_dict=coverage_dict,
        selected_days=selected["selected_days"],
    )

    output = {}
    for day in selected["selected_days"]:
        output[day] = {
            "criterios_de_selecao": selected["reverse_rules"].get(day, []),
            "metricas_do_dia": selected["summary"].get(day, {}),
            **filtered_coverage.get(day, {"tema_dominante": None, "documentos": []}),
        }

    return {
        "dias_por_criterio": selected["rules"],
        "dias_selecionados": selected["selected_days"],
        "dias_com_cobertura": list(filtered_coverage.keys()),
        "dias_sem_cobertura": [
            d for d in selected["selected_days"] if d not in filtered_coverage
        ],
        "resultado_compacto": output,
    }

def build_top_vehicles_coverage_from_dict(
    coverage_dict: Dict[str, Dict[str, Any]],
    vehicles_df: pd.DataFrame,
    *,
    source_col: str = "Fonte",
    promoter_col: str = "Promotores",
    detractor_col: str = "Detratores",
    top_n: int = 10,
) -> Dict[str, Any]:
    """
    Seleciona os veículos mais relevantes com base no peso composto:
    composite_score = Promotores - Detratores

    Depois retorna a cobertura desses veículos usando o coverage_dict.
    """

    df = vehicles_df.copy()

    required_cols = [source_col, promoter_col, detractor_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes em vehicles_df: {missing}")

    df[promoter_col] = pd.to_numeric(df[promoter_col], errors="coerce").fillna(0)
    df[detractor_col] = pd.to_numeric(df[detractor_col], errors="coerce").fillna(0)

    df["composite_score"] = df[promoter_col] - df[detractor_col]

    ranking_df = (
        df.sort_values(
            by=["composite_score", promoter_col, detractor_col],
            ascending=[False, False, True]
        )
        .dropna(subset=[source_col])
        .drop_duplicates(subset=[source_col])
        .head(top_n)
        .copy()
    )

    selected_vehicles = ranking_df[source_col].tolist()

    coverage_output = {vehicle: [] for vehicle in selected_vehicles}

    for day, payload in coverage_dict.items():
        normalized_day = _normalize_date_value(day)
        documentos = payload.get("documentos", [])

        for doc in documentos:
            fonte = doc.get("fonte")

            if fonte in selected_vehicles:
                coverage_output[fonte].append({
                    "data": normalized_day,
                    **doc
                })

    for vehicle, docs in coverage_output.items():
        coverage_output[vehicle] = sorted(
            docs,
            key=lambda x: (
                -(x.get("alcance") or 0),
                _tier_rank(x.get("tier")),
                -(x.get("doc_score") or 0),
            )
        )

    return {
        "ranking_veiculos": ranking_df[
            [source_col, promoter_col, detractor_col, "composite_score"]
        ].to_dict(orient="records"),
        "cobertura": coverage_output,
    }




def build_specific_topics_reports_dict(
    assunto_df_period: pd.DataFrame,
    daily_top_news_dict: Dict[str, Dict[str, Any]],
    *,
    empresa_col: str = "Empresa analisada",
    topic_col: str = "Assunto específico",
    contrib_col: str = "nps_contrib_assunto_especifico",
    topic_nps_col: str = "nps_score_assunto_especifico",
    total_topic_col: str = "total_assunto_especifico",
    denom_total_col: str = "denom_total",
    period_nps_col: str = "nps_score_periodo",
    period_filter_col: str = "mes_index",
    period_filter_value: int = 0,
    top_n_positive: int = 5,
    top_n_negative: int = 5,
    docs_key: str = "documentos",
    doc_topic_key: str = "Assuntos específicos",
    doc_company_key: str = "empresa",
    sort_reports: bool = True,
) -> Dict[str, Any]:
    """
    Retorna um dicionário com os assuntos específicos mais promotores e detratores
    do período, trazendo as reportagens encontradas no daily_top_news_dict.

    Estrutura de saída:
    {
        "americanas sa": {
            "nps_score_periodo": ...,
            "assuntos_promotores": {
                "tema x": {
                    "metricas_assunto": {...},
                    "reportagens": [...]
                }
            },
            "assuntos_detratores": {
                "tema y": {
                    "metricas_assunto": {...},
                    "reportagens": [...]
                }
            }
        }
    }
    """

    def _normalize_text(value: Any) -> Optional[str]:
        if pd.isna(value) or value is None:
            return None
        value = str(value).strip()
        return value if value else None

    def _safe_float(value: Any) -> Optional[float]:
        if pd.isna(value):
            return None
        try:
            return float(value)
        except Exception:
            return None

    def _tier_rank(tier: Any) -> int:
        if pd.isna(tier) or tier is None:
            return 999
        t = str(tier).strip().lower()
        if "tier 1" in t or t == "1" or "t1" in t:
            return 1
        if "tier 2" in t or t == "2" or "t2" in t:
            return 2
        if "tier 3" in t or t == "3" or "t3" in t:
            return 3
        if "tier 4" in t or t == "4" or "t4" in t:
            return 4
        return 999

    required_cols = [
        empresa_col,
        topic_col,
        contrib_col,
        topic_nps_col,
        total_topic_col,
        denom_total_col,
        period_nps_col,
    ]
    missing = [c for c in required_cols if c not in assunto_df_period.columns]
    if missing:
        raise ValueError(f"Colunas ausentes em assunto_df_period: {missing}")

    df = assunto_df_period.copy()

    if period_filter_col in df.columns:
        df = df[df[period_filter_col].isin([period_filter_value])].copy()

    if df.empty:
        return {}

    for col in [contrib_col, topic_nps_col, total_topic_col, denom_total_col, period_nps_col]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df[empresa_col] = df[empresa_col].apply(_normalize_text)
    df[topic_col] = df[topic_col].apply(_normalize_text)
    df = df.dropna(subset=[empresa_col, topic_col]).copy()

    # ---------------------------------------------------
    # Indexa reportagens por empresa + assunto específico
    # ---------------------------------------------------
    reports_map: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for data_ref, payload in daily_top_news_dict.items():
        if not isinstance(payload, dict):
            continue

        documentos = payload.get(docs_key, [])
        if not isinstance(documentos, list):
            continue

        for doc in documentos:
            if not isinstance(doc, dict):
                continue

            empresa_doc = _normalize_text(doc.get(doc_company_key))
            assunto_doc = _normalize_text(doc.get(doc_topic_key))

            if empresa_doc is None or assunto_doc is None:
                continue

            reports_map.setdefault(empresa_doc, {})
            reports_map[empresa_doc].setdefault(assunto_doc, [])

            doc_payload = {
                "data": data_ref,
                **doc,
            }
            reports_map[empresa_doc][assunto_doc].append(doc_payload)

    if sort_reports:
        for empresa, topics in reports_map.items():
            for assunto, docs in topics.items():
                reports_map[empresa][assunto] = sorted(
                    docs,
                    key=lambda x: (
                        -(x.get("alcance") or 0),
                        _tier_rank(x.get("tier")),
                        -(x.get("doc_score") or 0),
                    )
                )

    # ---------------------------------------------------
    # Monta saída final
    # ---------------------------------------------------
    output: Dict[str, Any] = {}

    for empresa, empresa_df in df.groupby(empresa_col, dropna=False):
        empresa_df = empresa_df.copy()

        positivos = (
            empresa_df[empresa_df[contrib_col] > 0]
            .sort_values(
                by=[contrib_col, total_topic_col, topic_nps_col],
                ascending=[False, False, False]
            )
            .drop_duplicates(subset=[topic_col], keep="first")
            .head(top_n_positive)
        )

        negativos = (
            empresa_df[empresa_df[contrib_col] < 0]
            .sort_values(
                by=[contrib_col, total_topic_col, topic_nps_col],
                ascending=[True, False, True]
            )
            .drop_duplicates(subset=[topic_col], keep="first")
            .head(top_n_negative)
        )

        output[empresa] = {
            "nps_score_periodo": (
                None
                if empresa_df[period_nps_col].dropna().empty
                else float(empresa_df[period_nps_col].dropna().iloc[0])
            ),
            "assuntos_promotores": {},
            "assuntos_detratores": {},
        }

        for _, row in positivos.iterrows():
            assunto = _normalize_text(row[topic_col])
            if assunto is None:
                continue

            output[empresa]["assuntos_promotores"][assunto] = {
                "metricas_assunto": {
                    "empresa_analisada": empresa,
                    "assunto_especifico": assunto,
                    "nps_contrib_assunto_especifico": _safe_float(row[contrib_col]),
                    "nps_score_assunto_especifico": _safe_float(row[topic_nps_col]),
                    "total_assunto_especifico": _safe_float(row[total_topic_col]),
                    "denom_total": _safe_float(row[denom_total_col]),
                    "direcao": "promotora",
                },
                "reportagens": reports_map.get(empresa, {}).get(assunto, []),
            }

        for _, row in negativos.iterrows():
            assunto = _normalize_text(row[topic_col])
            if assunto is None:
                continue

            output[empresa]["assuntos_detratores"][assunto] = {
                "metricas_assunto": {
                    "empresa_analisada": empresa,
                    "assunto_especifico": assunto,
                    "nps_contrib_assunto_especifico": _safe_float(row[contrib_col]),
                    "nps_score_assunto_especifico": _safe_float(row[topic_nps_col]),
                    "total_assunto_especifico": _safe_float(row[total_topic_col]),
                    "denom_total": _safe_float(row[denom_total_col]),
                    "direcao": "detratora",
                },
                "reportagens": reports_map.get(empresa, {}).get(assunto, []),
            }

    return output