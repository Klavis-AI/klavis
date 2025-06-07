# Constants for Close CRM API

# API Configuration
CLOSE_API_VERSION = "v1"
CLOSE_BASE_URL = "https://api.close.com/api"
CLOSE_MAX_CONCURRENT_REQUESTS = 10
CLOSE_MAX_TIMEOUT_SECONDS = 120

# Common field limits
CLOSE_MAX_LIMIT = 200

# Lead Status Types (common ones)
class LeadStatus:
    LEAD = "lead"
    QUALIFIED = "qualified"
    CUSTOMER = "customer"
    CANCELLED = "cancelled"
    POTENTIAL = "potential"

# Task Types
class TaskType:
    LEAD = "lead"
    INCOMING_EMAIL = "incoming_email"
    EMAIL_FOLLOWUP = "email_followup"
    MISSED_CALL = "missed_call"
    VOICEMAIL = "voicemail"
    OPPORTUNITY_DUE = "opportunity_due"
    INCOMING_SMS = "incoming_sms"

# Sort Orders
class SortOrder:
    ASC = "asc"
    DESC = "desc"

# Object Types for Activities
class ActivityType:
    CALL = "call"
    EMAIL = "email"
    EMAIL_THREAD = "emailthread"
    NOTE = "note"
    SMS = "sms"
    MEETING = "meeting"
    CREATED = "created"

# Opportunity Status Types (common ones)
class OpportunityStatus:
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"

# Contact Field Types
class ContactFieldType:
    PHONE = "phone"
    EMAIL = "email"
    URL = "url" 