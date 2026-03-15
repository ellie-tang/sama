# Vuzix Blade 2 AI Assistant - Learning Guide for Students

Welcome! This guide will help you understand how this Android app works. It's a facial recognition app for Vuzix Blade 2 smart glasses.

---

## Table of Contents
1. [What Does This App Do?](#what-does-this-app-do)
2. [Project Structure Overview](#project-structure-overview)
3. [Understanding the Code Modules](#understanding-the-code-modules)
4. [How Everything Works Together](#how-everything-works-together)
5. [Key Concepts to Learn](#key-concepts-to-learn)

---

## What Does This App Do?

This app turns Vuzix Blade 2 smart glasses into a face recognition assistant. Here's what happens:

1. **Camera captures images** - Every 1 second, the camera takes a photo
2. **Sends to AI server** - The photo is sent to a web server via HTTP
3. **Gets recognition result** - The server tells us who the person is
4. **Shows on display** - The name appears on the smart glasses screen
5. **Speaks the name** - Text-to-speech announces who was recognized

**Use Case**: Imagine wearing smart glasses that can recognize people you meet and remind you of their names!

---

## Project Structure Overview

Let's look at how the code is organized:

```
Blade_2_Template_App/
├── app/
│   ├── src/main/
│   │   ├── java/.../blade_template_app/
│   │   │   ├── center_content_template_activity.java    ← Main entry point (UI)
│   │   │   ├── CameraCaptureService.java               ← Takes photos automatically
│   │   │   ├── FaceRecognitionApiClient.java           ← Talks to the server
│   │   │   ├── FaceRecognitionBroadcastReceiver.java   ← Receives results
│   │   │   ├── BladeSampleApplication.java             ← App initialization
│   │   │   └── Template_Widget.java                    ← Home screen widget
│   │   │
│   │   ├── res/
│   │   │   ├── layout/
│   │   │   │   └── activity_center_content_template_style.xml  ← UI design
│   │   │   ├── values/
│   │   │   │   └── strings.xml                         ← Text strings
│   │   │   └── xml/
│   │   │       └── network_security_config.xml         ← Network permissions
│   │   │
│   │   └── AndroidManifest.xml                         ← App configuration
│   │
│   └── build.gradle                                    ← Dependencies & build settings
│
└── client-server-api-spec.md                           ← API documentation
```

### What Each Folder Does:

- **`java/` folder**: Contains all the Java code that makes the app work
- **`res/` folder**: Contains resources like layouts (UI design), images, and text
- **`AndroidManifest.xml`**: Tells Android about your app (like its name, permissions, etc.)
- **`build.gradle`**: Lists all the libraries your app needs

---

## Understanding the Code Modules

Let's explore each major code file and what it does:

---

### 1. **Main Entry Point: `center_content_template_activity.java`**

**Location**: `app/src/main/java/.../center_content_template_activity.java`

**What it does**: This is the main screen you see when you open the app. Think of it as the "homepage."

#### Key Parts:

```java
public class center_content_template_activity extends ActionMenuActivity
    implements FaceRecognitionBroadcastReceiver.FaceRecognitionListener
```

- **`extends ActionMenuActivity`**: This is a special Vuzix class that gives you menu functionality
- **`implements FaceRecognitionListener`**: Says "I want to receive face recognition results"

#### Important Methods:

**a) `onCreate()` - App Startup**
```java
protected void onCreate(Bundle savedInstanceState) {
    // This runs when the app starts
    setupFullscreen();                    // Make app use full screen
    setContentView(R.layout.activity_center_content_template_style);  // Load the UI
    welcomeBanner = findViewById(R.id.welcome_banner);  // Connect to UI elements
    setupRecognitionReceiver();           // Listen for recognition results
    initializeTextToSpeech();            // Setup voice announcements
    checkAndRequestCameraPermission();   // Ask user for camera access
}
```

**b) `onFaceRecognized()` - When Someone is Recognized**
```java
public void onFaceRecognized(String displayName, String personName, ...) {
    // This runs when the server sends back a recognition result
    updateBannerWithRecognitionResult(displayName, personName, confidence);

    // Only announce if it's a new person (avoid repeating)
    if (!displayName.equals("No known person found!") &&
        !displayName.equals(lastRecognizedPerson)) {
        announceRecognition(displayName);  // Speak the name
    }
}
```

**c) `announceRecognition()` - Text-to-Speech**
```java
private void announceRecognition(String displayName) {
    String announcement = displayName;
    textToSpeech.speak(announcement, TextToSpeech.QUEUE_FLUSH, null, "RECOGNITION_...");
}
```

#### What You Can Learn Here:
- **Android Activity Lifecycle**: `onCreate()`, `onDestroy()`
- **UI Updates**: How to change text on screen
- **Text-to-Speech**: Making your app talk
- **Permissions**: Asking users for camera access

---

### 2. **Camera Service: `CameraCaptureService.java`**

**Location**: `app/src/main/java/.../CameraCaptureService.java`

**What it does**: Runs in the background, taking photos every 1 seconds automatically.

#### Key Concept: **Android Service**
A Service is a component that runs in the background without a UI. Perfect for continuous camera capture!

#### Important Parts:

**a) Starting the Timer**
```java
private void startPeriodicCapture() {
    captureTimer = new Timer();
    captureTimer.scheduleAtFixedRate(new TimerTask() {
        @Override
        public void run() {
            captureImage();  // Take a photo
        }
    }, 2000, CAPTURE_INTERVAL_MS);  // Start after 2 seconds, repeat every 2 seconds
}
```

**b) Capturing the Image**
```java
private void captureImage() {
    // 1. Check if camera is ready
    if (cameraDevice == null || captureSession == null) {
        openCamera();
        return;
    }

    // 2. Trigger auto-focus for better image quality
    triggerAutoFocus();

    // 3. Take the actual picture
    performActualCapture();
}
```

