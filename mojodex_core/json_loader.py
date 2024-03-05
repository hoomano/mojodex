import json
import logging

# This is a wrapper to use any time a GPT call should return a correct JSON.
# It will retry the call if the JSON is not correct or if it does not contain the required keys.
# Use it like this:
# @json_decode_retry(retries=3, required_keys=["key1", "key2"])
# def my_function():
#    # Any code to generate a String result
#   ...
#    ##
#    return result
def json_decode_retry(retries=3, required_keys=None,
                      on_json_error=lambda result, function_name, retries: logging.error(f"Error decoding json of function {function_name} after {retries} retries: {result}")):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for retry in range(retries + 1):
                result = func(*args, **kwargs)
                result = result.strip()
                if result.startswith("```json"):
                    result = result[7:-3]
                elif result.startswith("```"):
                    result = result[3:-3]
                try:
                    # Attempt to decode JSON
                    decoded_json = json.loads(result)

                    # Check for required keys
                    if required_keys:
                        missing_keys = [key for key in required_keys if key not in decoded_json]
                        if missing_keys:
                            raise KeyError(f"Missing required keys: {', '.join(missing_keys)}")

                    return decoded_json
                except Exception as e:
                    if retry < retries:
                        logging.warning(f"{func.__name__} - incorrect JSON - {e} : retrying...")
                    else:
                        on_json_error(result, func.__name__, retries)

        return wrapper
    return decorator
