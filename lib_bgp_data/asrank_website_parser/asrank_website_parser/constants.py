import os


class Constants:
    FILE_PATH = os.path.dirname(os.path.abspath(__file__))
    CHROMEDRIVER_PATH = os.path.join(FILE_PATH, 'chromedrivers')

    URL = 'https://asrank.caida.org/'
    CSV_FILE_NAME = 'asrank_caida.csv'
    ENTRIES_PER_PAGE = 1000
