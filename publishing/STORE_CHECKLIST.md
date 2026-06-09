# ASIMNEXUS App Store Publishing Checklist

This guide covers the complete process for publishing ASIMNEXUS to:
- **Apple App Store** (iOS via Expo EAS Build)
- **Google Play Store** (Android via Expo EAS Build)
- **Desktop distribution** (Windows/macOS/Linux via electron-builder)

---

## 1. Prerequisites

### Common Requirements
- [ ] Bump version in all relevant `package.json` files (mobile + desktop)
- [ ] Update `app.json` with correct version
- [ ] Run full test suite: `python -m pytest tests/ -v`
- [ ] Verify all 51+ economy API tests pass
- [ ] Build backend: `python -m PyInstaller --onefile simple_backend.py` (or Docker)

### iOS (Apple App Store)
- [ ] Apple Developer Account ($99/year) with App Store Connect access
- [ ] App ID registered: `com.asimnexus.worldos`
- [ ] Apple Push Notification certificate (if using push)
- [ ] App-specific password for notarization
- [ ] Screenshots: 6.5" iPhone (1242×2688), 5.5" iPhone (1242×2208), 12.9" iPad (2048×2732)
- [ ] App icon: 1024×1024 PNG (already in assets/)

### Android (Google Play Store)
- [ ] Google Play Developer Account ($25 one-time)
- [ ] App signing key (keystore) generated
- [ ] Google Play Service Account JSON key for automated uploads
- [ ] Screenshots: 2-8 screenshots per device type (phone 1080×1920, tablet 2000×1200)
- [ ] Feature graphic: 1024×500 PNG

### Desktop
- [ ] Code signing certificates:
  - Windows: DigiCert/Comodo EV Code Signing Certificate
  - macOS: Apple Developer ID Application certificate
  - Linux: GPG signing key (optional)
- [ ] Icon files: 256×256 (Windows .ico), 512×512 (macOS .icns), 256×256 (Linux .png)

---

## 2. Mobile App (iOS/Android) — Expo EAS Build

### Setup
```bash
cd mobile/react_native

# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Configure EAS (already done in eas.json)
eas build:configure

# Setup credentials for iOS/Android
eas credentials
```

### Development Build
```bash
# iOS Simulator
eas build --platform ios --profile development

# Android APK
eas build --platform android --profile development
```

### Preview Build (Internal Testing)
```bash
eas build --platform all --profile preview
```

### Production Build
```bash
# Build for both platforms
eas build --platform all --profile production

# Or individually
eas build --platform ios --profile production
eas build --platform android --profile production
```

### Submit to Stores
```bash
# Using EAS Submit
eas submit --platform ios --profile production
eas submit --platform android --profile production

# Or using Fastlane (after building)
cd fastlane
fastlane ios deploy
fastlane android deploy
```

---

## 3. Desktop App — Electron Builder

### Configuration
The `desktop/package.json` already contains complete `electron-builder` config.

### Build Commands
```bash
cd desktop

# Install dependencies
npm install

# Build for current platform
npm start          # Run in development
npm run build:win  # Windows (NSIS installer + portable)
npm run build:mac  # macOS (DMG + ZIP)
npm run build:linux # Linux (AppImage + deb)
npm run build:all  # All platforms
```

### macOS Notarization
```bash
export APPLE_ID="developer@asimnexus.org"
export APPLE_ID_PASSWORD="@keychain:AC_PASSWORD"
export APPLE_TEAM_ID="TEAM_ID"

npm run build:mac
```

### Windows Code Signing
Set environment variables:
```bash
set WIN_CSC_LINK=path\to\certificate.p12
set WIN_CSC_KEY_PASSWORD=password
npm run build:win
```

### Output Location
All builds go to: `desktop/release/`

---

## 4. Store Listing Information

### App Name
- **Display Name**: ASIMNEXUS World OS
- **Subtitle**: Decentralized AI, Economy & Identity

### Keywords
`AI, blockchain, wallet, tokens, marketplace, staking, decentralized, digital twin, agent, automation`

### Categories
- **iOS**: Productivity / Utilities
- **Android**: Productivity / Tools
- **Desktop**: Utilities

### Age Rating
- **iOS**: 4+ (no objectionable content)
- **Android**: Everyone (ESRB: Everyone)
- **Desktop**: General

### Privacy Policy URL
`https://asimnexus.org/privacy`

### Support URL
`https://asimnexus.org/support`

### Marketing URL
`https://asimnexus.org`

---

## 5. Pre-Submission Checklist

### Functionality
- [ ] App launches without crashes
- [ ] All tabs navigate correctly (Dashboard, Economy, Agents, Chat, Settings)
- [ ] Economy API calls succeed (Wallet, Tokens, Escrow, Marketplace, Staking)
- [ ] Chat functionality works with both Local and World OS modes
- [ ] Settings persist across app restarts
- [ ] Connection indicator accurately reflects backend status
- [ ] Error states display gracefully (no blank screens)

### iOS-Specific
- [ ] Safe area insets respected on all devices (iPhone SE → Pro Max)
- [ ] No hardcoded UIKit APIs that would fail App Store review
- [ ] iTunes Connect metadata complete (description, keywords, support URL)
- [ ] TestFlight build installed and tested on physical devices
- [ ] No private API usage flagged by `nm -u`
- [ ] Notarization completed (if deploying via Enterprise)

### Android-Specific
- [ ] APK/AAB file size within limits (under 150MB recommended)
- [ ] Permissions justified in store listing
- [ ] Target API level 33+ (Android 13+)
- [ ] 64-bit native libraries included
- [ ] App Bundles (.aab) preferred over APK

### Desktop-Specific
- [ ] Code signing certificates installed
- [ ] Notarization passed (macOS)
- [ ] Windows Defender / SmartScreen tested
- [ ] Auto-update endpoint configured
- [ ] Installer tested on clean OS (no pre-existing runtime)

### Legal
- [ ] Privacy policy drafted and linked
- [ ] Terms of Service drafted and linked
- [ ] EULA (End User License Agreement) included with installers
- [ ] Open-source licenses included (for bundled dependencies)
- [ ] COPPA compliance if applicable (no data collection from under-13)

---

## 6. CI/CD Automation

### GitHub Actions Workflow
Create `.github/workflows/publish.yml` for automated builds:

```yaml
name: Publish

on:
  push:
    tags:
      - 'v*'

jobs:
  mobile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm install -g eas-cli
      - run: eas build --platform all --non-interactive
        env:
          EXPO_TOKEN: ${{ secrets.EXPO_TOKEN }}

  desktop:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm install
        working-directory: desktop
      - run: npm run build:all
        working-directory: desktop
      - uses: softprops/action-gh-release@v2
        with:
          files: desktop/release/*
```

---

## 7. Post-Launch

- [ ] Monitor crash reporting (Sentry/Crashlytics)
- [ ] Review App Store/Play Store ratings and reviews
- [ ] Track analytics (opt-in only)
- [ ] Plan next update cycle
- [ ] Update release notes for next version

---

## Quick Reference Commands

```bash
# Mobile — Build & Submit
cd mobile/react_native
eas build --platform all --profile production
eas submit --platform ios --profile production
eas submit --platform android --profile production

# Desktop — Build Installers
cd desktop
npm run build:all

# Desktop — Sign & Notarize (macOS)
npm run build:mac

# Version Bump
npm version patch  # or minor / major
git push --tags
```
