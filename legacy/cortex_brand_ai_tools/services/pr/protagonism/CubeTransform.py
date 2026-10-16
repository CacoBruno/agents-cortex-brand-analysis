
from pr import pr_io
from pr.text_treatment import text_processing
import pandas as pd
from collections import Counter


class CubeTransform:

    def __init__(self, info):
        self.cube_name = info['cube_name']
        self.product_column_name = info['product_column_name']
        self.company_column_name = info['company_column_name']
        self.mentions_column_name = info['mentions_column_name']
        self.cleaning_tasks = info['cleaning_tasks']
        self.language = info['language']

    def get_and_treat_cube(self, client_config, variation_column_name):
        """ Access mentions cube for Protagonism. Check if it exists and 
            formatt text to match analysis.

        Args:
            client_config (dict): Client infos (Cubes ids, filters, etc...)

        Returns:
            Pandas DataFrame: 
        """
        mentions_df = pd.DataFrame()
        try:
            mentions_df = pr_io.get_cubes(client_config, [self.cube_name])
            mentions_df = mentions_df[self.cube_name]

        except FileNotFoundError as not_found:
            print(f'Cube not found! Check if "{self.cube_name}" cube exists')
            print(f'Error {not_found.filename}')
        else:
            
            if variation_column_name == 'Produtos citados':
                mentions_df.fillna('-', inplace=True)
                for idx, row in mentions_df.iterrows():
                    if row[variation_column_name] == '-':
                        mentions_df.loc[idx, variation_column_name] = row[self.company_column_name]

            mentions_df[variation_column_name] = mentions_df[variation_column_name].apply(lambda x: text_processing.clean_text(x, self.language, cleaning_tasks=self.cleaning_tasks))
            mentions_df['Menção'] = mentions_df['Menção'].apply(lambda x: text_processing.clean_text(x, self.language, cleaning_tasks=self.cleaning_tasks))

            return mentions_df

        return mentions_df

    def protagonism_cube_to_dict(self, client_config):
        """ Creates the nested dictionary from cube in format:
         {'term':{'mentionA':unique_term, 'mentionB':unique_term}}

        Args:
            client_config (dict): Client infos (Cubes ids, filters, etc...)

        Returns:
            dict
        """

        dictionary = {}
        variation_column_name = 'Empresas citadas' if self.mentions_column_name == 'Empresa' else 'Produtos citados'
        mentions_df = self.get_and_treat_cube(
            client_config, variation_column_name)

        if len(mentions_df) > 0:
            counting_mentions = Counter(mentions_df[variation_column_name])
            dictionary = {}
            for granularity, granularity_counting in counting_mentions.items():
                dictionary[granularity] = {}
                list_of_variation = (list(
                    mentions_df[mentions_df[variation_column_name] == granularity]['Menção'].values))
                if len(list_of_variation) > 1:
                    sub_dict = {}
                    for value in list_of_variation:
                        sub_dict[value] = granularity
                    dictionary[granularity] = sub_dict
                elif len(list_of_variation) == 1:
                    sub_dict = {}
                    sub_dict[granularity] = granularity
                    dictionary[granularity] = sub_dict
        else:
            print(
                f'Empty dictionary! Check the filling of the information in "{self.cube_name}" cube')

        return dictionary

    def __call__(self, client_config):
        return self.protagonism_cube_to_dict(client_config)
