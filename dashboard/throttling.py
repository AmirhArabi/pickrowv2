from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class ProductCodeCheckThrottle(AnonRateThrottle):
    """
    Throttle for product code verification API
    Limits:
    - 5 requests per minute for anonymous users
    - 10 requests per minute for authenticated users
    """
    rate = '5/minute'  # Default rate for anonymous users
    scope = 'product_code_check'

    def get_cache_key(self, request, view):
        # Use IP address as the cache key
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }

    def allow_request(self, request, view):
        # Check if the request is from a mobile device
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_mobile = any(device in user_agent for device in ['android', 'iphone', 'mobile'])
        
        # Allow more requests for mobile devices
        if is_mobile:
            self.rate = '10/minute'
        else:
            self.rate = '5/minute'
            
        return super().allow_request(request, view) 