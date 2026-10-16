import spacy
from spacy_langdetect import LanguageDetector


def correct_predominant_language(dataframe, content_column):
    """Corrects the designated language for each news item

    Args:
        dataframe (Pandas Dataframe)

    Returns:
        [Pandas Dataframe]
    """
    print("Inspect predominant language...")

    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe(LanguageDetector(), name="language_detector", last=True)

    if len(dataframe) > 0:
        dataframe.loc[:, "Predominant language"] = dataframe[content_column].apply(
            lambda x: nlp(x[0:2000])._.language["language"]
        )

        dataframe.loc[dataframe["Predominant language"] == "pt", "Idioma"] = "Portuguese"
        dataframe.loc[dataframe["Predominant language"] == "en", "Idioma"] = "English"

    return dataframe
