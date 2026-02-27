import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';

dotenv.config();

// Response interfaces
interface GoogleMapsResponse {
  status: string;
  error_message?: string;
}

interface GeocodeResponse extends GoogleMapsResponse {
  results: Array<{
    place_id: string;
    formatted_address: string;
    geometry: {
      location: {
        lat: number;
        lng: number;
      }
    };
    address_components: Array<{
      long_name: string;
      short_name: string;
      types: string[];
    }>;
  }>;
}

interface PlacesSearchResponse extends GoogleMapsResponse {
  results: Array<{
    name: string;
    place_id: string;
    formatted_address: string;
    geometry: {
      location: {
        lat: number;
        lng: number;
      }
    };
    rating?: number;
    types: string[];
  }>;
}

interface PlaceDetailsResponse extends GoogleMapsResponse {
  result: {
    name: string;
    place_id: string;
    formatted_address: string;
    formatted_phone_number?: string;
    website?: string;
    rating?: number;
    reviews?: Array<{
      author_name: string;
      rating: number;
      text: string;
      time: number;
    }>;
    opening_hours?: {
      weekday_text: string[];
      open_now: boolean;
    };
    geometry: {
      location: {
        lat: number;
        lng: number;
      }
    };
  };
}

interface DistanceMatrixResponse extends GoogleMapsResponse {
  origin_addresses: string[];
  destination_addresses: string[];
  rows: Array<{
    elements: Array<{
      status: string;
      duration: {
        text: string;
        value: number;
      };
      distance: {
        text: string;
        value: number;
      };
    }>;
  }>;
}

interface ElevationResponse extends GoogleMapsResponse {
  results: Array<{
    elevation: number;
    location: {
      lat: number;
      lng: number;
    };
    resolution: number;
  }>;
}

interface DirectionsResponse extends GoogleMapsResponse {
  routes: Array<{
    summary: string;
    legs: Array<{
      distance: {
        text: string;
        value: number;
      };
      duration: {
        text: string;
        value: number;
      };
      steps: Array<{
        html_instructions: string;
        distance: {
          text: string;
          value: number;
        };
        duration: {
          text: string;
          value: number;
        };
        travel_mode: string;
      }>;
    }>;
  }>;
}

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
    apiKey: string;
}>();

// Getter function for the API key
function getApiKey(): string {
    const store = asyncLocalStorage.getStore();
    if (!store) {
        throw new Error('No request context available');
    }
    return store.apiKey;
}

// Utility functions
function safeLog(level: 'error' | 'debug' | 'info' | 'notice' | 'warning' | 'critical' | 'alert' | 'emergency', data: any): void {
    try {
        const logData = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
        console.log(`[${level.toUpperCase()}] ${logData}`);
    } catch (error) {
        console.log(`[${level.toUpperCase()}] [LOG_ERROR] Could not serialize log data`);
    }
}

function extractApiKey(req: Request): string {
    let authData = process.env.AUTH_DATA;

    if (!authData && req.headers['x-auth-data']) {
        try {
            authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
        } catch (error) {
            console.error('Error parsing x-auth-data:', error);
        }
    }

    if (!authData) {
        console.error('Error: Google Maps API key is missing. Provide it via AUTH_DATA env var or x-auth-data header with api_key field.');
        return '';
    }

    const authDataJson = JSON.parse(authData);
    return authDataJson.api_key ?? '';
}

// Tool definitions
const GEOCODE_TOOL: Tool = {
    name: "maps_geocode",
    description: "Convert an address into geographic coordinates",
    inputSchema: {
      type: "object",
      properties: {
        address: {
          type: "string",
          description: "The address to geocode"
        }
      },
      required: ["address"]
    }
  };

const REVERSE_GEOCODE_TOOL: Tool = {
  name: "maps_reverse_geocode",
  description: "Convert coordinates into an address",
  inputSchema: {
    type: "object",
    properties: {
      latitude: {
        type: "number",
        description: "Latitude coordinate"
      },
      longitude: {
        type: "number",
        description: "Longitude coordinate"
      }
    },
    required: ["latitude", "longitude"]
  }
};

const SEARCH_PLACES_TOOL: Tool = {
  name: "maps_search_places",
  description: "Search for places using Google Places API",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Search query"
      },
      location: {
        type: "object",
        properties: {
          latitude: { type: "number" },
          longitude: { type: "number" }
        },
        description: "Optional center point for the search"
      },
      radius: {
        type: "number",
        description: "Search radius in meters (max 50000)"
      }
    },
    required: ["query"]
  }
};

