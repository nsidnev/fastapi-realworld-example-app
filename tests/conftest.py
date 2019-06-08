from pytest import fixture
from starlette.config import environ
from starlette.testclient import TestClient


@fixture(scope="session")
def test_client():
    from app.main import app
    with TestClient(app) as test_client:
        yield test_client


# This line would raise an error if we use it after 'settings' has been imported.
environ['TESTING'] = 'TRUE'


@fixture(autouse=True, scope="session")
def setup_test_database():
    """
    Create a clean test database every time the tests are run.
    """
    # url = str(settings.DATABASE_URL)
    # engine = create_engine(url)
    # assert not database_exists(url), 'Test database already exists. Aborting tests.'
    # create_database(url)             # Create the test database.
    # metadata.create_all(engine)      # Create the tables.
    # yield                            # Run the tests.
    # drop_database(url)               # Drop the test database.
    pass