package devkit.blade.vuzix.com.blade_template_app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * BroadcastReceiver to handle face recognition result notifications
 */
public class FaceRecognitionBroadcastReceiver extends BroadcastReceiver {
    private static final String TAG = "FaceRecognitionReceiver";

    public static final String ACTION_FACE_RECOGNIZED = "devkit.blade.vuzix.com.blade_template_app.FACE_RECOGNIZED";
    public static final String EXTRA_DISPLAY_NAME = "display_name";
    public static final String EXTRA_PERSON_NAME = "person_name";
    public static final String EXTRA_RELATIONSHIP = "relationship";
    public static final String EXTRA_CONFIDENCE = "confidence";
    public static final String EXTRA_FACES_DETECTED = "faces_detected";
    public static final String EXTRA_FILENAME = "filename";
    public static final String EXTRA_IMAGE_PATH = "image_path";
    public static final String EXTRA_ERROR = "error";

    private FaceRecognitionListener listener;

    public interface FaceRecognitionListener {
        void onFaceRecognized(String displayName, String personName, String relationship,
                             double confidence, int facesDetected, String filename, String imagePath);
        void onRecognitionError(String errorMessage);
    }

    public void setFaceRecognitionListener(FaceRecognitionListener listener) {
        this.listener = listener;
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        if (ACTION_FACE_RECOGNIZED.equals(intent.getAction())) {
            String displayName = intent.getStringExtra(EXTRA_DISPLAY_NAME);
            String error = intent.getStringExtra(EXTRA_ERROR);

            Log.d(TAG, "Received face recognition notification");

            if (listener != null) {
                if (error != null) {
                    // Error occurred
                    Log.e(TAG, "Recognition error: " + error);
                    listener.onRecognitionError(error);
                } else if (displayName != null) {
                    // Successful recognition (or no face found)
                    String personName = intent.getStringExtra(EXTRA_PERSON_NAME);
                    String relationship = intent.getStringExtra(EXTRA_RELATIONSHIP);
                    double confidence = intent.getDoubleExtra(EXTRA_CONFIDENCE, -1.0);
                    int facesDetected = intent.getIntExtra(EXTRA_FACES_DETECTED, 0);
                    String filename = intent.getStringExtra(EXTRA_FILENAME);
                    String imagePath = intent.getStringExtra(EXTRA_IMAGE_PATH);

                    Log.d(TAG, "Face recognition result - Display: " + displayName +
                            ", Person: " + personName +
                            ", Faces: " + facesDetected);

                    listener.onFaceRecognized(displayName, personName, relationship,
                            confidence, facesDetected, filename, imagePath);
                }
            }
        }
    }
}