**c) Processing the Image**
```java
private final ImageReader.OnImageAvailableListener imageAvailableListener =
    new ImageReader.OnImageAvailableListener() {
    @Override
    public void onImageAvailable(ImageReader reader) {
        Image image = reader.acquireLatestImage();

        // Save image and create thumbnail
        File[] imageFiles = saveImageAndThumbnail(image);
        File fullImage = imageFiles[0];
        File thumbnail = imageFiles[1];

        // Send to face recognition API
        apiClient.processImageAsync(fullImage, thumbnail.getAbsolutePath());
    }
};
```

#### What You Can Learn Here:
- **Android Services**: Background processing
- **Camera2 API**: How to use device cameras in Android
- **Timer & Scheduling**: Running tasks repeatedly
- **Image Processing**: Rotating and resizing images

---

### 3. **Network Communication: `FaceRecognitionApiClient.java`**

**Location**: `app/src/main/java/.../FaceRecognitionApiClient.java`

**What it does**: Sends images to the web server and receives recognition results.

#### Key Technology: **REST API with HTTP**

REST APIs allow apps to communicate with servers over the internet using HTTP requests.

#### Important Parts:

**a) Configuration**
```java
// Server URL - where we send images
private static final String SERVER_HOST = "192.168.1.201";
private static final int SERVER_PORT = 8000;
private static final String BASE_URL = "http://" + SERVER_HOST + ":" + SERVER_PORT;
```

**b) Sending an Image**
```java
private void processImage(File imageFile, String thumbnailPath) {
    // 1. Create a multipart request (for uploading files)
    RequestBody requestBody = new MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart("file", imageFile.getName(),
            RequestBody.create(imageFile, MediaType.parse("image/jpeg")))
        .build();

    // 2. Build the HTTP request
    Request request = new Request.Builder()
        .url(PROCESS_IMAGE_ENDPOINT)
        .post(requestBody)
        .build();

    // 3. Send the request and get response
    Response response = httpClient.newCall(request).execute();
    handleResponse(response, imageFile, thumbnailPath);
}
```

