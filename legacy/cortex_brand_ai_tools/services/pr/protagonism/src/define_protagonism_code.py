def get_code(variable_position_in_text_slices, 
             variable_position_in_words_slices,
             varibale_in_title):
    
        protagonism = "Revisar"
        empty_text = variable_position_in_text_slices['empty_text']
        empty_words_list = variable_position_in_words_slices['empty_list']

        first_words_list_slice = variable_position_in_words_slices['more_relevant']
        second_words_list_slice = variable_position_in_words_slices['medium_relevant']
        final_words_list_slice = variable_position_in_words_slices['less_relevant']

        first_text_slice = variable_position_in_text_slices['slice_one']
        second_text_slice = variable_position_in_text_slices['slice_two']
        final_text_slice = variable_position_in_text_slices['final_slice']

        if first_words_list_slice and varibale_in_title:
            protagonism = 'A'
        elif first_words_list_slice and first_text_slice:
            protagonism = 'B'
        elif first_words_list_slice and second_text_slice:
            protagonism = 'C'
        elif first_words_list_slice and final_text_slice:
            protagonism = 'D'
        elif second_words_list_slice and varibale_in_title:
            protagonism = 'E'
        elif second_words_list_slice and first_text_slice:
            protagonism = 'F'
        elif second_words_list_slice and second_text_slice:
            protagonism = 'G'
        elif second_words_list_slice and final_text_slice:
            protagonism = 'H'
        elif final_words_list_slice and varibale_in_title:
            protagonism = 'I'
        elif final_words_list_slice and first_text_slice:
            protagonism = 'J'
        elif final_words_list_slice and second_text_slice:
            protagonism = 'K'
        elif final_words_list_slice and final_text_slice:
            protagonism = 'L'
        elif empty_text and empty_words_list and varibale_in_title:
            protagonism = 'M'
        elif varibale_in_title:
            protagonism = 'M'
        if varibale_in_title:
            protagonism = 'M'            
            
        return protagonism