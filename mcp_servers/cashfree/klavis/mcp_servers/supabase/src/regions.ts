import { parseKeyValueList, type UnionToTuple, type ValueOf } from './util.js';

export type AwsRegion = {
  code: string;
  displayName: string;
  location: Location;
};

export type Location = {
  lat: number;
  lng: number;
};

export const EARTH_RADIUS = 6371; // in kilometers
export const TRACE_URL = 'https://www.cloudflare.com/cdn-cgi/trace';

export const COUNTRY_COORDINATES = {
  AF: { lat: 33, lng: 65 },
  AX: { lat: 60.116667, lng: 19.9 },
  AL: { lat: 41, lng: 20 },
  DZ: { lat: 28, lng: 3 },
  AS: { lat: -14.3333, lng: -170 },
  AD: { lat: 42.5, lng: 1.6 },
  AO: { lat: -12.5, lng: 18.5 },
  AI: { lat: 18.25, lng: -63.1667 },
  AQ: { lat: -90, lng: 0 },
  AG: { lat: 17.05, lng: -61.8 },
  AR: { lat: -34, lng: -64 },
  AM: { lat: 40, lng: 45 },
  AW: { lat: 12.5, lng: -69.9667 },
  AU: { lat: -27, lng: 133 },
  AT: { lat: 47.3333, lng: 13.3333 },
  AZ: { lat: 40.5, lng: 47.5 },
  BS: { lat: 24.25, lng: -76 },
  BH: { lat: 26, lng: 50.55 },
  BD: { lat: 24, lng: 90 },
  BB: { lat: 13.1667, lng: -59.5333 },
  BY: { lat: 53, lng: 28 },
  BE: { lat: 50.8333, lng: 4 },
  BZ: { lat: 17.25, lng: -88.75 },
  BJ: { lat: 9.5, lng: 2.25 },
  BM: { lat: 32.3333, lng: -64.75 },
  BT: { lat: 27.5, lng: 90.5 },
  BO: { lat: -17, lng: -65 },
  BQ: { lat: 12.183333, lng: -68.233333 },
  BA: { lat: 44, lng: 18 },
  BW: { lat: -22, lng: 24 },
  BV: { lat: -54.4333, lng: 3.4 },
  BR: { lat: -10, lng: -55 },
  IO: { lat: -6, lng: 71.5 },
  BN: { lat: 4.5, lng: 114.6667 },
  BG: { lat: 43, lng: 25 },
  BF: { lat: 13, lng: -2 },
  MM: { lat: 22, lng: 98 },
  BI: { lat: -3.5, lng: 30 },
  KH: { lat: 13, lng: 105 },
  CM: { lat: 6, lng: 12 },
  CA: { lat: 60, lng: -95 },
  CV: { lat: 16, lng: -24 },
  KY: { lat: 19.5, lng: -80.5 },
  CF: { lat: 7, lng: 21 },
  TD: { lat: 15, lng: 19 },
  CL: { lat: -30, lng: -71 },
  CN: { lat: 35, lng: 105 },
  CX: { lat: -10.5, lng: 105.6667 },
  CC: { lat: -12.5, lng: 96.8333 },
  CO: { lat: 4, lng: -72 },
  KM: { lat: -12.1667, lng: 44.25 },
  CD: { lat: 0, lng: 25 },
  CG: { lat: -1, lng: 15 },
  CK: { lat: -21.2333, lng: -159.7667 },
  CR: { lat: 10, lng: -84 },
  CI: { lat: 8, lng: -5 },
  HR: { lat: 45.1667, lng: 15.5 },
  CU: { lat: 21.5, lng: -80 },
  CW: { lat: 12.166667, lng: -68.966667 },
  CY: { lat: 35, lng: 33 },
  CZ: { lat: 49.75, lng: 15.5 },
  DK: { lat: 56, lng: 10 },
  DJ: { lat: 11.5, lng: 43 },
  DM: { lat: 15.4167, lng: -61.3333 },
  DO: { lat: 19, lng: -70.6667 },
  EC: { lat: -2, lng: -77.5 },
  EG: { lat: 27, lng: 30 },
  SV: { lat: 13.8333, lng: -88.9167 },
  GQ: { lat: 2, lng: 10 },
  ER: { lat: 15, lng: 39 },
  EE: { lat: 59, lng: 26 },
  ET: { lat: 8, lng: 38 },
  FK: { lat: -51.75, lng: -59 },
  FO: { lat: 62, lng: -7 },
  FJ: { lat: -18, lng: 175 },
  FI: { lat: 64, lng: 26 },
  FR: { lat: 46, lng: 2 },
  GF: { lat: 4, lng: -53 },
  PF: { lat: -15, lng: -140 },
  TF: { lat: -43, lng: 67 },
  GA: { lat: -1, lng: 11.75 },
  GM: { lat: 13.4667, lng: -16.5667 },
  GE: { lat: 42, lng: 43.5 },
  DE: { lat: 51, lng: 9 },
  GH: { lat: 8, lng: -2 },
  GI: { lat: 36.1833, lng: -5.3667 },
  GR: { lat: 39, lng: 22 },
  GL: { lat: 72, lng: -40 },
  GD: { lat: 12.1167, lng: -61.6667 },
  GP: { lat: 16.25, lng: -61.5833 },
  GU: { lat: 13.4667, lng: 144.7833 },
  GT: { lat: 15.5, lng: -90.25 },
  GG: { lat: 49.5, lng: -2.56 },
  GW: { lat: 12, lng: -15 },
  GN: { lat: 11, lng: -10 },
  GY: { lat: 5, lng: -59 },
  HT: { lat: 19, lng: -72.4167 },
  HM: { lat: -53.1, lng: 72.5167 },
  VA: { lat: 41.9, lng: 12.45 },
  HN: { lat: 15, lng: -86.5 },
  HK: { lat: 22.25, lng: 114.1667 },
  HU: { lat: 47, lng: 20 },
  IS: { lat: 65, lng: -18 },
  IN: { lat: 20, lng: 77 },
  ID: { lat: -5, lng: 120 },
  IR: { lat: 32, lng: 53 },
  IQ: { lat: 33, lng: 44 },
  IE: { lat: 53, lng: -8 },
  IM: { lat: 54.23, lng: -4.55 },
  IL: { lat: 31.5, lng: 34.75 },
  IT: { lat: 42.8333, lng: 12.8333 },
  JM: { lat: 18.25, lng: -77.5 },
  JP: { lat: 36, lng: 138 },
  JE: { lat: 49.21, lng: -2.13 },
  JO: { lat: 31, lng: 36 },
  KZ: { lat: 48, lng: 68 },
  KE: { lat: 1, lng: 38 },
  KI: { lat: 1.4167, lng: 173 },
  KP: { lat: 40, lng: 127 },
  KR: { lat: 37, lng: 127.5 },
  XK: { lat: 42.583333, lng: 21 },
  KW: { lat: 29.3375, lng: 47.6581 },
  KG: { lat: 41, lng: 75 },
  LA: { lat: 18, lng: 105 },
  LV: { lat: 57, lng: 25 },
  LB: { lat: 33.8333, lng: 35.8333 },
  LS: { lat: -29.5, lng: 28.5 },
  LR: { lat: 6.5, lng: -9.5 },
  LY: { lat: 25, lng: 17 },
  LI: { lat: 47.1667, lng: 9.5333 },
  LT: { lat: 56, lng: 24 },
  LU: { lat: 49.75, lng: 6.1667 },
  MO: { lat: 22.1667, lng: 113.55 },
  MK: { lat: 41.8333, lng: 22 },
  MG: { lat: -20, lng: 47 },
  MW: { lat: -13.5, lng: 34 },
  MY: { lat: 2.5, lng: 112.5 },
  MV: { lat: 3.25, lng: 73 },
  ML: { lat: 17, lng: -4 },
  MT: { lat: 35.8333, lng: 14.5833 },
  MH: { lat: 9, lng: 168 },
  MQ: { lat: 14.6667, lng: -61 },
  MR: { lat: 20, lng: -12 },
  MU: { lat: -20.2833, lng: 57.55 },
  YT: { lat: -12.8333, lng: 45.1667 },
  MX: { lat: 23, lng: -102 },
  FM: { lat: 6.9167, lng: 158.25 },
  MD: { lat: 47, lng: 29 },
  MC: { lat: 43.7333, lng: 7.4 },
  MN: { lat: 46, lng: 105 },
  ME: { lat: 42, lng: 19 },
  MS: { lat: 16.75, lng: -62.2 },
  MA: { lat: 32, lng: -5 },
  MZ: { lat: -18.25, lng: 35 },
  NA: { lat: -22, lng: 17 },
  NR: { lat: -0.5333, lng: 166.9167 },
  NP: { lat: 28, lng: 84 },
  AN: { lat: 12.25, lng: -68.75 },
  NL: { lat: 52.5, lng: 5.75 },
  NC: { lat: -21.5, lng: 165.5 },
  NZ: { lat: -41, lng: 174 },
  NI: { lat: 13, lng: -85 },
  NE: { lat: 16, lng: 8 },
  NG: { lat: 10, lng: 8 },
  NU: { lat: -19.0333, lng: -169.8667 },
  NF: { lat: -29.0333, lng: 167.95 },
  MP: { lat: 15.2, lng: 145.75 },
  NO: { lat: 62, lng: 10 },
  OM: { lat: 21, lng: 57 },
  PK: { lat: 30, lng: 70 },
  PW: { lat: 7.5, lng: 134.5 },
  PS: { lat: 32, lng: 35.25 },
  PA: { lat: 9, lng: -80 },
  PG: { lat: -6, lng: 147 },
  PY: { lat: -23, lng: -58 },
  PE: { lat: -10, lng: -76 },
  PH: { lat: 13, lng: 122 },
  PN: { lat: -24.7, lng: -127.4 },
  PL: { lat: 52, lng: 20 },
  PT: { lat: 39.5, lng: -8 },
  PR: { lat: 18.25, lng: -66.5 },
  QA: { lat: 25.5, lng: 51.25 },
  RE: { lat: -21.1, lng: 55.6 },
  RO: { lat: 46, lng: 25 },
  RU: { lat: 60, lng: 100 },
  RW: { lat: -2, lng: 30 },
  BL: { lat: 17.897728, lng: -62.834244 },
  SH: { lat: -15.9333, lng: -5.7 },
  KN: { lat: 17.3333, lng: -62.75 },
  LC: { lat: 13.8833, lng: -61.1333 },
  MF: { lat: 18.075278, lng: -63.06 },
  PM: { lat: 46.8333, lng: -56.3333 },
  VC: { lat: 13.25, lng: -61.2 },
  WS: { lat: -13.5833, lng: -172.3333 },
  SM: { lat: 43.7667, lng: 12.4167 },
  ST: { lat: 1, lng: 7 },
  SA: { lat: 25, lng: 45 },
  SN: { lat: 14, lng: -14 },
  RS: { lat: 44, lng: 21 },
  SC: { lat: -4.5833, lng: 55.6667 },
  SL: { lat: 8.5, lng: -11.5 },
  SG: { lat: 1.3667, lng: 103.8 },
  SX: { lat: 18.033333, lng: -63.05 },
  SK: { lat: 48.6667, lng: 19.5 },
  SI: { lat: 46, lng: 15 },
  SB: { lat: -8, lng: 159 },
  SO: { lat: 10, lng: 49 },
  ZA: { lat: -29, lng: 24 },
  GS: { lat: -54.5, lng: -37 },
  SS: { lat: 8, lng: 30 },
  ES: { lat: 40, lng: -4 },
  LK: { lat: 7, lng: 81 },
  SD: { lat: 15, lng: 30 },
  SR: { lat: 4, lng: -56 },
  SJ: { lat: 78, lng: 20 },
  SZ: { lat: -26.5, lng: 31.5 },
  SE: { lat: 62, lng: 15 },
  CH: { lat: 47, lng: 8 },
  SY: { lat: 35, lng: 38 },
  TW: { lat: 23.5, lng: 121 },
  TJ: { lat: 39, lng: 71 },
  TZ: { lat: -6, lng: 35 },
  TH: { lat: 15, lng: 100 },
  TL: { lat: -8.55, lng: 125.5167 },
  TG: { lat: 8, lng: 1.1667 },
  TK: { lat: -9, lng: -172 },
  TO: { lat: -20, lng: -175 },
  TT: { lat: 11, lng: -61 },
  TN: { lat: 34, lng: 9 },
  TR: { lat: 39, lng: 35 },
  TM: { lat: 40, lng: 60 },
  TC: { lat: 21.75, lng: -71.5833 },
  TV: { lat: -8, lng: 178 },
  UG: { lat: 1, lng: 32 },
  UA: { lat: 49, lng: 32 },
  AE: { lat: 24, lng: 54 },
  GB: { lat: 54, lng: -2 },
  UM: { lat: 19.2833, lng: 166.6 },
  US: { lat: 38, lng: -97 },
  UY: { lat: -33, lng: -56 },
  UZ: { lat: 41, lng: 64 },
  VU: { lat: -16, lng: 167 },
  VE: { lat: 8, lng: -66 },
  VN: { lat: 16, lng: 106 },
  VG: { lat: 18.5, lng: -64.5 },
  VI: { lat: 18.3333, lng: -64.8333 },
  WF: { lat: -13.3, lng: -176.2 },
  EH: { lat: 24.5, lng: -13 },
  YE: { lat: 15, lng: 48 },
  ZM: { lat: -15, lng: 30 },
  ZW: { lat: -20, lng: 30 },
} as const satisfies Record<string, Location>;

