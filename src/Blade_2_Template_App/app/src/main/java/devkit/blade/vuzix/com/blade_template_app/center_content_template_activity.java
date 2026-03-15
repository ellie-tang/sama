package devkit.blade.vuzix.com.blade_template_app;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.util.Log;
import android.view.Menu;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.TextView;
import android.widget.Toast;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import java.util.Locale;

import com.vuzix.hud.actionmenu.ActionMenuActivity;


/**
 * Main Template Activity, This application follows the Center Lock style of the Vuzix Camera App.
 * All Navigation buttons are MenuItems and the Rotation is handle by the ActionMenuActivity.
 * The Center of the screen is your normal Layout.
 * For more information on the ActionMenuActivity read the JavaDocs in Android Studio or download the
 * Java docs at:  https://www.vuzix.com/support/Downloads_Drivers
 */
public class center_content_template_activity extends ActionMenuActivity implements FaceRecognitionBroadcastReceiver.FaceRecognitionListener {

    private static final String TAG = "BladeTemplateApp";
    private static final int CAMERA_PERMISSION_REQUEST_CODE = 100;

    private TextView welcomeBanner;
    private TextView statusMessage;
    private android.widget.ImageView thumbnailImage;
    private FaceRecognitionBroadcastReceiver recognitionReceiver;
    private TextToSpeech textToSpeech;
    private ToneGenerator toneGenerator;
    private String lastRecognizedPerson = "";

    // Voice announcement control - set to true to enable voice announcements
    private static final boolean ENABLE_VOICE_ANNOUNCEMENTS = true ;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Set fullscreen mode to use full 480x480 resolution
        setupFullscreen();

        setContentView(R.layout.activity_center_content_template_style);
        maximizeContentRealEstate();

        welcomeBanner = findViewById(R.id.welcome_banner);
        statusMessage = findViewById(R.id.status_message);
        thumbnailImage = findViewById(R.id.thumbnail_image);
        if (thumbnailImage != null) {
            thumbnailImage.setVisibility(View.GONE); // HUD is text-only for now; keep view for future use.
        }

        // Setup broadcast receiver for face recognition results
        setupRecognitionReceiver();

        // Play welcome beep sound
        playWelcomeBeep();

        // Initialize Text-to-Speech
        initializeTextToSpeech();

