import os
import time
import uuid
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class Facebook:
    def __init__(self, driver) -> None:
        self.driver = driver
        #self.handle_listings_to_remove()
        #self.handle_listings_to_create()
        self.update_results()
    
    def update_results(self):
        accounts = self.driver.send_http_request('GET', 'accounts/toupdate')
        if accounts:
            for account in accounts:
                try:
                    if self.driver.currentAccount != account:
                        if self.driver:
                            self.driver.stop_driver()
                        
                        # Initialize a new driver instance for the current account
                        self.driver.currentAccount = account
                        self.driver.start_driver()
                        self.login()

                    self.update_account_results()
                    time.sleep(random.uniform(3.0, 5.0))
                except Exception as e:
                    # Log errors related to account processing
                    self.driver.record_log('error', f"Failed to process account {account.get('id', 'unknown')}: {e}")
    
    def update_account_results(self):
        self.driver.webDriver.get("https://www.facebook.com/marketplace/you/selling")
        
        init_xpath = "//div[contains(@style, 'border-radius: max(0px, min(var(--card-corner-radius), calc((100vw - 4px - 100%) * 9999))) / var(--card-corner-radius);')]/../.."

        loading_xpath = "//div[@aria-label='Loading...' and @role='status' and @data-visualcompletion='loading-state']"
        
        elements = self.driver.webDriver.find_elements(By.XPATH, init_xpath)
        is_loading = True

        while is_loading:
            self.driver.webDriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))
            
            elements = self.driver.webDriver.find_elements(By.XPATH, init_xpath)
            time.sleep(random.uniform(1, 2))

            try:
                element = self.driver.webDriver.find_element(By.XPATH, loading_xpath)
                is_loading = True
            except NoSuchElementException:
                is_loading = False
            
            time.sleep(random.uniform(1, 2))
            if len(elements) >= self.driver.currentAccount['total_listings']:
                break
        
        for element in elements:
            title_xpath = "(((//div[@aria-label='Your Listing']//a/div)[1]/div)[2]/div/div/span)[1]"
            clicks_xpath = '//div[@aria-label="The number of times people viewed the details page of your Marketplace listing in the last 14 days."]/..'
            location_xpath = "//div[@aria-label='Your Listing']//a//span/span/span/span[@aria-hidden='true']/../.."
            
            clicks = element.find_element(By.XPATH, clicks_xpath).text
            
            element.click()
            time.sleep(2)

            title = element.find_element(By.XPATH, title_xpath).text
            location = element.find_element(By.XPATH, location_xpath).text

            data = {
                "title": title,
                "clicks": clicks,
                "location": location,
            }
        
            try:
                self.driver.send_http_request('POST', f"accounts/{self.driver.currentAccount['id']}/update", data)
                self.driver.record_log('info', f"Data updated")
            except Exception as e:
                self.driver.record_log('error', f"Error updating the data: {e}")

            self.driver.click("//div[@aria-label='Close']")

    def handle_listings_to_create(self):
        """
        Handles the process of creating listings on the marketplace.

        This method retrieves listings from the backend, checks for account changes, handles blocked drivers,
        and creates new listings. It logs appropriate messages for successes and failures, and ensures
        the driver is properly managed throughout the process.
        """
        listings = self.driver.send_http_request('GET', 'listings/get')
        
        if listings:
            for listing in listings['listings']:
                try:
                    self.currentPostingId = listing['posting_id']
                    # Check if the current account needs to be updated
                    if self.driver.currentAccount != listing['account']:
                        if self.driver:
                            self.driver.stop_driver()
                        
                        # Initialize a new driver instance for the current account
                        self.driver.currentAccount = listing['account']
                        self.driver.start_driver()
                        self.login()
                    
                    # Check if the driver is blocked and perform necessary actions
                    if self.driver.currentAccount is not None and self.is_blocked():
                        self.driver.webDriver.delete_all_cookies()
                        self.login()
                    
                    # Create the listing
                    self.create_listing(listing)
                    time.sleep(random.uniform(3.0, 5.0))
                except Exception as e:
                    # Log errors related to listing processing
                    self.driver.record_log('error', f"Failed to process listing {listing.get('id', 'unknown')}: {e}")
            
            # Stop the driver after processing all listings
            if self.driver:
                self.driver.stop_driver()
        else:
            # Log info if no new listings are found
            self.driver.record_log('info', "No new listings to add.")

    def handle_listings_to_remove(self):
        """
        Handles the removal of listings by processing each listing and performing necessary actions.

        This method retrieves listings to remove, manages the WebDriver instance based on the current account,
        performs login, checks for blocks, and creates listings. It logs errors if any operations fail and
        stops the WebDriver once processing is complete or if no listings are found.
        """
        # Fetch the listings to remove
        accounts = self.driver.send_http_request('GET', 'listings/remove')

        if accounts:
            for account in accounts:
                try:
                    # Check if the current account needs to be updated
                    if self.driver.currentAccount != account:
                        if self.driver:
                            self.driver.stop_driver()
                        
                        # Initialize a new driver instance for the current account
                        self.driver.currentAccount = account
                        self.driver.start_driver()
                        self.login()
                    
                    # drop the listings
                    self.drop_listings()
                    time.sleep(random.uniform(3.0, 5.0))
                except Exception as e:
                    # Log errors related to listing processing
                    self.driver.record_log('error', f"Failed to drop listings from {account.get('id', 'unknown')}: {e}")
            
            # Stop the driver after processing all listings
            if self.driver:
                self.driver.stop_driver()
        else:
            # Log info if no new listings are found
            self.driver.record_log('info', "No new listings to remove.")
    
    def drop_listings(self):
        self.driver.webDriver.get("https://www.facebook.com/"+self.driver.currentAccount['facebook_user_id']+"/allactivity?category_key=MARKETPLACELISTINGS")
        
        # Find the element using the defined XPath
        try:
            time.sleep(2)
            init_xpath = "//div[@aria-label='Activity Log Item']/div/div/div/div/div/div[2]/div[2]"
            element = self.driver.webDriver.find_element(By.XPATH, init_xpath)

            # Loop until the element is no longer found
            while element:
                time.sleep(2)
                try:
                    xpath = "//div[@aria-label='Action options']"
                    button = element.find_element(By.XPATH, xpath)
                    if button:
                        button.click()

                        delete_xpath = "//div[span[text()='Delete']]"
                        delete = self.driver.webDriver.find_element(By.XPATH, delete_xpath)
                        delete.click()

                        delete_confirm_xpath = "//span[span[text()='Delete']]"
                        delete_confirm = self.driver.webDriver.find_element(By.XPATH, delete_confirm_xpath)
                        delete_confirm.click()
                    element = self.driver.webDriver.find_element(By.XPATH, init_xpath)
                except NoSuchElementException:
                    # Break the loop if the element is not found
                    element = None
            
            self.listings_droped()
        except:
            self.listings_droped()
    
    def is_blocked(self) -> bool:
        """
        Checks if the current user is blocked by looking for a specific element on the page.

        This method searches for an element that indicates the user has been blocked (e.g., an "OK" button). 
        It returns True if the element is found, indicating the user is blocked; otherwise, it returns False.

        Returns:
            bool: True if the user is blocked, False otherwise.
        """
        try:
            # Search for the "OK" button which indicates a blocked status
            elements = self.driver.webDriver.find_elements(By.XPATH, "//span/span[contains(., 'OK')]")

            # Check if the element indicating blocked status is present
            if len(elements) > 0:
                self.driver.record_log('info', "Marketplace is blocked.")
                return True
            else:
                self.driver.record_log('info', "Marketplace is not blocked.")
                return False

        except Exception as e:
            # Log any exceptions that occur during the check
            self.driver.record_log('error', f"Error checking blocked status: {e}")
            raise

    def login(self):
        """
        Attempts to log into Facebook using the credentials provided in the current account.

        This method navigates to the Facebook login page, enters the username and password, and clicks the login button.
        It logs the progress and errors during the login process.

        Raises:
            Exception: If any part of the login process fails.
        """
        try:

            # Navigate to the Facebook mobile site
            self.driver.webDriver.get("https://mbasic.facebook.com/profile.php")
            try:
                # Locate the elemesnt once and store it
                strong_element = self.driver.webDriver.find_element(By.XPATH, '//span/strong')
                
                if strong_element:
                    # Access the innerHTML attribute
                    strong_text = strong_element.get_attribute('innerHTML')
                    self.driver.record_log('info', f"Connected as {strong_text}")
                    return
            except NoSuchElementException:
                # Handle the case where the element is not found
                self.driver.record_log('info', "Not logged in, attempting login.")
                
                
            self.driver.webDriver.get("https://mbasic.facebook.com/")

            if self.driver.click("//button[@name='accept_only_essential' and @value='1']"):
                self.driver.webDriver.get("https://mbasic.facebook.com/")
            self.driver.webDriver.get("https://mbasic.facebook.com/")

            # Enter the username
            if not self.driver.type("email", self.driver.currentAccount['username'], by=By.NAME):
                self.driver.record_log('error', "Failed to type username.")
                raise Exception("Username entry failed")
            
            # Enter the password
            if not self.driver.type("pass", self.driver.currentAccount['password'], by=By.NAME):
                self.driver.record_log('error', "Failed to type password.")
                raise Exception("Password entry failed")
            
            # Click the login button
            if not self.driver.click("login", by=By.NAME):
                self.driver.record_log('error', "Failed to click login button.")
                raise Exception("Login button click failed")
            
            try:
                if not self.driver.click("//input[@value='OK']"):
                    self.driver.record_log('error', "Failed to click 'OK' button.")
            except:
                pass
            # Wait for the login attempt to complete
            time.sleep(5)
            
            # Log the successful completion of the login attempt
            self.driver.record_log('info', "Login attempt finished.")

        except Exception as e:
            # Log any errors encountered during the login process
            self.driver.record_log('error', f"Login error: {e}")
            raise

    def limite_reached(self) -> bool:
        """
        Checks if a limit has been reached by looking for a specific element on the page.

        This method searches for an element that indicates a limit has been reached (e.g., a specific message or status). 
        It returns True if the element is found, indicating the limit has been reached; otherwise, it returns False.

        Returns:
            bool: True if the limit is reached, False otherwise.
        """
        try:
            # Define the XPath for the element that indicates the limit has been reached
            xpath = "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[1]/div/div[2]/div[1]/div[2]/div/div/div[2]/div/div/div/div/span/div/div/div[2]/div/div[1]/span/span/span"

            # Find elements matching the XPath
            elements = self.driver.webDriver.find_elements(By.XPATH, xpath)

            # Check if the element indicating limit reached is present
            if len(elements) > 0:
                self.driver.record_log('info', "Limit has been reached.")
                return True
            else:
                self.driver.record_log('info', "Limit has not been reached.")
                return False

        except Exception as e:
            # Log any exceptions that occur during the check
            self.driver.record_log('error', f"Error checking limit status: {e}")
            raise

    def create_listing(self, listing: dict) -> None:
        """
        Creates a marketplace listing on Facebook with the provided details.

        This method navigates to the Facebook Marketplace create item page and fills out the form with the provided
        listing details. It performs various checks and updates based on the success or failure of each step.
        
        Args:
            listing (dict): A dictionary containing the listing details such as photos, title, price, etc.

        Raises:
            Exception: If an error occurs during the creation of the listing.
        """
        # Navigate to the create listing page
        self.driver.webDriver.get("https://www.facebook.com/marketplace/create/item")

        # Check if the limit has been reached before proceeding
        if self.limite_reached():
            self.driver.record_log('info', "Listing creation aborted: Limit reached.")
            return

        try:
            # Add pictures to the listing
            if not self.add_pictures(listing.get("photos", [])):
                raise Exception("Failed to add pictures")
            
            # Add title to the listing
            if not self.add_title(listing.get("title", "")):
                raise Exception("Failed to add title")
            
            # Add price to the listing
            if not self.add_price(listing.get("postings_price", "")):
                raise Exception("Failed to add price")
            
            # Add category to the listing
            if not self.add_category(listing.get("category", "")):
                raise Exception("Failed to add category")
            
            # Add condition to the listing
            if not self.add_condition(listing.get("condition", "")):
                raise Exception("Failed to add condition")
            
            # Add description to the listing
            if not self.add_description(listing.get("description", "")):
                raise Exception("Failed to add description")
            
            # Add availability to the listing
            if not self.add_availability(listing.get("availability", "")):
                raise Exception("Failed to add availability")
            
            # Add tags to the listing
            if not self.add_tags(listing.get("tags", [])):
                raise Exception("Failed to add tags")
            
            # Add location to the listing
            location = self.add_location()
            if not location:
                raise Exception("Failed to add location")
            
            # Hide listing from friends if required
            if not self.hide_from_friends():
                raise Exception("Failed to hide from friends")
            
            # Proceed to the next step
            if not self.next():
                raise Exception("Failed to proceed to the next step")
            
            # Publish the listing
            if not self.publish():
                raise Exception("Failed to publish listing")
            
            # Confirm listing publication
            if not self.listing_published(listing, location):
                raise Exception("Failed to confirm listing publication")

            # Log success
            self.driver.record_log('info', "Listing created successfully.")

        except Exception as e:
            # Log the error and update listing status
            self.driver.record_log('error', f"Error creating listing: {e}")
            self.listing_unpublished(listing, str(e))
        
    def add_pictures(self, pictures):
        """
        Adds pictures to the listing.

        This method downloads pictures from given URLs and uploads them to the listing. It handles the downloading
        and uploading processes and logs any errors encountered.

        Args:
            pictures (list): A list of dictionaries containing picture URLs.

        Returns:
            bool: True if pictures were successfully added, False otherwise.

        Raises:
            Exception: If an error occurs while adding pictures.
        """
        try:
            self.driver.record_log('info', "Adding pictures.")
            
            download_folder = "download/photos"
            os.makedirs(download_folder, exist_ok=True)
            
            photos_paths = []
            for picture in pictures:
                photo_url = picture["photo"]["photo"]
                unique_filename = f"{uuid.uuid4()}.jpg" 
                download_path = os.path.join(download_folder, unique_filename)
                self.driver.download_file(photo_url, download_path)
                photos_paths.append(os.path.abspath(download_path))
            
            pictures_paths_str = "\n".join(photos_paths)
            xpath = "//input[@type='file'][@multiple]"
            
            if not self.driver.type(xpath, pictures_paths_str):
                self.driver.record_log('error', "Failed to upload pictures.")
                return False
            
            self.driver.record_log('info', "Pictures added successfully.")
            return True
        
        except Exception as e:
            self.driver.record_log('error', f"Error adding pictures: {e}")
            raise

    def add_title(self, title):
        """
        Adds a title to the listing.

        This method types the given title into the title field of the listing form. It logs the process and any errors
        encountered during the operation.

        Args:
            title (dict): A dictionary containing the title for the listing.

        Returns:
            bool: True if the title was successfully added, False otherwise.

        Raises:
            Exception: If an error occurs while adding the title.
        """
        try:
            self.driver.record_log('info', "Adding title.")
            xpath = "//*[contains(@aria-label, 'Title')]//input"
            if not self.driver.type(xpath, title["title"]):
                self.driver.record_log('error', "Failed to add title.")
                return False
            self.driver.record_log('info', "Title added successfully.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error adding title: {e}")
            raise

    def add_price(self, price):
        """
        Adds a price to the listing.

        This method types the given price into the price field of the listing form. It logs the process and any errors
        encountered during the operation.

        Args:
            price (dict): A dictionary containing the price for the listing.

        Returns:
            bool: True if the price was successfully added, False otherwise.

        Raises:
            Exception: If an error occurs while adding the price.
        """
        try:
            self.driver.record_log('info', "Adding price.")
            xpath = "//*[contains(@aria-label, 'Price')]//input"
            if not self.driver.type(xpath, price["price"]):
                self.driver.record_log('error', "Failed to add price.")
                return False
            self.driver.record_log('info', "Price added successfully.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error adding price: {e}")
            raise

    def add_category(self, category):
        """
        Adds a category to the listing.

        This method opens the category dropdown and selects the given category. It handles dropdown interactions
        and logs any errors encountered during the operation.

        Args:
            category (dict): A dictionary containing the category for the listing.

        Returns:
            bool: True if the category was successfully added, False otherwise.

        Raises:
            Exception: If an error occurs while adding the category.
        """
        try:
            self.driver.record_log('info', "Adding category.")
            xpath = "//*[contains(@aria-label, 'Category')]//div/div"
            if not self.driver.click(xpath):
                self.driver.record_log('error', "Failed to open category dropdown.")
                return False
            
            time.sleep(random.uniform(0.8, 1.8))
            xpath = "//span/div/span[contains(., '"+category["category"]+"')]"
            if not self.driver.click(xpath):
                self.driver.record_log('error', "Failed to select category.")
                return False
            
            self.driver.record_log('info', "Category added successfully.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error adding category: {e}")
            raise

    def add_condition(self, condition):
        """
        Adds a condition to the listing.

        This method opens the condition dropdown and selects the given condition. It handles dropdown interactions
        and logs any errors encountered during the operation.

        Args:
            condition (dict): A dictionary containing the condition for the listing.

        Returns:
            bool: True if the condition was successfully added, False otherwise.

        Raises:
            Exception: If an error occurs while adding the condition.
        """
        try:
            self.driver.record_log('info', "Adding condition.")
            xpath = "//label[contains(., 'Condition')]//div/div"
            if not self.driver.click(xpath):
                self.driver.record_log('error', "Failed to open condition dropdown.")
                return False
            
            time.sleep(random.uniform(0.8, 1.8))
            xpath = "//span[contains(., '"+condition["condition"]+"')]"
            if not self.driver.click(xpath):
                self.driver.record_log('error', "Failed to select condition.")
                return False
            
            self.driver.record_log('info', "Condition added successfully.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error adding condition: {e}")
            raise

    def add_description(self, description):
        """
        Adds a description to the listing.

        This method types the given description into the description field of the listing form. It logs the process
        and any errors encountered during the operation.

        Args:
            description (dict): A dictionary containing the description for the listing.

        Returns:
            bool: True if the description was successfully added, False otherwise.

        Raises:
            Exception: If an error occurs while adding the description.
        """
        try:
            self.driver.record_log('info', "Adding description.")
            xpath = "//*[contains(@aria-label, 'Description')]//textarea"
            if description is not None and not self.driver.type(xpath, description["description"]):
                self.driver.record_log('error', "Failed to add description.")
                return False
            
            self.driver.record_log('info', "Description added successfully.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error adding description: {e}")
            raise

    def add_availability(self, availability):
        """
        Adds availability to the listing.

        This method opens the availability dropdown and selects the given availability option. It handles dropdown
        interactions and logs any errors encountered during the operation.

        Args:
            availability (dict): A dictionary containing the availability status for the listing.

        Returns:
            bool: True if the availability was successfully added, False otherwise.

        Raises:
            Exception: If an error occurs while adding the availability.
        """
        try:
            self.driver.record_log('info', "Adding availability.")
            xpath = "//label[contains(., 'Availability')]//div/div"
            if not self.driver.click(xpath):
                self.driver.record_log('error', "Failed to open availability dropdown.")
                return False
            
            time.sleep(random.uniform(0.8, 1.8))
            xpath = "//span[contains(., '"+availability["availability"]+"')]"
            if not self.driver.click(xpath):
                self.driver.record_log('error', "Failed to select availability.")
                return False
            
            time.sleep(random.uniform(0.8, 1.8))
            self.driver.record_log('info', "Availability added successfully.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error adding availability: {e}")
            raise

    def add_tags(self, tags):
        """
        Adds tags to the listing.

        This method types the given tags into the tags field of the listing form. It logs the process and any errors
        encountered during the operation.

        Args:
            tags (dict): A dictionary containing the tags for the listing.

        Returns:
            bool: True if the tags were successfully added, False otherwise.

        Raises:
            Exception: If an error occurs while adding the tags.
        """
        try:
            self.driver.record_log('info', "Adding tags.")
            xpath = "//*[contains(@aria-label, 'Product tags')]//textarea"
            if tags is not None and not self.driver.type(xpath, tags["tags"]):
                self.driver.record_log('error', "Failed to add tags.")
                return False
            
            self.driver.record_log('info', "Tags added successfully.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error adding tags: {e}")
            raise

    def add_location(self, iter=0):
        """
        Adds a location to the listing.

        This method types the location into the location field and selects it from the suggestions. It handles
        the process of typing and selecting the location, and retries if necessary. It logs any errors encountered
        during the operation.

        Args:
            iter (int, optional): The current iteration count for retries. Defaults to 0.

        Returns:
            str: The ID of the selected location if successful, None otherwise.

        Raises:
            Exception: If an error occurs while adding the location.
        """
        try:
            self.driver.record_log('info', "Adding location.")
            
            location = self.driver.send_http_request('GET', 'locations/'+self.driver.currentPostingId+'/get')
            location_str = f"{location['name']}, {location['wilaya']['name']}, Algeria"

            xpath = "//label[contains(., 'Location')]//input"
            if not self.driver.type(xpath, location_str, deleteBefore=True):
                self.driver.record_log('error', "Failed to type location.")
                return None
            
            xpath = "//ul[@role='listbox']/li[@role='option'][1]"
            time.sleep(random.uniform(1.5, 2))
            if not self.driver.click(xpath) and iter < 100:
                return self.add_location(iter=iter + 1)
            
            self.driver.record_log('info', "Location added successfully.")
            return location['id']
        except Exception as e:
            self.driver.record_log('error', f"Error adding location: {e}")
            if iter < 100:
                return self.add_location(iter=iter + 1)
            raise

    def hide_from_friends(self):
        """
        Hides the listing from friends.

        This method clicks the checkbox to hide the listing from friends. It logs the process and any errors encountered.

        Returns:
            bool: True if the listing was successfully hidden from friends, False otherwise.

        Raises:
            Exception: If an error occurs while hiding the listing from friends.
        """
        try:
            self.driver.record_log('info', "Hiding from friends.")
            xpath = "(//input[@type='checkbox'])[2]"
            if not self.driver.click(xpath):
                self.driver.record_log('error', "Failed to hide listing from friends.")
                return False
            
            self.driver.record_log('info', "Listing hidden from friends successfully.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error hiding from friends: {e}")
            raise

    def next(self):
        """
        Clicks the 'Next' button in the listing form.

        This method clicks the 'Next' button to proceed to the next step in the listing creation process. It logs
        the process and any errors encountered.

        Returns:
            bool: True if the 'Next' button was successfully clicked, False otherwise.

        Raises:
            Exception: If an error occurs while clicking the 'Next' button.
        """
        try:
            self.driver.record_log('info', "Clicking next button.")
            xpath = "//span[contains(., 'Next')]/span"
            if not self.driver.click(xpath):
                self.driver.record_log('error', "Failed to click next button.")
                return False
            
            self.driver.record_log('info', "'Next' button clicked successfully.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error clicking next button: {e}")
            raise

    def publish(self):
        """
        Clicks the 'Publish' button to publish the listing.

        This method clicks the 'Publish' button to make the listing live. It logs the process and any errors
        encountered.

        Returns:
            bool: True if the 'Publish' button was successfully clicked, False otherwise.

        Raises:
            Exception: If an error occurs while clicking the 'Publish' button.
        """
        try:
            self.driver.record_log('info', "Clicking publish button.")
            xpath = "//span[contains(., 'Publish')]/span"
            if not self.driver.click(xpath):
                self.driver.record_log('error', "Failed to click publish button.")
                return False
            
            self.driver.record_log('info', "'Publish' button clicked successfully.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error clicking publish button: {e}")
            raise
    
    def listing_published(self, listing, location, iter=1):
        """
        Marks the listing as published in the backend.

        This method sends a POST request to the backend API to update the status of the listing to 'published'.
        It includes retry logic in case of failure, with a maximum of 10 retries.

        Args:
            listing (dict): A dictionary containing the listing details, including the listing ID.
            location (str): The location associated with the listing.
            iter (int): The current iteration number for retries.

        Returns:
            bool: True if the request was successful and the listing was marked as published, False otherwise.

        Raises:
            Exception: If the maximum number of retries is exceeded.
        """
        data = {
            "state": "published",
            "location": location
        }
        
        try:
            self.driver.send_http_request('POST', f"listings/{listing['id']}/published", data)
            self.driver.record_log('info', f"Iteration {iter}: Listing {listing['id']} marked as published.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Iteration {iter}: Error marking listing {listing['id']} as published: {e}")
            if iter < 10:
                time.sleep(2 ** iter)  # Exponential backoff before retrying
                return self.listing_published(listing, location, iter + 1)
            else:
                self.driver.record_log('error', f"Aborting after {iter} failed attempts: Listing {listing['id']} can't be marked as published.")
                return False

    def listing_unpublished(self, listing, exception):
        """
        Marks the listing as unpublished in the backend.

        This method sends a POST request to the backend API to update the status of the listing to 'unpublished'.
        It logs the success or failure of the request and returns a boolean indicating the result.

        Args:
            listing (dict): A dictionary containing the listing details, including the listing ID.
            exception (str): An explanation of why the listing could not be published.

        Returns:
            bool: True if the request was successful and the listing was marked as unpublished, False otherwise.
        """
        data = {
            "state": "unpublished",
            "exception": exception
        }
        
        try:
            self.driver.send_http_request('POST', f"listings/{listing['id']}/unpublished", data)
            self.driver.record_log('info', f"Listing {listing['id']} marked as unpublished.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error marking listing {listing['id']} as unpublished: {e}")
            return False

    def listings_droped(self):
        """
        Marks the listing as unpublished in the backend.

        This method sends a POST request to the backend API to update the status of the listing to 'unpublished'.
        It logs the success or failure of the request and returns a boolean indicating the result.

        Args:
            listing (dict): A dictionary containing the listing details, including the listing ID.
            exception (str): An explanation of why the listing could not be published.

        Returns:
            bool: True if the request was successful and the listing was marked as unpublished, False otherwise.
        """
        data = {
            "state": "droped",
        }
        
        try:
            self.driver.send_http_request('POST', f"listings/{self.driver.currentAccount['id']}/droped", data)
            self.driver.record_log('info', f"Listings from {self.driver.currentAccount['id']} marked as droped.")
            return True
        except Exception as e:
            self.driver.record_log('error', f"Error marking listings from {self.driver.currentAccount['id']} as droped: {e}")
            return False

