package devkit.blade.vuzix.com.blade_template_app;

import android.app.Application;
// import com.vuzix.hud.resources.DynamicThemeApplication;

/**
 * Main Application reference in the Manifest.
 *
 * DYNAMIC THEME SWITCHING: Currently DISABLED
 * - Extends Application instead of DynamicThemeApplication to prevent automatic theme switching
 * - Theme switching based on ambient light was causing frequent app restarts
 *
 * TO ENABLE DYNAMIC THEME SWITCHING IN THE FUTURE:
 * 1. Comment out "extends Application" below
 * 2. Uncomment the import and extends line marked with [DYNAMIC THEME]
 * 3. Uncomment the theme methods at the bottom of this file
 * 4. The widget will automatically work with dynamic themes
 *
 * For more information: https://www.vuzix.com/support/Downloads_Drivers
 */
public class BladeSampleApplication extends Application {
// [DYNAMIC THEME] public class BladeSampleApplication extends DynamicThemeApplication {

    @Override
    public void onCreate() {
        super.onCreate();
        // App will use the dark theme specified in AndroidManifest.xml (HudTheme)
    }

    /**
     * Method to check if app is in light mode.
     * Currently always returns false (dark mode only).
     * Used by Template_Widget to determine which layout to use.
     *
     * @return false (always dark mode)
     */
    public boolean isLightMode() {
        return false; // Always use dark mode when DynamicThemeApplication is disabled
        // When DynamicThemeApplication is enabled, this will be provided by parent class
    }

    /* [DYNAMIC THEME] Uncomment these methods when enabling DynamicThemeApplication:

    @Override
    protected int getNormalThemeResId() {
        return R.style.AppTheme;
    }

    @Override
    protected int getLightThemeResId() {
        return R.style.AppTheme_Light;
    }

    // Remove or comment out the isLightMode() method above when enabling dynamic themes
    */
}
