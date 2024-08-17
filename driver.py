import logging
import requests
import time
import os
from datetime import datetime
import random
from typing import Optional, Dict, Any
from fake_useragent import UserAgent
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from video_frame_extractor import VideoFrameExtractor
from facebook import Facebook

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Driver:
    def __init__(self, base_url: str, sleep_time: int = 60) -> None:
        """
        Initialize the driver with given parameters.

        :param base_url: Base URL of the API.
        :param sleep_time: Time in seconds to wait between iterations (default: 60).
        """
        self.url = base_url
        self.currentAccount: Optional[Any] = None
        self.webDriver: Optional[Any] = None
        self.sleep_time = sleep_time
    
    def start_driver(self):
        """
        Starts the WebDriver with custom configurations.

        This method initializes the WebDriver with specified Chrome options, including setting up
        user data directories, configuring user-agent strings, and applying performance and stealth settings.
        It logs the progress and handles errors related to missing configurations or files.

        Raises:
            ValueError: If the current account is not set.
            FileNotFoundError: If the chromedriver executable is not found at the specified path.
        """
        self.record_log('info', "Starting the webDriver.")
        if not self.currentAccount:
            self.record_log('error', "Current account is not set.")
            raise ValueError("Current account is not set.")
        
        # Create user data directory if it doesn't exist
        userDataDir = os.path.abspath(f"data/chrome/{self.currentAccount['id']}/")
        os.makedirs(userDataDir, exist_ok=True)

        # Set up Chrome options
        chromeOptions = ChromeOptions()
        chromeOptions.add_argument(f"user-data-dir={userDataDir}")

        # Set a random user-agent
        #userAgent = UserAgent().random
        #chromeOptions.add_argument(f'user-agent={userAgent}')

        # Other Chrome options for better performance and stealth
        chromeOptions.add_experimental_option("detach", True)
        chromeOptions.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})
        chromeOptions.add_argument("--disable-infobars")
        chromeOptions.add_argument("start-maximized")
        chromeOptions.add_argument("--encoding=UTF-8")
        chromeOptions.add_argument("--disable-extensions")
        chromeOptions.add_argument("--disable-gpu")
        chromeOptions.add_argument("--log-level=3")
        chromeOptions.add_argument("--disable-search-engine-choice-screen")
        chromeOptions.add_argument("--silent")
        chromeOptions.add_experimental_option("excludeSwitches", ["enable-automation"])
        chromeOptions.add_experimental_option("useAutomationExtension", False)
        chromeOptions.add_argument("--disable-popup-blocking")

        # Path to the chromedriver executable
        #chromedriver_path = os.path.abspath("data/chromedriver.exe")
        #if not os.path.exists(chromedriver_path):
        #    self.record_log('error', f"Chromedriver not found at path: {chromedriver_path}")
        #    raise FileNotFoundError(f"Chromedriver not found at path: {chromedriver_path}")
        
        # Initialize the WebDriver
        self.webDriver = webdriver.Chrome(options=chromeOptions)
        self.record_log('info', "WebDriver started successfully.")

    def download_file(self, url, download_path):
        """Download an file from a URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(download_path, 'wb') as file:
                file.write(response.content)
            self.record_log('info', f"File downloaded successfully from {url}")
        except requests.exceptions.RequestException as e:
            self.record_log('error', f"Failed to download file: {e}")
            raise

    def type(self, element: str, value: str, by=By.XPATH, deleteBefore=False, asHuman=False):
        """
        Type a value into a web element.

        Args:
            element (str): The identifier of the web element.
            value (str): The value to type into the element.
            by: The method to locate the element (default is By.XPATH).
            deleteBefore (bool): Whether to delete existing content before typing (default is False).
            asHuman (bool): Whether to simulate human typing by adding delays (default is False).

        Raises:
            Exception: If an error occurs while typing into the element.
        """
        try:
            elem = self.webDriver.find_element(by, element)
            if deleteBefore:
                elem.send_keys(Keys.CONTROL + "a")
                elem.send_keys(Keys.DELETE)

            if asHuman:
                for char in value:
                    elem.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.2))
            else:
                elem.send_keys(value)
            self.record_log('info', f"Successfully typed into element {element}")
            return True
        except Exception as e:
            self.record_log('error', f"Error typing into element {element}: {e}")
            raise
    
    def click(self, element: str, by=By.XPATH, asHuman=False):
        """
        Click on a web element.

        Args:
            element (str): The identifier of the web element.
            by: The method to locate the element (default is By.XPATH).
            asHuman (bool): Whether to simulate a human click by adding a delay (default is False).

        Raises:
            Exception: If an error occurs while clicking the element.
        """
        try:
            elem = self.webDriver.find_element(by, element)
            if asHuman:
                time.sleep(random.uniform(0.5, 1))
            try:
                elem.click()
            except Exception:
                self.webDriver.execute_script("arguments[0].scrollIntoView(true);", elem)
                self.webDriver.execute_script("arguments[0].click();", elem)
            self.record_log('info', f"Successfully clicked on element {element}")

            return True
        except Exception as e:
            self.record_log('error', f"Error clicking on element {element}: {e}")
            raise
        
    def stop_driver(self):
        """
        Stops and quits the WebDriver.

        This method will gracefully close the WebDriver if it is running and then set
        the `webDriver` attribute to None. It also logs the action for tracking purposes.

        Raises:
            Exception: If an error occurs while stopping the WebDriver.
        """
        if self.webDriver:
            try:
                self.webDriver.quit()
                self.webDriver = None
                self.record_log('info', "WebDriver stopped successfully.")
            except Exception as e:
                self.record_log('error', f"Error stopping WebDriver: {e}")
                raise

    def record_log(self, log_type: str, content: str) -> None:
        """
        Records a log message to both local logging and a remote logging service.

        Args:
            log_type (str): The type of log ('error' or 'info').
            content (str): The log message content.

        Raises:
            ValueError: If an unsupported log type is provided.
        """
        # Log locally using Python's logging module
        if log_type == 'error':
            logging.error(content)
        elif log_type == 'info':
            logging.info(content)
        else:
            # Raise an exception for unsupported log types
            raise ValueError(f"Unsupported log type: {log_type}")

        # Record the log message to a remote logging service
        log_entry = {
            'type': log_type,
            'content': content,
            'logged_at': datetime.now().isoformat()
        }

        # Example usage in a logging function
        #self.send_http_request('POST', 'logs/add', log_entry)

    def send_http_request(self, request_type: str, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sends an HTTP request to the specified URL and handles the response.

        Args:
            request_type (str): The type of HTTP request ('get' or 'post').
            path (str): The path to append to the base URL.
            data (dict, optional): The data to send with a POST request.

        Returns:
            dict: The JSON response from the server if successful.

        Raises:
            ValueError: If an unsupported request type is provided or if the response is not in JSON format.
            requests.RequestException: For errors in the HTTP request.
        """
        url = f'{self.url}/{path}'
        try:
            request_type_lower = request_type.lower()

            # Determine request type and send appropriate request
            if request_type_lower == 'post':
                response = requests.post(url, json=data)
            elif request_type_lower == 'get':
                response = requests.get(url)
            else:
                raise ValueError(f"Unsupported request type: {request_type}")

            # Check if the response indicates success
            if response.status_code // 100 != 2:
                #logging.error("error", f"Server responded with status code: {response.status_code}")
                #logging.error("error", f"Response content: {response.text}")
                response.raise_for_status()  # Raise HTTPError for bad responses

            # Attempt to parse JSON response
            try:
                text = response.json()
                return text
            except ValueError:
                #logging.error("error", "Response content is not in JSON format.")
                #logging.error("error", response.text)
                raise
            #logging.info("Request sent and response received successfully.")
        except requests.RequestException as e:
            #logging.error(f"Request failed: {e}")
            raise
        

    def start(self) -> None:
        """
        Starts the driver and enters the main loop, handling iterations and logging.

        Logs the start of the driver and continuously runs iterations while handling exceptions.
        """
        # Log that the driver has started
        self.record_log('info', "Driver started.")
        
        while True:
            try:
                # Execute a single iteration of drivers's main function
                self.run_iter()
                # Sleep for the specified amount of time between iterations
                time.sleep(self.sleep_time)

            except Exception as e:
                # Log any errors that occur during the iteration
                self.record_log('error', f"An error occurred in start loop: {e}")
                # Sleep before continuing the loop to avoid rapid error logging
                time.sleep(self.sleep_time)
    

    def run_iter(self) -> None:
        VideoFrameExtractor(self)
        Facebook(self)