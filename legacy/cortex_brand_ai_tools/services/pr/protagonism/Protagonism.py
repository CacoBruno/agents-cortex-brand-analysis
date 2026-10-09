""" Implements the cortex methodology for protagonism classification """

#### Setup ####
import sys
from nltk import word_tokenize

from services.pr.text_treatment.text_processing import clean_text
from services.pr.protagonism.src.text_slicing import slicing

from services.pr.protagonism.src.ngrams_generation import (
    ngrams_from_words,
    ngrams_from_slices,
    ngrams_from_title)

from services.pr.protagonism.src.search_variable_position import (
    search_in_title,
    search_in_words_list,
    search_in_text_slices)

from services.pr.protagonism.src.cleaning import (
    clean_words,
    clean_slices,
    clean_title_tokenize)

from services.pr.protagonism.src.normalization import (
    title_normalization,
    slices_normalization,
    words_normalization)

from services.pr.protagonism.src.define_protagonism_code import get_code


class Protagonism:
    """ Implements the cortex methodology for protagonism classification """

    def __init__(self, dictionary, cleaning_tasks):
        self.dictionary = dictionary
        self.language = 'pt'
        self.cleaning_tasks = cleaning_tasks

    def define_protagonism(self, variable_position_in_words_slices,
                           variable_position_in_text_slices,
                           varibale_in_title):
        
        """ Receives the term position dictionaries to determine Protagonism classification

        Args:
            variable_position_in_words_slices (dict)
            variable_position_in_text_slices (dict)
            varibale_in_title (bool)

        Returns:
            [str]: A letter that corresponds to Protagonism
        """        
        protagonism_code = get_code(variable_position_in_text_slices,
                                    variable_position_in_words_slices,                                    
                                     varibale_in_title)
        return protagonism_code

    def run_protagonism(self, variable, title, text):
        """ Performs all steps to generate protagonism classification
        Args:
            variable (str): Company or product name to search
            title (str): Raw news title
            text (str): Raw news body            

        Returns:
            [str]: Protagonism code

        """
        language = self.language
        variable = clean_text(variable, language, cleaning_tasks=self.cleaning_tasks)     
        title = clean_text(title, language, cleaning_tasks=self.cleaning_tasks)       
        
        try:                        
            dictionary = self.dictionary[variable]                        
            title_tokenize = word_tokenize(title)
            
            if len(variable.split(' ')) > 3:
                new_dict = {}
                for k, v in dictionary.items():
                    new_dict[k] = " ".join(variable.split(' ')[0:3])
                dictionary = new_dict
                variable = " ".join(variable.split(' ')[0:3])                
            
            raw_slices = slicing(text)

            slices = clean_slices(language, raw_slices, self.cleaning_tasks)
            title = clean_title_tokenize(language, title, title_tokenize, self.cleaning_tasks)
            words = clean_words(language, text, self.cleaning_tasks)

            slices = slices_normalization(dictionary, slices)
            title = title_normalization(dictionary, title)
            words = words_normalization(dictionary, words)  
                        
            ngrams_from_frequency_words_slices = ngrams_from_words(words)
            ngrams_from_text_slices = ngrams_from_slices(slices)
            ngrams_title = ngrams_from_title(title)

            variable_position_in_words = search_in_words_list(
                ngrams_from_frequency_words_slices, variable)
            variable_position_in_text = search_in_text_slices(
                ngrams_from_text_slices, variable)
            variable_in_title = search_in_title(
                ngrams_title, title, title_tokenize, variable)
    
            return self.define_protagonism(variable_position_in_words,
                                           variable_position_in_text,
                                           variable_in_title)                      
        except:            
            return 'Revisar'
            
    def __call__(self, variable, title, text):
        
        """ Runs the algorithm to predict the level company or product Protagonism in the news

        Args:
            variable (str): Company or product (from the corresponding dataset column: 'Empresa 
            analisada' or 'Produto analisado')
            title (str): News title (from Título)
            text (str): News body (from Conteúdo)

        Returns:
            [str]:  Protagonism code - code that defines the type 
            of protagonism based on the position and frequency in
            the text of the analyzed company / product
        """        
        
        if variable in ('-', ''):
            return 'Revisar'        
        return self.run_protagonism(variable, title, text)
