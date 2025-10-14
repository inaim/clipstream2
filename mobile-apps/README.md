# 📱 ClipStream Native Mobile Apps

This directory contains native app wrappers for iOS and Android that wrap the ClipStream PWA for distribution on App Store and Google Play.

## 📁 Directory Structure

```
mobile-apps/
├── ios/                    # iOS app (Swift)
│   ├── ClipStream/
│   │   ├── Info.plist
│   │   ├── AppDelegate.swift
│   │   ├── SceneDelegate.swift
│   │   ├── ViewController.swift
│   │   └── Assets.xcassets/
│   ├── ClipStream.xcodeproj
│   └── Podfile
├── android/                # Android app (Kotlin)
│   ├── app/
│   │   ├── src/
│   │   │   └── main/
│   │   │       ├── AndroidManifest.xml
│   │   │       ├── java/
│   │   │       │   └── com/clipstream/app/
│   │   │       │       └── MainActivity.kt
│   │   │       └── res/
│   │   └── build.gradle
│   ├── build.gradle
│   └── gradle.properties
├── capacitor/              # Capacitor-based wrapper (recommended)
│   ├── capacitor.config.ts
│   ├── package.json
│   └── README.md
└── README.md
```

## 🎯 Approach Options

### Option 1: Capacitor (Recommended) ⭐
- **Easiest and fastest**
- Automatically generates iOS and Android apps
- Maintains single codebase
- Built-in plugins for native features
- Easy updates

### Option 2: Native Wrappers
- Pure Swift (iOS) and Kotlin (Android)
- More control over native features
- Larger app size
- Requires separate maintenance

## 🚀 Quick Start

### Using Capacitor (Recommended)

```bash
cd mobile-apps/capacitor
npm install
npm run build
npx cap add ios
npx cap add android
npx cap sync
```

### iOS App Store Submission
```bash
npx cap open ios
# Open in Xcode, configure signing, and archive
```

### Android Play Store Submission
```bash
npx cap open android
# Open in Android Studio, generate signed APK/AAB
```

## 📋 Requirements

### For iOS Development:
- macOS with Xcode 14+
- Apple Developer Account ($99/year)
- CocoaPods installed
- iOS 14.0+ target

### For Android Development:
- Android Studio
- Google Play Developer Account ($25 one-time)
- JDK 11+
- Android SDK 24+

## 📦 What's Included

All three approaches include:
- ✅ WebView wrapper for PWA
- ✅ Splash screen
- ✅ App icons (all sizes)
- ✅ Push notification support
- ✅ Deep linking
- ✅ Camera/gallery access
- ✅ File upload support
- ✅ Offline support
- ✅ Native share functionality

## 🎨 Branding Assets Needed

Before building, prepare:
- App icon (1024x1024 PNG)
- Splash screen (2732x2732 PNG)
- Screenshots for stores
- App description
- Privacy policy URL
- Support URL

## 📝 Next Steps

1. Choose your approach (Capacitor recommended)
2. Follow the specific README in that directory
3. Configure app signing
4. Test on real devices
5. Submit to stores

See individual directories for detailed instructions.

