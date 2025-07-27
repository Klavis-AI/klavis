## Cal.com API (v2) MCP Server – Notes

**Docs:**  
https://cal.com/docs/api-reference/v2/introduction

---

### Testing videos
- Schedule test: https://youtu.be/98O_6qsRUyE  
- Verified resources test: https://youtu.be/wpM6XUm3ygQ  
- Webhooks test: https://youtu.be/CXUkTUbwa7Y

---

### Important

- Didn’t test Stripe — had local Stripe issues.
- `cal_request_phone_verification_code` and `cal_verify_phone_code` not tested.  
  They also don’t work on Cal.com site itself, probably due to Indian numbers.
- These tools are added in `tools/` but commented out in `server.py`.
