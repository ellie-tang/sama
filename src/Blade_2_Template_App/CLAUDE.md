# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a Vuzix Blade 2 template application that demonstrates three different UI styles for developing Android applications for Vuzix smart glasses. The project is built with Java and uses Gradle as the build system.

## Build Commands
- **Build the project**: `./gradlew build`
- **Clean build**: `./gradlew clean`
- **Install debug APK**: `./gradlew installDebug`
- **Assemble APK**: `./gradlew assemble`

## Architecture
The application follows the Vuzix HUD development patterns:

### Core Components
- **BladeSampleApplication**: Extends DynamicThemeApplication to handle automatic theme switching based on ambient light
- **ActionMenuActivity**: Base class for activities that use Vuzix's circular action menu system
- **Three template activities** demonstrating different UI layouts:
  - `center_content_template_activity`: Main launcher activity with center-focused content
  - `around_content_template_activity`: Content arranged around the display edges
  - `center_content_pop_up_menu_template_activity`: Center content with popup menu

### Key Dependencies
- **Vuzix HUD Libraries**:
  - `com.vuzix:hud-actionmenu:2.9.1` - Circular action menu system
  - `com.vuzix:hud-resources:2.4.0` - Theme and resource management
- **Android Support**: AndroidX AppCompat 1.7.0
- **Kotlin**: Standard library 1.8.22

### Package Structure
- Main package: `devkit.blade.vuzix.com.blade_template_app`
- All activities follow the ActionMenuActivity pattern for navigation
- Widget support through Template_Widget and Template_Widget_Update_Receiver

### Key Configuration
- **Namespace**: `devkit.blade.vuzix.com.blade_template_app`
- **Min SDK**: 22 (Android 5.1)
- **Target SDK**: 34 (Android 14)
- **Theme**: Uses `HudTheme` for proper Vuzix display rendering
- **Icon tinting**: Enabled for Vuzix launcher integration

### Development Notes
- Activities must extend ActionMenuActivity instead of regular Activity for proper Vuzix integration
- Use onCreateActionMenu() instead of onCreateOptionsMenu() for menu creation
- The application supports dynamic theming based on ambient light conditions
- Widget functionality is configured through AndroidManifest.xml with specific Vuzix metadata