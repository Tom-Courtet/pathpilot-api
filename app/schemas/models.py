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

class SelectedTransport(BaseModel):
    id: str = Field(..., alias="$id")
    departureDate: str

    model_config = ConfigDict(populate_by_name=True)

class SelectedLodging(BaseModel):
    id: str = Field(..., alias="$id")
    numberOfNights: int

    model_config = ConfigDict(populate_by_name=True)

class TripSelection(BaseModel):
    selectedTransports: List[SelectedTransport]
    selectedLodgings: List[SelectedLodging]
    tripStartDate: str
    tripEndDate: str
    totalCost: str
    remainingBudget: str

class TripGenerateResponse(BaseModel):
    success: bool
    tripId: str
    createdAt: str
    request: TripRequest
    selection: TripSelection


class TravelLocationPoint(BaseModel):
    name: str
    country: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class TravelDestination(BaseModel):
    id: str
    name: str
    country: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    duration: Optional[int] = None

class SchemaTransport(BaseModel):
    id: str
    type: str
    departureHour: str
    arrivalHour: str
    price: float
    company: str

class TransportLeg(BaseModel):
    fromLocation: str = Field(..., alias="from")
    toLocation: str = Field(..., alias="to")
    date: Optional[str] = None
    availableTransports: List[SchemaTransport] = []
    selectedTransportId: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

class SchemaLodging(BaseModel):
    lodgingId: str
    destinationId: str
    checkInDate: Optional[str] = None
    checkOutDate: Optional[str] = None

class TravelPreferences(BaseModel):
    sharedExpensesTracking: Optional[bool] = False
    activityLevel: Optional[str] = "medium"
    dietaryPreference: Optional[str] = None
    reducedMobility: Optional[bool] = False
    travelWithChildren: bool = False
    children: List[Child] = []
    spokenLanguages: List[str] = []
    ecologicalPreference: bool = False

class TravelSchema(BaseModel):
    tripType: Optional[str] = None
    departurePoint: Optional[TravelLocationPoint] = None
    returnPoint: Optional[TravelLocationPoint] = None
    destinations: List[TravelDestination] = []
    transportLegs: List[TransportLeg] = []
    selectedLodgings: List[SchemaLodging] = []
    preferences: Optional[TravelPreferences] = None

class TravelDocument(BaseModel):
    id: Optional[str] = Field(None, alias="$id")
    name: str
    startDate: str
    endDate: str
    travelers: int = 1
    visible: Optional[bool] = True
    userIds: List[str] = []
    uuid: Optional[str] = None
    inviteToken: Optional[str] = None
    inviteExpiresAt: Optional[str] = None
    schema_: str = Field(..., alias="schema")
    createdAt: Optional[str] = Field(None, alias="$createdAt")
    updatedAt: Optional[str] = Field(None, alias="$updatedAt")

    model_config = ConfigDict(populate_by_name=True)