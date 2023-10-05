from datetime import datetime
import re
from .. import (
    AbstractEntity,
    AbstractVectorStoreEntry,
    OPEN_AI_EMBEDDING_VECTOR_LENGTH,
    INSTRUCT_EMBEDDING_VECTOR_LENGTH,
)
from .. import Optional, Field, List, root_validator


class NycTripEvent(AbstractEntity):
    """
    use NYC data see notebook sample to fetch
    ask questions from the tool such as
    1. How many times has Lyra been dropped off to Lenox Hill West
    2. Who has been to Carroll Gardens most often? How many times have they gone. List all their trips and then tell me when they went last
    3. Where are the last three places JohnWalker has gone?" #purposeful use a variant of the name to exploit enums
    4. How many times as the trip not been paid for? #requires inferring the enumeration of payment types
    5. Do people pay more often by credit card or cash when going to carroll gardens?
    6. What is least popular destination in new york city?
    """

    class Config:
        about = """
        Trips made by New York City’s iconic yellow taxis have been recorded and provided to the TLC
        since 2009. Yellow taxis are traditionally hailed by signaling to a driver who is on duty and seeking
        a passenger (street hail), but now they may also be hailed using an e-hail app like Curb or Arro.
        Yellow taxis are the only vehicles permitted to respond to a street hail from a passenger in all five
        boroughs.
        Records include fields capturing pick-up and drop-off dates/times, pick-up and drop-off locations,
        trip distances, itemized fares, rate types, payment types, and driver-reported passenger counts.
        The records were collected and provided to the NYC Taxi and Limousine Commission (TLC) by
        technology service providers. The trip data was not created by the TLC, and TLC cannot
        guarantee their accuracy.
        """

    index: int = Field(is_key=True)
    passenger_name: str
    pick_up_at: datetime
    drop_off_at: datetime
    passenger_count: int
    trip_distance: float
    payment_type: str
    congestion_surcharge: Optional[float]
    airport_fee: Optional[float]
    borough_pick_up: str
    zone_pick_up: str
    borough_drop_off: str
    zone_drop_off: str


class AvengingPassengers(AbstractVectorStoreEntry):
    gender: Optional[str]
    appearances: Optional[int]
    uri: Optional[str]
    vector: Optional[List[float]] = Field(
        fixed_size_length=OPEN_AI_EMBEDDING_VECTOR_LENGTH
    )


class AvengingPassengersInstruct(AvengingPassengers):
    class Config:
        embeddings_provider = "instruct"

    vector: Optional[List[float]] = Field(
        fixed_size_length=INSTRUCT_EMBEDDING_VECTOR_LENGTH
    )


class Places(AbstractVectorStoreEntry):
    vector: Optional[List[float]] = Field(
        fixed_size_length=OPEN_AI_EMBEDDING_VECTOR_LENGTH
    )


class PlacesInstruct(Places):
    class Config:
        embeddings_provider = "instruct"

    vector: Optional[List[float]] = Field(
        fixed_size_length=INSTRUCT_EMBEDDING_VECTOR_LENGTH
    )


"""
The book views
"""


class TopUniversities(AbstractEntity):
    """
    For this dataset we took the top 200 that did not have null values
    https://www.kaggle.com/datasets/mylesoneill/world-university-rankings
    """

    world_rank: str
    university_name: str = Field(is_key=True)
    country: str
    teaching: float
    international: float
    research: float
    citations: float
    income: float
    total_score: float
    num_students: int
    student_staff_ratio: float
    international_students: str
    female_male_ratio: str
    year: int


class BookReviews(AbstractEntity):
    """
    generated a dataset based on amazon book reviews
    but cleaned here in the notebook see notebooks for datasets
    """

    id: str = Field(is_key=True)
    title: str
    topic: str
    review_score: float
    review_time: int
    review_text: str
    profile_name: str
    user_id: str


class BookReviewers(AbstractEntity):
    user_id: str = Field(is_key=True)
    review_count: int
    review_min: float
    review_max: float
    review_average: float
    profile_name: str
    favourite_book: str
    favourite_topic: str
    university_attended: str


class Books(AbstractEntity):
    title: str = Field(is_key=True)
    description: Optional[str] = Field("No Description")
    first_author: str
    category: str
    published_date: str
    preview_link: Optional[str]
    image: Optional[str]

    @root_validator
    def default_ids(cls, values):
        """
        an example of cleaning data
        """
        values["title"] = re.sub(r"[^a-zA-Z0-9\s]", "", values["title"])
        return values
