#!/bin/bash

# Function that wraps another function and provides context about what process will occur
sleep_dec() {
        # First parameter is the context, second parameter is the function
        echo ""
        echo "${1} ..."
        sleep 1

        # Call the function that is the second argument
        $2

        echo "Done."
        sleep 0.5
        echo ""
}

# Install Selenium if not already installed
run_sel_check () {
        pip list | grep -F selenium
}

install_selenium () {
        sel_check=$(run_sel_check)
        if ! [[ $sel_check == *"s"* ]]; then
                pip install -U selenium
        fi
}

sleep_dec "Installing selenium if necessary" install_selenium


# Set up prerequisites
install_prereqs () {
        sudo apt-get update
        sudo apt-get install -y unzip xvfb libxi6 libgconf-2-4
}

sleep_dec "Installing prerequisites" install_prereqs


# Uninstall any previous instances of chrome if exists
uninstall_chrome () {
        chrome_dpkg=$(dpkg -s google-chrome-stable)
        if [[ $chrome_dpkg == *"Status: install ok installed"* ]]; then
                sudo apt-get remove google-chrome-stable
        fi
}

sleep_dec "Uninstalling any previous instances of google-chrome-stable if exists" uninstall_chrome


# Install google chrome
#sudo curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add
install_chrome () {
        sudo echo "deb [arch=amd64]  http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
        sudo apt-get -y update
        sudo apt-get -y install google-chrome-stable
}

sleep_dec "Installing newest version of google-chrome-stable" install_chrome


# Install latest version of chromedriver
install_chromedriver () {
        wget https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip
        unzip chromedriver_linux64.zip

        # Create a chromedrivers folder if it doesn't exist
        if ! [ -d "./chromedrivers" ]; then
                mkdir chromedrivers
        fi

        # Remove old version of chromedriver
        if [ -f "./chromedrivers/chromedriver" ]; then
                rm chromedrivers/chromedriver
        fi

        # Give permission to chromedriver and move it into appropriate directory
        mv chromedriver chromedrivers
        sudo chmod +x chromedrivers
        rm chromedriver_linux64.zip
}

sleep_dec "Installing latest version of chromedriver" install_chromedriver
