"""
Salesforce API Response Normalization Module.
Provides utilities to transform raw Salesforce API responses into clean, consistent data structures.
"""

from typing import Any, Dict, List, Callable, Optional


def get_path(data: dict, path: str) -> Any:
    """Safe dot-notation access. Returns None if path fails."""
    if not data:
        return None
    current = data
    for key in path.split('.'):
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


def normalize(source: dict, mapping: dict[str, Any]) -> dict:
    """
    Creates a new clean dictionary based strictly on the mapping rules.
    Excludes fields with None/null values from the output.
    Args:
        source: Raw Salesforce JSON.
        mapping: Dict of { "TargetFieldName": "Source.Path" OR Lambda_Function }
    """
    if not source:
        return {}
    clean_data = {}
    for target_key, rule in mapping.items():
        value = None
        if isinstance(rule, str):
            value = get_path(source, rule)
        elif callable(rule):
            try:
                value = rule(source)
            except Exception:
                value = None
        if value is not None:
            clean_data[target_key] = value
    return clean_data


# =============================================================================
# Mapping Rules for Salesforce Objects
# =============================================================================

# Address normalization helper
ADDRESS_RULES = {
    "street": "Street",
    "city": "City",
    "state": "State",
    "postalCode": "PostalCode",
    "country": "Country",
}


def normalize_billing_address(source: dict) -> Optional[dict]:
    """Normalize billing address from an Account record."""
    address = {
        "street": get_path(source, "BillingStreet"),
        "city": get_path(source, "BillingCity"),
        "state": get_path(source, "BillingState"),
        "postalCode": get_path(source, "BillingPostalCode"),
        "country": get_path(source, "BillingCountry"),
    }
    # Only return if at least one field has a value
    return {k: v for k, v in address.items() if v is not None} or None


def normalize_shipping_address(source: dict) -> Optional[dict]:
    """Normalize shipping address from an Account record."""
    address = {
        "street": get_path(source, "ShippingStreet"),
        "city": get_path(source, "ShippingCity"),
        "state": get_path(source, "ShippingState"),
        "postalCode": get_path(source, "ShippingPostalCode"),
        "country": get_path(source, "ShippingCountry"),
    }
    return {k: v for k, v in address.items() if v is not None} or None


def normalize_mailing_address(source: dict) -> Optional[dict]:
    """Normalize mailing address from a Contact record."""
    address = {
        "street": get_path(source, "MailingStreet"),
        "city": get_path(source, "MailingCity"),
        "state": get_path(source, "MailingState"),
        "postalCode": get_path(source, "MailingPostalCode"),
        "country": get_path(source, "MailingCountry"),
    }
    return {k: v for k, v in address.items() if v is not None} or None


def normalize_lead_address(source: dict) -> Optional[dict]:
    """Normalize address from a Lead record."""
    address = {
        "street": get_path(source, "Street"),
        "city": get_path(source, "City"),
        "state": get_path(source, "State"),
        "postalCode": get_path(source, "PostalCode"),
        "country": get_path(source, "Country"),
    }
    return {k: v for k, v in address.items() if v is not None} or None


# Account normalization rules
ACCOUNT_RULES = {
    "accountId": "Id",
    "name": "Name",
    "industry": "Industry",
    "type": "Type",
    "phone": "Phone",
    "fax": "Fax",
    "website": "Website",
    "annualRevenue": "AnnualRevenue",
    "employees": "NumberOfEmployees",
    "description": "Description",
    "rating": "Rating",
    "billingAddress": normalize_billing_address,
    "shippingAddress": normalize_shipping_address,
    "ownerId": "OwnerId",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
}


# Contact normalization rules
CONTACT_RULES = {
    "contactId": "Id",
    "firstName": "FirstName",
    "lastName": "LastName",
    "fullName": lambda x: f"{get_path(x, 'FirstName') or ''} {get_path(x, 'LastName') or ''}".strip() or None,
    "email": "Email",
    "phone": "Phone",
    "mobilePhone": "MobilePhone",
    "title": "Title",
    "department": "Department",
    "accountId": "AccountId",
    "accountName": "Account.Name",
    "mailingAddress": normalize_mailing_address,
    "birthdate": "Birthdate",
    "leadSource": "LeadSource",
    "ownerId": "OwnerId",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
}


# Opportunity normalization rules
OPPORTUNITY_RULES = {
    "opportunityId": "Id",
    "name": "Name",
    "stage": "StageName",
    "amount": "Amount",
    "closeDate": "CloseDate",
    "probability": "Probability",
    "accountId": "AccountId",
    "accountName": "Account.Name",
    "type": "Type",
    "leadSource": "LeadSource",
    "description": "Description",
    "nextStep": "NextStep",
    "ownerId": "OwnerId",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
}


