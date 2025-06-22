# HubSpot

Hubspot SDK - https://pypi.org/project/hubspot-api-client/

Obtain OAuth2 access token:

```
from hubspot.oauth import ApiException

try:
    tokens = api_client.oauth.tokens_api.create(
        grant_type="authorization_code",
        redirect_uri='http://localhost',
        client_id='client_id',
        client_secret='client_secret',
        code='code'
    )
except ApiException as e:
    print("Exception when calling create_token method: %s\n" % e)
```

# Scopes - 
    "crm.objects.companies.read "
    "crm.objects.companies.write "
    "crm.objects.contacts.read "
    "crm.objects.contacts.write "
    "crm.objects.deals.read "
    "crm.objects.deals.write "
    "crm.schemas.companies.read "
    "crm.schemas.companies.write "
    "crm.schemas.contacts.read "
    "crm.schemas.contacts.write "
    "crm.schemas.deals.read "
    "crm.schemas.deals.write "
    "oauth "
    "tickets"


Look at this video(mine) - https://youtu.be/pdJXOmC1-uA

You will get that code on the link when you will do auth 2.0
after localhost/9999 , as we set that, you have to retrive that code from there.

You can also check this video - https://www.youtube.com/watch?v=MMLJMcJhBWo&t=321s
