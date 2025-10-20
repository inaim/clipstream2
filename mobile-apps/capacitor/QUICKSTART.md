# 🚀 ClipStream Mobile - 5 Minute Quick Start

Get your app running on iOS and Android in 5 minutes!

## Prerequisites

- ✅ macOS (for iOS)
- ✅ Xcode installed
- ✅ Android Studio installed
- ✅ Node.js installed

## Step 1: Install (1 minute)

```bash
cd mobile-apps/capacitor
npm install
```

## Step 2: Build Frontend (1 minute)

```bash
npm run build
```

This builds your React app into `frontend/dist`.

## Step 3: Add Platforms (1 minute)

```bash
# Add iOS
npm run add:ios

# Add Android
npm run add:android

# Sync everything
npm run sync
```

## Step 4: Configure App ID (1 minute)

Edit `capacitor.config.ts`:

```typescript
const config: CapacitorConfig = {
  appId: 'com.yourcompany.clipstream', // ⚠️ CHANGE THIS!
  appName: 'ClipStream',
  // ... rest stays the same
};
```

Then sync again:

```bash
npm run sync
```

## Step 5: Open & Run (1 minute)

### iOS

```bash
npm run ios
```

This opens Xcode. Then:
1. Select a simulator (e.g., iPhone 15 Pro)
2. Click ▶️ Run
3. App launches! 🎉

### Android

```bash
npm run android
```

This opens Android Studio. Then:
1. Wait for Gradle sync
2. Select an emulator
3. Click ▶️ Run
4. App launches! 🎉

## ✅ Done!

Your app is now running on iOS and Android!

## Next Steps

### Test on Real Device

**iOS:**
1. Connect iPhone via USB
2. In Xcode, select your iPhone
3. Click Run
4. Trust developer on iPhone

**Android:**
1. Enable Developer Options on phone
2. Enable USB Debugging
3. Connect via USB
4. Select device in Android Studio
5. Click Run

### Make Changes

When you update your web app:

```bash
# 1. Build frontend
npm run build

# 2. Sync to native apps
npm run sync

# 3. Rerun in Xcode/Android Studio
```

### Prepare for App Stores

See the full guide: `README.md`

Key steps:
1. Create app icons (1024x1024)
2. Take screenshots
3. Configure signing
4. Archive and upload

## Common Commands

```bash
# Build frontend and sync
npm run build && npm run sync

# Update Capacitor
npm run update

# Clean and resync
npm run clean

# Open iOS in Xcode
npm run ios

# Open Android in Android Studio
npm run android
```

## Troubleshooting

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

### Changes Not Showing

```bash
npm run build
npm run sync
# Then rebuild in Xcode/Android Studio
```

## 🎉 Success!

You now have:
- ✅ iOS app running
- ✅ Android app running
- ✅ Hot reload working
- ✅ Ready for development

**Next:** Follow `README.md` for app store submission!

---

**Need help?** Check the full documentation in `README.md` or `../SETUP_GUIDE.md`

