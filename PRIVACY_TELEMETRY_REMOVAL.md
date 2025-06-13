# Telemetry Removal Guide for Privacy-Focused OMI Fork

## Overview

This document outlines the complete removal of telemetry from the OMI (Friend) codebase, with a focus on the macOS desktop application. While the desktop app already disables most analytics by default, we'll remove all telemetry code entirely for a truly privacy-focused fork.

## Current Telemetry Status

### Desktop (macOS/Windows)
- **Mixpanel**: Disabled via platform check
- **Intercom**: Disabled via platform check  
- **Instabug**: Disabled via platform check
- **PostHog**: Still active (needs removal)

### Services to Remove

1. **Mixpanel** (User behavior analytics)
   - Package: `mixpanel_flutter: ^2.3.2`
   - Integration: `/app/lib/services/mixpanel.dart`

2. **PostHog** (Product analytics)
   - Package: `posthog_flutter: ^4.4.2`
   - Integration: `/app/lib/env/prod_env.dart`, `/app/lib/env/dev_env.dart`

3. **Intercom** (Customer support)
   - Package: `intercom_flutter: ^8.1.2`
   - Integration: `/app/lib/services/intercom.dart`

4. **Instabug** (Bug reporting)
   - Package: `instabug_flutter: ^13.4.1`
   - Integration: `/app/lib/services/instabug.dart`

5. **Firebase** (If present)
   - Analytics, Crashlytics, Performance monitoring

## Phase 1: Mobile App Telemetry Removal

### Step 1: Remove Dependencies

Edit `/app/pubspec.yaml`:

```yaml
# Remove these lines:
  mixpanel_flutter: ^2.3.2
  posthog_flutter: ^4.4.2
  intercom_flutter: ^8.1.2
  instabug_flutter: ^13.4.1
  # Also remove any Firebase analytics packages if present
```

### Step 2: Remove Service Files

Delete these files:
- `/app/lib/services/mixpanel.dart`
- `/app/lib/services/intercom.dart`
- `/app/lib/services/instabug.dart`

### Step 3: Clean Environment Configuration

#### In `/app/lib/env/dev_env.dart`:
```dart
// Remove:
static const String? instabugApiKeyAndroid = null;
static const String? instabugApiKeyIos = null;
static const String? mixpanelProjectToken = null;
static const String? posthogApiKey = null;
static const String? posthogHostUrl = null;
```

#### In `/app/lib/env/prod_env.dart`:
```dart
// Remove all analytics-related environment variables
```

### Step 4: Update main.dart

Remove all analytics initialization:

```dart
// Remove these imports:
import 'package:posthog_flutter/posthog_flutter.dart';
import 'services/instabug.dart';
import 'services/intercom.dart';
import 'services/mixpanel.dart';

// In main() function, remove:
if (ProdEnv.posthogApiKey.isNotEmpty) {
  unawaited(Posthog().init(...));
}

// Remove from initializeApp():
MixpanelManager.init();
IntercomManager.init();
await InstabugWrapper.init();
```

### Step 5: Remove Analytics Calls

Search and remove all analytics tracking calls throughout the codebase:

```bash
# Find all analytics calls
grep -r "MixpanelManager\." app/lib/
grep -r "IntercomManager\." app/lib/
grep -r "InstabugManager\." app/lib/
grep -r "Posthog\." app/lib/
```

Common patterns to remove:
- `MixpanelManager().track(...)`
- `MixpanelManager().setUserProperty(...)`
- `IntercomManager.instance.displayMessenger()`
- `InstabugWrapper.logEvent(...)`

### Step 6: Update Settings

Remove analytics preferences from:
- `/app/lib/pages/settings/privacy_settings_page.dart`
- Remove `optInAnalytics` from SharedPreferencesUtil

## Phase 2: Backend Telemetry Removal

### Step 1: Identify Backend Analytics

Common services to look for:
- Mixpanel API calls
- Google Analytics
- Segment
- Custom logging to external services
- Sentry error tracking

### Step 2: Remove Python Dependencies

