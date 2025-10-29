"""
SerpApi Client Wrapper for Google Hotels API
Handles authentication, rate limiting, and error handling
"""
import os
import requests
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime
import dotenv
dotenv.load_dotenv()

logger = logging.getLogger(__name__)


class SerpApiError(Exception):
    """Custom exception for SerpApi errors"""
    pass


class GoogleHotelsApiClient:
    """
    Client wrapper for SerpApi's Google Hotels API
    Provides clean, atomic methods for hotel search operations
    """
    
    BASE_URL = "https://serpapi.com/search"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the API client
        
        Args:
            api_key: SerpApi API key. If not provided, will look for SERPAPI_API_KEY env var
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "SerpApi API key is required. Set SERPAPI_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "GoogleHotelsMCP/1.0.0"
        })
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make authenticated request to SerpApi
        
        Args:
            params: Query parameters for the API request
            
        Returns:
            JSON response from API
            
        Raises:
            SerpApiError: If the request fails or returns an error
        """
        # Add required parameters
        params.update({
            "api_key": self.api_key,
            "engine": "google_hotels"
        })
        
        try:
            logger.debug(f"Making SerpApi request with params: {params}")
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if "error" in data:
                raise SerpApiError(f"SerpApi error: {data['error']}")
            
            # Check search status
            search_metadata = data.get("search_metadata", {})
            if search_metadata.get("status") == "Error":
                error_msg = search_metadata.get("error", "Unknown error")
                raise SerpApiError(f"Search failed: {error_msg}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise SerpApiError(f"Request failed: {str(e)}")
        except ValueError as e:
            raise SerpApiError(f"Invalid JSON response: {str(e)}")
    
    def search_hotels(
        self,
        query: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 2,
        children: int = 0,
        currency: str = "USD",
        country: str = "us",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Search for hotels with basic parameters
        
        Args:
            query: Location or hotel name to search
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            adults: Number of adults (default: 2)
            children: Number of children (default: 0)
            currency: Currency code (default: USD)
            country: Country code (default: us)
            language: Language code (default: en)
            
        Returns:
            Search results containing properties array and metadata
        """
        # Validate date format
        self._validate_date_format(check_in_date)
        self._validate_date_format(check_out_date)
        
        params = {
            "q": query,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "adults": adults,
            "children": children,
            "currency": currency,
            "gl": country,
            "hl": language
        }
        
        return self._make_request(params)
    
    def search_hotels_with_filters(
        self,
        query: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 2,
        children: int = 0,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        amenities: Optional[List[int]] = None,
        brands: Optional[List[int]] = None,
        property_types: Optional[List[int]] = None,
        sort_by: Optional[int] = None,
        currency: str = "USD",
        country: str = "us",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Advanced hotel search with filtering options
        
        Args:
            query: Location or hotel name to search
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            adults: Number of adults (default: 2)
            children: Number of children (default: 0)
            min_price: Minimum price per night
            max_price: Maximum price per night
            min_rating: Minimum hotel rating (3.5, 4.0, 4.5)
            amenities: List of amenity IDs to filter by
            hotel_brands: List of brand IDs to filter by
            property_types: List of property type IDs
            sort_by: Sort order (3 for lowest price, 13 for highest rating)
            currency: Currency code (default: USD)
            country: Country code (default: us)
            language: Language code (default: en)
            
        Returns:
            Filtered search results
        """
        # Validate date format
        self._validate_date_format(check_in_date)
        self._validate_date_format(check_out_date)
        
        params = {
            "q": query,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "adults": adults,
            "children": children,
            "currency": currency,
            "gl": country,
            "hl": language
        }
        
        # Add optional filters
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if min_rating is not None:
            # Convert rating to SerpApi format
            rating_map = {3.5: 7, 4.0: 8, 4.5: 9}
            params["rating"] = rating_map.get(min_rating, 8)
        if amenities:
            params["amenities"] = ",".join(map(str, amenities))
        if brands:
            params["brands"] = ",".join(map(str, brands))
        if property_types:
            params["property_type"] = ",".join(map(str, property_types))
        if sort_by is not None:
            params["sort_by"] = sort_by
        
        return self._make_request(params)

    def get_hotel_details(
        self,
        property_token: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 2,
        children: int = 0,
        currency: str = "USD",
        country: str = "us",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific hotel
        
        Args:
            property_token: Unique token for the hotel property
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            adults: Number of adults (default: 2)
            children: Number of children (default: 0)
            currency: Currency code (default: USD)
            country: Country code (default: us)
            language: Language code (default: en)
            
        Returns:
            Detailed hotel information including prices, amenities, reviews
        """
        # Validate date format
        self._validate_date_format(check_in_date)
        self._validate_date_format(check_out_date)
        
        # For hotel details, we need to include a query parameter along with property_token
        # This is based on SerpApi's Google Hotels documentation
        params = {
            "q": "hotel details",  # Required base query
            "property_token": property_token,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "adults": adults,
            "children": children,
            "currency": currency,
            "gl": country,
            "hl": language
        }
        
        return self._make_request(params)
    
    def get_booking_links(
        self,
        property_token: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 2,
        children: int = 0,
        currency: str = "USD",
        country: str = "us",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get booking links and options for a specific hotel
        
        Args:
            property_token: Unique token for the hotel property
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            adults: Number of adults
            children: Number of children
            currency: Currency code
            country: Country code
            language: Language code
            
        Returns:
            Hotel details with booking options and links
        """
        # This uses the same endpoint as get_hotel_details but focuses on booking data
        return self.get_hotel_details(
            property_token=property_token,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults,
            children=children,
            currency=currency,
            country=country,
            language=language
        )
    
    def _validate_date_format(self, date_str: str) -> None:
        """
        Validate that date string is in YYYY-MM-DD format
        
        Args:
            date_str: Date string to validate
            
        Raises:
            ValueError: If date format is invalid
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD")
    
    def get_supported_amenities(self) -> List[Dict[str, Union[int, str]]]:
        """
        Get list of supported amenities with their IDs
        Note: This is a static list based on SerpApi documentation
        
        Returns:
            List of amenities with id and name
        """
        return[
            {"id": 1, "name": "Free parking"},
            {"id": 3, "name": "Parking"},
            {"id": 4, "name": "Indoor pool"},
            {"id": 5, "name": "Outdoor pool"},
            {"id": 6, "name": "Pool"},
            {"id": 7, "name": "Fitness center"},
            {"id": 8, "name": "Restaurant"},
            {"id": 9, "name": "Free breakfast"},
            {"id": 10, "name": "Spa"},
            {"id": 11, "name": "Beach access"},
            {"id": 12, "name": "Child-friendly"},
            {"id": 15, "name": "Bar"},
            {"id": 19, "name": "Pet-friendly"},
            {"id": 22, "name": "Room service"},
            {"id": 35, "name": "Free Wi-Fi"},
            {"id": 40, "name": "Air-conditioned"},
            {"id": 52, "name": "All-inclusive available"},
            {"id": 53, "name": "Wheelchair accessible"},
            {"id": 61, "name": "EV charger"}
        ]
