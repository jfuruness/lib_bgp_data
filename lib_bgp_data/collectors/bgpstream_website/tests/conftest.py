import pytest
from .create_HTML import HTML_Creator

@pytest.fixture(scope='session')
def setup():
    # setting scope so HTML is only created once per test session
    html = HTML_Creator()
    html.setup()
    return html

