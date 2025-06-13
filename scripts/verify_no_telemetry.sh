#!/bin/bash
# Verification script to ensure all telemetry has been removed

echo "=== Telemetry Verification Script ==="
echo "Checking for any remaining analytics/telemetry code..."
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

FOUND_ISSUES=0

# Check pubspec.yaml for analytics packages
echo "1. Checking pubspec.yaml for analytics packages..."
if grep -E "(mixpanel|posthog|intercom|instabug|firebase_analytics|firebase_crashlytics)" app/pubspec.yaml 2>/dev/null; then
    echo -e "${RED}✗ Found analytics packages in pubspec.yaml${NC}"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo -e "${GREEN}✓ No analytics packages in pubspec.yaml${NC}"
fi
echo

# Check for analytics imports in Dart files
echo "2. Checking for analytics imports..."
IMPORT_FILES=$(find app/lib -name "*.dart" -exec grep -l "import.*\(mixpanel\|posthog\|intercom\|instabug\|firebase_analytics\)" {} \; 2>/dev/null)
if [ -n "$IMPORT_FILES" ]; then
    echo -e "${RED}✗ Found analytics imports in:${NC}"
    echo "$IMPORT_FILES"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo -e "${GREEN}✓ No analytics imports found${NC}"
fi
echo

# Check for analytics method calls
echo "3. Checking for analytics method calls..."
TRACKING_CALLS=$(grep -r "\.track(" app/lib/ 2>/dev/null | grep -v "privacy_analytics" | grep -v "local_analytics")
if [ -n "$TRACKING_CALLS" ]; then
    echo -e "${RED}✗ Found tracking calls:${NC}"
    echo "$TRACKING_CALLS" | head -5
    echo "..."
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo -e "${GREEN}✓ No tracking calls found${NC}"
fi
echo

# Check for analytics service files
echo "4. Checking for analytics service files..."
SERVICE_FILES="app/lib/services/mixpanel.dart app/lib/services/intercom.dart app/lib/services/instabug.dart"
for file in $SERVICE_FILES; do
    if [ -f "$file" ]; then
        echo -e "${RED}✗ Found: $file${NC}"
        FOUND_ISSUES=$((FOUND_ISSUES + 1))
    fi
done
if [ $FOUND_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ No analytics service files found${NC}"
fi
echo

# Check environment files for analytics keys
echo "5. Checking environment files for analytics keys..."
ENV_KEYS=$(grep -E "(mixpanel|posthog|instabug|intercom).*Token|.*ApiKey" app/lib/env/*.dart 2>/dev/null)
if [ -n "$ENV_KEYS" ]; then
    echo -e "${RED}✗ Found analytics keys in environment files:${NC}"
    echo "$ENV_KEYS"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo -e "${GREEN}✓ No analytics keys in environment files${NC}"
fi
echo

# Check backend requirements.txt
echo "6. Checking backend requirements.txt..."
if [ -f "backend/requirements.txt" ]; then
    BACKEND_ANALYTICS=$(grep -E "(mixpanel|sentry|segment|analytics|posthog)" backend/requirements.txt 2>/dev/null)
    if [ -n "$BACKEND_ANALYTICS" ]; then
        echo -e "${YELLOW}⚠ Found potential analytics packages in backend:${NC}"
        echo "$BACKEND_ANALYTICS"
        echo -e "${YELLOW}Note: Manual review needed for backend${NC}"
    else
        echo -e "${GREEN}✓ No obvious analytics packages in backend requirements${NC}"
    fi
else
    echo -e "${YELLOW}⚠ backend/requirements.txt not found${NC}"
fi
echo

# Summary
echo "=== Summary ==="
if [ $FOUND_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ No telemetry issues found in Flutter app!${NC}"
    echo -e "${YELLOW}Note: Backend still needs manual review${NC}"
else
    echo -e "${RED}✗ Found $FOUND_ISSUES telemetry issues that need attention${NC}"
    echo "Run './scripts/remove_telemetry.py' to remove telemetry"
fi
echo

# Optional: Check for network calls (requires running app)
echo "=== Additional Checks ==="
echo "To verify no network calls to analytics services:"
echo "1. Run the app with a network proxy (Charles, Proxyman, etc.)"
echo "2. Check for requests to:"
echo "   - api.mixpanel.com"
echo "   - api.posthog.com"
echo "   - api.intercom.io"
echo "   - api.instabug.com"
echo "   - firebase/google analytics endpoints"