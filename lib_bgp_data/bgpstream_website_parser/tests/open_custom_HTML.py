from bs4 import BeautifulSoup as Soup

def open_custom_HTML(path: str, tag: str):
        # trying to request a specific event page
        if '229087' in path:
            with open('./test_HTML/hijack.html') as f:
                return [x for x in Soup(f.read(), 'html.parser').select(tag)]
        if '229100' in path:
            with open('./test_HTML/leak.html') as f:
                return [x for x in Soup(f.read(), 'html.parser').select(tag)]
        if '229106' in path:
            with open('./test_HTML/outage.html') as f:
                return [x for x in Soup(f.read(), 'html.parser').select(tag)]

        with open('./test_HTML/page.html') as f:
            return [x for x in Soup(f.read(), 'html.parser').select(tag)]

