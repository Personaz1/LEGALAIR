#!/usr/bin/env python3
"""
Legal AI Crawler Connectivity Monitor
ΔΣ::Cursor - Continuous connectivity monitoring with Prometheus metrics

Designed for cron execution (hourly), writes connectivity status to Prometheus
textfile collector for alerting when portals become available.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.test_crawler_connectivity import CrawlerConnectivityTest

class ConnectivityMonitor:
    """Monitor crawler connectivity and export Prometheus metrics"""
    
    def __init__(self):
        self.metrics_dir = Path("monitoring/textfile_collector")
        self.metrics_file = self.metrics_dir / "crawler_connectivity.prom"
        self.history_file = Path("logs/connectivity_history.json")
        
        # Ensure directories exist
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def test_connectivity(self) -> dict:
        """Run connectivity tests and return simplified results"""
        tester = CrawlerConnectivityTest()
        
        # Test only key sources for monitoring
        key_sources = ['pravo.gov.ru', 'kad.arbitr.ru']
        results = {}
        
        for source in key_sources:
            print(f"🔍 Testing {source}...")
            
            if source in tester.targets:
                source_result = tester.test_source_connectivity(source)
                
                # Simplify for monitoring
                results[source] = {
                    'status': source_result['overall_status'],
                    'http_success_rate': self._calculate_http_success_rate(source_result),
                    'dns_success': any(r['success'] for r in source_result.get('dns_results', [])),
                    'port_success': any(r['success'] for r in source_result.get('port_results', [])),
                    'last_check': datetime.now().isoformat()
                }
            else:
                results[source] = {
                    'status': 'unknown',
                    'http_success_rate': 0.0,
                    'dns_success': False,
                    'port_success': False,
                    'last_check': datetime.now().isoformat()
                }
        
        return results
    
    def _calculate_http_success_rate(self, source_result: dict) -> float:
        """Calculate HTTP success rate from test results"""
        http_results = source_result.get('http_results', [])
        if not http_results:
            return 0.0
        
        successful = sum(1 for r in http_results if r['success'])
        return successful / len(http_results)
    
    def write_prometheus_metrics(self, results: dict):
        """Write Prometheus metrics to textfile collector format"""
        
        timestamp = int(time.time())
        metrics = []
        
        # Add metric header
        metrics.append("# HELP crawler_connectivity_status Crawler source connectivity status (1=good, 0.5=partial, 0=failed)")
        metrics.append("# TYPE crawler_connectivity_status gauge")
        
        # Connectivity status metrics
        for source, data in results.items():
            status_value = {'good': 1, 'partial': 0.5, 'failed': 0, 'unknown': 0}[data['status']]
            source_label = source.replace('.', '_').replace('-', '_')
            
            metrics.append(f'crawler_connectivity_status{{source="{source}"}} {status_value} {timestamp}')
        
        # HTTP success rate metrics
        metrics.append("")
        metrics.append("# HELP crawler_http_success_rate HTTP request success rate for crawler sources")
        metrics.append("# TYPE crawler_http_success_rate gauge")
        
        for source, data in results.items():
            metrics.append(f'crawler_http_success_rate{{source="{source}"}} {data["http_success_rate"]:.2f} {timestamp}')
        
        # DNS/Port connectivity
        metrics.append("")
        metrics.append("# HELP crawler_dns_success DNS resolution success for crawler sources")
        metrics.append("# TYPE crawler_dns_success gauge")
        
        for source, data in results.items():
            dns_value = 1 if data['dns_success'] else 0
            metrics.append(f'crawler_dns_success{{source="{source}"}} {dns_value} {timestamp}')
        
        metrics.append("")
        metrics.append("# HELP crawler_port_success Port connectivity success for crawler sources")
        metrics.append("# TYPE crawler_port_success gauge")
        
        for source, data in results.items():
            port_value = 1 if data['port_success'] else 0
            metrics.append(f'crawler_port_success{{source="{source}"}} {port_value} {timestamp}')
        
        # Last check timestamp
        metrics.append("")
        metrics.append("# HELP crawler_last_check_timestamp Unix timestamp of last connectivity check")
        metrics.append("# TYPE crawler_last_check_timestamp gauge")
        metrics.append(f'crawler_last_check_timestamp {timestamp}')
        
        # Write metrics file atomically
        temp_file = self.metrics_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            f.write('\n'.join(metrics) + '\n')
        
        temp_file.rename(self.metrics_file)
    
    def update_history(self, results: dict):
        """Update connectivity history for trend analysis"""
        
        # Load existing history
        history = []
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            except Exception:
                history = []
        
        # Add current results
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'results': results
        }
        history.append(history_entry)
        
        # Keep only last 24 hours of data (hourly checks)
        history = history[-24:]
        
        # Save history
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def check_status_changes(self, results: dict) -> list:
        """Check for status changes and return notifications"""
        
        notifications = []
        
        # Load previous results
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                
                if history:
                    previous_results = history[-1]['results']
                    
                    for source, current in results.items():
                        if source in previous_results:
                            previous = previous_results[source]
                            
                            # Check for status improvements
                            if (previous['status'] in ['failed', 'partial'] and 
                                current['status'] == 'good'):
                                notifications.append({
                                    'type': 'recovery',
                                    'source': source,
                                    'message': f"✅ {source} connectivity restored!"
                                })
                            
                            # Check for status degradation
                            elif (previous['status'] == 'good' and 
                                  current['status'] in ['failed', 'partial']):
                                notifications.append({
                                    'type': 'degradation', 
                                    'source': source,
                                    'message': f"⚠️ {source} connectivity degraded"
                                })
            except Exception:
                pass
        
        return notifications
    
    def run_monitoring_cycle(self) -> dict:
        """Run complete monitoring cycle"""
        
        print("🔬 Legal AI Crawler Connectivity Monitor")
        print("=======================================")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test connectivity
        results = self.test_connectivity()
        
        # Check for status changes
        notifications = self.check_status_changes(results)
        
        # Write Prometheus metrics
        self.write_prometheus_metrics(results)
        print(f"📊 Metrics written to: {self.metrics_file}")
        
        # Update history
        self.update_history(results)
        
        # Print summary
        print("\n📋 Current Status:")
        for source, data in results.items():
            status_icon = {'good': '✅', 'partial': '⚠️', 'failed': '❌', 'unknown': '❓'}[data['status']]
            print(f"  {status_icon} {source:20} {data['status'].upper()} (HTTP: {data['http_success_rate']:.0%})")
        
        # Print notifications
        if notifications:
            print("\n🔔 Status Changes:")
            for notif in notifications:
                print(f"  {notif['message']}")
        
        return {
            'results': results,
            'notifications': notifications,
            'metrics_file': str(self.metrics_file),
            'history_updated': True
        }


def main():
    """Main entry point for cron execution"""
    
    monitor = ConnectivityMonitor()
    
    try:
        cycle_result = monitor.run_monitoring_cycle()
        
        # Exit with appropriate code
        failed_sources = [
            source for source, data in cycle_result['results'].items()
            if data['status'] == 'failed'
        ]
        
        if failed_sources:
            print(f"\n⚠️ {len(failed_sources)} source(s) currently unavailable")
            # Don't exit with error for cron - this is expected
            sys.exit(0)  
        else:
            print(f"\n✅ All sources accessible")
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 