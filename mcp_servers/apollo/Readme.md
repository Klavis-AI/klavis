# Apollo

A Python toolkit for working with [Apollo.io](https://apollo.io) — a sales intelligence and engagement platform.
These tools let you manage accounts, calls, contacts, deals, sequences, tasks, enrichment, and more.

---

## 📜 Available Tools

### **Accounts**

| Tool                                     | Description                                                                 |
| ---------------------------------------- | --------------------------------------------------------------------------- |
| **apollo\_create\_account**              | Create a new account in Apollo by adding a company to your team's database. |
| **apollo\_update\_account**              | Update details of an existing account by account ID.                        |
| **apollo\_search\_accounts**             | Search for accounts in your team's Apollo database.                         |
| **apollo\_view\_account**                | Retrieve details of an existing account by account ID.                      |
| **apollo\_update\_account\_stage\_bulk** | Update the account stage for multiple accounts.                             |
| **apollo\_update\_account\_owner\_bulk** | Assign multiple accounts to a different owner.                              |
| **apollo\_list\_account\_stages**        | Retrieve all account stage IDs available in your Apollo team.               |

### **Calls**

| Tool                             | Description                                     |
| -------------------------------- | ----------------------------------------------- |
| **apollo\_create\_call\_record** | Log calls made via outside systems in Apollo.   |
| **apollo\_search\_calls**        | Search for calls made or received by your team. |
| **apollo\_update\_call**         | Update an existing call record by call ID.      |

### **Contacts**

| Tool                                | Description                                            |
| ----------------------------------- | ------------------------------------------------------ |
| **apollo\_create\_contact**         | Create a new contact in your team's Apollo database.   |
| **apollo\_update\_contact**         | Update details of an existing contact by contact ID.   |
| **apollo\_search\_contacts**        | Search for contacts in your team's Apollo database.    |
| **apollo\_update\_contact\_stages** | Update the contact stage for multiple contacts.        |
| **apollo\_update\_contact\_owners** | Assign multiple contacts to a different owner.         |
| **apollo\_list\_contact\_stages**   | Retrieve all contact stage IDs available in your team. |

### **Deals**

| Tool                           | Description                                              |
| ------------------------------ | -------------------------------------------------------- |
| **apollo\_create\_deal**       | Create a new deal for an Apollo account.                 |
| **apollo\_list\_all\_deals**   | Retrieve all deals with optional sorting and pagination. |
| **apollo\_view\_deal**         | Retrieve details for a specific deal.                    |
| **apollo\_update\_deal**       | Update details of an existing deal.                      |
| **apollo\_list\_deal\_stages** | Retrieve all deal stages available in your account.      |

### **Enrichment**

| Tool                                       | Description                                         |
| ------------------------------------------ | --------------------------------------------------- |
| **apollo\_organisation\_enrichment**       | Enrich data for a single organization by domain.    |
| **apollo\_bulk\_organisation\_enrichment** | Enrich data for up to 10 organizations in one call. |

### **Miscellaneous**

| Tool                                   | Description                                         |
| -------------------------------------- | --------------------------------------------------- |
| **apollo\_list\_users**                | Retrieve the list of all teammates in your account. |
| **apollo\_list\_email\_accounts**      | Retrieve linked email inbox information.            |
| **apollo\_list\_all\_custom\_fields**  | Retrieve all custom fields in your account.         |
| **apollo\_get\_all\_lists\_and\_tags** | Retrieve all lists and tags in your account.        |
| **apollo\_view\_api\_usage\_stats**    | Retrieve API usage statistics and rate limits.      |

### **Search**

| Tool                                    | Description                                                |
| --------------------------------------- | ---------------------------------------------------------- |
| **apollo\_organization\_job\_postings** | Retrieve current job postings for a specific organization. |
| **apollo\_news\_articles\_search**      | Search news articles related to companies.                 |

### **Sequences**

| Tool                                              | Description                                        |
| ------------------------------------------------- | -------------------------------------------------- |
| **apollo\_search\_sequences**                     | Search for sequences in your account.              |
| **apollo\_add\_contacts\_to\_sequence**           | Add contacts to an existing sequence.              |
| **apollo\_update\_contact\_status\_in\_sequence** | Update contact status in one or more sequences.    |
| **apollo\_search\_outreach\_emails**              | Search outreach emails sent via sequences.         |
| **apollo\_check\_email\_stats**                   | Retrieve statistics for a specific outreach email. |

### **Tasks**

| Tool                      | Description                                          |
| ------------------------- | ---------------------------------------------------- |
| **apollo\_create\_tasks** | Create tasks for multiple contacts to track actions. |
| **apollo\_search\_tasks** | Search for tasks with filtering and sorting options. |

---

## 📄 Documentation

For complete API request and response details, see the official docs:
[https://docs.apollo.io/reference](https://docs.apollo.io/reference)
