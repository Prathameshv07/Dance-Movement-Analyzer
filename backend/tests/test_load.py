"""
Load Testing Script for Dance Movement Analyzer
Tests system performance under various loads
"""

import asyncio
import aiohttp
import time
import statistics
from pathlib import Path
from typing import List, Dict
import json


class LoadTester:
    """Load testing utility for the API"""
    
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url
        self.results: List[Dict] = []
    
    async def upload_video(self, session: aiohttp.ClientSession, video_path: Path) -> Dict:
        """Upload a video and measure response time"""
        start_time = time.time()
        
        try:
            with open(video_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file',
                             f,
                             filename=video_path.name,
                             content_type='video/mp4')
                
                async with session.post(f"{self.base_url}/api/upload", data=data) as response:
                    response_time = time.time() - start_time
                    result = await response.json()
                    
                    return {
                        'endpoint': 'upload',
                        'status': response.status,
                        'response_time': response_time,
                        'success': response.status == 200,
                        'session_id': result.get('session_id') if response.status == 200 else None
                    }
        except Exception as e:
            return {
                'endpoint': 'upload',
                'status': 0,
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }
    
    async def health_check(self, session: aiohttp.ClientSession) -> Dict:
        """Check API health"""
        start_time = time.time()
        
        try:
            async with session.get(f"{self.base_url}/health") as response:
                response_time = time.time() - start_time
                
                return {
                    'endpoint': 'health',
                    'status': response.status,
                    'response_time': response_time,
                    'success': response.status == 200
                }
        except Exception as e:
            return {
                'endpoint': 'health',
                'status': 0,
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }
    
    async def concurrent_uploads(self, video_path: Path, num_concurrent: int = 5):
        """Test concurrent uploads"""
        print(f"\n🔄 Testing {num_concurrent} concurrent uploads...")
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.upload_video(session, video_path) for _ in range(num_concurrent)]
            results = await asyncio.gather(*tasks)
            
            self.results.extend(results)
            
            # Calculate statistics
            response_times = [r['response_time'] for r in results if r['success']]
            success_rate = sum(1 for r in results if r['success']) / len(results) * 100
            
            print(f"\n📊 Results:")
            print(f"   Success Rate: {success_rate:.1f}%")
            if response_times:
                print(f"   Avg Response Time: {statistics.mean(response_times):.2f}s")
                print(f"   Min Response Time: {min(response_times):.2f}s")
                print(f"   Max Response Time: {max(response_times):.2f}s")
                print(f"   Median Response Time: {statistics.median(response_times):.2f}s")
            
            return results
    
    async def stress_test(self, video_path: Path, duration_seconds: int = 60):
        """Stress test by continuously uploading for a duration"""
        print(f"\n⚡ Stress testing for {duration_seconds} seconds...")
        
        start_time = time.time()
        upload_count = 0
        errors = 0
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration_seconds:
                result = await self.upload_video(session, video_path)
                self.results.append(result)
                
                if result['success']:
                    upload_count += 1
                else:
                    errors += 1
                
                # Brief pause between requests
                await asyncio.sleep(0.1)
        
        total_time = time.time() - start_time
        requests_per_second = upload_count / total_time
        
        print(f"\n📊 Stress Test Results:")
        print(f"   Total Requests: {upload_count + errors}")
        print(f"   Successful: {upload_count}")
        print(f"   Failed: {errors}")
        print(f"   Duration: {total_time:.2f}s")
        print(f"   Requests/Second: {requests_per_second:.2f}")
    
    async def latency_test(self, num_requests: int = 100):
        """Test API latency with health checks"""
        print(f"\n⚡ Testing latency with {num_requests} health checks...")
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.health_check(session) for _ in range(num_requests)]
            results = await asyncio.gather(*tasks)
            
            response_times = [r['response_time'] for r in results if r['success']]
            
            if response_times:
                print(f"\n📊 Latency Results:")
                print(f"   Average: {statistics.mean(response_times)*1000:.2f}ms")
                print(f"   Min: {min(response_times)*1000:.2f}ms")
                print(f"   Max: {max(response_times)*1000:.2f}ms")
                print(f"   Median: {statistics.median(response_times)*1000:.2f}ms")
                print(f"   P95: {sorted(response_times)[int(len(response_times)*0.95)]*1000:.2f}ms")
                print(f"   P99: {sorted(response_times)[int(len(response_times)*0.99)]*1000:.2f}ms")
    
    def generate_report(self, output_path: str = "load_test_report.json"):
        """Generate JSON report of test results"""
        
        # Calculate overall statistics
        upload_results = [r for r in self.results if r['endpoint'] == 'upload']
        health_results = [r for r in self.results if r['endpoint'] == 'health']
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_requests': len(self.results),
            'summary': {
                'uploads': {
                    'total': len(upload_results),
                    'successful': sum(1 for r in upload_results if r['success']),
                    'failed': sum(1 for r in upload_results if not r['success']),
                    'avg_response_time': statistics.mean([r['response_time'] for r in upload_results if r['success']]) if upload_results else 0
                },
                'health_checks': {
                    'total': len(health_results),
                    'successful': sum(1 for r in health_results if r['success']),
                    'failed': sum(1 for r in health_results if not r['success']),
                    'avg_response_time': statistics.mean([r['response_time'] for r in health_results if r['success']]) if health_results else 0
                }
            },
            'detailed_results': self.results
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to {output_path}")


async def main():
    """Run load tests"""
    
    print("=" * 60)
    print("🧪 Dance Movement Analyzer - Load Testing")
    print("=" * 60)
    
    # Initialize tester
    tester = LoadTester()
    
    # Check if test video exists
    test_video = Path("sample_videos/test_dance.mp4")
    if not test_video.exists():
        print(f"\n❌ Test video not found: {test_video}")
        print("   Please place a test video in sample_videos/test_dance.mp4")
        return
    
    print(f"\n✅ Using test video: {test_video}")
    print(f"   Size: {test_video.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Test 1: Latency Test
    print("\n" + "="*60)
    print("TEST 1: API Latency")
    print("="*60)
    await tester.latency_test(num_requests=100)
    
    # Test 2: Concurrent Uploads (Light)
    print("\n" + "="*60)
    print("TEST 2: Concurrent Uploads (Light Load)")
    print("="*60)
    await tester.concurrent_uploads(test_video, num_concurrent=3)
    
    # Test 3: Concurrent Uploads (Medium)
    print("\n" + "="*60)
    print("TEST 3: Concurrent Uploads (Medium Load)")
    print("="*60)
    await tester.concurrent_uploads(test_video, num_concurrent=5)
    
    # Test 4: Concurrent Uploads (Heavy)
    print("\n" + "="*60)
    print("TEST 4: Concurrent Uploads (Heavy Load)")
    print("="*60)
    await tester.concurrent_uploads(test_video, num_concurrent=10)
    
    # Test 5: Stress Test (Optional - commented out by default)
    # print("\n" + "="*60)
    # print("TEST 5: Stress Test (60 seconds)")
    # print("="*60)
    # await tester.stress_test(test_video, duration_seconds=60)
    
    # Generate report
    print("\n" + "="*60)
    print("📊 Generating Report")
    print("="*60)
    tester.generate_report()
    
    print("\n✅ Load testing complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
