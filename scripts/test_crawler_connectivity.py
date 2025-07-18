#!/usr/bin/env python3
"""
Legal AI Crawler Connectivity Test
ΔΣ::Cursor - Diagnose connection issues with crawler targets

Tests network connectivity, DNS resolution, HTTP responses,
and crawler-specific requirements for all target sources.
"""

import sys
import socket
import requests
import time
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class CrawlerConnectivityTest:
    """Test connectivity to crawler target sources"""
    
    def __init__(self):
        self.targets = {
            'pravo.gov.ru': {
                'urls': [
                    'https://publication.pravo.gov.ru',
                    'https://publication.pravo.gov.ru/documents',
                    'https://publication.pravo.gov.ru/SignatoryAuthority/fz',
                ],
                'expected_status': [200, 403],  # 403 might be normal for anti-bot
                'required_headers': ['content-type'],
                'timeout': 15
            },
            'kad.arbitr.ru': {
                'urls': [
                    'https://kad.arbitr.ru',
                    'https://kad.arbitr.ru/Card',
                ],
                'expected_status': [200, 403, 503],
                'required_headers': ['content-type'],
                'timeout': 20
            },
            'gibdd.ru': {
                'urls': [
                    'https://gibdd.ru',
                    'https://forms.gibdd.ru',
                ],
                'expected_status': [200, 403],
                'required_headers': ['content-type'],
                'timeout': 15
            }
        }
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Legal-AI-Crawler/1.0 (+https://legal-ai.com/bot)',
        ]
    
    def test_dns_resolution(self, domain: str) -> Tuple[bool, str]:
        """Test DNS resolution for domain"""
        try:
            ip = socket.gethostbyname(domain)
            return True, f"✅ DNS: {domain} → {ip}"
        except socket.gaierror as e:
            return False, f"❌ DNS: {domain} → {e}"
    
    def test_port_connectivity(self, domain: str, port: int, timeout: int = 5) -> Tuple[bool, str]:
        """Test TCP connectivity to specific port"""
        try:
            sock = socket.create_connection((domain, port), timeout)
            sock.close()
            return True, f"✅ PORT: {domain}:{port} is reachable"
        except (socket.timeout, socket.error) as e:
            return False, f"❌ PORT: {domain}:{port} → {e}"
    
    def test_http_request(self, url: str, user_agent: str, timeout: int = 15) -> Tuple[bool, str, Dict]:
        """Test HTTP request to URL"""
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru,en',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            
            result_info = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'response_time': response.elapsed.total_seconds(),
                'final_url': response.url,
                'content_length': len(response.content),
                'encoding': response.encoding
            }
            
            if response.status_code in [200, 403, 503]:
                return True, f"✅ HTTP: {url} → {response.status_code} ({response.elapsed.total_seconds():.2f}s)", result_info
            else:
                return False, f"❌ HTTP: {url} → {response.status_code}", result_info
                
        except requests.exceptions.RequestException as e:
            return False, f"❌ HTTP: {url} → {e}", {}
    
    def test_robots_txt(self, base_url: str) -> Tuple[bool, str]:
        """Test robots.txt accessibility"""
        robots_url = f"{base_url.rstrip('/')}/robots.txt"
        
        try:
            response = requests.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                # Check for crawler restrictions
                content = response.text.lower()
                if 'crawl-delay' in content:
                    delay_match = [line for line in content.split('\n') if 'crawl-delay' in line]
                    return True, f"✅ ROBOTS: Found robots.txt with crawl delay: {delay_match[0] if delay_match else 'unknown'}"
                else:
                    return True, f"✅ ROBOTS: Found robots.txt (no specific crawl delay)"
            else:
                return True, f"⚠️ ROBOTS: robots.txt not found (will proceed)"
                
        except Exception as e:
            return True, f"⚠️ ROBOTS: Could not fetch robots.txt ({e})"
    
    def test_source_connectivity(self, source_name: str) -> Dict:
        """Test connectivity for a specific source"""
        print(f"\n🔍 Testing {source_name}")
        print("=" * 50)
        
        config = self.targets.get(source_name, {})
        urls = config.get('urls', [])
        timeout = config.get('timeout', 15)
        
        results = {
            'source': source_name,
            'overall_status': 'unknown',
            'dns_results': [],
            'port_results': [],
            'http_results': [],
            'robots_results': [],
            'recommendations': []
        }
        
        # Extract domains for DNS testing
        domains = list(set(urlparse(url).netloc for url in urls))
        
        # DNS tests
        print("📡 DNS Resolution:")
        dns_success = 0
        for domain in domains:
            success, message = self.test_dns_resolution(domain)
            print(f"  {message}")
            results['dns_results'].append({'domain': domain, 'success': success, 'message': message})
            if success:
                dns_success += 1
        
        # Port connectivity tests
        print("\n🔌 Port Connectivity:")
        port_success = 0
        for domain in domains:
            # Test HTTPS (443) and HTTP (80)
            for port in [443, 80]:
                success, message = self.test_port_connectivity(domain, port, 5)
                print(f"  {message}")
                results['port_results'].append({'domain': domain, 'port': port, 'success': success, 'message': message})
                if success:
                    port_success += 1
        
        # HTTP tests with different user agents
        print("\n🌐 HTTP Requests:")
        http_success = 0
        for url in urls:
            for i, user_agent in enumerate(self.user_agents):
                ua_label = "Browser" if i == 0 else "Crawler"
                success, message, info = self.test_http_request(url, user_agent, timeout)
                print(f"  [{ua_label}] {message}")
                
                results['http_results'].append({
                    'url': url,
                    'user_agent_type': ua_label,
                    'success': success,
                    'message': message,
                    'info': info
                })
                
                if success:
                    http_success += 1
                
                # Delay between requests
                time.sleep(1)
        
        # Robots.txt tests
        print("\n🤖 Robots.txt:")
        for url in urls[:1]:  # Test only base URL
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            success, message = self.test_robots_txt(base_url)
            print(f"  {message}")
            results['robots_results'].append({'url': base_url, 'success': success, 'message': message})
        
        # Determine overall status and recommendations
        total_tests = len(results['http_results'])
        success_rate = http_success / total_tests if total_tests > 0 else 0
        
        if success_rate >= 0.5:
            results['overall_status'] = 'good'
        elif success_rate >= 0.25:
            results['overall_status'] = 'partial'
        else:
            results['overall_status'] = 'failed'
        
        # Generate recommendations
        if dns_success == 0:
            results['recommendations'].append("❌ DNS resolution failed - check internet connection")
        
        if port_success == 0:
            results['recommendations'].append("❌ Port connectivity failed - check firewall/proxy settings")
        
        if http_success == 0:
            results['recommendations'].append("❌ All HTTP requests failed - server may be blocking requests")
        elif success_rate < 0.5:
            results['recommendations'].append("⚠️ Partial connectivity - try different user agents or delays")
        
        # Check for user agent differences
        browser_success = sum(1 for r in results['http_results'] if r['user_agent_type'] == 'Browser' and r['success'])
        crawler_success = sum(1 for r in results['http_results'] if r['user_agent_type'] == 'Crawler' and r['success'])
        
        if browser_success > crawler_success:
            results['recommendations'].append("🤖 Server prefers browser user agents - adjust crawler headers")
        
        print(f"\n📊 Summary: {results['overall_status'].upper()} ({success_rate:.1%} success rate)")
        
        return results
    
    def run_full_test(self) -> Dict:
        """Run connectivity tests for all sources"""
        print("🕷️ Legal AI Crawler Connectivity Test")
        print("=====================================")
        
        all_results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'sources': {},
            'overall_recommendations': []
        }
        
        for source_name in self.targets.keys():
            results = self.test_source_connectivity(source_name)
            all_results['sources'][source_name] = results
        
        # Generate overall recommendations
        failed_sources = [name for name, result in all_results['sources'].items() 
                         if result['overall_status'] == 'failed']
        
        if failed_sources:
            all_results['overall_recommendations'].append(
                f"❌ Failed sources: {', '.join(failed_sources)} - check network/firewall"
            )
        
        partial_sources = [name for name, result in all_results['sources'].items() 
                          if result['overall_status'] == 'partial']
        
        if partial_sources:
            all_results['overall_recommendations'].append(
                f"⚠️ Partial sources: {', '.join(partial_sources)} - adjust crawler settings"
            )
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎯 OVERALL CONNECTIVITY SUMMARY")
        print("=" * 60)
        
        for source_name, result in all_results['sources'].items():
            status_icon = {"good": "✅", "partial": "⚠️", "failed": "❌"}[result['overall_status']]
            print(f"{status_icon} {source_name:20} {result['overall_status'].upper()}")
        
        print("\n📋 RECOMMENDATIONS:")
        for source_name, result in all_results['sources'].items():
            if result['recommendations']:
                print(f"\n{source_name}:")
                for rec in result['recommendations']:
                    print(f"  {rec}")
        
        if all_results['overall_recommendations']:
            print(f"\nGeneral:")
            for rec in all_results['overall_recommendations']:
                print(f"  {rec}")
        
        return all_results


def main():
    """Main entry point"""
    print("🔬 Testing crawler connectivity...")
    
    tester = CrawlerConnectivityTest()
    results = tester.run_full_test()
    
    # Save results
    results_file = Path("logs/connectivity_test.json")
    results_file.parent.mkdir(exist_ok=True)
    
    import json
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    # Exit code based on overall success
    failed_count = sum(1 for result in results['sources'].values() 
                      if result['overall_status'] == 'failed')
    
    if failed_count == 0:
        print("\n✅ All connectivity tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {failed_count} source(s) failed connectivity tests")
        sys.exit(1)


if __name__ == '__main__':
    main() 