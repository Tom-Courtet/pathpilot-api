from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import date

class PromptRequest(BaseModel):
    message: str = Field(..., description="La question ou le prompt à envoyer à l'IA", min_length=1)

class PromptResponse(BaseModel):
    response: str = Field(..., description="La réponse générée par l'IA")

class LocationPoint(BaseModel):
    name: str
    country: Optional[str] = ""

class Child(BaseModel):
    age: int

class Preferences(BaseModel):
    travelWithChildren: bool = False
    children: List[Child] = []
    ecologicalPreference: bool = False

class Lodging(BaseModel):
    id: str = Field(..., alias="$id")
    lodgingName: str
    location: str
    pricePerNight: float
    numberOfGuests: int
    numberOfRooms: int
    wifi: bool = False
    clim: bool = False
    
    model_config = ConfigDict(populate_by_name=True)

class Transport(BaseModel):
    id: str = Field(..., alias="$id")
    type: str
    departureLocation: str
    arrivalLocation: str
    departureHour: str
    arrivalHour: str
    company: str
    price: float
    
    model_config = ConfigDict(populate_by_name=True)

class TripRequest(BaseModel):
    tripGoal: str
    budget: str
    numberOfPeople: int
    departurePoint: LocationPoint
    returnPoint: LocationPoint
    startDate: date
    endDate: date
    availableLodgings: List[Lodging] = []
    availableTransports: List[Transport] = []
    preferences: Preferences

class TripGenerateResponse(BaseModel):
    success: bool
    tripId: str
    createdAt: str
    request: TripRequest
    selection: Dict[str, Any]