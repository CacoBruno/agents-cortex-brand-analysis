
from services.pr.text_treatment.text_processing import clean_text

#### Globals ####

def clean_words(language, content, cleaning_tasks):    
    """Function used to clean news body text

    Args:
        language (str): Idiom
        text (str): News body

    Returns:
        [str]: Cleaned words (list of all words from text)
    """
    return clean_text(content, language, cleaning_tasks=cleaning_tasks)


def clean_slices(language, slices, cleaning_tasks):
    """Function used to clean text slices

    Args:
        language (str): Idiom   
        slices (str): Text slices

    Returns:
        [dict]: With all text slices cleaned
    """    
    
    cleaned_slices ={}
    
    if slices['slice_one'] != '':
        slice_one = clean_text(
            slices['slice_one'],
            language,
            cleaning_tasks=cleaning_tasks)
    else:
        slice_one = ''

    if slices['slice_two'] != '':
        slice_two = clean_text(
            slices['slice_two'],
            language,
            cleaning_tasks=cleaning_tasks)
    else:
        slice_two = ''

    if slices['final_slice'] != '':
        final_slice = clean_text(
            slices['final_slice'],
            language,
            cleaning_tasks=cleaning_tasks)
    else:
        final_slice = ''

    cleaned_slices['slice_one'] = slice_one
    cleaned_slices['slice_two'] = slice_two
    cleaned_slices['final_slice'] = final_slice

    return cleaned_slices


def clean_title_tokenize(language, title, title_tokenize, cleaning_tasks):
    """Function used to clean tokenized title

    Args:
        language (str): Idiom   
        title (str): Original news title
        title_tokenize (list): Title divided by words        

    Returns:        
        [str]: Cleaned tokens    
    """    

    if title != '':
        title_tokenize = clean_text(
            " ".join(title_tokenize),
            language,
            cleaning_tasks=cleaning_tasks)
    return title_tokenize  
        