export const AWS_REGIONS = {
  WEST_US: {
    code: 'us-west-1',
    displayName: 'West US (North California)',
    location: { lat: 37.774929, lng: -122.419418 },
  },
  EAST_US: {
    code: 'us-east-1',
    displayName: 'East US (North Virginia)',
    location: { lat: 37.926868, lng: -78.024902 },
  },
  EAST_US_2: {
    code: 'us-east-2',
    displayName: 'East US (Ohio)',
    location: { lat: 39.9612, lng: -82.9988 },
  },
  CENTRAL_CANADA: {
    code: 'ca-central-1',
    displayName: 'Canada (Central)',
    location: { lat: 56.130367, lng: -106.346771 },
  },
  WEST_EU: {
    code: 'eu-west-1',
    displayName: 'West EU (Ireland)',
    location: { lat: 53.3498, lng: -6.2603 },
  },
  WEST_EU_2: {
    code: 'eu-west-2',
    displayName: 'West Europe (London)',
    location: { lat: 51.507351, lng: -0.127758 },
  },
  WEST_EU_3: {
    code: 'eu-west-3',
    displayName: 'West EU (Paris)',
    location: { lat: 2.352222, lng: 48.856613 },
  },
  CENTRAL_EU: {
    code: 'eu-central-1',
    displayName: 'Central EU (Frankfurt)',
    location: { lat: 50.110924, lng: 8.682127 },
  },
  CENTRAL_EU_2: {
    code: 'eu-central-2',
    displayName: 'Central Europe (Zurich)',
    location: { lat: 47.3744489, lng: 8.5410422 },
  },
  NORTH_EU: {
    code: 'eu-north-1',
    displayName: 'North EU (Stockholm)',
    location: { lat: 59.3251172, lng: 18.0710935 },
  },
  SOUTH_ASIA: {
    code: 'ap-south-1',
    displayName: 'South Asia (Mumbai)',
    location: { lat: 18.9733536, lng: 72.8281049 },
  },
  SOUTHEAST_ASIA: {
    code: 'ap-southeast-1',
    displayName: 'Southeast Asia (Singapore)',
    location: { lat: 1.357107, lng: 103.8194992 },
  },
  NORTHEAST_ASIA: {
    code: 'ap-northeast-1',
    displayName: 'Northeast Asia (Tokyo)',
    location: { lat: 35.6895, lng: 139.6917 },
  },
  NORTHEAST_ASIA_2: {
    code: 'ap-northeast-2',
    displayName: 'Northeast Asia (Seoul)',
    location: { lat: 37.5665, lng: 126.978 },
  },
  OCEANIA: {
    code: 'ap-southeast-2',
    displayName: 'Oceania (Sydney)',
    location: { lat: -33.8688, lng: 151.2093 },
  },
  SOUTH_AMERICA: {
    code: 'sa-east-1',
    displayName: 'South America (São Paulo)',
    location: { lat: -1.2043218, lng: -47.1583944 },
  },
} as const satisfies Record<string, AwsRegion>;

