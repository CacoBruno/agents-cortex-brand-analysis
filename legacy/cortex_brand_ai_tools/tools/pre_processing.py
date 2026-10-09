from tools.key_words import get_leia_mais_terms, company_names, specific_terms
import regex as re
import unidecode
from bs4 import BeautifulSoup
import nltk
nltk.download('stopwords')
nltk.download('rslp')
from nltk.corpus import stopwords
stopwords = stopwords.words('portuguese')
from unidecode import unidecode
import regex as re 
import spacy
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from tools import config_tools
import tensorflow_hub as hub


nlp = spacy.load("pt_core_news_lg")


def generate_mentions_pattern(mentions_df) -> re.Pattern:
    """_summary_

    Args:
        mentions_df (_type_): _description_

    Returns:
        re.Pattern: _description_
    """
    values_list = mentions_df['Menção'].values    
    values_list = "\\b|\\b".join(values_list).replace(' ,', '').lower()
    return  re.compile(rf"\b{values_list}\b")  


def get_references_pattens(dataframe, mentions_df, column):
    """_summary_

    Args:
        dataframe (_type_): _description_
        mentions_df (_type_): _description_
        column (_type_): _description_

    Returns:
        _type_: _description_
    """
    ref_patterns = {}
    references = dataframe[column].unique()
    for ref in references:
        ref_patterns[ref] = generate_pattern(mentions_df[mentions_df['Empresa/Produto'] == ref], dataframe)    
    return  ref_patterns


def get_tfifd_dict(sentence):
    """_summary_

    Args:
        sentence (_type_): _description_

    Returns:
        _type_: _description_
    """
    if len(sentence) > nlp.max_length:
        sentence = sentence[0: nlp.max_length]
    doc = nlp(sentence)
    phrases = [sent.text.strip() for sent in doc.sents]    
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(phrases)
    pesos_das_frases = tfidf_matrix.sum(axis=1)
    pesos_das_frases_normalizados = pesos_das_frases / pesos_das_frases.sum()    
    frases_dict = {}
    for i, frase in enumerate(phrases):
        frases_dict[frase] =  pesos_das_frases_normalizados[i, 0]
    return frases_dict


def get_summary(sentence, names_pattern, max_sentence=300):
    """_summary_

    Args:
        sentence (_type_): _description_
        names_pattern (_type_): _description_
        max_sentence (int, optional): _description_. Defaults to 300.

    Returns:
        _type_: _description_
    """
    if len(sentence) > max_sentence:
        frases_dict = get_tfifd_dict(sentence)        
        max_weight = get_max_weights(frases_dict)
        return get_weighted_summary_ss(frases_dict, max_weight, names_pattern)
    else:
        return sentence    

# def get_summary(sentence, names_pattern):
#     """_summary_

#     Args:
#         sentence (_type_): _description_
#         names_pattern (_type_): _description_

#     Returns:
#         _type_: _description_
#     """
#     if len(sentence)> 100:
#         frases_dict = get_tfifd_dict(sentence)        
#         max_weight = get_max_weights(frases_dict)        
#         return get_weighted_summary_ss(frases_dict, max_weight, names_pattern)
#     else:
#         return sentence    
    

def find_term_in_text(text):
    """ Com base em todos os termos possíveis de 'Leia mais' 
        elencados acima, busca esses termos no texto
        agrupando-os em uma lista
    Args:
        text (str): News body (raw)

    Returns:
        [str]: List of terms (if it doesn't exist return empty list)
    """
    terms = get_leia_mais_terms()

    terms_found = set()
    for term in terms.split('|'):
        term = term.strip()
        pattern_term = re.compile(rf"\b{term}\b")
        if pattern_term.findall(text):
            terms_found.add(term)
    return terms_found


def remove_leia_mais_terms(text):
    """_summary_

    Args:
        text (_type_): _description_

    Returns:
        _type_: _description_
    """
    terms = find_term_in_text(text)    
    if len(terms) > 0:
        for term in terms:        
            text = text.replace(term, '')            
        return text
    else:
        return text
    

def remove_html_tags(string):
    """Remove HTML tags from text

    Args:
        s (str)

    Returns:
        [str]: Cleaned text
    """
    soup = BeautifulSoup(string, features="html.parser")
    return soup.get_text()


def remove_trash_from_text(text):
    """_summary_

    Args:
        text (_type_): _description_

    Returns:
        _type_: _description_
    """
    text = re.sub(r'[-\(\)/\[\]\|?]', ' ', text)
    clean_text = remove_html_tags(text)
    clean_text = re.sub(r' (\w) \1+', r'\1', clean_text)
    clean_text = re.sub(r' ([a-z]) \1+', ' ', clean_text)
    clean_text = clean_text.replace('\n', ' ')
    clean_text = clean_text.replace('\t', ' ')
    clean_text = clean_text.replace('  ', ' ')     
    clean_text = clean_text.replace('\r', ' ')             
    clean_text = " ".join([word for word in clean_text.split(' ') if len(word) < 20])    
    if len(clean_text) > 0:        
        return clean_text
    else:
        return text

