import pytest
from .create_HTML import HTML_Creator

# https://docs.pytest.org/en/stable/tmpdir.html#the-tmpdir-factory-fixture
@pytest.fixture(scope='session')
def setup(tmpdir_factory):
    # setting scope so HTML is only created once per test session
    html = HTML_Creator(tmpdir_factory.mktemp("test_html"))
    html.setup()
    return html