export type RegionCodes = ValueOf<typeof AWS_REGIONS>['code'];

export const AWS_REGION_CODES = Object.values(AWS_REGIONS).map(
  (region) => region.code
) as UnionToTuple<RegionCodes>;

/**
 * Calculates the closest AWS region to a given location.
 */
export function getClosestAwsRegion(location: Location) {
  const distances = Object.entries(AWS_REGIONS).map<
    [region: string, distance: number]
  >(([name, region]) => {
    return [name, getDistance(location, region.location)] as const;
  });

  const closestRegion = distances.reduce<
    [region: string, distance: number] | undefined
  >(
    (min, current) =>
      min === undefined ? current : current[1] < min[1] ? current : min,
    undefined
  );

  if (!closestRegion) {
    throw new Error('no closest region found');
  }

  const [regionName] = closestRegion;

  return AWS_REGIONS[regionName as keyof typeof AWS_REGIONS];
}

/**
 * Fetches the user's country code based on their IP address.
 */
export async function getCountryCode() {
  const response = await fetch(TRACE_URL);
  const data = await response.text();
  const info = parseKeyValueList(data);
  const countryCode = info['loc'];

  if (!countryCode) {
    throw new Error('location not found');
  }

  return countryCode;
}

/**
 * Gets the approximate coordinates of a country based on its country code.
 */
export function getCountryCoordinates(countryCode: string) {
  const location: Location =
    COUNTRY_COORDINATES[countryCode as keyof typeof COUNTRY_COORDINATES];

  if (!location) {
    throw new Error(`unknown location code: ${countryCode}`);
  }

  return location;
}

/**
 * Calculates the distance between two points on Earth using the Haversine formula.
 *
 * @returns Distance between the points in kilometers
 */
export function getDistance(a: Location, b: Location): number {
  const lat = degreesToRadians(b.lat - a.lat);
  const lng = degreesToRadians(b.lng - a.lng);
  const a1 =
    Math.sin(lat / 2) * Math.sin(lat / 2) +
    Math.cos(degreesToRadians(a.lat)) *
      Math.cos(degreesToRadians(b.lat)) *
      Math.sin(lng / 2) *
      Math.sin(lng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a1), Math.sqrt(1 - a1));
  return EARTH_RADIUS * c;
}

/**
 * Converts degrees to radians
 *
 * @returns The angle in radians
 */
export function degreesToRadians(deg: number): number {
  return deg * (Math.PI / 180);
}
