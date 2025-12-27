# 📱 ClipStream Capacitor Mobile Apps

This is the **recommended approach** for creating iOS and Android apps from your ClipStream PWA.

## 🎯 Why Capacitor?

- ✅ **Single Codebase** - One configuration for both iOS and Android
- ✅ **Easy Updates** - Just rebuild your frontend and sync
- ✅ **Native Features** - Access camera, push notifications, etc.
- ✅ **Fast Development** - No need to write Swift or Kotlin
- ✅ **Maintained by Ionic** - Well-supported and documented

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd mobile-apps/capacitor
npm install
```

### 2. Build Frontend

```bash
npm run build
```

This builds your React frontend into `frontend/dist`.

### 3. Add Platforms

```bash
# Add iOS (requires macOS)
npm run add:ios

# Add Android
npm run add:android
```

### 4. Sync Changes

```bash
npm run sync
```

This copies your web app to the native projects.

### 5. Open in Native IDEs

```bash
# Open iOS in Xcode
npm run ios

# Open Android in Android Studio
npm run android
```

## 📱 iOS App Store Submission

### Prerequisites
- macOS with Xcode 14+
- Apple Developer Account ($99/year)
- App Store Connect access

### Steps

1. **Open in Xcode**
   ```bash
   npm run ios
   ```

2. **Configure App Identity**
   - Open `ios/App/App.xcodeproj` in Xcode
   - Select the project in the navigator
   - Under "Signing & Capabilities":
     - Select your Team
     - Change Bundle Identifier to your unique ID (e.g., `com.yourcompany.clipstream`)

3. **Update App Information**
   - Display Name: `ClipStream`
   - Version: `1.0.0`
   - Build: `1`

4. **Add App Icons**
   - Drag your app icon (1024x1024) to `ios/App/App/Assets.xcassets/AppIcon.appiconset/`
   - Xcode will generate all required sizes

5. **Configure Capabilities**
   - Enable "Push Notifications"
   - Enable "Background Modes" → "Remote notifications"
   - Enable "Camera" usage
   - Enable "Photo Library" usage

6. **Update Info.plist**
   Add these privacy descriptions:
   ```xml
   <key>NSCameraUsageDescription</key>
   <string>ClipStream needs camera access to record videos</string>
   <key>NSPhotoLibraryUsageDescription</key>
   <string>ClipStream needs photo library access to upload videos</string>
   <key>NSMicrophoneUsageDescription</key>
   <string>ClipStream needs microphone access to record audio</string>
   ```

7. **Archive and Upload**
   - Product → Archive
   - Distribute App → App Store Connect
   - Upload
   - Submit for Review in App Store Connect

### App Store Connect Setup

1. **Create App**
   - Go to https://appstoreconnect.apple.com
   - My Apps → + → New App
   - Platform: iOS
   - Name: ClipStream
   - Primary Language: English
   - Bundle ID: (your bundle ID)
   - SKU: clipstream-ios

2. **App Information**
   - Category: Photo & Video
   - Subcategory: Social Networking
   - Content Rights: No

3. **Pricing**
   - Price: Free
   - Availability: All countries

4. **Prepare for Submission**
   - Screenshots (required sizes):
     - 6.7" (iPhone 14 Pro Max): 1290 x 2796
     - 6.5" (iPhone 11 Pro Max): 1242 x 2688
     - 5.5" (iPhone 8 Plus): 1242 x 2208
   - App Preview (optional video)
   - Description
   - Keywords
   - Support URL
   - Privacy Policy URL

5. **Submit for Review**
   - Add build from TestFlight
   - Answer questionnaire
   - Submit

## 🤖 Google Play Store Submission

### Prerequisites
- Android Studio
- Google Play Developer Account ($25 one-time)
- Java Development Kit (JDK) 11+

### Steps

1. **Open in Android Studio**
   ```bash
   npm run android
   ```

2. **Configure App**
   - Open `android/app/build.gradle`
   - Update:
     ```gradle
     android {
         defaultConfig {
             applicationId "com.yourcompany.clipstream"
             versionCode 1
             versionName "1.0.0"
         }
     }
     ```

3. **Update App Name**
   - Edit `android/app/src/main/res/values/strings.xml`:
     ```xml
     <string name="app_name">ClipStream</string>
     ```

4. **Add App Icons**
   - Replace icons in `android/app/src/main/res/mipmap-*/`
   - Use Android Studio's Image Asset tool:
     - Right-click `res` → New → Image Asset
     - Icon Type: Launcher Icons
     - Path: (your 1024x1024 icon)

5. **Generate Signing Key**
   ```bash
   keytool -genkey -v -keystore clipstream-release.keystore \
     -alias clipstream -keyalg RSA -keysize 2048 -validity 10000
   ```

6. **Configure Signing**
   - Create `android/key.properties`:
     ```properties
     storePassword=YOUR_STORE_PASSWORD
     keyPassword=YOUR_KEY_PASSWORD
     keyAlias=clipstream
     storeFile=../clipstream-release.keystore
     ```

   - Update `android/app/build.gradle`:
     ```gradle
     def keystoreProperties = new Properties()
     def keystorePropertiesFile = rootProject.file('key.properties')
     if (keystorePropertiesFile.exists()) {
         keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
     }

     android {
         signingConfigs {
             release {
                 keyAlias keystoreProperties['keyAlias']
                 keyPassword keystoreProperties['keyPassword']
                 storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
                 storePassword keystoreProperties['storePassword']
             }
         }
         buildTypes {
             release {
                 signingConfig signingConfigs.release
             }
         }
     }
     ```

7. **Build Release APK/AAB**
   ```bash
   cd android
   ./gradlew bundleRelease  # For AAB (recommended)
   # OR
   ./gradlew assembleRelease  # For APK
   ```

   Output:
   - AAB: `android/app/build/outputs/bundle/release/app-release.aab`
   - APK: `android/app/build/outputs/apk/release/app-release.apk`

### Google Play Console Setup

1. **Create App**
   - Go to https://play.google.com/console
   - Create app
   - App name: ClipStream
   - Default language: English
   - App or game: App
   - Free or paid: Free

2. **Store Listing**
   - Short description (80 chars)
   - Full description (4000 chars)
   - App icon (512x512 PNG)
   - Feature graphic (1024x500 PNG)
   - Screenshots:
     - Phone: 2-8 screenshots (min 320px)
     - 7" Tablet: 1-8 screenshots
     - 10" Tablet: 1-8 screenshots
   - Category: Social
   - Contact details
   - Privacy policy URL

3. **Content Rating**
   - Complete questionnaire
   - Get rating

4. **App Content**
   - Privacy policy
   - Ads declaration
   - Target audience
   - News app declaration

5. **Release**
   - Production → Create new release
   - Upload AAB
   - Release name: 1.0.0
   - Release notes
   - Review and rollout

## 🔄 Updating Your App

When you update your web app:

```bash
# 1. Build frontend
cd ../../frontend
npm run build

