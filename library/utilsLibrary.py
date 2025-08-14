import time
import functools
from requests.exceptions import RequestException

class decorators:
  @staticmethod
  def retryRequest(min_wait=1.0,wait_multiplier=2.0,max_retries=3,exceptions=(RequestException)): #Can also add personalised exceptions or others
      """
      Decorator made to retry a request after an amount of time decided by the
      user if the function using the decorator raises a requests exception.
  
      Args:
          min_wait (float): Minimum wait time in seconds between retries.
          wait_multiplier (float): Multiplier for wait time on each retry.
          max_retries (int): Maximum number of retries before giving up.
          exceptions (tuple): Exceptions to catch and retry on. 
          
      """
      def decorator(func):
          @functools.wraps(func)
          def wrapper(*args, **kwargs):
              wait_time = min_wait
              last_exception = None
              for attempt in range(max_retries + 1):
                  try:
                      return func(*args, **kwargs)
                  except exceptions as e:
                      last_exception = e
                      if attempt < max_retries:
                          time.sleep(wait_time)
                          wait_time *= wait_multiplier
                      else:
                          raise
          return wrapper
      return decorator