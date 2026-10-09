""" Transform the mentions cube into a nested dictionary """

#### Setup ####
from pr import pr_io
from pr.text_treatment import text_processing


def transform_cube_to_dict(client_config, variable_column, language):
    """ This function access client cube to get normalization
        forms (Menções) which contains all
        possible variations about variable_column

        Args:
            client_config (dict): All information about a client generated from:
                                  pr_io.get_client_info(client_name)
            variable_column (str): Column in datasetof the term to be analyzed as protagonist

        Returns:
            [dict]: {'term':{'mentionA':term, 'mentionB':term}}
    """

    cube_name = 'Menções'
    mentions_df = pr_io.get_cubes(client_config, [cube_name])
    mentions_df = mentions_df[cube_name]

    cleaning_tasks = ['lower', 'punctuation']
    mentions_df[variable_column] = mentions_df[variable_column].apply(
        lambda x: text_processing.clean_text(x, language, cleaning_tasks=cleaning_tasks))

    # Creates the nested dictionary {'term':{'mentionA':unique_term, 'mentionB':unique_term}}
    dictionary = {}
    for idx, row in mentions_df[[variable_column, 'Menção']].iterrows():
        product = row[variable_column]
        mentions = row['Menção']
        dictionary[product] = {}
        if len(mentions) > 1:
            for mention in mentions.split(','):
                dictionary[product][text_processing.clean_text(
                    mention, language, cleaning_tasks=cleaning_tasks)] = product
        else:
            dictionary[product][text_processing.clean_text(
                mention, language, cleaning_tasks=cleaning_tasks)] = product
    return dictionary