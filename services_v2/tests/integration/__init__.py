from pytest import fixture

@fixture
def sample_data():
    return {"key": "value"}

def test_integration_example(sample_data):
    assert sample_data["key"] == "value"