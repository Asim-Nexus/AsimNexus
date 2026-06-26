/**
 * ASIMNEXUS Desktop - macOS Notarization Script
 * 
 * Usage:
 *   export APPLE_ID="developer@asimnexus.org"
 *   export APPLE_ID_PASSWORD="@keychain:AC_PASSWORD"  # App-specific password
 *   export APPLE_TEAM_ID="TEAM_ID"
 *   node scripts/notarize.js
 * 
 * This script is called by electron-builder after packaging for macOS.
 * It notarizes the app with Apple's notary service so Gatekeeper
 * allows it to run on macOS Catalina and later.
 */

const { notarize } = require('@electron/notarize');
const path = require('path');

exports.default = async function notarizing(context) {
    const { electronPlatformName, appOutDir } = context;

    // Only notarize on macOS during production builds
    if (electronPlatformName !== 'darwin') {
        return;
    }

    const appName = context.packager.appInfo.productFilename;

    console.log(`Notarizing ${appName}...`);

    try {
        await notarize({
            tool: 'notarytool',
            appPath: path.join(appOutDir, `${appName}.app`),
            appleId: process.env.APPLE_ID,
            appleIdPassword: process.env.APPLE_ID_PASSWORD,
            teamId: process.env.APPLE_TEAM_ID,
        });
        console.log('✅ Notarization successful!');
    } catch (error) {
        console.error('❌ Notarization failed:', error.message);
        throw error;
    }
};
