import numpy as np

def get_variations(string, client_name):
    """ Generates variations for the text

    Args:
        string (str): Company name

    Returns:
        _list: List with variations for the text
    """
    words_to_remove = ['da', 'do', 'e', 'a', 'de', 
                       'brasil', 'grupo','empresas', 'citadas']
    variation_list = []    
    if string.lower() != 'outros':
        
        joined = "".join(string.split(' '))
        variation_list.append(string)
        variation_list.append(string.upper())
        variation_list.append(string.lower())
        variation_list.append(string.capitalize())
        variation_list.append(joined)    
        variation_list.append(joined.upper())    
        variation_list.append(joined.lower())  

        splitted_string = string.split(' ')
        if len(splitted_string) > 0:
            for word in splitted_string:
                if string in word.lower():
                    variation_list.append(client_name.upper())
                    variation_list.append(client_name.capitalize())
                else:
                    if word.lower() not in words_to_remove:
                        variation_list.append(word.upper())
                        variation_list.append(word.capitalize())
                            
    return list(np.unique(variation_list))


def generate_rule_based_files(df, client_name, company_column_name):
    """ Generates the files needed for the rule-based relevance detection model

    Args:
        df (Pandas Dataframe): Dataframe ('Publicaçẽos' cube)
        client_name (str): Internal use client name (Ex: afkl)
        company_column_name (str): Company column names (Ex: Empresas citadas)

    Returns:
        dict, dict
    """
    
    companies_mentions = {}
    key_terms = {}
    
    companies = list(df[company_column_name].unique())
    companies = [c.split('|') for c in companies]
    companies = [c for c_ in companies for c in c_] 
    companies = np.unique(companies)
    
    for company in companies:
        companies_mentions[company] = get_variations(company, client_name)
        
    companies_nested_list = list(companies_mentions.values())
    companies_flat_list = [item for sublist in companies_nested_list for item in sublist]        
    
    key_terms[client_name] = companies_flat_list
    
    return companies_mentions, key_terms
