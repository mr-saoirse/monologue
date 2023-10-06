class WikiWalker:
    """
    utility for getting some summaries about things
    todo: some search features, disambiguate, network building
    """

    def __init__(self):
        import wikipediaapi

        self._ww = wikipediaapi.Wikipedia("Monlogue (amartey@gmail.com)", "en")

    def describe(self, thing):
        p = self._ww.page(thing)
        return {
            "name": thing,
            "url": p.fullurl,
            "text": p.summary,
            "sample_related_things": list(p.links.keys())[::10][:10],
            "doc_id": thing,
        }

    def iter_sections(self, thing, min_text_length=100):
        p = self._ww.page(thing)
        for s in p.sections:
            if len(s.text) > min_text_length:
                yield {
                    "name": f"{thing} {s.title}",
                    "url": p.fullurl,
                    "summary": p.summary,
                    "text": s.text,
                    "sample_related_things": list(p.links.keys())[::10][:10],
                    "doc_id": thing,
                }

    def explore(self, sentence):
        """

        WIP: explore a text and get more information on references

        sentence = "England Lifts Coronavirus Rules as Queen Elizabeth Battles Infection. New York, New York. cool"


        #We would store things like this
        PERSON:      People, including fictional.
        NORP:        Nationalities or religious or political groups.
        FAC:         Buildings, airports, highways, bridges, etc.
        ORG:         Companies, agencies, institutions, etc.
        GPE:         Countries, cities, states.
        LOC:         Non-GPE locations, mountain ranges, bodies of water.
        PRODUCT:     Objects, vehicles, foods, etc. (Not services.)
        EVENT:       Named hurricanes, battles, wars, sports events, etc.
        WORK_OF_ART: Titles of books, songs, etc.
        LAW:         Named documents made into laws.
        LANGUAGE:    Any named language.

        #we would note things like this
        DATE:        Absolute or relative dates or periods.
        TIME:        Times smaller than a day.
        PERCENT:     Percentage, including ”%“.
        MONEY:       Monetary values, including unit.
        QUANTITY:    Measurements, as of weight or distance.
        ORDINAL:     “first”, “second”, etc.
        CARDINAL:    Numerals that do not fall under another type.

        Extract entities and put them in their places

        """
        import spacy

        # python -m spacy download en_core_web_lg etc.
        nlp = spacy.load("en_core_web_trf")  # highest acc model

        doc = nlp(sentence)

        for ent in doc.ents:
            print(ent.text, ent.start_char, ent.end_char, ent.label_)

            # TODO look em up and save them
            # handle the ambigous cases e.g. using the related items links and walking those