**c) Handling the Response**
```java
private void handleResponse(Response response, File imageFile, String thumbnailPath) {
    if (statusCode == 200) {  // Success!
        // Parse JSON response
        FaceRecognitionResponse result = gson.fromJson(responseBody, FaceRecognitionResponse.class);

        // Check if a person was recognized
        if (result.facesDetected == 0) {
            displayName = "No known person found!";
        } else if (result.personName == null) {
            displayName = "No known person found!";
        } else {
            displayName = result.personName;  // Got a name!
        }

        // Send result to the UI
        sendRecognitionNotification(displayName, result, filename, thumbnailPath);
    }
}
```

**d) The Response Data Model**
```java
public static class FaceRecognitionResponse {
    public boolean success;
    public String personName;        // Who was recognized
    public String relationship;      // E.g., "Friend", "Family"
    public Double confidence;        // How sure? (0.0 to 1.0)
    public int facesDetected;        // How many faces in the image
    public String message;
    public String timestamp;
}
```

#### What You Can Learn Here:
- **HTTP Requests**: GET, POST methods
- **REST APIs**: How apps talk to servers
- **JSON**: Data format for web communication
- **OkHttp Library**: Popular HTTP client for Android
- **Async Programming**: Running network code without freezing the app

---

### 4. **Communication Between Components: `FaceRecognitionBroadcastReceiver.java`**

**Location**: `app/src/main/java/.../FaceRecognitionBroadcastReceiver.java`

**What it does**: Helps different parts of the app communicate with each other.

#### Key Concept: **Broadcast Receiver**

In Android, components can send "broadcasts" (like radio signals) to notify other components about events.

```
┌─────────────────────┐          ┌──────────────────────┐
│ ApiClient           │ Broadcast│ Activity (UI)        │
│ (Gets result from   │─────────>│ (Displays result)    │
│  server)            │          │                      │
└─────────────────────┘          └──────────────────────┘
```

#### How It Works:

**a) Sending a Broadcast** (from ApiClient):
```java
private void sendRecognitionNotification(String displayName, ...) {
    Intent intent = new Intent(FaceRecognitionBroadcastReceiver.ACTION_FACE_RECOGNIZED);
    intent.putExtra(EXTRA_DISPLAY_NAME, displayName);
    intent.putExtra(EXTRA_PERSON_NAME, result.personName);
    intent.putExtra(EXTRA_CONFIDENCE, result.confidence);
    // ... more data

    context.sendBroadcast(intent);  // Send it!
}
```

**b) Receiving the Broadcast** (in the receiver):
```java
public void onReceive(Context context, Intent intent) {
    // Extract the data
    String displayName = intent.getStringExtra(EXTRA_DISPLAY_NAME);
    String personName = intent.getStringExtra(EXTRA_PERSON_NAME);
    double confidence = intent.getDoubleExtra(EXTRA_CONFIDENCE, -1.0);

    // Notify the listener (the Activity)
    if (listener != null) {
        listener.onFaceRecognized(displayName, personName, ...);
    }
}
```

#### What You Can Learn Here:
- **Android Intents**: Passing data between components
- **Broadcast System**: Event-driven programming
- **Interfaces**: Defining contracts between classes

---

### 5. **App Configuration: `BladeSampleApplication.java`**

**Location**: `app/src/main/java/.../BladeSampleApplication.java`

**What it does**: Runs when the app first starts, before any activities.

```java
public class BladeSampleApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        // Global app initialization goes here
    }

    public boolean isLightMode() {
        return false;  // Always use dark mode
    }
}
```

#### What You Can Learn Here:
- **Application Class**: App-wide initialization
- **Singleton Pattern**: One instance for the entire app

---

### 6. **UI Layout: `activity_center_content_template_style.xml`**

**Location**: `app/src/main/res/layout/activity_center_content_template_style.xml`

**What it does**: Defines how the screen looks (like HTML for Android).

