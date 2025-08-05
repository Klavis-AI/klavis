from tools.list_vendors import list_vendors

def test_list_vendors():
    vendors = list_vendors(2)
    assert isinstance(vendors, dict)
    assert "response_status" in vendors
