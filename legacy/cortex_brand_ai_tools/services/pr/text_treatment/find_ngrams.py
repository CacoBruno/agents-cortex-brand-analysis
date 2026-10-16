from collections import Counter
from functools import reduce
from math import log

import nltk
import pandas as pd
import tqdm
from nltk import ngrams, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

NGRAMS_LIST = [1, 2, 3, 4]


def remove_items_from_dict(dictionary):
    """Removes elements with size less than two from the element dictionary

    Args:
        dictionary (dict)

    Returns:
        [dict]
    """

    to_remove = set()
    for key, value in dictionary.items():
        splited_keys = key.split()
        for k in splited_keys:
            if len(k) < 2:
                to_remove.add(key)
    for item in to_remove:
        dictionary.pop(item)
    return dictionary


def get_unigrams_count(doc_val, stopwords):

    return Counter(
        [
            t[0]
            for k, lst in doc_val["tagged_tokens"].items()
            for t in lst
            if t[1] in ["NOUN", "VERB", "ADJ"]
            and t[0] not in stopwords
            and len(t[0]) > 1
        ]
    )


def get_ngrams_count(doc_val, biggest_compound_noun, ngram_length, stopwords):

    if ngram_length == 1:
        return get_unigrams_count(doc_val, stopwords)

    tagged_sents_tokens = doc_val["tagged_tokens"]
    ngrams_ref = {}
    for k, tagged_sent_tokens in tagged_sents_tokens.items():
        if len(tagged_sent_tokens) >= ngram_length:
            ngrams_ref[k] = [
                grams for grams in ngrams(tagged_sent_tokens, ngram_length)
            ]

    # Find Proper Nouns among Ngrams
    word_lst = []
    discard_tags = set(
        ["."]
        + ["PNOUN" + str(i) for i in range(ngram_length, biggest_compound_noun + 1)]
    )
    for k, ngrams_list in ngrams_ref.items():
        for idx, ngram in enumerate(ngrams_list):
            tags = [tagged_word[1] for tagged_word in ngram]
            if len(set(tags).intersection(discard_tags)) == 0:
                pn_pieces = Counter(list(filter(lambda x: x[-1].isdigit(), tags)))
                full_name = False
                if len(pn_pieces) > 0:
                    full_name = reduce(
                        (lambda x, y: x * y),
                        [
                            True if pn_pieces[i] == int(i[-1]) else False
                            for i in pn_pieces
                        ],
                    )
                    if full_name:
                        word_piece_lst = [tagged_word[0] for tagged_word in ngram]
                        word_str = " ".join(word for word in word_piece_lst)
                        word_lst.append(word_str)
                else:
                    word_piece_lst = [tagged_word[0] for tagged_word in ngram]
                    word_str = " ".join(word for word in word_piece_lst)
                    word_lst.append(word_str)
    return Counter(word_lst)


def get_most_important_ngrams(list_of_texts, ngrams_config):
    """Search for the most important ngrams based on ngrams_config

    Args:
        list_of_texts (Pandas Dataframe)
        ngrams_config (dict): min max ngrams

    Returns:
        [dict]: ngrams analyzed in format: {'term term': 'term_term'}
    """

    D = len(list_of_texts)
    grams = ngrams_config.keys()
    ngrams_dict = {k: [] for k in grams}
    for i_text in list_of_texts:
        for sentence in nltk.tokenize.sent_tokenize(i_text):
            for gram in grams:
                ngrams_dict[gram].extend(
                    [w for w in ngrams(nltk.word_tokenize(sentence), int(gram))]
                )

    ngrams_counter = {k: Counter(v) for k, v in ngrams_dict.items()}
    ngrams_replace = {
        " ".join([i for i in k]): "_".join([i for i in k])
        for gram in grams
        for k, v in ngrams_counter[gram].items()
        if (
            v > D * ngrams_config[gram]["min_freq"]
            and v < D * ngrams_config[gram]["max_freq"]
        )
    }

    return ngrams_replace


def get_most_important_collocations(list_of_texts, language, percentual=0.01):
    """Search for the most important ngrams selected by collocations (expressions of multiple words which commonly co-occur)

    Args:
        dataframe (Pandas Dataframe)
        column (str): Column with text to extract ngrams
        language (str, optional): Defaults to 'en'.
        percentual (float, optional): Threshold of ngrams to consider. Defaults to 0.01.

    Returns:
        [dict]: ngrams analyzed in format: {'term term': 'term_term'}
    """

    # for portuguese
    terms_to_remove = [
        "a",
        "as",
        "à",
        "às",
        "de",
        "das",
        "da",
        "do",
        "o",
        "os",
        "dos",
        "que",
        "no",
        "na",
        "nos",
        "nas",
        "e",
        "é",
    ]

    length = round(len(list_of_texts) * percentual)
    sentences = " ".join(list_of_texts)
    sentences = sentences.split()

    bigram_measures = nltk.collocations.BigramAssocMeasures()
    trigram_measures = nltk.collocations.TrigramAssocMeasures()
    quad_measures = nltk.collocations.QuadgramAssocMeasures()

    finder = nltk.collocations.BigramCollocationFinder.from_words(sentences)
    bigrams_collocations = finder.nbest(bigram_measures.likelihood_ratio, length)

    finder = nltk.collocations.TrigramCollocationFinder.from_words(sentences)
    trigrams_collocations = finder.nbest(trigram_measures.likelihood_ratio, length)

    finder = nltk.collocations.QuadgramCollocationFinder.from_words(sentences)
    quadrigrams_collocations = finder.nbest(quad_measures.likelihood_ratio, length)

    aux_collocations = (
        bigrams_collocations + trigrams_collocations + quadrigrams_collocations
    )

    if language == "pt":
        collocation_list = [
            [colloc for colloc in terms if colloc not in terms_to_remove]
            for terms in aux_collocations
        ]

    collocation_list = [term for term in collocation_list if len(term) > 1]

    collocations_dict = {}
    for item in collocation_list:
        collocations_dict[" ".join(item)] = "_".join(item)

    collocations_dict = remove_items_from_dict(collocations_dict)
    return collocations_dict