const PLACE_DETAILS_TOOL: Tool = {
  name: "maps_place_details",
  description: "Get detailed information about a specific place",
  inputSchema: {
    type: "object",
    properties: {
      place_id: {
        type: "string",
        description: "The place ID to get details for"
      }
    },
    required: ["place_id"]
  }
};

const DISTANCE_MATRIX_TOOL: Tool = {
  name: "maps_distance_matrix",
  description: "Calculate travel distance and time for multiple origins and destinations",
  inputSchema: {
    type: "object",
    properties: {
      origins: {
        type: "array",
        items: { type: "string" },
        description: "Array of origin addresses or coordinates"
      },
      destinations: {
        type: "array",
        items: { type: "string" },
        description: "Array of destination addresses or coordinates"
      },
      mode: {
        type: "string",
        description: "Travel mode (driving, walking, bicycling, transit)",
        enum: ["driving", "walking", "bicycling", "transit"]
      }
    },
    required: ["origins", "destinations"]
  }
};

const ELEVATION_TOOL: Tool = {
  name: "maps_elevation",
  description: "Get elevation data for locations on the earth",
  inputSchema: {
    type: "object",
    properties: {
      locations: {
        type: "array",
        items: {
          type: "object",
          properties: {
            latitude: { type: "number" },
            longitude: { type: "number" }
          },
          required: ["latitude", "longitude"]
        },
        description: "Array of locations to get elevation for"
      }
    },
    required: ["locations"]
  }
};

const DIRECTIONS_TOOL: Tool = {
  name: "maps_directions",
  description: "Get directions between two points",
  inputSchema: {
    type: "object",
    properties: {
      origin: {
        type: "string",
        description: "Starting point address or coordinates"
      },
      destination: {
        type: "string",
        description: "Ending point address or coordinates"
      },
      mode: {
        type: "string",
        description: "Travel mode (driving, walking, bicycling, transit)",
        enum: ["driving", "walking", "bicycling", "transit"]
      }
    },
    required: ["origin", "destination"]
  }
};

const MAPS_TOOLS = [
  GEOCODE_TOOL,
  REVERSE_GEOCODE_TOOL,
  SEARCH_PLACES_TOOL,
  PLACE_DETAILS_TOOL,
  DISTANCE_MATRIX_TOOL,
  ELEVATION_TOOL,
  DIRECTIONS_TOOL,
] as const;

// API handlers
async function handleGeocode(address: string) {
  const url = new URL("https://maps.googleapis.com/maps/api/geocode/json");
  url.searchParams.append("address", address);
  url.searchParams.append("key", getApiKey());

  const response = await fetch(url.toString());
  const data = await response.json() as GeocodeResponse;

  if (data.status !== "OK") {
    return {
      content: [{
        type: "text",
        text: `Geocoding failed: ${data.error_message || data.status}`
      }],
      isError: true
    };
  }

  return {
    content: [{
      type: "text",
      text: JSON.stringify({
        location: data.results[0].geometry.location,
        formatted_address: data.results[0].formatted_address,
        place_id: data.results[0].place_id
      }, null, 2)
    }],
    isError: false
  };
}

async function handleReverseGeocode(latitude: number, longitude: number) {
  const url = new URL("https://maps.googleapis.com/maps/api/geocode/json");
  url.searchParams.append("latlng", `${latitude},${longitude}`);
  url.searchParams.append("key", getApiKey());

  const response = await fetch(url.toString());
  const data = await response.json() as GeocodeResponse;

  if (data.status !== "OK") {
    return {
      content: [{
        type: "text",
        text: `Reverse geocoding failed: ${data.error_message || data.status}`
      }],
      isError: true
    };
  }

  return {
    content: [{
      type: "text",
      text: JSON.stringify({
        formatted_address: data.results[0].formatted_address,
        place_id: data.results[0].place_id,
        address_components: data.results[0].address_components
      }, null, 2)
    }],
    isError: false
  };
}

