def standardize_columns_4_enrichment(
    dataframe, client_config, cube_key, destandardize=False
):
    """Change names in dataframe for standardization

    Args:
        dataframe (Pandas Dataframe)
        client_config (dict)
        cube_key (str)
        destandardize (bool, optional): Defaults to False.

    Returns:
        [Pandas Dataframe]: Standardized dataframe
    """
    # ======  Standardize columns Names ============
    CUBES = client_config["CUBES"]

    rename_dict = {
        CUBES[cube_key]["news_id"]: "ID News",
        CUBES[cube_key]["news_date"]: "Data da Notícia",
        CUBES[cube_key]["content"]: "Conteúdo",
        CUBES[cube_key]["title"]: "Título",
        CUBES[cube_key]["created_at"]: "Data de publicação",
    }

    if destandardize:
        rename_dict = {v: k for k, v in rename_dict.items()}

    return dataframe.rename(columns=rename_dict, inplace=False)