def treat_upper_case_words(text):    
    """_summary_

    Args:
        text (_type_): _description_

    Returns:
        _type_: _description_
    """
    company_names_lower = [c.lower() for c in company_names]
    upper_case_words =  re.findall(r'\b[A-ZÁÉÍÓÚÇÃÕÊÔÀÃÈÌÒÙÂÊÎÔÛÄËÏÖÜ]+\b', text)           
    if len(upper_case_words) > 0:
        for word in upper_case_words:                
            pattern = re.compile(rf'\b{word}\b')        
            if text.startswith(word) or word.lower() in company_names_lower:                
                text = re.sub(pattern,  word.capitalize(), text)    
            else:                        
                text = re.sub(pattern,  word.lower(), text)    
    return text        


def create_mentions_df(df):
    """_summary_

    Args:
        df (_type_): _description_

    Returns:
        _type_: _description_
    """
    companies = list(df['Empresa analisada'].unique())
    products = list(df['Produto analisado'].unique())
    companies.extend(products)      
    companies = [c for c in companies if c != '-']   
    mentions_df = pd.DataFrame()
    mentions_df['Menção'] = companies        
    return mentions_df


def generate_mentions_pattern(mentions_df) -> re.Pattern:
    """_summary_

    Args:
        mentions_df (_type_): _description_

    Returns:
        re.Pattern: _description_
    """
    values_list = mentions_df['Menção'].values    
    values_list = "\\b|\\b".join(values_list).replace(' ,', '').lower()
    return  re.compile(rf"\b{values_list}\b")  


def generate_pattern(mentions_df, dataframe):
    """_summary_

    Args:
        mentions_df (_type_): _description_
        dataframe (_type_): _description_

    Returns:
        _type_: _description_
    """
    mentions_values = list(mentions_df['Menção'].values)
    if 'Produto 1' in mentions_values or 'Empresa C Institucional' in mentions_values:
        mentions_df = create_mentions_df(dataframe)
    mentions_pattern = generate_mentions_pattern(mentions_df)    
    return mentions_pattern    


def get_max_weights(phrases_dict):    
    """_summary_

    Args:
        phrases_dict (_type_): _description_

    Returns:
        _type_: _description_
    """
    max_weight = np.max(list(phrases_dict.values()))    
    return  max_weight * config_tools.MAX_WEIGHT


def get_weighted_summary_ss(frases_dict, max_weight, names_pattern):
    """_summary_

    Args:
        frases_dict (_type_): _description_
        max_weight (_type_): _description_
        names_pattern (_type_): _description_

    Returns:
        _type_: _description_
    """
    new_summary = []        
    for key, value in frases_dict.items():               
        if value >= max_weight:            
            new_summary.append(key)        
        if value < max_weight and len(re.findall(names_pattern, key.lower())) > 0:            
            new_summary.append(key)        
    return " ".join(new_summary)


def get_weighted_summary(frases_dict, max_weight, company_name, product_name, df_names):    
    """_summary_

    Args:
        frases_dict (_type_): _description_
        max_weight (_type_): _description_
        company_name (_type_): _description_
        product_name (_type_): _description_
        df_names (_type_): _description_

    Returns:
        _type_: _description_
    """

    if product_name != '-':
        filtered_df_names = df_names[df_names['Produtos citados'] == product_name].copy()
    else:
        filtered_df_names = df_names[df_names['Empresas citadas'] == company_name].copy()
    
    new_summary = []
    company_name = list(filtered_df_names['Menção'].values)
    names_pattern = "\\b|\\b".join(company_name)
    names_pattern = f'\\b{names_pattern}\\b' 
        
    for key, value in frases_dict.items():               
        if value >=max_weight:            
            new_summary.append(key)        
        if value < max_weight and len(re.findall(names_pattern, key.lower())) > 0:            
            new_summary.append(key)        
    return " ".join(new_summary)


def get_embeddings_model():
    """_summary_

    Returns:
        _type_: _description_
    """
    return hub.load(config_tools.embeddings_url)


def generate_embeddings(dataframe, column_text):
    """_summary_

    Args:
        dataframe (_type_): _description_
        column_text (_type_): _description_

    Returns:
        _type_: _description_
    """
    assert (column_text in dataframe.columns), f'Dataframe não contém a coluna {column_text}'
    model = get_embeddings_model()
    dataframe['embeddings'] = [model([sentence]).numpy().flatten() for sentence in dataframe[column_text]]    
    return dataframe