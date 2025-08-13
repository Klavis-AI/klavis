"""
MCP Tool implementations for Google Hotels
Following atomicity principle - each tool does one specific job well
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from api_client import GoogleHotelsApiClient, SerpApiError
from schemas import HotelSearchRequest, HotelSummary, ToolResult

logger = logging.getLogger(__name__)


class GoogleHotelsTools:
    """
    Collection of atomic tools for Google Hotels functionality
    Each tool performs one specific task and provides clear, AI-friendly responses
    """
    
    def __init__(self, api_client: GoogleHotelsApiClient):
        self.api_client = api_client
    
    async def search_hotels(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for hotels by location and dates
        
        Tool name: search_hotels
        Description: Search for hotels in a specific location with check-in and check-out dates.
        Returns a list of available hotels with basic information like name, price, and rating.
        """
        try:
            # Validate and parse request
            request = HotelSearchRequest(**arguments)
            
            logger.info(f"Searching hotels: {request.query} from {request.check_in_date} to {request.check_out_date}")
            
            # Make API call
            results = self.api_client.search_hotels(
                query=request.query,
                check_in_date=request.check_in_date,
                check_out_date=request.check_out_date,
                adults=request.adults,
                children=request.children,
                currency=request.currency,
                country=request.country,
                language=request.language
            )
            
            # Extract and format hotels
            properties = results.get("properties", [])
            hotels = []
            
            for prop in properties[:10]:  # Limit to top 10 results
                hotel = self._format_hotel_summary(prop)
                hotels.append(hotel)
            
            # Prepare response
            total_found = len(properties)
            date_range = f"{request.check_in_date} to {request.check_out_date}"
            
            return {
                "success": True,
                "hotels_found": total_found,
                "location": request.query,
                "date_range": date_range,
                "guests": f"{request.adults} adults" + (f", {request.children} children" if request.children > 0 else ""),
                "currency": request.currency,
                "hotels": hotels,
                "message": f"Found {total_found} hotels in {request.query} for {date_range}"
            }
            
        except ValueError as e:
            logger.error(f"Invalid search parameters: {e}")
            return {
                "success": False,
                "error": f"Invalid parameters: {str(e)}",
                "suggestion": "Please check your date format (YYYY-MM-DD) and ensure check-out is after check-in"
            }
        except SerpApiError as e:
            logger.error(f"API error during hotel search: {e}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "suggestion": "Please try a different location or date range"
            }
        except Exception as e:
            logger.error(f"Unexpected error in search_hotels: {e}")
            return {
                "success": False,
                "error": "An unexpected error occurred",
                "suggestion": "Please try your search again"
            }
    
    async def get_supported_amenities(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get list of supported amenities for filtering
        
        Tool name: get_supported_amenities
        Description: Get a list of all supported amenities with their IDs for use in 
        advanced hotel searches. Use these IDs with the search_hotels_with_filters tool.
        """
        try:
            amenities = self.api_client.get_supported_amenities()
            
            return {
                "success": True,
                "total_amenities": len(amenities),
                "amenities": amenities,
                "message": "Use these amenity IDs with the search_hotels_with_filters tool",
                "example": "To find hotels with free WiFi and parking, use amenity IDs: [2, 3]"
            }
            
        except Exception as e:
            logger.error(f"Error getting amenities: {e}")
            return {
                "success": False,
                "error": "Failed to get supported amenities"
            }
    
    async def compare_hotel_prices(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare prices across multiple hotels in search results
        
        Tool name: compare_hotel_prices
        Description: Compare prices, ratings, and value across hotels in a location. 
        Identifies the cheapest, highest-rated, and best value options.
        """
        try:
            # Use the basic search first
            search_result = await self.search_hotels(arguments)
            
            if not search_result.get("success"):
                return search_result
            
            hotels = search_result.get("hotels", [])
            
            if len(hotels) < 2:
                return {
                    "success": False,
                    "error": "Not enough hotels found for comparison",
                    "suggestion": "Try a different location or date range"
                }
            
            # Find best options
            cheapest = min(hotels, key=lambda h: h.get("rate_per_night", float('inf')), default=None)
            highest_rated = max(hotels, key=lambda h: h.get("rating", 0), default=None)
            
            # Price statistics
            prices = [h.get("rate_per_night") for h in hotels if h.get("rate_per_night")]
            avg_price = sum(prices) / len(prices) if prices else 0
            
            return {
                "success": True,
                "total_hotels": len(hotels),
                "location": search_result.get("location"),
                "date_range": search_result.get("date_range"),
                "price_range": {
                    "min": min(prices) if prices else None,
                    "max": max(prices) if prices else None,
                    "average": round(avg_price, 2) if avg_price else None
                },
                "recommendations": {
                    "cheapest": self._format_recommendation(cheapest, "cheapest option"),
                    "highest_rated": self._format_recommendation(highest_rated, "highest rated")
                },
                "all_hotels": hotels,
                "message": f"Compared {len(hotels)} hotels to find the best options"
            }
            
        except Exception as e:
            logger.error(f"Error in price comparison: {e}")
            return {
                "success": False,
                "error": "Failed to compare hotel prices"
            }
        
    async def get_booking_links(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get booking links and options for a specific hotel
        
        Tool name: get_booking_links
        Description: Get booking links and pricing options for a specific hotel.
        Provides direct links to book the hotel on various platforms.
        """
        try:
            # Validate required parameters
            property_token = arguments.get("property_token")
            check_in_date = arguments.get("check_in_date")
            check_out_date = arguments.get("check_out_date")
            
            if not property_token:
                return {
                    "success": False,
                    "error": "Property token is required",
                    "suggestion": "Please provide the hotel's property_token from search results"
                }
            
            if not check_in_date or not check_out_date:
                return {
                    "success": False,
                    "error": "Check-in and check-out dates are required",
                    "suggestion": "Please provide dates in YYYY-MM-DD format"
                }
            
            # Get optional parameters
            adults = arguments.get("adults", 2)
            children = arguments.get("children", 0)
            currency = arguments.get("currency", "USD")
            country = arguments.get("country", "us")
            language = arguments.get("language", "en")
            
            logger.info(f"Getting booking links for property: {property_token}")
            
            # Make a fresh search to get current hotel data with booking information
            # We'll search for a broad query and then find our specific hotel
            results = self.api_client.search_hotels(
                query="hotels",  # Broad search
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                adults=adults,
                children=children,
                currency=currency,
                country=country,
                language=language
            )
            
            # Find the hotel with matching property_token
            properties = results.get("properties", [])
            target_hotel = None
            
            for hotel in properties:
                if hotel.get("property_token") == property_token:
                    target_hotel = hotel
                    break
            
            # If not found in broad search, create a booking info from the token itself
            if not target_hotel:
                # Create a basic response with Google Hotels link
                booking_info = self._create_basic_booking_info(property_token, check_in_date, check_out_date, adults, children)
                return {
                    "success": True,
                    "hotel_name": "Hotel (from search)",
                    "property_token": property_token,
                    "booking_info": booking_info,
                    "message": "Created booking links using property token. For full details, please search for hotels again."
                }
            
            # Format booking information from the found hotel
            booking_info = self._format_booking_info(target_hotel, check_in_date, check_out_date, adults, children)
            
            return {
                "success": True,
                "hotel_name": target_hotel.get("name"),
                "property_token": property_token,
                "booking_info": booking_info,
                "message": f"Found booking options for {target_hotel.get('name', 'this hotel')}"
            }
            
        except ValueError as e:
            logger.error(f"Invalid booking request: {e}")
            return {
                "success": False,
                "error": f"Invalid parameters: {str(e)}",
                "suggestion": "Please check your date format (YYYY-MM-DD) and property token"
            }
        except SerpApiError as e:
            logger.error(f"API error getting booking links: {e}")
            return {
                "success": False,
                "error": f"Failed to get booking links: {str(e)}",
                "suggestion": "Please verify the property token and try again"
            }
        except Exception as e:
            logger.error(f"Unexpected error getting booking links: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "suggestion": "Please try your request again",
                "debug_info": str(e)
            }
        
    async def search_hotels_with_filters(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for hotels with advanced filtering options
        
        Tool name: search_hotels_with_filters
        Description: Advanced hotel search with filtering options like price range, minimum rating,
        amenities, and hotel brands. Perfect for finding specific types of accommodations.
        
        Args:
            arguments: Dictionary containing search parameters and filters
            
        Returns:
            Dictionary with filtered search results
        """
        try:
            # Validate required parameters
            query = arguments.get("query")
            check_in_date = arguments.get("check_in_date") 
            check_out_date = arguments.get("check_out_date")
            
            if not query:
                return {
                    "success": False,
                    "error": "Location query is required",
                    "suggestion": "Please provide a location to search (e.g., 'New York', 'Paris')"
                }
            
            if not check_in_date or not check_out_date:
                return {
                    "success": False,
                    "error": "Check-in and check-out dates are required",
                    "suggestion": "Please provide dates in YYYY-MM-DD format"
                }
            
            # Get all parameters
            adults = arguments.get("adults", 2)
            children = arguments.get("children", 0)
            min_price = arguments.get("min_price")
            max_price = arguments.get("max_price")
            min_rating = arguments.get("min_rating")
            amenities = arguments.get("amenities")
            brands = arguments.get("brands")
            property_types = arguments.get("property_types")
            sort_by = arguments.get("sort_by")
            currency = arguments.get("currency", "USD")
            country = arguments.get("country", "us")
            language = arguments.get("language", "en")
            
            logger.info(f"Advanced search: {query} with filters")
            
            # Make API call with filters
            results = self.api_client.search_hotels_with_filters(
                query=query,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                adults=adults,
                children=children,
                min_price=min_price,
                max_price=max_price,
                min_rating=min_rating,
                amenities=amenities,
                brands=brands,
                property_types=property_types,
                sort_by=sort_by,
                currency=currency,
                country=country,
                language=language
            )
            
            # Process results
            properties = results.get("properties", [])
            hotels = []
            
            for prop in properties:
                hotel = self._format_hotel_summary(prop)
                hotels.append(hotel)
            
            # Build filter summary
            filters_applied = []
            if min_price: filters_applied.append(f"min price: ${min_price}")
            if max_price: filters_applied.append(f"max price: ${max_price}")
            if min_rating: filters_applied.append(f"min rating: {min_rating}⭐")
            if amenities: filters_applied.append(f"{len(amenities)} amenities")
            if brands: filters_applied.append(f"{len(brands)} brands")
            if sort_by == 3: filters_applied.append("sorted by lowest price")
            elif sort_by == 13: filters_applied.append("sorted by highest rating")
            
            filter_text = ", ".join(filters_applied) if filters_applied else "no filters"
            
            return {
                "success": True,
                "hotels_found": len(properties),
                "location": query,
                "date_range": f"{check_in_date} to {check_out_date}",
                "guests": f"{adults} adults" + (f", {children} children" if children > 0 else ""),
                "filters_applied": filter_text,
                "hotels": hotels,
                "message": f"Found {len(properties)} hotels matching your criteria in {query}"
            }
            
        except ValueError as e:
            logger.error(f"Invalid search parameters: {e}")
            return {
                "success": False,
                "error": f"Invalid parameters: {str(e)}",
                "suggestion": "Please check your filters and date format"
            }
        except SerpApiError as e:
            logger.error(f"API error during filtered search: {e}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "suggestion": "Try relaxing your filters or choosing a different location"
            }
        except Exception as e:
            logger.error(f"Unexpected error in filtered search: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "suggestion": "Please try your search again",
                "debug_info": str(e)
            }
    
    def _format_hotel_summary(self, hotel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format hotel data into a clean summary
        """
        # Extract price information - handle both formats
        price_per_night = None
        total_price = None
        
        # Try SerpApi format first (rate_per_night with extracted_lowest)
        if hotel_data.get("rate_per_night"):
            price_per_night = hotel_data["rate_per_night"].get("extracted_lowest")
        # Fallback to standard format (price_per_night with extracted_price)
        elif hotel_data.get("price_per_night"):
            price_per_night = hotel_data["price_per_night"].get("extracted_price")
        
        # Try SerpApi format first (total_rate with extracted_lowest)
        if hotel_data.get("total_rate"):
            total_price = hotel_data["total_rate"].get("extracted_lowest")
        # Fallback to standard format (total_price with extracted_price)
        elif hotel_data.get("total_price"):
            total_price = hotel_data["total_price"].get("extracted_price")
        
        # Build location string
        location_parts = []
        if hotel_data.get("city"):
            location_parts.append(hotel_data["city"])
        if hotel_data.get("country"):
            location_parts.append(hotel_data["country"])
        location = ", ".join(location_parts) if location_parts else None
        
        return {
            "name": hotel_data.get("name"),
            "property_token": hotel_data.get("property_token"),
            "description": hotel_data.get("description"),
            "location": location,
            "price_per_night": price_per_night,
            "total_price": total_price,
            "rating": hotel_data.get("overall_rating"),
            "reviews_count": hotel_data.get("reviews"),
            "hotel_class": hotel_data.get("extracted_hotel_class"),
            "deal": hotel_data.get("deal"),
            "check_in_time": hotel_data.get("check_in_time"),
            "check_out_time": hotel_data.get("check_out_time"),
            "website": hotel_data.get("link")
        }
    
    def _format_recommendation(self, hotel: Optional[Dict[str, Any]], category: str) -> Dict[str, Any]:
        """
        Format a hotel recommendation
        """
        if not hotel:
            return {"category": category, "hotel": None, "reason": "No suitable hotel found"}
        
        reason = ""
        if category == "cheapest option" and hotel.get("rate_per_night"):
            reason = f"${hotel['rate_per_night']}/night"
        elif category == "highest rated" and hotel.get("rating"):
            reason = f"{hotel['rating']}⭐ rating"
        
        return {
            "category": category,
            "hotel": hotel,
            "reason": reason
        }
    
    def _format_booking_info(self, hotel_data: Dict[str, Any], check_in_date: str, check_out_date: str, adults: int, children: int) -> Dict[str, Any]:
        """
        Format booking information for a hotel
        
        Args:
            hotel_data: Raw hotel data from API
            check_in_date: Check-in date
            check_out_date: Check-out date
            adults: Number of adults
            children: Number of children
            
        Returns:
            Formatted booking information
        """
        # Extract basic hotel info
        hotel_summary = self._format_hotel_summary(hotel_data)
        
        # Extract booking-specific data
        booking_links = []
        
        # Check for direct hotel website - this is the most valuable link
        if hotel_data.get("link"):
            booking_links.append({
                "platform": "Hotel Website",
                "url": hotel_data["link"],
                "type": "direct",
                "description": f"Book directly with {hotel_data.get('name', 'the hotel')} - often best for loyalty points and rates"
            })
        
        # Check for booking platforms in the data (third-party sites)
        if hotel_data.get("booking_options"):
            for option in hotel_data["booking_options"]:
                booking_links.append({
                    "platform": option.get("name", "Booking Platform"),
                    "url": option.get("link", ""),
                    "price": option.get("price"),
                    "type": "third_party",
                    "description": f"Book through {option.get('name', 'this platform')}"
                })
        
        # Check for ads/sponsored links (these are often major booking sites)
        if hotel_data.get("ads"):
            for ad in hotel_data["ads"]:
                booking_links.append({
                    "platform": ad.get("name", "Booking Platform"),
                    "url": ad.get("link", ""),
                    "price": ad.get("price"),
                    "type": "sponsored",
                    "description": f"Book through {ad.get('name', 'this platform')}"
                })
        
        # Calculate nights
        from datetime import datetime
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        nights = (check_out - check_in).days
        
        return {
            "hotel_details": hotel_summary,
            "stay_details": {
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "nights": nights,
                "adults": adults,
                "children": children
            },
            "pricing": {
                "price_per_night": hotel_summary.get("price_per_night"),
                "total_price": hotel_summary.get("total_price"),
                "currency": "USD",
                "deal": hotel_summary.get("deal")
            },
            "booking_links": booking_links,
            "booking_summary": {
                "total_platforms": len(booking_links),
                "has_direct_booking": any(link["type"] == "direct" for link in booking_links),
                "has_third_party": any(link["type"] in ["third_party", "sponsored"] for link in booking_links)
            }
        }
    

    def _create_basic_booking_info(self, property_token: str, check_in_date: str, check_out_date: str, adults: int, children: int) -> Dict[str, Any]:
        """
        Create basic booking information when hotel details aren't available
        """
        # Calculate nights
        from datetime import datetime
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
        nights = (check_out - check_in).days
        
        # No booking links if we don't have hotel details
        booking_links = []
        
        return {
            "hotel_details": {
                "name": "Hotel (search for full details)",
                "property_token": property_token
            },
            "stay_details": {
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "nights": nights,
                "adults": adults,
                "children": children
            },
            "pricing": {
                "price_per_night": None,
                "total_price": None,
                "currency": "USD",
                "deal": None
            },
            "booking_links": booking_links,
            "booking_summary": {
                "total_platforms": len(booking_links),
                "has_direct_booking": False,
                "has_third_party": False
            }
        }