```xml
<RelativeLayout>
    <!-- Top banner - shows recognized person's name -->
    <TextView
        android:id="@+id/welcome_banner"
        android:text="Welcome to AI Assistant"
        android:textSize="29sp"
        android:textColor="@color/hud_white"
        android:layout_alignParentTop="true"/>

    <!-- Bottom status bar -->
    <TextView
        android:id="@+id/status_message"
        android:text="System Ready"
        android:textSize="26sp"
        android:layout_alignParentBottom="true"/>
</RelativeLayout>
```

#### What You Can Learn Here:
- **XML Layouts**: Designing UI without code
- **View Hierarchy**: Parent-child relationships
- **Styling**: Colors, sizes, fonts

---

### 7. **Network Security: `network_security_config.xml`**

**Location**: `app/src/main/res/xml/network_security_config.xml`

**What it does**: Tells Android which servers the app can connect to.

```xml
<network-security-config>
    <!-- Allow HTTP (not just HTTPS) to our server -->
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="false">192.168.1.201</domain>
    </domain-config>

    <!-- For other domains, require HTTPS -->
    <base-config cleartextTrafficPermitted="false" />
</network-security-config>
```

**Why needed?** Android blocks HTTP by default (only allows HTTPS for security). This config makes an exception for our local server.

#### What You Can Learn Here:
- **Network Security**: HTTP vs HTTPS
- **Android Security Policies**: Protecting user data

---

### 8. **Dependencies: `build.gradle`**

**Location**: `app/build.gradle`

**What it does**: Lists all the libraries (code from other developers) that our app uses.

```gradle
dependencies {
    // Vuzix HUD libraries for smart glasses
    implementation 'com.vuzix:hud-actionmenu:2.9.1'
    implementation 'com.vuzix:hud-resources:2.4.0'

    // HTTP client for talking to the server
    implementation 'com.squareup.okhttp3:okhttp:4.12.0'

    // JSON parsing (converting JSON text to Java objects)
    implementation 'com.google.code.gson:gson:2.10.1'

    // Camera support
    implementation 'androidx.camera:camera-core:1.3.0'
    implementation 'androidx.camera:camera-camera2:1.3.0'
}
```

#### What You Can Learn Here:
- **Dependency Management**: Using existing libraries
- **Gradle Build System**: How Android projects are built

---

### 9. **App Permissions: `AndroidManifest.xml`**

**Location**: `app/src/main/AndroidManifest.xml`

**What it does**: Declares what the app needs to access (camera, internet, etc.)

```xml
<manifest>
    <!-- Permissions the app needs -->
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <!-- Camera hardware required -->
    <uses-feature android:name="android.hardware.camera" android:required="true" />

    <application
        android:name=".BladeSampleApplication"
        android:theme="@style/HudTheme"
        android:networkSecurityConfig="@xml/network_security_config">

        <!-- Main activity (the screen user sees) -->
        <activity android:name=".center_content_template_activity"
                  android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- Background service for camera -->
        <service android:name=".CameraCaptureService"
                 android:enabled="true"
                 android:exported="false" />
    </application>
</manifest>
```

#### What You Can Learn Here:
- **Android Permissions Model**: Privacy and security
- **App Components**: Activities, Services, Receivers
- **Intent Filters**: What starts when you tap the app icon

---

## How Everything Works Together

Let's trace what happens from start to finish:

### Step 1: App Launch
```
1. Android starts BladeSampleApplication.onCreate()
2. Then starts center_content_template_activity.onCreate()
3. Activity requests camera permission from user
4. Activity starts CameraCaptureService
```

### Step 2: Camera Capture Loop
```
Every 2 seconds:
1. CameraCaptureService.captureImage() takes a photo
2. saveImageAndThumbnail() processes the image
3. apiClient.processImageAsync() is called with the image
```

### Step 3: Network Communication
```
1. FaceRecognitionApiClient creates HTTP POST request
2. Sends image to http://192.168.1.201:8000/api/process-image
3. Server processes image and sends back JSON response
4. Client parses JSON into FaceRecognitionResponse object
```

