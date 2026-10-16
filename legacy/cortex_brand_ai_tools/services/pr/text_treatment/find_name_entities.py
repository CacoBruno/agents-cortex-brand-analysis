from nltk import FreqDist
from joblib import Parallel, delayed
import nltk

nltk.download("averaged_perceptron_tagger")

NER_LIST = ["ORG", "PERSON", "PRODUCT"]

# ----------------------------------------------------------------------
# Opitimization Fuctions
# ----------------------------------------------------------------------
def chunker(iterable, total_length, chunksize):
    """Optimization function"""
    return (
        iterable[pos : pos + chunksize] for pos in range(0, total_length, chunksize)
    )


def flatten(list_of_lists):
    """Optimization function"""
    ner_dict_grouped = []
    for list_ in list_of_lists:
        for value in list_:
            ner_dict_grouped.append(value)
    return ner_dict_grouped


def process_chunk(texts, nlp):
    """Optimization function"""
    preproc_pipe = []
    for doc in nlp.pipe(texts, batch_size=64):
        for ent in doc.ents:
            if ent.label_ in NER_LIST:
                if len(ent.text.split()) > 1 and len(ent.text.split()) < 4:
                    preproc_pipe.append(ent.text)
    return preproc_pipe


def get_optimized_name_entity_recognition(texts, nlp, chunksize=100):

    print("Run optimized ner...")

    executor = Parallel(n_jobs=7, backend="multiprocessing", prefer="processes", max_nbytes=None)
    do_optimization = delayed(process_chunk)
    tasks = (
        do_optimization(chunk, nlp)
        for chunk in chunker(texts, len(texts), chunksize=chunksize)
    )
    result = executor(tasks)
    return flatten(result)


# ----------------------------------------------------------------------
# Find NER filtered by most common
# ----------------------------------------------------------------------
def get_validated_name_entity_recognition(list_of_texts, nlp, min_freq):
    """Use SpaCy library with optimized functions to find the best
        Name Entities Recognition terms.

    Args:
        dataframe (Pandas Dataframe)
        column (str): Text column where NER will be extracted
        nlp (obj): SpaCy model

    Returns:
        [dict]: Dictionary containing NER (term term: term_term)
    """

    ner = get_optimized_name_entity_recognition(list_of_texts, nlp, chunksize=300)
    ner_freq = FreqDist(ner)
    min_count = int(len(list_of_texts) * min_freq)

    validated_ner = [term for (term, freq) in ner_freq.items() if freq >= min_count]

    validated_ner_dict = {}
    for name_entity_recognition in validated_ner:
        validated_ner_dict[name_entity_recognition] = "_".join(
            name_entity_recognition.split()
        )
    return validated_ner_dict