async function handlePlaceSearch(
  query: string,
  location?: { latitude: number; longitude: number },
  radius?: number
) {
  const url = new URL("https://maps.googleapis.com/maps/api/place/textsearch/json");
  url.searchParams.append("query", query);
  url.searchParams.append("key", getApiKey());

  if (location) {
    url.searchParams.append("location", `${location.latitude},${location.longitude}`);
  }
  if (radius) {
    url.searchParams.append("radius", radius.toString());
  }

  const response = await fetch(url.toString());
  const data = await response.json() as PlacesSearchResponse;

  if (data.status !== "OK") {
    return {
      content: [{
        type: "text",
        text: `Place search failed: ${data.error_message || data.status}`
      }],
      isError: true
    };
  }

  return {
    content: [{
      type: "text",
      text: JSON.stringify({
        places: data.results.map((place) => ({
          name: place.name,
          formatted_address: place.formatted_address,
          location: place.geometry.location,
          place_id: place.place_id,
          rating: place.rating,
          types: place.types
        }))
      }, null, 2)
    }],
    isError: false
  };
}

async function handlePlaceDetails(place_id: string) {
  const url = new URL("https://maps.googleapis.com/maps/api/place/details/json");
  url.searchParams.append("place_id", place_id);
  url.searchParams.append("key", getApiKey());

  const response = await fetch(url.toString());
  const data = await response.json() as PlaceDetailsResponse;

  if (data.status !== "OK") {
    return {
      content: [{
        type: "text",
        text: `Place details request failed: ${data.error_message || data.status}`
      }],
      isError: true
    };
  }

  return {
    content: [{
      type: "text",
      text: JSON.stringify({
        name: data.result.name,
        formatted_address: data.result.formatted_address,
        location: data.result.geometry.location,
        formatted_phone_number: data.result.formatted_phone_number,
        website: data.result.website,
        rating: data.result.rating,
        reviews: data.result.reviews,
        opening_hours: data.result.opening_hours
      }, null, 2)
    }],
    isError: false
  };
}
async function handleDistanceMatrix(
  origins: string[],
  destinations: string[],
  mode: "driving" | "walking" | "bicycling" | "transit" = "driving"
) {
  const url = new URL("https://maps.googleapis.com/maps/api/distancematrix/json");
  url.searchParams.append("origins", origins.join("|"));
  url.searchParams.append("destinations", destinations.join("|"));
  url.searchParams.append("mode", mode);
  url.searchParams.append("key", getApiKey());

  const response = await fetch(url.toString());
  const data = await response.json() as DistanceMatrixResponse;

  if (data.status !== "OK") {
    return {
      content: [{
        type: "text",
        text: `Distance matrix request failed: ${data.error_message || data.status}`
      }],
      isError: true
    };
  }

  return {
    content: [{
      type: "text",
      text: JSON.stringify({
        origin_addresses: data.origin_addresses,
        destination_addresses: data.destination_addresses,
        results: data.rows.map((row) => ({
          elements: row.elements.map((element) => ({
            status: element.status,
            duration: element.duration,
            distance: element.distance
          }))
        }))
      }, null, 2)
    }],
    isError: false
  };
}

async function handleElevation(locations: Array<{ latitude: number; longitude: number }>) {
  const url = new URL("https://maps.googleapis.com/maps/api/elevation/json");
  const locationString = locations
    .map((loc) => `${loc.latitude},${loc.longitude}`)
    .join("|");
  url.searchParams.append("locations", locationString);
  url.searchParams.append("key", getApiKey());

  const response = await fetch(url.toString());
  const data = await response.json() as ElevationResponse;

  if (data.status !== "OK") {
    return {
      content: [{
        type: "text",
        text: `Elevation request failed: ${data.error_message || data.status}`
      }],
      isError: true
    };
  }

  return {
    content: [{
      type: "text",
      text: JSON.stringify({
        results: data.results.map((result) => ({
          elevation: result.elevation,
          location: result.location,
          resolution: result.resolution
        }))
      }, null, 2)
    }],
    isError: false
  };
}

async function handleDirections(
  origin: string,
  destination: string,
  mode: "driving" | "walking" | "bicycling" | "transit" = "driving"
) {
  const url = new URL("https://maps.googleapis.com/maps/api/directions/json");
  url.searchParams.append("origin", origin);
  url.searchParams.append("destination", destination);
  url.searchParams.append("mode", mode);
  url.searchParams.append("key", getApiKey());

  const response = await fetch(url.toString());
  const data = await response.json() as DirectionsResponse;

  if (data.status !== "OK") {
    return {
      content: [{
        type: "text",
        text: `Directions request failed: ${data.error_message || data.status}`
      }],
      isError: true
    };
  }

  return {
    content: [{
      type: "text",
      text: JSON.stringify({
        routes: data.routes.map((route) => ({
          summary: route.summary,
          distance: route.legs[0].distance,
          duration: route.legs[0].duration,
          steps: route.legs[0].steps.map((step) => ({
            instructions: step.html_instructions,
            distance: step.distance,
            duration: step.duration,
            travel_mode: step.travel_mode
          }))
        }))
      }, null, 2)
    }],
    isError: false
  };
}

