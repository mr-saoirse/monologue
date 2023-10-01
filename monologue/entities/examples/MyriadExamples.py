from datetime import datetime
from .. import AbstractEntity, Optional, Field

class NycTripEvent(AbstractEntity):
    """
    use NYC data see notebook sample to fetch
    ask questions from the tool such as 
    1. How many times has Lyra been dropped off to Lenox Hill West
    2. Who has been to Carroll Gardens most often? How many times have they gone. List all their trips and then tell me when they went last
    3. "Where are the last three places JohnWalker has gone?" #purposeful use a variant of the name to exploit enums 
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
    
    
class AvengingPassengers(AbstractEntity):
    name: str = Field(is_key=True)
    gender: Optional[str]
    appearances: Optional[int]
    uri: Optional[str] 
    text: str = Field(long_text=True)
    
    
class Places(AbstractEntity):
    name: str = Field(is_key=True)
    text: str = Field(long_text=True)