def get_tfidf_ngrams(list_of_texts, ngrams_config):
    """Search for the most important ngrams selected by TFIDF
        (find meaning of sentences consisting of words and cancels out
        the incapabilities of Bag of Words technique which
        is good for text classification or for helping a
        machine read words in numbers)

    Args:
        lis_of_texts: List of strings

    Returns:
        [dict]: ngrams analyzed in format: {'term term': 'term_term'}
    """

    tfidf_ngrams = {}
    tfidf_unigrams = set()

    # Corpus
    sentences = list_of_texts    
    grams = ngrams_config.keys()
    grams = sorted(grams)
    gram_range_1 = int(grams[0])
    gram_range_2 = int(grams[-1])

    # Getting TFIDF ngrams
    vectorizer = TfidfVectorizer(ngram_range=(gram_range_1, gram_range_2))
    vect_sentences = vectorizer.fit_transform(sentences)
    features = vectorizer.get_feature_names()

    # Getting top ranking features
    sums = vect_sentences.sum(axis=0)
    values = []
    for col, term in enumerate(features):
        values.append((term, sums[0, col]))
    ranking = pd.DataFrame(values, columns=["term", "rank"])
    words = ranking.sort_values("rank", ascending=False)

    # used for unigrams
    if gram_range_1 == 1 and gram_range_2 == 1:
        threshold = int(words.shape[0] * 0.6)
        words = words[0:threshold]
        for w in words["term"]:
            tfidf_unigrams.add(w)
        to_return = tfidf_unigrams

    threshold = words[words["rank"] >= words["rank"].quantile(0.999)].count()[0]
    words = words[0:threshold]
    for w in words["term"]:
        if len(w.split()) > 1:
            terms = w.split()
            terms = [t for t in terms if len(t) > 2]
            if len(terms) > 1:
                tfidf_ngrams[" ".join(terms)] = "_".join(terms)
    to_return = tfidf_ngrams

    to_return = remove_items_from_dict(to_return)
    return to_return


def get_PMI_bigrams(list_of_texts):

    """Function that calculate bigrams with PMI.
        The pointwise mutual information (PMI) for a (word, context) pair in our corpus is
        defined as the probability of their co-occurrence divided by the probabilities of them appearing individually
        Expression: log(p(x,y) / (p(x) * p(y)))

        Good collocation pairs have high PMI because the probability of co-occurrence is only slightly lower than the
        probabilities of occurrence of each word. Conversely, a pair of words whose probabilities of
        occurrence are considerably higher than their probability of co-occurrence gets a small PMI score.

    Args:        
        s (str)

    Returns:
        [dict]: Format: item item : item_item
    """

    sentences = list_of_texts
    sentences = [word_tokenize(line) for line in sentences]

    unigrams_freq = Counter()
    bigrams_freq = Counter()
    pmi_samples = Counter()
    data = []

    for line in sentences:
        for word in line:
            unigrams_freq[word] += 1
        for word1, word2 in ngrams(line, 2):
            bigrams_freq[(word1, word2)] += 1

    # sum for probabilities
    sum_unigrams = sum(unigrams_freq.values())
    sum_bigrams = sum(bigrams_freq.values())
    bigrams_freq = [(key, value) for (key, value) in bigrams_freq.items() if value > 50]
    bigrams_freq = dict(bigrams_freq)

    for (w1, w2), N in tqdm.tqdm(bigrams_freq.items()):
        data.append(
            log(
                (N / sum_bigrams)
                / (unigrams_freq[w1] / sum_unigrams)
                / (unigrams_freq[w2] / sum_unigrams)
            )
        )
        pmi_samples[(w1, w2)] = data[-1]

    pmi_samples_dict = {}
    for words, pmi in pmi_samples.items():
        pmi_samples_dict["_".join(words)] = pmi

    pmi_samples_dict = remove_items_from_dict(pmi_samples_dict)
    return pmi_samples_dict


# ----------------------------------------------------------------------
# Used in Protagonism Classification
# ----------------------------------------------------------------------
def find_ngrams_in_protagonism_text(text):

    """This function generates ngrams (defined in the global list NGRAMS_LIST)
        maintaining the proportion of ngrams in the text (does not calculate most_common
        that would change the position text according to the frequency)

    Args:
        text (str)

    Returns:
        [list]: Ngram list
    """
    text_tokens = word_tokenize(text)
    ngrams_terms = [dict(Counter(ngrams(text_tokens, x))) for x in NGRAMS_LIST]
    ngrams_terms = [
        " ".join(key) for inner_dictionary in ngrams_terms for key in inner_dictionary
    ]

    return ngrams_terms


def find_ngrams_counter(words):

    """
      This function generates ngrams (defined in the global list NGRAMS_LIST)
      making a count of the most frequent ngrams calculated with most_common

    Args:
        words (list)

    Returns:
        [dict]: Ngram dicionary with ngram as key and frequency as value
    """

    words = word_tokenize(words)
    counter_words = [
        dict(Counter(ngrams(words, x)).most_common(None)) for x in NGRAMS_LIST
    ]
    counter_words = [
        (key, freq)
        for inner_dictionary in counter_words
        for (key, freq) in inner_dictionary.items()
    ]
    return counter_words
