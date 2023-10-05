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
