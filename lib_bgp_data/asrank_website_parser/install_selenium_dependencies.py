from .constants import Constants
import time
import os


def run_shell():
    if not os.path.exists(os.path.join(Constants.CHROMEDRIVER_PATH, 'chromedriver')):
        print("Chromedriver doesn't exist. Installing chromedriver and chrome")
        os.system('sudo echo ""')
        os.system('./install_selenium_dependencies.sh')
    else:
        print('Chromedriver already exists')
