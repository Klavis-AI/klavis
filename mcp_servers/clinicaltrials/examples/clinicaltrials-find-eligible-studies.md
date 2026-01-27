# Example: Finding Eligible Clinical Trials

This example demonstrates how to use the `clinicaltrials_find_eligible_studies` tool to find clinical trials that match a patient's specific demographic and medical profile.

## Example 1: Basic Search for Eligible Studies

### Tool Call

```json
{
  "age": 35,
  "sex": "Female",
  "conditions": ["Migraine"],
  "location": {
    "country": "Canada",
    "state": "Ontario"
  },
  "recruitingOnly": true,
  "maxResults": 2
}
```

### Tool Response

```
# Eligible Clinical Trials

Found **8** matching studies for:
- **Conditions:** Migraine
- **Location:** Ontario
- **Patient:** 35 years old, Female

Showing top 2 results:

---
## 1. A Study to Evaluate the Effectiveness and Safety of Dysport® for the Prevention of Chronic Migraine in Adults
**NCT ID:** NCT06047444
**Match Score:** 75/100
**Why You Match:**
- Age 35 within eligible range (18-any)
- Study accepts all sexes
- Eligibility status matches study requirements
**Eligibility Summary:**
- Age Range: 18 Years - N/A
- Sex: ALL
- Healthy Volunteers: No
**Study Summary:**
The purpose of this study is to understand the safety and effectiveness of the study drug, Dysport® when compared with placebo in preventing chronic migraine.

A migraine is a headache with severe throbbing pain or a pulsating sensation, usually on one side of the head, and is often accompanied by feeling or being sick and a sensitivity to bright lights and sound.

Chronic migraine is defined as having at least 15 days of headache a month with at least 8 of those days being migraine headache days.

Migraines are caused by a series of events which cause the brain to get stimulated/activated, which results in the release of chemicals that cause pain. Dysport® is a formulation of Botulinum toxin type A (BoNT-A), a medication that stops the release of these chemical messengers.

The study will consist of 3 periods:

1. A 'screening period' of 6 to 12 weeks to assess whether the participant can take part to the study and requires 1 visit.
2. A first Treatment Phase of 24 weeks. On Day 1 and at Week 12 of the first Treatment Phase, participants will receive injections into various muscles across the head, neck, face and shoulders.

   The injections will contain either a dose "A" or dose "B" of Dysport® or a placebo (an inactive substance or treatment that looks the same as, and is given in the same way as, an active drug or intervention/treatment being studied). Participants will make 4 visits to the clinic in person and have 4 remote (online) visits.
3. A second Treatment Phase of 24 weeks (extension phase). At Week 24 and at Week 36, all participants will get Dysport® (dose "A" or dose "B").

There will be 3 in person visits and 4 remote visits.

Participants will need to complete an e-diary and questionnaires throughout the study. Participants will undergo blood samplings, urine collections, physical examinations, and clinical evaluations.

They may continue some other medications, but the details need to be recorded. The total study duration for a participant will be up to 60 weeks (approx. 14 months).

**Study Details:**
- Phase: PHASE3
- Status: RECRUITING
- Sponsor: Ipsen
- Target Enrollment: 720
**Nearby Locations (128):**
- Central Research Associates - Birmingham, Alabama
- CCT Research - Phoenix, Arizona
- HonorHealth Neurology - Scottsdale, Arizona
- ...and 125 more locations
**Contact:** Ipsen Clinical Study Enquiries | See e mail | clinical.trials@ipsen.com
---
## 2. A Study to Evaluate the Effectiveness and Safety of Dysport® for the Prevention of Episodic Migraine in Adults
**NCT ID:** NCT06047457
**Match Score:** 75/100
**Why You Match:**
- Age 35 within eligible range (18-any)
- Study accepts all sexes
- Eligibility status matches study requirements
**Eligibility Summary:**
- Age Range: 18 Years - N/A
- Sex: ALL
- Healthy Volunteers: No
**Study Summary:**
The purpose of this study is to understand the safety and effectiveness of the study drug, Dysport® when compared with placebo in preventing episodic migraine.

A migraine is a headache with severe throbbing pain or a pulsating sensation, usually on one side of the head, and is often accompanied by feeling or being sick and a sensitivity to bright lights and sound.

Episodic Migraine is defined as having less than 15 days of headache a month with at least 6 days with migraine headaches.

Migraines are caused by a series of events which cause the brain to get stimulated / activated, which results in the release of chemicals that cause pain.

Dysport® is a formulation of Botulinum toxin type A (BoNT-A), a medication that stops the release of these chemical messengers.

The study will consist of 3 periods:

1. A 'screening period' of 6 to 12 weeks to assess whether the participant can take part to the study and requires 1 visit.
2. A first Treatment Phase of 24 weeks. On Day 1 and at Week 12 of the first Treatment Phase, participants will receive injections into various muscles across the head, neck, face and shoulders.

   The injections will contain either a dose "A" or a dose ''B'' of Dysport® or a placebo (an inactive substance or treatment that looks the same as, and is given in the same way as, an active drug or intervention/treatment being studied).

   Participants will make 4 visits to the clinic in person and have 4 remote (online) visits.
3. A second Treatment Phase of 24 weeks (extension phase). At Week 24 and at Week 36, all participants will get Dysport® (dose "A" or dose "B").

There will be 3 in person visits and 4 remote visits.

Participants will need to complete an e-diary and questionnaires throughout the study.

Participants will undergo blood samplings, urine collections, physical examinations, and clinical evaluations. They may continue some other medications, but the details need to be recorded.

The total study duration for a participant will be up to 60 weeks (approx. 14 months).

**Study Details:**
- Phase: PHASE3
- Status: RECRUITING
- Sponsor: Ipsen
- Target Enrollment: 714
**Nearby Locations (110):**
- Central Research Associates - Birmingham, Alabama
- CCT Research - Phoenix, Arizona
- HonorHealth Neurology - Scottsdale, Arizona
- ...and 107 more locations
**Contact:** Ipsen Clinical Study Enquiries | See email | clinical.trials@ipsen.com
---
```

---

## Notes

### Input Parameters

- `age`: Patient's age in years.
- `sex`: Patient's biological sex (`Male`, `Female`, `All`).
- `conditions`: An array of medical conditions.
- `location`: An object with `country`, and optional `state` and `city`.
- `healthyVolunteer`: (Optional) Boolean, `true` if the patient is a healthy volunteer. Defaults to `false`.
- `recruitingOnly`: (Optional) Boolean, `true` to only include recruiting studies. Defaults to `true`.
- `maxResults`: (Optional) The maximum number of studies to return. Defaults to 10.

### Response Format

- Provides a summary of the search and the number of matching studies found.
- Returns a ranked list of eligible studies, with details about why each study is a potential match.
- Includes key study details like NCT ID, phase, status, and sponsor.
- Lists nearby locations and contact information for each study.
