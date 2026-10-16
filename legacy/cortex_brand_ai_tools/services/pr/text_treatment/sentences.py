import nltk
import string


def break_into_sentences(content_dict, first_letter_to_lower=True):
    """
    content_dict: Dict {number: string}
    Task: Split content into senteces and store it on a dict
    return: Dict {tuple: string}
    """
    if first_letter_to_lower:
        sentences_dict = {
            str((kp, ks + 1)): fill_empty_string(
                remove_punct(_fix_sentence_case(sentence))
            )
            for kp, paragraph in content_dict.items()
            for ks, sentence in enumerate(nltk.tokenize.sent_tokenize(paragraph))
        }
    else:
        sentences_dict = {
            str((kp, ks + 1)): fill_empty_string(remove_punct(sentence))
            for kp, paragraph in content_dict.items()
            for ks, sentence in enumerate(nltk.tokenize.sent_tokenize(paragraph))
        }

    return sentences_dict


def fill_empty_string(s):
    if len(s) == 0:
        return "-"
    return s


def remove_punct(s):
    return s.translate(str.maketrans("", "", string.punctuation))


def _fix_sentence_case(sentence):
    """ """
    if sentence.isupper():
        sentence = sentence.lower()
    else:
        sentence = sentence[0].lower() + sentence[1:]
    return sentence


def tag_words_in_sentences(sentences, tagger):
    """ """
    return {
        k: tagger.tag(nltk.tokenize.word_tokenize(sentence))
        for k, sentence in sentences
    }


if __name__ == "__main__":
    pass