# Lead normalization rules
LEAD_RULES = {
    "leadId": "Id",
    "firstName": "FirstName",
    "lastName": "LastName",
    "fullName": lambda x: f"{get_path(x, 'FirstName') or ''} {get_path(x, 'LastName') or ''}".strip() or None,
    "email": "Email",
    "phone": "Phone",
    "mobilePhone": "MobilePhone",
    "company": "Company",
    "title": "Title",
    "status": "Status",
    "leadSource": "LeadSource",
    "industry": "Industry",
    "rating": "Rating",
    "address": normalize_lead_address,
    "website": "Website",
    "description": "Description",
    "employees": "NumberOfEmployees",
    "annualRevenue": "AnnualRevenue",
    "ownerId": "OwnerId",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
}


# Case normalization rules
CASE_RULES = {
    "caseId": "Id",
    "caseNumber": "CaseNumber",
    "subject": "Subject",
    "description": "Description",
    "status": "Status",
    "priority": "Priority",
    "type": "Type",
    "reason": "Reason",
    "origin": "Origin",
    "accountId": "AccountId",
    "accountName": "Account.Name",
    "contactId": "ContactId",
    "contactName": "Contact.Name",
    "contactEmail": "Contact.Email",
    "contactPhone": "Contact.Phone",
    "suppliedName": "SuppliedName",
    "suppliedEmail": "SuppliedEmail",
    "suppliedPhone": "SuppliedPhone",
    "suppliedCompany": "SuppliedCompany",
    "ownerId": "OwnerId",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
    "dateClosed": "ClosedDate",
}


# Campaign normalization rules
CAMPAIGN_RULES = {
    "campaignId": "Id",
    "name": "Name",
    "type": "Type",
    "status": "Status",
    "startDate": "StartDate",
    "endDate": "EndDate",
    "isActive": "IsActive",
    "description": "Description",
    "budgetedCost": "BudgetedCost",
    "actualCost": "ActualCost",
    "expectedRevenue": "ExpectedRevenue",
    "expectedResponse": "ExpectedResponse",
    "numberSent": "NumberSent",
    "numberOfLeads": "NumberOfLeads",
    "numberOfConvertedLeads": "NumberOfConvertedLeads",
    "numberOfContacts": "NumberOfContacts",
    "numberOfResponses": "NumberOfResponses",
    "numberOfOpportunities": "NumberOfOpportunities",
    "numberOfWonOpportunities": "NumberOfWonOpportunities",
    "amountAllOpportunities": "AmountAllOpportunities",
    "amountWonOpportunities": "AmountWonOpportunities",
    "ownerId": "OwnerId",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
}


# Attachment/File normalization rules
ATTACHMENT_RULES = {
    "fileId": "Id",
    "title": "Title",
    "fileType": "FileType",
    "contentSize": "ContentSize",
    "ownerName": "Owner.Name",
    "latestVersionId": "LatestPublishedVersionId",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
}


# Content Document Link normalization rules (for files attached to records)
CONTENT_DOCUMENT_LINK_RULES = {
    "fileId": "ContentDocumentId",
    "title": "ContentDocument.Title",
    "fileType": "ContentDocument.FileType",
    "contentSize": "ContentDocument.ContentSize",
    "ownerName": "ContentDocument.Owner.Name",
    "latestVersionId": "ContentDocument.LatestPublishedVersionId",
    "dateCreated": "ContentDocument.CreatedDate",
    "dateModified": "ContentDocument.LastModifiedDate",
}


# =============================================================================
# Normalization Functions
# =============================================================================

def normalize_account(raw_account: dict) -> dict:
    """Normalize a single account record."""
    return normalize(raw_account, ACCOUNT_RULES)


def normalize_contact(raw_contact: dict) -> dict:
    """Normalize a single contact record."""
    return normalize(raw_contact, CONTACT_RULES)


def normalize_opportunity(raw_opportunity: dict) -> dict:
    """Normalize a single opportunity record."""
    return normalize(raw_opportunity, OPPORTUNITY_RULES)


def normalize_lead(raw_lead: dict) -> dict:
    """Normalize a single lead record."""
    return normalize(raw_lead, LEAD_RULES)


def normalize_case(raw_case: dict) -> dict:
    """Normalize a single case record."""
    return normalize(raw_case, CASE_RULES)


def normalize_campaign(raw_campaign: dict) -> dict:
    """Normalize a single campaign record."""
    return normalize(raw_campaign, CAMPAIGN_RULES)


def normalize_attachment(raw_attachment: dict) -> dict:
    """Normalize a single attachment/file record."""
    return normalize(raw_attachment, ATTACHMENT_RULES)


