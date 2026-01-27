# Example: Retrieving Clinical Studies

This example demonstrates how to use the `clinicaltrials_get_study` tool to fetch detailed information for clinical trials using their NCT IDs.

## Example 1: Single Study with Full Data

### Tool Call

```json
{
  "nctIds": "NCT03372603",
  "summaryOnly": false
}
```

### Tool Response

Returns the complete study data including:

- Protocol sections (identification, status, description, conditions, interventions, design, eligibility, locations, outcomes)
- Results section (if available) with participant flow, baseline characteristics, outcome measures, adverse events
- Document section with protocol and analysis plan links
- Derived sections with condition/intervention classifications

Response size: ~200KB of detailed clinical trial data (truncated for brevity).

---

## Example 2: Single Study with Summary Only

### Tool Call

```json
{
  "nctIds": "NCT03372603",
  "summaryOnly": true
}
```

### Tool Response

```json
{
  "studies": [
    {
      "nctId": "NCT03372603",
      "title": "A Placebo-controlled, Double-blind (Sponsor Open), Randomized, Crossover Study to Assess the Efficacy, Safety, and Tolerability of GSK2798745 in Participants With Chronic Cough",
      "briefSummary": "GSK2798745 is a potent and selective transient receptor potential vanilloid 4 (TRPV4) channel blocker being investigated for the treatment of chronic cough. This is a multi-center, randomized, placebo-controlled, double-blind, two-period crossover study with a purpose to evaluate efficacy and safety of GSK2798745. Each subject will have 2 treatment periods, and will be randomized to one of the following treatments in each period: A) Placebo matching to GSK2798745 once daily for 7 days. B) 4.8 milligrams (mg) GSK2798745 on Day 1, followed by 2.4 mg GSK2798745 once daily for 6 days. There will be a washout period of 14 to 21 days between the treatment periods. A maximum of 48 subjects will be enrolled in the study and the total duration of participation in the study will be maximum of 10 and a half weeks including follow-up visit.",
      "overallStatus": "TERMINATED",
      "conditions": ["Cough"],
      "interventions": [
        {
          "name": "GSK2798745",
          "type": "DRUG"
        },
        {
          "name": "Placebo",
          "type": "DRUG"
        }
      ],
      "leadSponsor": "GlaxoSmithKline"
    }
  ]
}
```

---

## Example 3: Multiple Studies

### Tool Call

```json
{
  "nctIds": ["NCT03372603", "NCT04280783", "NCT05477043"],
  "summaryOnly": true
}
```

### Tool Response

```json
{
  "studies": [
    {
      "nctId": "NCT03372603",
      "title": "A Placebo-controlled, Double-blind (Sponsor Open), Randomized, Crossover Study to Assess the Efficacy, Safety, and Tolerability of GSK2798745 in Participants With Chronic Cough",
      "briefSummary": "GSK2798745 is a potent and selective transient receptor potential vanilloid 4 (TRPV4) channel blocker being investigated for the treatment of chronic cough...",
      "overallStatus": "TERMINATED",
      "conditions": ["Cough"],
      "interventions": [
        {
          "name": "GSK2798745",
          "type": "DRUG"
        },
        {
          "name": "Placebo",
          "type": "DRUG"
        }
      ],
      "leadSponsor": "GlaxoSmithKline"
    },
    {
      "nctId": "NCT05477043",
      "title": "Ultrasound Evaluation of Ureteral Patency After Uterosacral Ligaments Suspension",
      "briefSummary": "Uterosacral ligament suspension (USLS) is a commonly performed procedure used to correct prolapse of the vaginal apex...",
      "overallStatus": "UNKNOWN",
      "conditions": [
        "Uterovaginal Prolapse",
        "Ureteral Injury",
        "Surgery--Complications"
      ],
      "interventions": [
        {
          "name": "Transabdominal ultrasound and cistoscopy",
          "type": "DIAGNOSTIC_TEST"
        }
      ],
      "leadSponsor": "University of Milano Bicocca"
    },
    {
      "nctId": "NCT04280783",
      "title": "Feasibility and Acceptability of a Web-based Physical Activity for the Heart (PATH) Intervention Designed to Reduce the Risk of Heart Disease Among Inactive African Americans",
      "briefSummary": "Barriers to physical activity (PA) among African Americans (AAs) have been extensively studied...",
      "overallStatus": "COMPLETED",
      "conditions": [
        "Cardiovascular Risk Factor",
        "Prediabetes",
        "Overweight and Obesity",
        "Sedentary Behavior"
      ],
      "interventions": [
        {
          "name": "The Physical Activity for The Heart (PATH) intervention",
          "type": "BEHAVIORAL"
        },
        {
          "name": "Be Active Your Way Booklet",
          "type": "BEHAVIORAL"
        }
      ],
      "leadSponsor": "University of Pittsburgh"
    }
  ]
}
```

---

## Example 4: Invalid NCT ID

### Tool Call

```json
{
  "nctIds": "NCT99999999",
  "summaryOnly": true
}
```

### Tool Response

```
Error: Failed to fetch any studies. Errors: NCT99999999: Fetch failed for https://clinicaltrials.gov/api/v2/studies/NCT99999999. Status: 404
```

## Notes

- The `summaryOnly` parameter defaults to `false` (returns full data)
- You can request up to 5 studies at once by providing an array of NCT IDs
- NCT IDs must match the format: NCT followed by 8 digits (case-insensitive)
- Invalid or non-existent NCT IDs will return error messages
- Full data responses can be very large (100-200KB per study)