# 2. Sync to native apps
cd ../mobile-apps/capacitor
npm run sync

# 3. Increment version
# iOS: Update in Xcode (General → Version & Build)
# Android: Update versionCode and versionName in build.gradle

# 4. Rebuild and resubmit
```

## 🧪 Testing

### iOS Testing
```bash
# Run on simulator
npm run ios
# Select simulator and run

# Run on device
# Connect iPhone via USB
# Select device in Xcode and run
```

### Android Testing
```bash
# Run on emulator
npm run android
# Select emulator and run

# Run on device
# Enable USB debugging on Android device
# Connect via USB
# Select device in Android Studio and run
```

## 📋 Checklist Before Submission

### Both Platforms
- [ ] App icons (all sizes)
- [ ] Splash screen
- [ ] Privacy policy URL
- [ ] Support/contact URL
- [ ] App description
- [ ] Screenshots
- [ ] Test on real devices
- [ ] Check all features work
- [ ] Verify deep links
- [ ] Test push notifications

### iOS Specific
- [ ] Apple Developer account
- [ ] Bundle ID registered
- [ ] Signing certificate
- [ ] Provisioning profile
- [ ] TestFlight testing
- [ ] App Store Connect setup

### Android Specific
- [ ] Google Play Developer account
- [ ] Signing key generated
- [ ] key.properties configured
- [ ] AAB built and tested
- [ ] Internal testing track

## 🆘 Troubleshooting

### iOS Build Fails
```bash
cd ios/App
pod install
cd ../..
npm run sync
```

### Android Build Fails
```bash
cd android
./gradlew clean
cd ..
npm run sync
```

### Web App Not Loading
- Check `capacitor.config.ts` webDir path
- Ensure frontend is built: `npm run build`
- Run `npm run sync` after changes

## 📚 Resources

- [Capacitor Documentation](https://capacitorjs.com/docs)
- [iOS App Store Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Google Play Policy](https://play.google.com/about/developer-content-policy/)
- [App Store Connect](https://appstoreconnect.apple.com)
- [Google Play Console](https://play.google.com/console)

## 💡 Tips

1. **Start with TestFlight/Internal Testing** - Test thoroughly before public release
2. **Prepare Screenshots Early** - Use tools like Fastlane Snapshot
3. **Write Good Descriptions** - Include keywords for ASO (App Store Optimization)
4. **Monitor Reviews** - Respond to user feedback
5. **Plan Updates** - Regular updates improve rankings

## 🎉 Success!

Once approved, your app will be available:
- **iOS**: https://apps.apple.com/app/clipstream/id[YOUR_APP_ID]
- **Android**: https://play.google.com/store/apps/details?id=com.clipstream.app

Congratulations! 🚀