// Main server function
const getGoogleMapsMcpServer = () => {
    const server = new Server(
        {
            name: "mcp-server/google-maps",
            version: "0.1.0",
        },
        {
            capabilities: {
                tools: {},
            },
        },
    );

    // Set up request handlers
    server.setRequestHandler(ListToolsRequestSchema, async () => ({
        tools: MAPS_TOOLS,
    }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;

        try {
            switch (name) {
                case "maps_geocode": {
                    const { address } = args as { address: string };
                    return await handleGeocode(address);
                }

                case "maps_reverse_geocode": {
                    const { latitude, longitude } = args as {
                        latitude: number;
                        longitude: number;
                    };
                    return await handleReverseGeocode(latitude, longitude);
                }

                case "maps_search_places": {
                    const { query, location, radius } = args as {
                        query: string;
                        location?: { latitude: number; longitude: number };
                        radius?: number;
                    };
                    return await handlePlaceSearch(query, location, radius);
                }

                case "maps_place_details": {
                    const { place_id } = args as { place_id: string };
                    return await handlePlaceDetails(place_id);
                }

                case "maps_distance_matrix": {
                    const { origins, destinations, mode } = args as {
                        origins: string[];
                        destinations: string[];
                        mode?: "driving" | "walking" | "bicycling" | "transit";
                    };
                    return await handleDistanceMatrix(origins, destinations, mode);
                }

                case "maps_elevation": {
                    const { locations } = args as {
                        locations: Array<{ latitude: number; longitude: number }>;
                    };
                    return await handleElevation(locations);
                }

                case "maps_directions": {
                    const { origin, destination, mode } = args as {
                        origin: string;
                        destination: string;
                        mode?: "driving" | "walking" | "bicycling" | "transit";
                    };
                    return await handleDirections(origin, destination, mode);
                }

                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        } catch (error: any) {
            safeLog('error', `Tool ${name} failed: ${error.message}`);
            return {
                content: [{
                    type: "text",
                    text: `Error: ${error.message}`,
                }],
                isError: true,
            };
        }
    });

    return server;
};

const app = express();


//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
    const apiKey = extractApiKey(req);

    const server = getGoogleMapsMcpServer();
    try {
        const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);
        asyncLocalStorage.run({ apiKey }, async () => {
            await transport.handleRequest(req, res, req.body);
        });
        res.on('close', () => {
            console.log('Request closed');
            transport.close();
            server.close();
        });
    } catch (error) {
        console.error('Error handling MCP request:', error);
        if (!res.headersSent) {
            res.status(500).json({
                jsonrpc: '2.0',
                error: {
                    code: -32603,
                    message: 'Internal server error',
                },
                id: null,
            });
        }
    }
});

app.get('/mcp', async (req: Request, res: Response) => {
    console.log('Received GET MCP request');
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: {
            code: -32000,
            message: "Method not allowed."
        },
        id: null
    }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
    console.log('Received DELETE MCP request');
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: {
            code: -32000,
            message: "Method not allowed."
        },
        id: null
    }));
});

//=============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================

// to support multiple simultaneous connections we have a lookup object from
// sessionId to transport
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
    const transport = new SSEServerTransport(`/messages`, res);

    // Set up cleanup when connection closes
    res.on('close', async () => {
        console.log(`SSE connection closed for transport: ${transport.sessionId}`);
        try {
            transports.delete(transport.sessionId);
        } finally {
        }
    });

    transports.set(transport.sessionId, transport);

    const server = getGoogleMapsMcpServer();
    await server.connect(transport);

    console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);
    if (transport) {
        const apiKey = extractApiKey(req);

        asyncLocalStorage.run({ apiKey }, async () => {
            await transport.handlePostMessage(req, res);
        });
    } else {
        console.error(`Transport not found for session ID: ${sessionId}`);
        res.status(404).send({ error: "Transport not found" });
    }
});

app.listen(5000, () => {
    console.log('server running on port 5000');
});
