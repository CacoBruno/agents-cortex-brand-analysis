from cortex_brand_analysis.nlp.models.text_treatment.text_processing import replace_protagonism_terms_in_text

def words_normalization(dictionary, words):
    """ Used to replace all variations of the item with 
        a single value in word list
    Args:        
        dictionary (dict)
        
    Returns:
        [str]: Normalized words
    """     
    return replace_protagonism_terms_in_text(words, dictionary)
    

def title_normalization(dictionary, title):
    """ Used to replace all variations of the item with 
        a single value in title

    Args:        
        dictionary (dict)
        title (str)

    Returns:        
        [str]: Normalized title
    """   

    return replace_protagonism_terms_in_text(title, dictionary)
    

def slices_normalization(dictionary, slices):
    """ Used to replace all variations of the item with 
        a single value in text slices

    Args:        
        dictionary (dict)
        slices (dict)

    Returns:
        [dict]: Normalized slices        
    """    
    normalized_slices = {}

    normalized_slices['slice_one'] = replace_protagonism_terms_in_text(
        slices['slice_one'], dictionary)
    normalized_slices['slice_two'] = replace_protagonism_terms_in_text(
        slices['slice_two'], dictionary)
    normalized_slices['final_slice'] = replace_protagonism_terms_in_text(
        slices['final_slice'], dictionary)

    return normalized_slices