### Step 4: Broadcasting Results
```
1. ApiClient calls sendRecognitionNotification()
2. Creates an Intent with recognition data
3. Sends broadcast to all registered receivers
4. FaceRecognitionBroadcastReceiver.onReceive() catches it
```

### Step 5: UI Update
```
1. Receiver calls listener.onFaceRecognized()
2. Activity (which implements the listener) receives the call
3. updateBannerWithRecognitionResult() updates the screen
4. announceRecognition() speaks the name via TTS
```

### Flow Diagram:
```
┌─────────────────────┐
│ User launches app   │
└──────────┬──────────┘
           │
           v
┌─────────────────────────────┐
│ Activity starts             │
│ - Setup UI                  │
│ - Start camera service      │
│ - Register for broadcasts   │
└──────────┬──────────────────┘
           │
           v
┌─────────────────────────────┐
│ Camera Service (Background) │
│ ┌─────────────────────────┐ │
│ │ Every 2 seconds:        │ │
│ │ 1. Capture photo        │ │
│ │ 2. Save & rotate image  │ │
│ │ 3. Send to API client   │ │
│ └─────────┬───────────────┘ │
└───────────┼─────────────────┘
            │
            v
┌───────────────────────────────┐
│ API Client (Network)          │
│ 1. Create HTTP POST request   │
│ 2. Upload image to server     │
│ 3. Receive JSON response      │
│ 4. Parse response             │
│ 5. Send broadcast with result │
└───────────┬───────────────────┘
            │
            v
┌───────────────────────────────┐
│ Broadcast Receiver            │
│ - Catches broadcast           │
│ - Extracts data               │
│ - Notifies activity           │
└───────────┬───────────────────┘
            │
            v
┌───────────────────────────────┐
│ Activity (UI)                 │
│ - Updates text on screen      │
│ - Speaks person's name (TTS)  │
└───────────────────────────────┘
```

---

## Key Concepts to Learn

### 1. **Android Activity Lifecycle**
Activities go through states: Created → Started → Resumed → Paused → Stopped → Destroyed

```java
onCreate()    // Initialize UI and setup
onStart()     // Activity becomes visible
onResume()    // User can interact
onPause()     // User leaving
onStop()      // Activity hidden
onDestroy()   // Clean up resources
```

### 2. **Background Services**
Services run without UI, perfect for:
- Playing music in background
- Continuous camera capture
- Network monitoring

### 3. **Async Programming**
Never block the main thread (UI thread)!
```java
// Bad - freezes the app
String response = sendNetworkRequest();  // Takes 2 seconds!

// Good - runs in background
executorService.execute(() -> {
    String response = sendNetworkRequest();
    // Update UI when done
});
```

### 4. **REST APIs & HTTP**
- **GET**: Retrieve data from server
- **POST**: Send data to server (we use this for uploading images)
- **Status Codes**: 200 = OK, 404 = Not Found, 500 = Server Error

### 5. **JSON (JavaScript Object Notation)**
Text format for data exchange:
```json
{
  "success": true,
  "person_name": "John Doe",
  "confidence": 0.85,
  "faces_detected": 1
}
```

### 6. **Observer Pattern (Listeners)**
One object notifies many others when something happens:
```java
interface OnClickListener {
    void onClick();
}

button.setOnClickListener(new OnClickListener() {
    public void onClick() {
        // Button was clicked!
    }
});
```

### 7. **Android Intents**
Messages that carry data between components:
```java
Intent intent = new Intent(ACTION_FACE_RECOGNIZED);
intent.putExtra("name", "John");
sendBroadcast(intent);
```

### 8. **Permissions Model**
Apps must ask users for sensitive access:
- Camera
- Location
- Microphone
- Storage
- Internet (no prompt needed)

---

## What Makes This Project Special?

### 1. **Real-Time Processing**
Unlike typical apps, this captures and processes images continuously in the background.

### 2. **Multiple Components Working Together**
- UI (Activity)
- Background service
- Network communication
- Text-to-speech
- Camera hardware access

