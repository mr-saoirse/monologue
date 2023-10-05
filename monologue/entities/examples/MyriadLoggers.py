"""
    This is one pattern for communicating a "type" for raw data
    this is simply because the logger reports the meta
    
    below we ingest people and topics which means the receiver will route them differently
"""
from monologue import log_event
import random
from monologue.core.data.io import typed_record_iterator
from .MyriadExamples import BookReviews, BookReviewers
from monologue.core.data.clients import WikiWalker

"""
routing handlers
"""


def people(data):
    log_event(data)


def books(data):
    log_event(data)


def topics(data):
    log_event(data)


"""

Sample data reader
- at this stage we have imported books, universities and users into the store
- but we will "stream" reviews into the system
- as we do we will fetch some text context about book titles and categories and add them as topics radonly
"""


SAMPLE_ROOT = "/Users/sirsh/Downloads/monologue_dataset"


def ingest_book_reviewers_sample(limit=10):
    """
    This illustrates
    """
    ww = WikiWalker()
    # lazy polar iterator over the rows
    path = f"{SAMPLE_ROOT}/amz_books_reviewer_users_generated.feather"
    _limit = 0
    for record in typed_record_iterator(path, BookReviewers):
        log_event(f"{record}")
        if random.random() > 0.8:
            # with some probability, iterate over the topic sections and log the info
            for data in ww.iter_sections(record.favourite_topic):
                message = f""" ***{data['name']}***
                {data['text']}
                """
                topics(message)
        # with some probability, iterate over the books section and log the info
        if random.random() > 0.8:
            for data in ww.iter_sections(record.favourite_book):
                message = f""" ***{data['name']}***
                {data['text']}
                """
                books(message)

        _limit += 1
        if _limit > limit:
            break