Edit `/backend/requirements.txt`:
```bash
# Remove lines for:
# mixpanel
# sentry-sdk
# segment-analytics-python
# google-analytics-python
```

### Step 3: Remove Analytics Middleware

Check and clean:
- `/backend/main.py`
- `/backend/middleware/`
- All routers in `/backend/routers/`

### Step 4: Environment Variables

Remove from `.env` files:
- `MIXPANEL_TOKEN`
- `SENTRY_DSN`
- `SEGMENT_WRITE_KEY`
- Any other analytics tokens

## Phase 3: Privacy-Focused Replacements

### Local Analytics (Optional)

If usage metrics are needed for development:

```dart
// Create local_analytics.dart
class LocalAnalytics {
  static final _events = <String, dynamic>{};
  
  static void track(String event, [Map<String, dynamic>? properties]) {
    if (kDebugMode) {
      print('[LOCAL] Event: $event, Properties: $properties');
    }
    // Store locally if needed, never transmit
  }
}
```

### Error Logging

Replace crash reporting with local logging:

```dart
// local_error_logger.dart
class LocalErrorLogger {
  static void logError(dynamic error, StackTrace? stack) {
    // Log to local file
    final timestamp = DateTime.now().toIso8601String();
    final log = '$timestamp: $error\n$stack\n\n';
    // Write to app documents directory
  }
}
```

## Phase 4: Verification

### Automated Checks

Create verification script:

```bash
#!/bin/bash
# verify_no_telemetry.sh

echo "Checking for telemetry packages..."
grep -E "(mixpanel|posthog|intercom|instabug|analytics)" app/pubspec.yaml

echo "Checking for telemetry imports..."
find app/lib -name "*.dart" -exec grep -l "import.*mixpanel\|posthog\|intercom\|instabug" {} \;

echo "Checking for tracking calls..."
grep -r "\.track(" app/lib/ | grep -v "local_analytics"

echo "Checking backend requirements..."
grep -E "(mixpanel|sentry|segment|analytics)" backend/requirements.txt
```

### Network Monitoring

Test the app with network monitoring:
1. Run the app with Charles Proxy or similar
2. Verify no requests to:
   - api.mixpanel.com
   - api.posthog.com
   - api.intercom.io
   - api.instabug.com
   - Any analytics endpoints

## Phase 5: Documentation

### Update README

Add privacy section:

```markdown
## Privacy Features

This fork removes all telemetry and analytics:
- ✅ No usage tracking
- ✅ No crash reporting to external services
- ✅ No behavioral analytics
- ✅ All data stays local
- ✅ No third-party analytics SDKs
```

### Create PRIVACY.md

Document privacy stance and removed services.

## Migration Script

Create an automated removal script:

```python
#!/usr/bin/env python3
# remove_telemetry.py

import os
import re
import fileinput

def remove_from_pubspec():
    """Remove analytics dependencies from pubspec.yaml"""
    analytics_packages = [
        'mixpanel_flutter',
        'posthog_flutter', 
        'intercom_flutter',
        'instabug_flutter'
    ]
    
    with fileinput.FileInput('app/pubspec.yaml', inplace=True) as file:
        for line in file:
            if not any(pkg in line for pkg in analytics_packages):
                print(line, end='')

def remove_imports(directory):
    """Remove analytics imports from Dart files"""
    analytics_imports = [
        r"import.*mixpanel",
        r"import.*posthog",
        r"import.*intercom",
        r"import.*instabug"
    ]
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.dart'):
                filepath = os.path.join(root, file)
                # Remove imports and update file
                
def main():
    print("Starting telemetry removal...")
    remove_from_pubspec()
    remove_imports('app/lib')
    print("Telemetry removal complete!")
    
if __name__ == "__main__":
    main()
```

## Next Steps

1. Run the removal process
2. Test thoroughly on macOS
3. Verify no network calls to analytics services
4. Update documentation
5. Create privacy-focused announcement

---

*This is a living document. Update as new telemetry is discovered.*