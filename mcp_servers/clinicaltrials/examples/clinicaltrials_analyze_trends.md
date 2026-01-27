# Example: Analyzing Clinical Trial Trends

This example demonstrates how to use the `clinicaltrials_analyze_trends` tool to get aggregated statistical insights across clinical studies.

## Example 1: Multiple Analysis Types

### Tool Call

```json
{
  "query": "COVID-19 vaccine",
  "filter": "AREA[Phase]PHASE3",
  "analysisType": ["countByStatus", "countByCountry", "countBySponsorType"]
}
```

### Tool Response

```
Completed 3 analyses

Analysis: countByStatus
Total Studies: 299
Top Categories:
  • COMPLETED: 148 (49.5%)
  • UNKNOWN: 79 (26.4%)
  • WITHDRAWN: 26 (8.7%)
  • TERMINATED: 17 (5.7%)
  • ACTIVE_NOT_RECRUITING: 12 (4.0%)
  • RECRUITING: 12 (4.0%)
  • NOT_YET_RECRUITING: 3 (1.0%)
  • ENROLLING_BY_INVITATION: 1 (0.3%)
  • SUSPENDED: 1 (0.3%)

---

Analysis: countByCountry
Total Studies: 299
Top Categories:
  • United States: 3575 (1195.7%)
  • United Kingdom: 496 (165.9%)
  • South Africa: 245 (81.9%)
  • Australia: 201 (67.2%)
  • Brazil: 198 (66.2%)
  • Spain: 174 (58.2%)
  • Canada: 156 (52.2%)
  • Russia: 147 (49.2%)
  • Mexico: 134 (44.8%)
  • Germany: 127 (42.5%)
  ...and 79 more

---

Analysis: countBySponsorType
Total Studies: 299
Top Categories:
  • INDUSTRY: 176 (58.9%)
  • OTHER: 94 (31.4%)
  • OTHER_GOV: 20 (6.7%)
  • NIH: 6 (2.0%)
  • NETWORK: 3 (1.0%)
```

---

## Example 2: Single Analysis Type

### Tool Call

```json
{
  "query": "alzheimer",
  "analysisType": "countByPhase"
}
```

### Tool Response

```
Completed 1 analysis

Analysis: countByPhase
Total Studies: 3992
Top Categories:
  • NA: 1470 (36.8%)
  • Unknown: 831 (20.8%)
  • PHASE2: 723 (18.1%)
  • PHASE1: 560 (14.0%)
  • PHASE3: 359 (9.0%)
  • PHASE4: 145 (3.6%)
  • EARLY_PHASE1: 67 (1.7%)
```

---

## Example 3: Error Handling - Query Too Large

### Tool Call

```json
{
  "query": "COVID-19",
  "analysisType": "countByStatus"
}
```

### Tool Response

```
Error: The query returned 11708 studies, which exceeds the limit of 5000 for analysis. Please provide a more specific query.
```

**Solution:** Add filters to narrow the results:

```json
{
  "query": "COVID-19",
  "filter": "AREA[Phase]PHASE3 AND AREA[OverallStatus]COMPLETED",
  "analysisType": "countByStatus"
}
```

---

## Notes

### Analysis Types

The `analysisType` parameter accepts either a single type or an array of types:

1. **`countByStatus`** - Distribution by recruitment status (RECRUITING, COMPLETED, TERMINATED, etc.)
2. **`countByCountry`** - Geographic distribution of study locations
3. **`countBySponsorType`** - Distribution by sponsor type (INDUSTRY, NIH, OTHER, etc.)
4. **`countByPhase`** - Distribution by trial phase (PHASE1, PHASE2, PHASE3, PHASE4, etc.)

### Query and Filter Parameters

- **`query`**: Text search across study fields (required for trend analysis)
- **`filter`**: Use ClinicalTrials.gov filter syntax to narrow results
  - Example: `"AREA[Phase]PHASE3 AND AREA[OverallStatus]RECRUITING"`
  - Helps prevent exceeding the 5000 study limit

### Study Limit

- Maximum: 5,000 studies can be analyzed per request
- If your query returns more studies, you'll receive an error
- Solution: Add more specific filters to narrow the result set

### Percentages

- Country percentages can exceed 100% because studies often have multiple locations
- Other categories (status, phase, sponsor) use mutually exclusive classifications

### Response Format

- Shows total number of studies analyzed
- Lists categories in descending order by count
- Includes both absolute counts and percentages
- Truncates long lists (shows "...and X more" when applicable)

### Best Practices

1. Start with broader queries to understand the dataset
2. Use filters to focus on specific subsets (e.g., only Phase 3 trials)
3. Combine multiple analysis types in one call for comprehensive insights
4. If you get a "too many studies" error, add filters to narrow the scope
