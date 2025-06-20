#!/bin/bash
# Run all tests

echo "Running all tests..."
echo "=================="

# Activate virtual environment
source venv/bin/activate

# Run basic functionality tests
echo "1. Basic functionality tests:"
python -m unittest tests.test_basic_functionality -v
BASIC_RESULT=$?

# Run existing unit tests
echo -e "\n2. All unit tests:"
python -m unittest discover tests -v
ALL_RESULT=$?

# Summary
echo -e "\n=================="
echo "Test Summary:"
echo "=================="

if [ $BASIC_RESULT -eq 0 ]; then
    echo "✅ Basic functionality: PASSED"
else
    echo "❌ Basic functionality: FAILED"
fi

if [ $ALL_RESULT -eq 0 ]; then
    echo "✅ All unit tests: PASSED"
else
    echo "❌ All unit tests: FAILED"
fi

# Exit with failure if any tests failed
if [ $BASIC_RESULT -ne 0 ] || [ $ALL_RESULT -ne 0 ]; then
    exit 1
fi

echo -e "\n🎉 All tests passed!"
exit 0