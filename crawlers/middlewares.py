import random
import time
from typing import Union, Optional

from scrapy import signals
from scrapy.http import Request, Response
from scrapy.spiders import Spider
from scrapy.downloadermiddlewares.retry import RetryMiddleware as BaseRetryMiddleware
from scrapy.exceptions import NotConfigured, IgnoreRequest


class RetryMiddleware(BaseRetryMiddleware):
    """Enhanced retry middleware with exponential backoff"""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.max_retry_times = settings.getint('RETRY_TIMES', 3)
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST', -1)
        
        # Exponential backoff settings
        self.base_delay = settings.getfloat('RETRY_BASE_DELAY', 1.0)
        self.max_delay = settings.getfloat('RETRY_MAX_DELAY', 60.0)
        self.backoff_factor = settings.getfloat('RETRY_BACKOFF_FACTOR', 2.0)
    
    def process_response(self, request: Request, response: Response, spider: Spider) -> Union[Request, Response]:
        """Process response and retry if needed"""
        
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        
        return response
    
    def process_exception(self, request: Request, exception: Exception, spider: Spider) -> Optional[Request]:
        """Process exception and retry if appropriate"""
        
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            return self._retry(request, exception, spider)
        
        return None
    
    def _retry(self, request: Request, reason: Union[str, Exception], spider: Spider) -> Optional[Request]:
        """Retry request with exponential backoff"""
        
        retry_times = request.meta.get('retry_times', 0) + 1
        
        if retry_times <= self.max_retry_times:
            # Calculate delay with exponential backoff
            delay = min(
                self.base_delay * (self.backoff_factor ** (retry_times - 1)),
                self.max_delay
            )
            
            # Add some randomization to avoid thundering herd
            delay = delay * (0.5 + random.random() * 0.5)
            
            spider.logger.info(
                f"Retrying {request.url} (attempt {retry_times}/{self.max_retry_times}) "
                f"after {delay:.1f}s delay. Reason: {reason}"
            )
            
            # Sleep before retry
            time.sleep(delay)
            
            # Create retry request
            retry_request = request.copy()
            retry_request.meta['retry_times'] = retry_times
            retry_request.priority = request.priority + self.priority_adjust
            retry_request.dont_filter = True
            
            return retry_request
        
        else:
            spider.logger.error(
                f"Gave up retrying {request.url} after {retry_times} attempts. "
                f"Final reason: {reason}"
            )
            return None


