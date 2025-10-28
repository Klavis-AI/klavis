import { describe, expect, it } from 'vitest';
import {
  EARTH_RADIUS,
  getClosestAwsRegion,
  getCountryCode,
  getCountryCoordinates,
  getDistance,
  TRACE_URL,
} from './regions.js';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const COUNTRY_CODE = 'US';

describe('getDistance', () => {
  it('should return 0 for the same coordinates', () => {
    const point = { lat: 50, lng: 50 };
    expect(getDistance(point, point)).toBe(0);
  });

  it('should calculate distance between two points correctly', () => {
    // New York City coordinates
    const nyc = { lat: 40.7128, lng: -74.006 };
    // Los Angeles coordinates
    const la = { lat: 34.0522, lng: -118.2437 };

    // Approximate distance between NYC and LA is ~3940 km
    const distance = getDistance(nyc, la);
    expect(distance).toBeCloseTo(3940, -2); // Allow ~100km margin
  });

  it('should handle coordinates at opposite sides of the Earth', () => {
    const point1 = { lat: 0, lng: 0 };
    const point2 = { lat: 0, lng: 180 };

    // Half circumference of Earth
    const expectedDistance = Math.PI * EARTH_RADIUS;
    expect(getDistance(point1, point2)).toBeCloseTo(expectedDistance, 0);
  });

  it('should handle negative coordinates', () => {
    const sydney = { lat: -33.8688, lng: 151.2093 };
    const buenosAires = { lat: -34.6037, lng: -58.3816 };

    // Approximate distance between Sydney and Buenos Aires is ~11800 km
    const distance = getDistance(sydney, buenosAires);
    expect(distance).toBeCloseTo(11800, -2); // Allow ~100km margin
  });

  it('should handle coordinates at the equator', () => {
    const point1 = { lat: 0, lng: 0 };
    const point2 = { lat: 0, lng: 180 };

    const expectedDistance = Math.PI * EARTH_RADIUS; // Half circumference
    expect(getDistance(point1, point2)).toBeCloseTo(expectedDistance, 0);
  });

  it('should be symmetrical (a to b equals b to a)', () => {
    const london = { lat: 51.5074, lng: -0.1278 };
    const tokyo = { lat: 35.6762, lng: 139.6503 };

    const distanceAtoB = getDistance(london, tokyo);
    const distanceBtoA = getDistance(tokyo, london);

    expect(distanceAtoB).toEqual(distanceBtoA);
  });
});

describe('getClosestRegion', () => {
  it('should find the closest AWS region to a specific location', () => {
    const tokyo = { lat: 35.6762, lng: 139.6503 };
    const result = getClosestAwsRegion(tokyo);
    expect(result.code).toBe('ap-northeast-1'); // Tokyo region
  });

  it('should find the correct AWS region for European location', () => {
    const london = { lat: 51.5074, lng: -0.1278 };
    const result = getClosestAwsRegion(london);
    expect(result.code).toBe('eu-west-2'); // London region
  });

  it('should find the correct AWS region for US West Coast location', () => {
    const sanFrancisco = { lat: 37.7749, lng: -122.4194 };
    const result = getClosestAwsRegion(sanFrancisco);
    expect(result.code).toBe('us-west-1'); // North California region
  });

  it('should find the correct AWS region for Sydney location', () => {
    const sydney = { lat: -33.8688, lng: 151.2093 };
    const result = getClosestAwsRegion(sydney);
    expect(result.code).toBe('ap-southeast-2'); // Sydney region
  });

  it('should find the correct AWS region for a location in South America', () => {
    const saoPaulo = { lat: -23.5505, lng: -46.6333 };
    const result = getClosestAwsRegion(saoPaulo);
    expect(result.code).toBe('sa-east-1'); // São Paulo region
  });
});

describe('getCountryCode', () => {
  const handlers = [
    http.get(TRACE_URL, () => {
      return HttpResponse.text(
        `fl=123abc\nvisit_scheme=https\nloc=${COUNTRY_CODE}\ntls=TLSv1.3\nhttp=http/2`
      );
    }),
  ];

  const server = setupServer(...handlers);
  server.listen({ onUnhandledRequest: 'error' });

  it('should return the correct country code for a given location', async () => {
    const code = await getCountryCode();
    expect(code).toEqual(COUNTRY_CODE);
  });
});

describe('getCountryCoordinates', () => {
  it('should throw an error for an invalid country code', async () => {
    const invalidCountryCode = 'INVALID_CODE';
    expect(() => getCountryCoordinates(invalidCountryCode)).toThrowError(
      /unknown location code/
    );
  });

  it('should return coordinates for a valid country code', () => {
    const result = getCountryCoordinates('US');
    expect(result).toEqual({ lat: 38, lng: -97 });
  });
});
