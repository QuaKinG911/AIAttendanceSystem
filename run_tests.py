#!/usr/bin/env python3
"""
Test runner for AI Attendance System
"""

import sys
import os
import unittest
import subprocess

def run_unit_tests():
    """Run unit tests"""
    print("🧪 Running Unit Tests...")
    result = subprocess.run([
        sys.executable, '-m', 'unittest', 'discover',
        '-s', 'tests', '-p', 'test_components.py', '-v'
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    return result.returncode == 0

def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running Integration Tests...")
    result = subprocess.run([
        sys.executable, '-m', 'unittest', 'discover',
        '-s', 'tests', '-p', 'test_integration.py', '-v'
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    return result.returncode == 0

def run_existing_tests():
    """Run existing test scripts"""
    print("📋 Running Existing Test Scripts...")

    test_scripts = [
        'test_detection.py',
        'test_attendance.py',
        'verify_system.py'
    ]

    results = []
    for script in test_scripts:
        if os.path.exists(script):
            print(f"Running {script}...")
            result = subprocess.run([
                sys.executable, script
            ], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(f"Errors in {script}:", result.stderr)
            results.append(result.returncode == 0)
        else:
            print(f"Test script {script} not found")
            results.append(False)

    return all(results)

def main():
    """Main test runner"""
    print("🚀 AI Attendance System Test Suite")
    print("=" * 50)

    # Change to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # Add src to path
    sys.path.insert(0, os.path.join(project_root, 'src'))

    # Run tests
    unit_passed = run_unit_tests()
    integration_passed = run_integration_tests()
    existing_passed = run_existing_tests()

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"  Unit Tests: {'✅ PASSED' if unit_passed else '❌ FAILED'}")
    print(f"  Integration Tests: {'✅ PASSED' if integration_passed else '❌ FAILED'}")
    print(f"  Existing Tests: {'✅ PASSED' if existing_passed else '❌ FAILED'}")

    overall_success = unit_passed and integration_passed and existing_passed
    print(f"\n🏁 Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")

    return 0 if overall_success else 1

if __name__ == '__main__':
    sys.exit(main())