class UserAgentMiddleware:
    """Rotate user agents for better stealth"""
    
    def __init__(self, settings):
        self.user_agents = [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            
            # Safari on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            
            # Chrome on Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            
            # Legal-specific user agent
            'Legal-AI-Crawler/1.0 (+https://legal-ai.com/bot)',
        ]
        
        # Filter to legal-specific if configured
        if settings.getbool('USER_AGENT_LEGAL_ONLY', False):
            self.user_agents = [ua for ua in self.user_agents if 'Legal-AI-Crawler' in ua]
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler"""
        if not crawler.settings.getbool('USER_AGENT_ROTATION_ENABLED', True):
            raise NotConfigured('User agent rotation disabled')
        
        return cls(crawler.settings)
    
    def process_request(self, request: Request, spider: Spider) -> None:
        """Set random user agent for request"""
        
        # Skip if user agent already set specifically
        if 'User-Agent' in request.headers:
            return
        
        # Select random user agent
        user_agent = random.choice(self.user_agents)
        request.headers['User-Agent'] = user_agent
        
        spider.logger.debug(f"Set User-Agent: {user_agent}")


class ProxyPoolMiddleware:
    """Advanced proxy pool middleware for bypassing geo-restrictions"""
    
    def __init__(self, settings):
        self.proxy_pools = {}
        self.current_proxies = {}
        self.proxy_stats = {}
        self.enabled = settings.getbool('PROXY_POOL_ENABLED', False)
        
        if self.enabled:
            self._load_proxy_config(settings.get('PROXY_POOL_CONFIG', 'crawler_proxy_pool.json'))
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler"""
        return cls(crawler.settings)
    
    def _load_proxy_config(self, config_file: str):
        """Load proxy pool configuration"""
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Load proxy pools by priority
            for pool_name, pool_config in config['proxy_pools'].items():
                self.proxy_pools[pool_name] = {
                    'proxies': pool_config['proxies'],
                    'priority': pool_config['priority'],
                    'timeout': pool_config.get('timeout', 15),
                    'current_index': 0,
                    'failures': 0
                }
            
            # Sort pools by priority
            self.proxy_pools = dict(sorted(
                self.proxy_pools.items(), 
                key=lambda x: x[1]['priority']
            ))
            
        except Exception as e:
            print(f"Warning: Failed to load proxy config: {e}")
            self.enabled = False
    
    def process_request(self, request: Request, spider: Spider) -> None:
        """Set proxy for request based on pool configuration"""
        
        if not self.enabled:
            return
        
        # Skip if proxy already set
        if 'proxy' in request.meta:
            return
        
        # Get next proxy from pool
        proxy_info = self._get_next_proxy(spider)
        
        if proxy_info:
            request.meta['proxy'] = proxy_info['url']
            
            # Set authentication if needed
            if proxy_info.get('auth'):
                auth = proxy_info['auth']
                if auth['username'] and auth['password']:
                    import base64
                    auth_string = f"{auth['username']}:{auth['password']}"
                    auth_bytes = base64.b64encode(auth_string.encode()).decode()
                    request.headers['Proxy-Authorization'] = f'Basic {auth_bytes}'
            
            # Track proxy usage
            proxy_url = proxy_info['url']
            if proxy_url not in self.proxy_stats:
                self.proxy_stats[proxy_url] = {'requests': 0, 'failures': 0, 'successes': 0}
            
            self.proxy_stats[proxy_url]['requests'] += 1
            
            spider.logger.debug(f"Using proxy: {proxy_url}")
    
    def _get_next_proxy(self, spider: Spider) -> Optional[dict]:
        """Get next available proxy from pool"""
        
        for pool_name, pool_config in self.proxy_pools.items():
            proxies = pool_config['proxies']
            
            # Skip pools with too many failures
            if pool_config['failures'] > 5:
                continue
            
            # Get next proxy in rotation
            current_index = pool_config['current_index']
            
            if current_index < len(proxies):
                proxy = proxies[current_index]
                
                # Update index for next request
                pool_config['current_index'] = (current_index + 1) % len(proxies)
                
                return proxy
        
        return None
    
    def process_response(self, request: Request, response: Response, spider: Spider) -> Union[Request, Response]:
        """Process response and update proxy statistics"""
        
        if not self.enabled:
            return response
        
        proxy_url = request.meta.get('proxy')
        if proxy_url and proxy_url in self.proxy_stats:
            
            if response.status in [200, 403]:  # Success or expected block
                self.proxy_stats[proxy_url]['successes'] += 1
            else:
                self.proxy_stats[proxy_url]['failures'] += 1
                
                # Mark pool as failed if too many failures
                self._update_pool_failures(proxy_url)
        
        return response
    
    def process_exception(self, request: Request, exception: Exception, spider: Spider) -> Optional[Request]:
        """Process exception and retry with different proxy"""
        
        if not self.enabled:
            return None
        
        proxy_url = request.meta.get('proxy')
        if proxy_url and proxy_url in self.proxy_stats:
            self.proxy_stats[proxy_url]['failures'] += 1
            self._update_pool_failures(proxy_url)
        
        # Retry with different proxy
        retry_count = request.meta.get('proxy_retry_count', 0)
        if retry_count < 3:
            new_proxy = self._get_next_proxy(spider)
            if new_proxy:
                retry_request = request.copy()
                retry_request.meta['proxy'] = new_proxy['url']
                retry_request.meta['proxy_retry_count'] = retry_count + 1
                retry_request.dont_filter = True
                
                spider.logger.info(f"Retrying with different proxy: {new_proxy['url']}")
                return retry_request
        
        return None
    
    def _update_pool_failures(self, proxy_url: str):
        """Update pool failure count"""
        for pool_name, pool_config in self.proxy_pools.items():
            for proxy in pool_config['proxies']:
                if proxy['url'] == proxy_url:
                    pool_config['failures'] += 1
                    break


class RobotsTxtMiddleware:
    """Enhanced robots.txt compliance"""
    
    def __init__(self, settings):
        self.respect_robots = settings.getbool('ROBOTSTXT_OBEY', True)
        self.custom_rules = settings.getdict('ROBOTSTXT_CUSTOM_RULES', {})
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler"""
        return cls(crawler.settings)
    
    def process_request(self, request: Request, spider: Spider) -> Optional[Request]:
        """Check robots.txt compliance"""
        
        if not self.respect_robots:
            return None
        
        # Add custom robots.txt checking logic here
        # For now, just log compliance
        spider.logger.debug(f"Checking robots.txt compliance for: {request.url}")
        
        return None


def response_status_message(status: int) -> str:
    """Get human-readable status message"""
    
    status_messages = {
        400: 'Bad Request',
        401: 'Unauthorized', 
        403: 'Forbidden',
        404: 'Not Found',
        408: 'Request Timeout',
        429: 'Too Many Requests',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable',
        504: 'Gateway Timeout',
    }
    
    return status_messages.get(status, f'HTTP {status}') 