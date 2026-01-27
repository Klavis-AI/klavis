# Example: Searching for Clinical Studies

This example demonstrates how to use the `clinicaltrials_search_studies` tool to find clinical trials based on specific criteria.

## Example 1: Basic Search

### Tool Call

```json
{
  "query": "cancer immunotherapy",
  "pageSize": 5
}
```

### Tool Response

```
Found 5 studies of 7659 total (more pages available)

• NCT06843551: The Miami "EMPIRE" Trial - Eradication of Metastatic Pancreatic Cancer With Immuno-Radiation
  Status: RECRUITING
• NCT07032129: Sequential CAR-T Cells Targeting BCMA/GPRC5D in Patients With Relapsed/ Refractory Multiple Myeloma
  Status: RECRUITING
• NCT00569231: Study With Candida Antigen for Treatment of Warts
  Status: COMPLETED
• NCT05255302: De-escalation Immunotherapy mAintenance Duration Trial for Stage IV Lung Cancer Patients With Disease Control After Chemo-immunotherapy Induction
  Status: RECRUITING
• NCT00285428: Study of hA20 (Humanized Anti-CD20) in Patients With CD20+ Non-Hodgkin's Lymphoma
  Status: COMPLETED

Next page token: ZVNj7o2Elu8o3lpiC82t5qr-mpOQJJxmYPap
```

---

## Example 2: Advanced Search with Filters

### Tool Call

```json
{
  "query": "diabetes",
  "filter": "AREA[OverallStatus]RECRUITING AND AREA[Phase]PHASE3",
  "pageSize": 10,
  "sort": "EnrollmentCount:desc"
}
```

### Tool Response

```
Found 10 studies of 186 total (more pages available)

• NCT06292013: A Study to Investigate the Effect of Lepodisiran on the Reduction of Major Adverse Cardiovascular Events in Adults With Elevated Lipoprotein(a) - ACCLAIM-Lp(a)
  Status: RECRUITING
• NCT05754957: A Study of Milvexian in Participants After a Recent Acute Coronary Syndrome
  Status: RECRUITING
• NCT07037433: Evaluating the Impact of Maridebart Cafraglutide on Cardiovascular Outcomes in Participants With Atherosclerotic Cardiovascular Disease and Overweight or Obesity
  Status: RECRUITING
• NCT07064473: A Study to Test Vicadrostat (BI 690517) Taken Together With Empagliflozin in People With Type 2 Diabetes, High Blood Pressure, and Cardiovascular Disease
  Status: RECRUITING
• NCT06531824: EASi-KIDNEY™ (The Studies of Heart & Kidney Protection With BI 690517 in Combination With Empagliflozin)
  Status: RECRUITING
...and 5 more

Next page token: ZVNj7o2Elu8o3lpiC82t5qr-mpOQJJxpZfGl5agQnT6Xuf4-KHc
```

---

## Example 3: Pagination

### Tool Call (using token from previous search)

```json
{
  "query": "diabetes",
  "filter": "AREA[OverallStatus]RECRUITING AND AREA[Phase]PHASE3",
  "pageSize": 5,
  "pageToken": "ZVNj7o2Elu8o3lpiC82t5qr-mpOQJJxpZfGl5agQnT6Xuf4-KHc",
  "sort": "EnrollmentCount:desc"
}
```

### Tool Response

```
Found 5 studies (more pages available)

• NCT05636176: A Research Study to Look at How Ziltivekimab Works Compared to Placebo in People With Heart Failure and Inflammation
  Status: RECRUITING
• NCT05182970: Metformin and Prevention of Cardiovascular Events in Patients With Acute Myocardial Infarction and Prediabetes (MIMET)
  Status: RECRUITING
• NCT07037459: Maridebart Cafraglutide in Heart Failure With Preserved or Mildly Reduced Ejection Fraction and Obesity
  Status: RECRUITING
• NCT07104500: VK2735 for Weight Management Phase 3
  Status: RECRUITING
• NCT07044297: A Clinical Study of MK-8527 to Prevent Human Immunodeficiency Virus Type 1 (HIV-1) (MK-8527-011)
  Status: RECRUITING

Next page token: ZVNj7o2Elu8o3lpiC82t5qr-mpOQJJxrZvil5agQlTmTv_w7IQ
```

---

## Notes

### Query Parameter

- Simple text search across study fields (conditions, interventions, sponsors, etc.)
- Case-insensitive
- Example: `"cancer immunotherapy"`, `"alzheimer"`, `"COVID-19 vaccine"`

### Filter Parameter

- Advanced filtering using ClinicalTrials.gov filter syntax
- Use `AREA[FieldName]Value` format
- Combine filters with `AND` or `OR`
- Common filters:
  - `AREA[OverallStatus]RECRUITING` - Only recruiting studies
  - `AREA[Phase]PHASE3` - Only Phase 3 trials
  - `AREA[StudyType]INTERVENTIONAL` - Only interventional studies
  - `AREA[LocationCountry]United States` - Studies in specific country

### Sort Parameter

- Format: `FieldName:asc` or `FieldName:desc`
- Common sort fields:
  - `EnrollmentCount` - Sort by number of participants
  - `LastUpdateDate` - Sort by most recently updated
  - `StartDate` - Sort by study start date

### Pagination

- Default `pageSize`: 10 (maximum: 200)
- Use `pageToken` from previous response to get next page
- Tokens are temporary and specific to the search query

### Response Format

- Displays NCT ID, title, and recruitment status
- Shows total matching studies and if more pages are available
- Provides pagination token for retrieving additional results
