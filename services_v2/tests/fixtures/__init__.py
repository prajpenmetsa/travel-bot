from pytest import fixture

@fixture(scope='session')
def setup_database():
    pass

@fixture
def sample_data():
    return {'key': 'value'}