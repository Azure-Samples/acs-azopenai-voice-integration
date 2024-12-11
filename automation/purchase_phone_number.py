import os
import time
import random
import json
import argparse
from azure.communication.phonenumbers import (
    PhoneNumbersClient,
    PhoneNumberType,
    PhoneNumberAssignmentType,
    PhoneNumberCapabilities,
    PhoneNumberCapabilityType,
)
from azure.core.exceptions import HttpResponseError


OUTPUT_FILE = "phone_number_result.json"


def check_existing_number():
    """Check if we already have a purchased number"""
    try:
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r") as f:
                data = json.load(f)
                if data.get("success", False) and data.get("phone_number"):
                    print(f"Found existing phone number: {data['phone_number']}")
                    return data["phone_number"]
    except Exception as e:
        print(f"Error checking existing number: {e}")
    return None


class RetryConfig:
    def __init__(self, max_retries=5, initial_delay=1, max_delay=32):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay


class PhoneNumberPurchaser:
    def __init__(self, connection_string, retry_config=None):
        if not connection_string:
            self._write_output(success=False, error="Connection string not provided")
            raise ValueError("Connection string not provided")

        self.connection_str = connection_string
        self.phone_numbers_client = PhoneNumbersClient.from_connection_string(
            self.connection_str
        )
        self.retry_config = retry_config or RetryConfig()
        self.purchased_number = None

    def _write_output(self, success, phone_number=None, error=None):
        """Write the result to a JSON file that Terraform can parse"""
        output = {
            "success": success,
            "phone_number": phone_number if success else "",
            "error": error if not success else "",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            with open(OUTPUT_FILE, "w") as f:
                json.dump(output, f, indent=2)
        except Exception as e:
            print(f"Error writing output file: {str(e)}")
            raise

    def exponential_backoff(self, retry_count):
        """Calculate exponential backoff with jitter"""
        delay = min(
            self.retry_config.max_delay,
            self.retry_config.initial_delay * (2**retry_count),
        )
        jitter = random.uniform(0, 0.1 * delay)
        return delay + jitter

    def handle_rate_limit(self, operation_name, operation_func, *args, **kwargs):
        """Generic handler for rate-limited operations"""
        retry_count = 0

        while retry_count < self.retry_config.max_retries:
            try:
                return operation_func(*args, **kwargs)
            except HttpResponseError as e:
                if (
                    "TooManyRequests" not in str(e)
                    or retry_count == self.retry_config.max_retries - 1
                ):
                    raise

                retry_count += 1
                delay = self.exponential_backoff(retry_count)
                print(
                    f"\n{operation_name} - Rate limit hit. Attempt {retry_count}/{self.retry_config.max_retries}."
                )
                print(f"Waiting {delay:.2f} seconds before retrying...")
                time.sleep(delay)

        raise Exception(
            f"Max retries ({self.retry_config.max_retries}) exceeded for {operation_name}"
        )

    def search_available_numbers(self):
        """Search for available phone numbers with retry logic"""

        def search_operation():
            capabilities = PhoneNumberCapabilities(
                calling=PhoneNumberCapabilityType.INBOUND_OUTBOUND,
                sms=PhoneNumberCapabilityType.NONE,
            )

            poller = self.phone_numbers_client.begin_search_available_phone_numbers(
                "GB",
                PhoneNumberType.GEOGRAPHIC,
                PhoneNumberAssignmentType.APPLICATION,
                capabilities,
                polling=True,
            )

            search_result = poller.result()
            print(
                f"Search completed successfully! Search ID: {search_result.search_id}"
            )

            if not search_result.phone_numbers:
                self._write_output(success=False, error="No phone numbers found")
                print("No phone numbers found!")
                return None, None

            print("\nAvailable phone numbers:")
            for number in search_result.phone_numbers:
                print(number)

            self.purchased_number = search_result.phone_numbers[0]
            return search_result.search_id, self.purchased_number

        try:
            return self.handle_rate_limit("Search operation", search_operation)
        except Exception as e:
            error_msg = f"Error during search: {str(e)}"
            print(error_msg)
            self._write_output(success=False, error=error_msg)
            return None, None

    def purchase_number(self, search_id, phone_number):
        """Purchase phone number using the search ID with retry logic"""

        def purchase_operation():
            print(f"\nAttempting to purchase number with search ID: {search_id}")
            poller = self.phone_numbers_client.begin_purchase_phone_numbers(
                search_id, polling=True
            )
            result = poller.result()
            status = poller.status().lower()
            print(f"Purchase operation completed result: {result} status: {status}")
            return status == "succeeded"

        try:
            success = self.handle_rate_limit("Purchase operation", purchase_operation)
            if success:
                self._write_output(success=True, phone_number=phone_number)
                return True
            else:
                self._write_output(success=False, error="Purchase operation failed")
                return False
        except Exception as e:
            error_msg = f"Error during purchase: {str(e)}"
            print(error_msg)
            self._write_output(success=False, error=error_msg)
            return False

    def execute_purchase_flow(self):
        """Execute the full search and purchase flow"""
        try:
            # Check for existing number before starting the flow
            existing_number = check_existing_number()
            if existing_number:
                print("Using existing phone number - skipping purchase flow")
                return existing_number

            print("No existing number found. Starting purchase flow...")

            print("Searching for available phone numbers...")
            search_id, phone_number = self.search_available_numbers()

            if not search_id or not phone_number:
                self._write_output(success=False, error="Failed to get search ID")
                return None

            time.sleep(2)  # Short delay between search and purchase

            success = self.purchase_number(search_id, phone_number)
            if success:
                print(f"\nPhone number {phone_number} purchased successfully!")
                return phone_number
            else:
                print("\nFailed to purchase phone number.")
                return None

        except Exception as e:
            error_msg = f"Error in purchase flow: {str(e)}"
            print(error_msg)
            self._write_output(success=False, error=error_msg)
            return None


def main():
    try:
        parser = argparse.ArgumentParser(
            description="Purchase a phone number using Azure Communication Services"
        )
        parser.add_argument(
            "--connection-string",
            required=True,
            help="Azure Communication Services connection string",
        )
        args = parser.parse_args()
        retry_config = RetryConfig(max_retries=5, initial_delay=1, max_delay=32)

        purchaser = PhoneNumberPurchaser(args.connection_string, retry_config)
        purchased_number = purchaser.execute_purchase_flow()

        if purchased_number:
            print(f"Successfully purchased number: {purchased_number}")
        else:
            print("Failed to purchase number")
            exit(1)

    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(error_msg)
        try:
            purchaser._write_output(success=False, error=error_msg)
        except Exception:
            pass
        exit(1)


if __name__ == "__main__":
    main()