### 3. **Enterprise-Grade Architecture**
Uses proper separation of concerns:
- UI layer (Activity)
- Business logic (ApiClient)
- Data layer (Service)
- Communication (BroadcastReceiver)

### 4. **Modern Android Development**
- Camera2 API (modern camera access)
- OkHttp (industry-standard HTTP client)
- Material Design principles
- Async/threading best practices

---

## Next Steps for Learning

### Beginner Projects:
1. **Modify the capture interval**: Change from 2 seconds to 5 seconds
2. **Change the welcome message**: Edit strings.xml
3. **Add a button**: Add a "Capture Now" button to the UI

### Intermediate Projects:
1. **Add a settings screen**: Let users configure the server IP
2. **Show confidence score**: Display the recognition confidence percentage
3. **Add sound effects**: Play a sound when someone is recognized

### Advanced Projects:
1. **Add local database**: Store recognized people using Room database
2. **Implement retry logic**: Automatically retry failed network requests
3. **Add ML model**: Run face detection locally on the device

---

## Resources for Learning More

### Android Basics:
- Android Developer Documentation: https://developer.android.com/
- Android Basics Course: https://developer.android.com/courses/android-basics-compose/course

### Camera Development:
- Camera2 API Guide: https://developer.android.com/training/camera2

### Networking:
- OkHttp Documentation: https://square.github.io/okhttp/
- REST API Tutorial: https://www.restapitutorial.com/

### Vuzix Specific:
- Vuzix Developer Portal: https://www.vuzix.com/Developer
- Vuzix SDK Documentation: https://www.vuzix.com/support/Downloads_Drivers

---

## Glossary of Terms

**Activity**: A screen in your app (like a webpage)

**Service**: Code that runs in the background without UI

**Intent**: A message to start activities or services

**Broadcast**: A system-wide announcement that components can listen for

**Listener/Callback**: Code that runs when an event happens

**Async/Asynchronous**: Code that runs without waiting (non-blocking)

**API (Application Programming Interface)**: Rules for how software components talk to each other

**REST API**: A type of web API using HTTP

**JSON**: Text format for exchanging data

**HTTP**: Protocol for web communication

**Thread**: A path of execution in your program (main thread = UI thread)

**Gradle**: Build system that compiles your Android app

**SDK (Software Development Kit)**: Tools and libraries for development

**TTS (Text-to-Speech)**: Converting text to spoken words

**Manifest**: File that declares your app's components and permissions

---

## Common Questions

**Q: Why use a Service instead of doing everything in the Activity?**

A: Activities can be paused or destroyed when the user switches apps. Services keep running in the background, ensuring continuous camera capture even when the user isn't looking at the app.

**Q: Why not just make one big class with all the code?**

A: Separation of concerns makes code easier to understand, test, and maintain. Each class has one job:
- Activity = UI
- Service = Camera
- ApiClient = Network
- BroadcastReceiver = Communication

**Q: What is OkHttp and why use it instead of basic Java HTTP?**

A: OkHttp is a popular library that handles:
- Connection pooling (reusing connections)
- Automatic retries
- Better error handling
- HTTPS support
- More efficient networking

**Q: Why do we need permissions?**

A: Android protects user privacy. Apps must ask permission before accessing:
- Camera (could spy on users)
- Location (tracks where you are)
- Files (could steal personal data)
- etc.

**Q: What happens if the network request fails?**

A: The catch block in `processImage()` catches errors and calls `sendErrorNotification()`, which updates the UI with an error message instead of crashing.

---

## Congratulations!

You now understand:
- ✅ What this app does (face recognition on smart glasses)
- ✅ How the code is organized (Activities, Services, Receivers)
- ✅ How components communicate (Intents, Broadcasts)
- ✅ How networking works (HTTP POST with OkHttp)
- ✅ How background tasks work (Services, Timers, Threads)
- ✅ How to use device hardware (Camera2 API)

Keep exploring, keep learning, and most importantly - keep building! 🚀

---

**Last Updated**: 2025-11-09
**Project Version**: 1.7
**Target**: High School Students Learning Android Development
