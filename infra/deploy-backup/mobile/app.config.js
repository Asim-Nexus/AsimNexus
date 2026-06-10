// ─── AsimNexus Mobile PWA Wrapper ────────────────────────────────────────────
// Expo / Capacitor configuration for wrapping the PWA as a mobile app.
// This provides an installable mobile surface while maintaining a single codebase.
// ─────────────────────────────────────────────────────────────────────────────

module.exports = {
  name: "AsimNexus",
  slug: "asimnexus",
  version: "0.1.0",
  orientation: "portrait",
  icon: "../pwa/icons/icon-512.png",
  userInterfaceStyle: "dark",
  splash: {
    backgroundColor: "#0a0a2e",
    resizeMode: "contain",
  },
  ios: {
    supportsTablet: true,
    bundleIdentifier: "com.asimnexus.mobile",
  },
  android: {
    package: "com.asimnexus.mobile",
    adaptiveIcon: {
      foregroundImage: "../pwa/icons/icon-512.png",
      backgroundColor: "#0a0a2e",
    },
  },
  web: {
    favicon: "../pwa/icons/icon-192.png",
    bundler: "metro",
  },
  extra: {
    backendUrl: "http://localhost:8080",
  },
};