        // Check and request camera permission, then start camera service
        checkAndRequestCameraPermission();
    }

    /**
     *  Main override to create the ACTION MENU. Notice that this is onCreate-ACTION-MENU. Not to be
     *  confuse with onCreate-Option-Menu which will create the basic Android menu that will not
     *  display properly in the small device screen.
     * @param menu Menu to inflate too.
     * @return Return if menu was setup correctly.
     */
    @Override
    protected boolean onCreateActionMenu(Menu menu) {
        super.onCreateActionMenu(menu);
        // Menu disabled - return false to not show any menus
        return false;
    }

    /**
     * Override of the ActionMenuActivity. FALSE will hide the Action Menu completely.
     * https://www.vuzix.com/Developer/KnowledgeBase/Detail/65
     */
    @Override
    protected boolean alwaysShowActionMenu() {
        return false;
    }

    private void showToast(final String text){

        final Activity activity = this;

        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Toast.makeText(activity, text, Toast.LENGTH_SHORT).show();
            }
        });
    }

    /**
     * Update status message at bottom of screen
     */
    private void updateStatusMessage(final String text) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (statusMessage != null) {
                    statusMessage.setText(text);
                    Log.d(TAG, "Status message updated: " + text);
                }
            }
        });
    }

    /**
     * Setup fullscreen mode to use full 480x480 resolution on Blade 2
     */
    private void setupFullscreen() {
        // Hide the status bar and navigation bar to get full screen
        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN
        );

        // For API 19+ (KitKat and above), enable immersive fullscreen
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            );
        }

        Log.d(TAG, "Fullscreen mode enabled for 480x480 resolution");
    }

    /**
     * Remove any default padding/margins applied by ActionMenu container so the layout can stretch
     * across the entire 480x480 display.
     */
    private void maximizeContentRealEstate() {
        View rootContainer = findViewById(R.id.root_container);
        if (rootContainer != null) {
            ViewGroup.LayoutParams params = rootContainer.getLayoutParams();
            if (params instanceof ViewGroup.MarginLayoutParams) {
                ((ViewGroup.MarginLayoutParams) params).setMargins(0, 0, 0, 0);
            }
            rootContainer.setLayoutParams(params);
            rootContainer.setPadding(0, 0, 0, 0);
            ViewCompat.setOnApplyWindowInsetsListener(rootContainer, (v, insets) -> WindowInsetsCompat.CONSUMED);
        }
    }

    /**
     * Maintain fullscreen mode when window regains focus
     */
    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            setupFullscreen();
        }
    }

    /**
     * Check and request camera permission
     */
    private void checkAndRequestCameraPermission() {
        if (ContextCompat.checkSelfPermission(this, android.Manifest.permission.CAMERA) 
                != PackageManager.PERMISSION_GRANTED) {
            // Request camera permission
            ActivityCompat.requestPermissions(this,
                    new String[]{android.Manifest.permission.CAMERA},
                    CAMERA_PERMISSION_REQUEST_CODE);
        } else {
            // Permission already granted, start camera service
            startCameraService();
        }
    }

    /**
     * Handle permission request results
     */
    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        
        if (requestCode == CAMERA_PERMISSION_REQUEST_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                // Camera permission granted, start service
                startCameraService();
            } else {
                // Permission denied, show message
                showToast("Camera permission is required for AI Assistant features");
            }
        }
    }

    /**
     * Start the camera capture service
     */
    private void startCameraService() {
        Intent serviceIntent = new Intent(this, CameraCaptureService.class);
        startService(serviceIntent);
        showToast("AI Assistant camera service started");
    }

    /**
     * Setup broadcast receiver for face recognition results
     */
    private void setupRecognitionReceiver() {
        recognitionReceiver = new FaceRecognitionBroadcastReceiver();
        recognitionReceiver.setFaceRecognitionListener(this);

        IntentFilter filter = new IntentFilter(FaceRecognitionBroadcastReceiver.ACTION_FACE_RECOGNIZED);
        registerReceiver(recognitionReceiver, filter);
    }

    /**
     * Play a simple beep sound through the speaker
     */
    private void playWelcomeBeep() {
        try {
            Log.d(TAG, "Playing welcome beep sound");
            updateStatusMessage("Playing beep sound...");

            // Create tone generator with notification stream at max volume
            toneGenerator = new ToneGenerator(AudioManager.STREAM_NOTIFICATION, 100);

            // Play a double beep pattern: beep-pause-beep
            toneGenerator.startTone(ToneGenerator.TONE_PROP_BEEP, 200); // 200ms beep

            // Schedule second beep after 300ms
            new Handler().postDelayed(new Runnable() {
                @Override
                public void run() {
                    if (toneGenerator != null) {
                        toneGenerator.startTone(ToneGenerator.TONE_PROP_BEEP, 200);
                    }
                }
            }, 300);

            Log.d(TAG, "Beep sound played successfully");
        } catch (Exception e) {
            Log.e(TAG, "Error playing beep sound: " + e.getMessage());
            updateStatusMessage("Error playing beep: " + e.getMessage());
        }
    }

    /**
     * Initialize Text-to-Speech engine
     *
     * NOTE: TTS is initialized for the welcome message and future use.
     * Face recognition announcements are controlled by ENABLE_VOICE_ANNOUNCEMENTS flag.
     */
    private void initializeTextToSpeech() {
        Log.d(TAG, "======== TTS INITIALIZATION DEBUG START ========");

        // Check system settings for TTS
        try {
            String defaultEngine = android.provider.Settings.Secure.getString(
                getContentResolver(),
                android.provider.Settings.Secure.TTS_DEFAULT_SYNTH
            );
            Log.d(TAG, "System default TTS engine: " + defaultEngine);
            updateStatusMessage("Default TTS: " + defaultEngine);
        } catch (Exception e) {
            Log.e(TAG, "Error reading TTS settings: " + e.getMessage());
        }

        Log.d(TAG, "Creating TextToSpeech instance...");
        updateStatusMessage("Initializing TTS...");

        try {
            // Use the default TTS engine (whatever is set as system default)
            textToSpeech = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
                @Override
                public void onInit(int status) {
                    Log.d(TAG, "======== TTS onInit CALLBACK ========");
                    Log.d(TAG, "Status code: " + status);
                    Log.d(TAG, "SUCCESS=0, ERROR=-1, Expected: 0");

                    if (status == TextToSpeech.SUCCESS) {
                        Log.d(TAG, "✓ TTS initialization successful!");
                        updateStatusMessage("TTS initialized successfully");

                        // Get engine info
                        try {
                            String defaultEngine = textToSpeech.getDefaultEngine();
                            Log.d(TAG, "Default engine: " + defaultEngine);

                            java.util.List<TextToSpeech.EngineInfo> engines = textToSpeech.getEngines();
                            Log.d(TAG, "Available engines count: " + engines.size());
                            for (TextToSpeech.EngineInfo engine : engines) {
                                Log.d(TAG, "  - Engine: " + engine.name + " (label: " + engine.label + ")");
                            }
                        } catch (Exception e) {
                            Log.e(TAG, "Error getting engine info: " + e.getMessage());
                        }

                        // Check available languages
                        try {
                            java.util.Set<Locale> availableLocales = textToSpeech.getAvailableLanguages();
                            if (availableLocales != null) {
                                Log.d(TAG, "Available languages count: " + availableLocales.size());
                                for (Locale locale : availableLocales) {
                                    Log.d(TAG, "  - Language: " + locale.toString());
                                }
                            } else {
                                Log.w(TAG, "No available languages returned (null)");
                            }
                        } catch (Exception e) {
                            Log.e(TAG, "Error getting available languages: " + e.getMessage());
                        }

                        // Try to set language to US English
                        Log.d(TAG, "Attempting to set language to US English...");
                        int result = textToSpeech.setLanguage(Locale.US);
                        Log.d(TAG, "setLanguage result code: " + result);
                        Log.d(TAG, "LANG_AVAILABLE=0, LANG_COUNTRY_AVAILABLE=1, LANG_COUNTRY_VAR_AVAILABLE=2");
                        Log.d(TAG, "LANG_MISSING_DATA=-1, LANG_NOT_SUPPORTED=-2");

                        if (result == TextToSpeech.LANG_MISSING_DATA) {
                            Log.e(TAG, "✗ Language data is missing!");
                            updateStatusMessage("TTS: Language data missing");
                        } else if (result == TextToSpeech.LANG_NOT_SUPPORTED) {
                            Log.e(TAG, "✗ Language not supported!");
                            updateStatusMessage("TTS: Language not supported");
                        } else if (result >= TextToSpeech.LANG_AVAILABLE) {
                            Log.d(TAG, "✓ Language set successfully (code: " + result + ")");

                            // Get current language
                            Locale currentLocale = textToSpeech.getLanguage();
                            Log.d(TAG, "Current TTS language: " + currentLocale);

                            // Set up utterance progress listener
                            Log.d(TAG, "Setting up utterance progress listener...");
                            textToSpeech.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                                @Override
                                public void onStart(String utteranceId) {
                                    Log.d(TAG, "✓ TTS started speaking: " + utteranceId);
                                    updateStatusMessage("Speaking welcome message...");
                                }

                                @Override
                                public void onDone(String utteranceId) {
                                    Log.d(TAG, "✓ TTS finished speaking: " + utteranceId);
                                    updateStatusMessage("System Ready");
                                }

                                @Override
                                public void onError(String utteranceId) {
                                    Log.e(TAG, "✗ TTS error for utterance: " + utteranceId);
                                    updateStatusMessage("TTS error occurred");
                                }
                            });

                            // Add a small delay before speaking to ensure everything is ready
                            Log.d(TAG, "Scheduling welcome message in 500ms...");
                            new Handler().postDelayed(new Runnable() {
                                @Override
                                public void run() {
                                    speakWelcomeMessage();
                                }
                            }, 500); // 500ms delay
                        } else {
                            Log.e(TAG, "✗ Unexpected language result: " + result);
                            updateStatusMessage("TTS: Unexpected error");
                        }
                    } else if (status == TextToSpeech.ERROR) {
                        Log.e(TAG, "✗ TTS initialization failed with ERROR status");
                        Log.e(TAG, "This usually means:");
                        Log.e(TAG, "  1. No TTS engine is installed");
                        Log.e(TAG, "  2. TTS engine is installed but not configured");
                        Log.e(TAG, "  3. TTS service is not running");
                        updateStatusMessage("TTS initialization failed");

                        // Try to get more info
                        try {
                            String defaultEngine = android.provider.Settings.Secure.getString(
                                getContentResolver(),
                                android.provider.Settings.Secure.TTS_DEFAULT_SYNTH
                            );
                            Log.e(TAG, "  Current default engine setting: " + defaultEngine);
                        } catch (Exception e) {
                            Log.e(TAG, "  Could not read default engine: " + e.getMessage());
                        }
                    } else {
                        Log.e(TAG, "✗ TTS initialization failed with unknown status: " + status);
                        updateStatusMessage("TTS: Unknown error");
                    }

                    Log.d(TAG, "======== TTS onInit CALLBACK END ========");
                }
            });

            Log.d(TAG, "TextToSpeech instance created, waiting for onInit callback...");

        } catch (Exception e) {
            Log.e(TAG, "✗ Exception creating TextToSpeech: " + e.getMessage());
            Log.e(TAG, "Stack trace:", e);
            updateStatusMessage("TTS Exception: " + e.getMessage());
        }

        Log.d(TAG, "======== TTS INITIALIZATION DEBUG END ========");
    }

    /**
     * Speak the welcome message
     */
    private void speakWelcomeMessage() {
        Log.d(TAG, "======== SPEAK WELCOME MESSAGE ========");

        if (textToSpeech != null) {
            String welcomeText = "Welcome to AI assistant SAMA ";
            Log.d(TAG, "TTS object is not null");
            Log.d(TAG, "Text to speak: \"" + welcomeText + "\"");
            updateStatusMessage("About to speak welcome message");

            try {
                // Check if TTS is still speaking
                boolean isSpeaking = textToSpeech.isSpeaking();
                Log.d(TAG, "Is currently speaking: " + isSpeaking);

                // Try to speak
                Log.d(TAG, "Calling textToSpeech.speak()...");
                int result = textToSpeech.speak(welcomeText, TextToSpeech.QUEUE_FLUSH, null, "WELCOME_UTTERANCE");
                Log.d(TAG, "speak() returned: " + result + " (SUCCESS=0, ERROR=-1)");

                if (result == TextToSpeech.ERROR) {
                    Log.e(TAG, "✗ speak() failed with ERROR");
                    updateStatusMessage("TTS speak failed");
                } else if (result == TextToSpeech.SUCCESS) {
                    Log.d(TAG, "✓ speak() queued successfully");
                    Log.d(TAG, "Waiting for onStart callback...");
                } else {
                    Log.w(TAG, "speak() returned unexpected code: " + result);
                }
            } catch (Exception e) {
                Log.e(TAG, "✗ Exception during speak(): " + e.getMessage());
                Log.e(TAG, "Stack trace:", e);
                updateStatusMessage("TTS Exception: " + e.getMessage());
            }
        } else {
            Log.e(TAG, "✗ textToSpeech is null in speakWelcomeMessage()");
            updateStatusMessage("TTS not initialized");
        }

        Log.d(TAG, "======== SPEAK WELCOME MESSAGE END ========");
    }

    /**
     * Implementation of FaceRecognitionListener interface
     */
    @Override
    public void onFaceRecognized(String displayName, String personName, String relationship,
                                 double confidence, int facesDetected, String filename, String imagePath) {
        long receivedTime = System.currentTimeMillis();
        Log.d(TAG, "[TIMING] Broadcast received in Activity at: " + receivedTime);

        // Update UI on UI thread
        runOnUiThread(() -> {
            long uiUpdateStartTime = System.currentTimeMillis();
            Log.d(TAG, "[TIMING] UI update started at: " + uiUpdateStartTime);

            // Thumbnail rendering disabled to keep the HUD text-only.
            // displayThumbnail(imagePath);

            updateBannerWithRecognitionResult(displayName, personName, confidence);

            long uiUpdateEndTime = System.currentTimeMillis();
            Log.d(TAG, "[TIMING] *** UI DISPLAY UPDATED at: " + uiUpdateEndTime + " ***");
            Log.d(TAG, "[TIMING] UI update took: " + (uiUpdateEndTime - uiUpdateStartTime) + "ms");
            Log.d(TAG, "═══════════════════════════════════════════════");

            // Voice announcement (controlled by ENABLE_VOICE_ANNOUNCEMENTS flag)
            // Only announce if recognized person AND person changed
            // Don't announce "No known person found!"
            if (ENABLE_VOICE_ANNOUNCEMENTS &&
                !displayName.equals("No known person found!") &&
                !displayName.equals(lastRecognizedPerson)) {
                lastRecognizedPerson = displayName;
                announceRecognition(displayName);
            }
        });
    }

    @Override
    public void onRecognitionError(String errorMessage) {
        // Update UI on UI thread
        runOnUiThread(() -> {
            if (welcomeBanner != null) {
                welcomeBanner.setText("Error: " + errorMessage);
            }
            updateStatusMessage("Recognition error: " + errorMessage);
            Log.e(TAG, "Face recognition error: " + errorMessage);
        });
    }

    /**
     * Display thumbnail image on the left/middle side
     */
    private void displayThumbnail(String imagePath) {
        if (thumbnailImage != null && imagePath != null) {
            try {
                java.io.File imageFile = new java.io.File(imagePath);
                if (imageFile.exists()) {
                    android.graphics.Bitmap bitmap = android.graphics.BitmapFactory.decodeFile(imagePath);
                    if (bitmap != null) {
                        thumbnailImage.setImageBitmap(bitmap);
                        thumbnailImage.setVisibility(android.view.View.VISIBLE);
                        Log.d(TAG, "Thumbnail displayed: " + imagePath);
                    } else {
                        Log.w(TAG, "Failed to decode thumbnail bitmap");
                    }
                } else {
                    Log.w(TAG, "Thumbnail file does not exist: " + imagePath);
                }
            } catch (Exception e) {
                Log.e(TAG, "Error displaying thumbnail", e);
            }
        }
    }

    /**
     * Update the welcome banner with face recognition result
     */
    private void updateBannerWithRecognitionResult(String displayName, String personName, double confidence) {
        // If no person found, show in top banner
        if (displayName.equals("No known person found!")) {
            if (welcomeBanner != null) {
                welcomeBanner.setText("No person found");
            }
            updateStatusMessage("No known person found!");
        } else {
            // Person recognized - update welcome banner
            if (welcomeBanner != null) {
                String message = displayName;

                // Add confidence if available and person was recognized
                if (confidence >= 0 && personName != null && !personName.equals("Unknown Person")) {
                    message += String.format(" [%.0f%%]", confidence * 100);
                }

                welcomeBanner.setText(message);
            }
            updateStatusMessage("Recognized: " + displayName);
        }
    }

    /**
     * Announce recognized person via TTS
     *
     * NOTE: Voice announcements are currently DISABLED via ENABLE_VOICE_ANNOUNCEMENTS flag.
     * This method is kept intact for future use.
     *
     * TO ENABLE: Change ENABLE_VOICE_ANNOUNCEMENTS to true at line 52
     */
    private void announceRecognition(String displayName) {
        if (textToSpeech != null) {
            String announcement;
            if (displayName.equals("No person found!")) {
                announcement = "No person found";
            } else {
                announcement = displayName;
            }

            Log.d(TAG, "Announcing: " + announcement);
            textToSpeech.speak(announcement, TextToSpeech.QUEUE_FLUSH, null, "RECOGNITION_" + System.currentTimeMillis());
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

        // Release ToneGenerator
        if (toneGenerator != null) {
            toneGenerator.release();
            toneGenerator = null;
        }

        // Shutdown Text-to-Speech
        if (textToSpeech != null) {
            textToSpeech.stop();
            textToSpeech.shutdown();
            textToSpeech = null;
        }

        // Unregister broadcast receiver
        if (recognitionReceiver != null) {
            unregisterReceiver(recognitionReceiver);
            recognitionReceiver = null;
        }

        // Stop the camera service when activity is destroyed
        Intent serviceIntent = new Intent(this, CameraCaptureService.class);
        stopService(serviceIntent);
    }

}
