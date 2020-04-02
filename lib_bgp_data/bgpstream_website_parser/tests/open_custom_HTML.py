from bs4 import BeautifulSoup as Soup

def open_custom_HTML(url: str, tag: str):
    """Function used for patching utils.get_tags()."""

    # hijacks and leaks have no countries or end times
    # outage.html is an outage with no country and no end time
    # outage_country is an outage with a country but no end time
    # outage_end is an outage with no country but an end time
    # outage_country_end has both
    url_to_path = {'229087': 'hijack_IPV4', '229100': 'leak', '229106': 'outage_country_end',
                   '230378': 'outage', '230354': 'outage_country', '230351': 'outage_end',
                   '230097': 'hijack_IPV6'}

    # if the url is to a specific event
    if '/event/' in url:
        # open to the corresponding path
        with open('./test_HTML/' + url_to_path[url.split('/')[4]] + '.html') as f:
            return [x for x in Soup(f.read(), 'html.parser').select(tag)]

    # or return the front page
    else:
        with open('./test_HTML/page.html') as f:
            return [x for x in Soup(f.read(), 'html.parser').select(tag)]

