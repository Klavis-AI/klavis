"""
Data models and schemas for Google Hotels MCP Server
Using Pydantic for validation and type safety
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class GpsCoordinates(BaseModel):
    """GPS coordinates for hotel location"""
    latitude: float
    longitude: float


class PriceInfo(BaseModel):
    """Price information with formatted and extracted values"""
    price: Optional[str] = None
    extracted_price: Optional[float] = None
    price_before_taxes: Optional[str] = None
    extracted_price_before_taxes: Optional[float] = None


class HotelProperty(BaseModel):
    """Individual hotel property from search results"""
    type: str = Field(..., description="Property type (hotel, resort, etc.)")
    property_token: str = Field(..., description="Unique identifier for the property")
    data_id: Optional[str] = None
    name: str = Field(..., description="Hotel name")
    link: Optional[str] = None
    description: Optional[str] = None
    gps_coordinates: Optional[GpsCoordinates] = None
    city: Optional[str] = None
    country: Optional[str] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    rate_per_night: Optional[PriceInfo] = None
    total_rate: Optional[PriceInfo] = None
    deal: Optional[str] = None
    deal_description: Optional[str] = None
    overall_rating: Optional[float] = None
    reviews: Optional[int] = None
    hotel_class: Optional[str] = None
    extracted_hotel_class: Optional[int] = None
    amenities: Optional[List[str]] = None


class HotelSearchRequest(BaseModel):
    """Request model for basic hotel search"""
    query: str = Field(..., description="Location or hotel name to search")
    check_in_date: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out_date: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    adults: int = Field(default=2, ge=1, le=30, description="Number of adults")
    children: int = Field(default=0, ge=0, le=10, description="Number of children")
    currency: str = Field(default="USD", description="Currency code (USD, EUR, etc.)")
    country: str = Field(default="us", description="Country code (us, uk, etc.)")
    language: str = Field(default="en", description="Language code (en, es, fr, etc.)")

    @field_validator('check_in_date', 'check_out_date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')

    @field_validator('check_out_date')
    @classmethod
    def validate_checkout_after_checkin(cls, v, info):
        # Get the check_in_date from the data being validated
        if info.data and 'check_in_date' in info.data:
            check_in = datetime.strptime(info.data['check_in_date'], "%Y-%m-%d")
            check_out = datetime.strptime(v, "%Y-%m-%d")
            if check_out <= check_in:
                raise ValueError('Check-out date must be after check-in date')
        return v


class HotelSummary(BaseModel):
    """Simplified hotel summary for comparison"""
    name: str
    property_token: str
    rate_per_night: Optional[float] = None
    total_rate: Optional[float] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    location: Optional[str] = None
    deal: Optional[str] = None


class ToolResult(BaseModel):
    """Base class for tool results"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None