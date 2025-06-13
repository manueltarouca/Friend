#!/usr/bin/env python3
"""
Telemetry Removal Script for OMI Privacy Fork
Removes all analytics and tracking code from the codebase
"""

import os
import re
from pathlib import Path
import argparse

class TelemetryRemover:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.removed_count = 0
        self.modified_files = []
        
        # Analytics packages to remove
        self.analytics_packages = [
            'mixpanel_flutter',
            'posthog_flutter', 
            'intercom_flutter',
            'instabug_flutter',
            'firebase_analytics',
            'firebase_crashlytics',
            'firebase_performance'
        ]
        
        # Import patterns to remove
        self.import_patterns = [
            r"import\s+['\"]package:mixpanel_flutter/.*['\"];?",
            r"import\s+['\"]package:posthog_flutter/.*['\"];?",
            r"import\s+['\"]package:intercom_flutter/.*['\"];?",
            r"import\s+['\"]package:instabug_flutter/.*['\"];?",
            r"import\s+['\"].*services/mixpanel\.dart['\"];?",
            r"import\s+['\"].*services/intercom\.dart['\"];?",
            r"import\s+['\"].*services/instabug\.dart['\"];?",
        ]
        
        # Service files to delete
        self.files_to_delete = [
            'app/lib/services/mixpanel.dart',
            'app/lib/services/intercom.dart',
            'app/lib/services/instabug.dart',
        ]
        
        # Analytics method calls to remove
        self.method_patterns = [
            r'MixpanelManager\(\)\.track\([^;]+\);?',
            r'MixpanelManager\(\)\.setUserProperty\([^;]+\);?',
            r'MixpanelManager\.init\(\);?',
            r'IntercomManager\..*\([^;]*\);?',
            r'InstabugWrapper\..*\([^;]*\);?',
            r'Posthog\(\)\..*\([^;]*\);?',
        ]

    def log(self, message):
        """Log message with dry-run prefix if applicable"""
        prefix = "[DRY RUN] " if self.dry_run else ""
        print(f"{prefix}{message}")

    def remove_from_pubspec(self):
        """Remove analytics dependencies from pubspec.yaml"""
        pubspec_path = 'app/pubspec.yaml'
        if not os.path.exists(pubspec_path):
            self.log(f"Warning: {pubspec_path} not found")
            return
            
        self.log(f"Processing {pubspec_path}...")
        
        with open(pubspec_path, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        removed = []
        
        for line in lines:
            should_remove = False
            for pkg in self.analytics_packages:
                if pkg in line and ':' in line:
                    should_remove = True
                    removed.append(line.strip())
                    break
            
            if not should_remove:
                new_lines.append(line)
        
        if removed:
            self.log(f"Removing from pubspec.yaml:")
            for r in removed:
                self.log(f"  - {r}")
            
            if not self.dry_run:
                with open(pubspec_path, 'w') as f:
                    f.writelines(new_lines)
            
            self.modified_files.append(pubspec_path)
            self.removed_count += len(removed)

    def remove_imports_from_file(self, filepath):
        """Remove analytics imports from a single Dart file"""
        with open(filepath, 'r') as f:
            content = f.read()
        
        original_content = content
        removed_imports = []
        
        for pattern in self.import_patterns:
            matches = re.findall(pattern, content)
            if matches:
                removed_imports.extend(matches)
                content = re.sub(pattern, '', content)
        
        # Remove empty lines left by import removal
        content = re.sub(r'\n\n+', '\n\n', content)
        
        if content != original_content:
            self.log(f"Modifying {filepath}")
            for imp in removed_imports:
                self.log(f"  - Removing import: {imp}")
            
            if not self.dry_run:
                with open(filepath, 'w') as f:
                    f.write(content)
            
            self.modified_files.append(filepath)
            self.removed_count += len(removed_imports)
            return True
        
        return False

    def remove_method_calls_from_file(self, filepath):
        """Remove analytics method calls from a single Dart file"""
        with open(filepath, 'r') as f:
            content = f.read()
        
        original_content = content
        removed_calls = []
        
        for pattern in self.method_patterns:
            matches = re.findall(pattern, content)
            if matches:
                removed_calls.extend(matches)
                content = re.sub(pattern, '', content)
        
        # Clean up empty lines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        if content != original_content:
            self.log(f"Removing method calls from {filepath}")
            for call in removed_calls[:3]:  # Show first 3 examples
                self.log(f"  - {call[:50]}...")
            if len(removed_calls) > 3:
                self.log(f"  - ... and {len(removed_calls) - 3} more")
            
            if not self.dry_run:
                with open(filepath, 'w') as f:
                    f.write(content)
            
            self.modified_files.append(filepath)
            self.removed_count += len(removed_calls)
            return True
        
        return False

    def remove_imports_and_calls(self, directory):
        """Remove analytics imports and method calls from all Dart files"""
        dart_files = list(Path(directory).rglob('*.dart'))
        self.log(f"Scanning {len(dart_files)} Dart files...")
        
        for filepath in dart_files:
            self.remove_imports_from_file(str(filepath))
            self.remove_method_calls_from_file(str(filepath))

    def delete_service_files(self):
        """Delete analytics service files"""
        for filepath in self.files_to_delete:
            if os.path.exists(filepath):
                self.log(f"Deleting {filepath}")
                if not self.dry_run:
                    os.remove(filepath)
                self.modified_files.append(filepath)
                self.removed_count += 1

    def clean_environment_files(self):
        """Remove analytics environment variables"""
        env_files = [
            'app/lib/env/dev_env.dart',
            'app/lib/env/prod_env.dart'
        ]
        
        env_vars_to_remove = [
            'instabugApiKeyAndroid',
            'instabugApiKeyIos',
            'mixpanelProjectToken',
            'posthogApiKey',
            'posthogHostUrl'
        ]
        
        for env_file in env_files:
            if not os.path.exists(env_file):
                continue
                
            with open(env_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            for var in env_vars_to_remove:
                # Remove variable declarations
                pattern = rf'static\s+const\s+String\??\s+{var}\s*=\s*[^;]+;'
                content = re.sub(pattern, '', content)
            
            if content != original_content:
                self.log(f"Cleaning environment file: {env_file}")
                if not self.dry_run:
                    with open(env_file, 'w') as f:
                        f.write(content)
                self.modified_files.append(env_file)

    def clean_main_dart(self):
        """Clean up main.dart initialization code"""
        main_file = 'app/lib/main.dart'
        if not os.path.exists(main_file):
            self.log(f"Warning: {main_file} not found")
            return
        
        with open(main_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Remove PostHog initialization
        content = re.sub(
            r'if\s*\(ProdEnv\.posthogApiKey\.isNotEmpty\)\s*\{[^}]+Posthog\(\)\.init\([^}]+\}',
            '', content, flags=re.DOTALL
        )
        
        # Remove analytics manager initializations
        analytics_inits = [
            'MixpanelManager.init();',
            'IntercomManager.init();',
            'await InstabugWrapper.init();'
        ]
        
        for init in analytics_inits:
            content = content.replace(init, '')
        
        if content != original_content:
            self.log("Cleaning main.dart initialization code")
            if not self.dry_run:
                with open(main_file, 'w') as f:
                    f.write(content)
            self.modified_files.append(main_file)

    def create_privacy_stub(self):
        """Create a privacy-focused analytics stub"""
        stub_content = '''// Privacy-focused analytics stub
// This file replaces external analytics with local-only logging

class PrivacyAnalytics {
  static bool _enabled = false;
  
  static void init() {
    // No initialization needed for privacy-focused analytics
    print('[Privacy] Analytics stub initialized - no data will be transmitted');
  }
  
  static void track(String event, [Map<String, dynamic>? properties]) {
    if (_enabled) {
      print('[Privacy] Local event: $event');
      // Could write to local log file if needed
    }
  }
  
  static void setUserProperty(String key, dynamic value) {
    // No-op - we don't track users
  }
  
  static void identify(String userId) {
    // No-op - we don't track users
  }
}

// Stub classes to prevent compilation errors
class MixpanelManager {
  static void init() => PrivacyAnalytics.init();
  void track(String event, [Map<String, dynamic>? properties]) => 
    PrivacyAnalytics.track(event, properties);
}

class IntercomManager {
  static void init() {}
  static IntercomManager instance = IntercomManager();
  void displayMessenger() {}
}

class InstabugWrapper {
  static Future<void> init() async {}
  static void logEvent(String event) {}
}
'''
        
        stub_path = 'app/lib/services/privacy_analytics.dart'
        self.log(f"Creating privacy stub at {stub_path}")
        
        if not self.dry_run:
            os.makedirs(os.path.dirname(stub_path), exist_ok=True)
            with open(stub_path, 'w') as f:
                f.write(stub_content)

    def run(self):
        """Execute the telemetry removal process"""
        self.log("Starting telemetry removal process...")
        
        # 1. Remove from pubspec.yaml
        self.remove_from_pubspec()
        
        # 2. Delete service files
        self.delete_service_files()
        
        # 3. Clean environment files
        self.clean_environment_files()
        
        # 4. Clean main.dart
        self.clean_main_dart()
        
        # 5. Remove imports and method calls
        if os.path.exists('app/lib'):
            self.remove_imports_and_calls('app/lib')
        
        # 6. Create privacy stub
        self.create_privacy_stub()
        
        # Summary
        self.log(f"\nTelemetry removal complete!")
        self.log(f"Total items removed: {self.removed_count}")
        self.log(f"Files modified: {len(set(self.modified_files))}")
        
        if self.dry_run:
            self.log("\nThis was a dry run. No files were actually modified.")
            self.log("Run without --dry-run to apply changes.")

def main():
    parser = argparse.ArgumentParser(description='Remove telemetry from OMI codebase')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be removed without making changes')
    parser.add_argument('--app-only', action='store_true',
                        help='Only process the Flutter app, skip backend')
    
    args = parser.parse_args()
    
    # Change to repository root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    os.chdir(repo_root)
    
    remover = TelemetryRemover(dry_run=args.dry_run)
    remover.run()
    
    if not args.app_only:
        print("\nNote: Backend telemetry removal not yet implemented.")
        print("Please review backend/requirements.txt and backend code manually.")

if __name__ == "__main__":
    main()