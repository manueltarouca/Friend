// Privacy-focused analytics stub
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