def normalize_content_document_link(raw_link: dict) -> dict:
    """Normalize a ContentDocumentLink record (file attached to a record)."""
    return normalize(raw_link, CONTENT_DOCUMENT_LINK_RULES)


# =============================================================================
# Query Result Normalization
# =============================================================================

def normalize_query_result(
    raw_result: dict,
    record_normalizer: Callable[[dict], dict]
) -> dict:
    """
    Normalize a Salesforce query result containing multiple records.
    
    Args:
        raw_result: Raw Salesforce query response with 'records' list
        record_normalizer: Function to normalize individual records
    
    Returns:
        Normalized result with cleaned records
    """
    records = raw_result.get('records', [])
    normalized_records = [record_normalizer(record) for record in records]
    
    return {
        "totalSize": raw_result.get('totalSize', len(normalized_records)),
        "done": raw_result.get('done', True),
        "records": normalized_records,
    }


def normalize_accounts_result(raw_result: dict) -> dict:
    """Normalize a query result containing accounts."""
    return normalize_query_result(raw_result, normalize_account)


def normalize_contacts_result(raw_result: dict) -> dict:
    """Normalize a query result containing contacts."""
    return normalize_query_result(raw_result, normalize_contact)


def normalize_opportunities_result(raw_result: dict) -> dict:
    """Normalize a query result containing opportunities."""
    return normalize_query_result(raw_result, normalize_opportunity)


def normalize_leads_result(raw_result: dict) -> dict:
    """Normalize a query result containing leads."""
    return normalize_query_result(raw_result, normalize_lead)


def normalize_cases_result(raw_result: dict) -> dict:
    """Normalize a query result containing cases."""
    return normalize_query_result(raw_result, normalize_case)


def normalize_campaigns_result(raw_result: dict) -> dict:
    """Normalize a query result containing campaigns."""
    return normalize_query_result(raw_result, normalize_campaign)


# =============================================================================
# Metadata Normalization Rules
# =============================================================================

# Object field description normalization rules
OBJECT_FIELD_RULES = {
    "name": "name",
    "label": "label",
    "type": "type",
    "length": "length",
    "precision": "precision",
    "scale": "scale",
    "isRequired": "nillable",  # Will be inverted in normalizer
    "isCustom": "custom",
    "isUnique": "unique",
    "isExternalId": "externalId",
    "isCalculated": "calculated",
    "isAutoNumber": "autoNumber",
    "defaultValue": "defaultValue",
    "picklistValues": lambda x: [p.get('value') for p in x.get('picklistValues', []) if p.get('active')] or None,
    "referenceTo": lambda x: x.get('referenceTo') if x.get('referenceTo') else None,
    "relationshipName": "relationshipName",
}


# Object description normalization rules
OBJECT_DESCRIPTION_RULES = {
    "name": "name",
    "label": "label",
    "labelPlural": "labelPlural",
    "keyPrefix": "keyPrefix",
    "isCustom": "custom",
    "isQueryable": "queryable",
    "isSearchable": "searchable",
    "isCreateable": "createable",
    "isUpdateable": "updateable",
    "isDeletable": "deletable",
    "isTriggerable": "triggerable",
    "recordTypeCount": lambda x: len(x.get('recordTypeInfos', [])) if x.get('recordTypeInfos') else None,
}


# Apex class normalization rules
APEX_CLASS_RULES = {
    "classId": "Id",
    "name": "Name",
    "body": "Body",
    "apiVersion": "ApiVersion",
    "status": "Status",
    "lengthWithoutComments": "LengthWithoutComments",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
}


# Apex trigger normalization rules
APEX_TRIGGER_RULES = {
    "triggerId": "Id",
    "name": "Name",
    "body": "Body",
    "tableName": "TableEnumOrId",
    "apiVersion": "ApiVersion",
    "status": "Status",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
}


# Flow normalization rules
FLOW_RULES = {
    "flowId": "Id",
    "masterLabel": "MasterLabel",
    "definition": "Definition",
    "processType": "ProcessType",
    "status": "Status",
    "apiVersion": "ApiVersion",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
}


# Generic metadata component rules
METADATA_COMPONENT_RULES = {
    "componentId": "Id",
    "developerName": "DeveloperName",
    "fullName": "FullName",
    "manageableState": "ManageableState",
    "dateCreated": "CreatedDate",
    "dateModified": "LastModifiedDate",
}


# =============================================================================
# Metadata Normalization Functions
# =============================================================================

def normalize_object_field(raw_field: dict) -> dict:
    """Normalize a single object field description."""
    normalized = normalize(raw_field, OBJECT_FIELD_RULES)
    # Invert nillable to isRequired
    if 'isRequired' in normalized:
        normalized['isRequired'] = not normalized['isRequired']
    return normalized


