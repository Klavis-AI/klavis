import os
import splunklib.client as client

def get_splunk_service():
    return client.connect(
        host=os.environ["SPLUNK_HOST"],
        port=int(os.environ["SPLUNK_PORT"]),
        username=os.environ["SPLUNK_USERNAME"],
        password=os.environ["SPLUNK_PASSWORD"]
    )
