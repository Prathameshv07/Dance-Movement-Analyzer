"""
Master Test Runner for Dance Movement Analyzer
Runs all test suites and generates comprehensive reports
"""

import subprocess
import sys
import os
from pathlib import Path
import time
import json


class TestRunner:
    """Orchestrate all test suites"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70 + "\n")
    
    def run_command(self, command, description):
        """Run a shell command and capture output"""
        print(f"🔄 {description}...")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            
            if success:
                print(f"✅ {description} - PASSED\n")
            else:
                print(f"❌ {description} - FAILED\n")
                if result.stderr:
                    print(f"Error output:\n{result.stderr[:500]}\n")
            
            return {
                'success': success,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            print(f"⏱️ {description} - TIMEOUT\n")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Test timeout after 5 minutes'
            }
        except Exception as e:
            print(f"❌ {description} - ERROR: {str(e)}\n")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
    
    def run_unit_tests(self):
        """Run unit tests from Phase 1 & 2"""
        self.print_header("PHASE 1 & 2: Unit Tests")
        
        # Pose analyzer tests
        result1 = self.run_command(
            "pytest tests/test_pose_analyzer.py -v --tb=short",
            "Pose Analyzer Tests"
        )
        self.results['pose_analyzer_tests'] = result1
        
        # Movement classifier tests
        result2 = self.run_command(
            "pytest tests/test_movement_classifier.py -v --tb=short",
            "Movement Classifier Tests"
        )
        self.results['movement_classifier_tests'] = result2
        
        return result1['success'] and result2['success']
    
    def run_api_tests(self):
        """Run API tests from Phase 3"""
        self.print_header("PHASE 3: API Tests")
        
        result = self.run_command(
            "pytest tests/test_api.py -v --tb=short",
            "API Endpoint Tests"
        )
        self.results['api_tests'] = result
        
        return result['success']
    
    def run_integration_tests(self):
        """Run integration tests from Phase 5"""
        self.print_header("PHASE 5: Integration Tests")
        
        result = self.run_command(
            "pytest tests/test_integration.py -v --tb=short",
            "Integration Tests"
        )
        self.results['integration_tests'] = result
        
        return result['success']
    
    def run_coverage_report(self):
        """Generate code coverage report"""
        self.print_header("Code Coverage Analysis")
        
        result = self.run_command(
            "pytest tests/ --cov=app --cov-report=html --cov-report=term",
            "Coverage Analysis"
        )
        self.results['coverage'] = result
        
        if result['success']:
            print("📊 Coverage report generated: htmlcov/index.html")
        
        return result['success']
    
    def check_code_quality(self):
        """Check code quality with flake8 (optional)"""
        self.print_header("Code Quality Check")
        
        # Check if flake8 is installed
        try:
            subprocess.run(['flake8', '--version'], capture_output=True, check=True)
            has_flake8 = True
        except:
            has_flake8 = False
        
        if has_flake8:
            result = self.run_command(
                "flake8 app/ --max-line-length=100 --ignore=E501,W503",
                "Code Quality (flake8)"
            )
            self.results['code_quality'] = result
        else:
            print("⚠️  flake8 not installed - skipping code quality check")
            print("   Install with: pip install flake8\n")
            self.results['code_quality'] = {'success': True, 'skipped': True}
    
    def generate_summary(self):
        """Generate test summary"""
        self.print_header("TEST SUMMARY")
        
        total_tests = len([k for k in self.results.keys() if not k.endswith('_skipped')])
        passed_tests = sum(1 for v in self.results.values() if v.get('success', False))
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Test Suites: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%\n")
        
        # Individual results
        status_emoji = {True: "✅", False: "❌"}
        
        print("Detailed Results:")
        print("-" * 50)
        for test_name, result in self.results.items():
            if result.get('skipped'):
                print(f"⚠️  {test_name}: SKIPPED")
            else:
                status = status_emoji.get(result.get('success', False), "❓")
                print(f"{status} {test_name}: {'PASSED' if result.get('success') else 'FAILED'}")
        
        print("\n" + "-" * 50)
        
        # Execution time
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            print(f"\n⏱️  Total Execution Time: {duration:.2f} seconds")
        
        # Overall status
        all_passed = failed_tests == 0
        print("\n" + "="*70)
        if all_passed:
            print("🎉 ALL TESTS PASSED! System is production-ready.")
        else:
            print(f"⚠️  {failed_tests} test suite(s) failed. Review logs above.")
        print("="*70 + "\n")
        
        return all_passed
    
    def save_report(self, filename="test_report.json"):
        """Save detailed test report to JSON"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'execution_time': self.end_time - self.start_time if self.start_time else 0,
            'results': {}
        }
        
        for test_name, result in self.results.items():
            report['results'][test_name] = {
                'success': result.get('success', False),
                'skipped': result.get('skipped', False),
                'returncode': result.get('returncode', 0)
            }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Detailed report saved to {filename}\n")
    
    def run_all(self):
        """Run all test suites"""
        print("\n" + "="*70)
        print("  🧪 DANCE MOVEMENT ANALYZER - COMPREHENSIVE TEST SUITE")
        print("="*70)
        
        self.start_time = time.time()
        
        # Check if we're in the right directory
        if not Path("app").exists():
            print("\n❌ Error: 'app' directory not found.")
            print("   Please run this script from the backend/ directory.\n")
            return False
        
        # Check if tests directory exists
        if not Path("tests").exists():
            print("\n❌ Error: 'tests' directory not found.")
            print("   Please ensure test files are in the tests/ directory.\n")
            return False
        
        print(f"\n🔍 Test environment:")
        print(f"   Python: {sys.version.split()[0]}")
        print(f"   Working directory: {os.getcwd()}")
        print(f"   Test directory: {Path('tests').absolute()}")
        
        # Run all test suites
        results = []
        
        # Phase 1 & 2: Unit Tests
        results.append(self.run_unit_tests())
        
        # Phase 3: API Tests
        results.append(self.run_api_tests())
        
        # Phase 5: Integration Tests
        results.append(self.run_integration_tests())
        
        # Coverage Report
        self.run_coverage_report()
        
        # Code Quality (optional)
        self.check_code_quality()
        
        self.end_time = time.time()
        
        # Generate summary
        all_passed = self.generate_summary()
        
        # Save detailed report
        self.save_report()
        
        return all_passed


def main():
    """Main entry point"""
    
    # Change to backend directory if not already there
    if Path("backend").exists() and not Path("app").exists():
        os.chdir("backend")
        print("📁 Changed directory to: backend/")
    
    runner = TestRunner()
    success = runner.run_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()