def normalize_object_description(raw_description: dict) -> dict:
    """Normalize an object description result."""
    base = normalize(raw_description, OBJECT_DESCRIPTION_RULES)
    
    # Normalize fields if present
    raw_fields = raw_description.get('fields', [])
    if raw_fields:
        base['fields'] = [normalize_object_field(f) for f in raw_fields]
    
    # Include record types if present
    record_types = raw_description.get('recordTypeInfos', [])
    if record_types:
        base['recordTypes'] = [
            {
                "recordTypeId": rt.get('recordTypeId'),
                "name": rt.get('name'),
                "developerName": rt.get('developerName'),
                "isActive": rt.get('active'),
                "isAvailable": rt.get('available'),
                "isDefault": rt.get('defaultRecordTypeMapping'),
            }
            for rt in record_types
            if rt.get('recordTypeId')  # Filter out None record types
        ] or None
    
    return {k: v for k, v in base.items() if v is not None}


def normalize_apex_class(raw_class: dict) -> dict:
    """Normalize an Apex class record."""
    return normalize(raw_class, APEX_CLASS_RULES)


def normalize_apex_trigger(raw_trigger: dict) -> dict:
    """Normalize an Apex trigger record."""
    return normalize(raw_trigger, APEX_TRIGGER_RULES)


def normalize_flow(raw_flow: dict) -> dict:
    """Normalize a Flow record."""
    return normalize(raw_flow, FLOW_RULES)


def normalize_metadata_component(raw_component: dict) -> dict:
    """Normalize a generic metadata component record."""
    return normalize(raw_component, METADATA_COMPONENT_RULES)


def normalize_soql_result(raw_result: dict) -> dict:
    """
    Normalize a SOQL query result.
    Since SOQL can return any object type, we clean up common Salesforce artifacts
    but preserve the original field names.
    """
    records = raw_result.get('records', [])
    
    def clean_record(record: dict) -> dict:
        """Remove Salesforce internal attributes from a record."""
        cleaned = {}
        for key, value in record.items():
            if key == 'attributes':
                continue  # Skip Salesforce metadata attributes
            if isinstance(value, dict) and 'attributes' in value:
                # Nested related record - clean it recursively
                cleaned[key] = clean_record(value)
            elif value is not None:
                cleaned[key] = value
        return cleaned
    
    normalized_records = [clean_record(record) for record in records]
    
    return {
        "totalSize": raw_result.get('totalSize', len(normalized_records)),
        "done": raw_result.get('done', True),
        "records": normalized_records,
    }


def normalize_tooling_result(raw_result: dict) -> dict:
    """
    Normalize a Tooling API query result.
    Similar to SOQL but may contain different metadata structures.
    """
    records = raw_result.get('records', [])
    
    def clean_record(record: dict) -> dict:
        """Remove Salesforce internal attributes from a record."""
        cleaned = {}
        for key, value in record.items():
            if key == 'attributes':
                continue
            if isinstance(value, dict) and 'attributes' in value:
                cleaned[key] = clean_record(value)
            elif value is not None:
                cleaned[key] = value
        return cleaned
    
    normalized_records = [clean_record(record) for record in records]
    
    return {
        "totalSize": raw_result.get('totalSize', len(normalized_records)),
        "done": raw_result.get('done', True),
        "records": normalized_records,
    }


def normalize_component_source_result(raw_result: dict, metadata_type: str) -> dict:
    """
    Normalize component source/metadata retrieval results.
    Applies type-specific normalization based on the metadata type.
    """
    results = raw_result.get('results', [])
    normalized_results = []
    
    for item in results:
        if 'error' in item:
            # Preserve error items as-is
            normalized_results.append(item)
            continue
        
        data = item.get('data', {})
        records = data.get('records', [])
        
        # Apply type-specific normalization
        normalized_records = []
        for record in records:
            if metadata_type == 'ApexClass':
                normalized_records.append(normalize_apex_class(record))
            elif metadata_type == 'ApexTrigger':
                normalized_records.append(normalize_apex_trigger(record))
            elif metadata_type == 'Flow':
                normalized_records.append(normalize_flow(record))
            else:
                normalized_records.append(normalize_metadata_component(record))
        
        normalized_results.append({
            "name": item.get('name'),
            "type": item.get('type'),
            "data": {
                "totalSize": data.get('totalSize', len(normalized_records)),
                "done": data.get('done', True),
                "records": normalized_records,
            } if normalized_records else {"totalSize": 0, "done": True, "records": []}
        })
    
    return {"results": normalized_results}
