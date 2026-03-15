package devkit.blade.vuzix.com.blade_template_app;

import android.content.Context;
import android.content.Intent;
import android.util.Log;

import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;

import java.io.IOException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * Client for Face Recognition Web Server REST API
 * Based on client-server-api-spec.md
 */
public class FaceRecognitionApiClient {
    private static final String TAG = "FaceRecognitionAPI";

    // Server configuration - UPDATE THIS WITH YOUR SERVER IP
    private static final String SERVER_HOST = "192.168.1.201";
    private static final int SERVER_PORT = 8000;
    private static final String BASE_URL = "http://" + SERVER_HOST + ":" + SERVER_PORT;
    private static final String PROCESS_IMAGE_ENDPOINT = BASE_URL + "/api/process-image";

    private final OkHttpClient httpClient;
    private final ExecutorService executorService;
    private final Context context;
    private final Gson gson;

    /**
     * Response model matching the API specification
     */
    public static class FaceRecognitionResponse {
        @SerializedName("success")
        public boolean success;

        @SerializedName("person_name")
        public String personName;

        @SerializedName("relationship")
        public String relationship;

        @SerializedName("confidence")
        public Double confidence;

        @SerializedName("faces_detected")
        public int facesDetected;

        @SerializedName("message")
        public String message;

        @SerializedName("timestamp")
        public String timestamp;

        @Override
        public String toString() {
            return "FaceRecognitionResponse{" +
                    "success=" + success +
                    ", personName='" + personName + '\'' +
                    ", relationship='" + relationship + '\'' +
                    ", confidence=" + confidence +
                    ", facesDetected=" + facesDetected +
                    ", message='" + message + '\'' +
                    ", timestamp='" + timestamp + '\'' +
                    '}';
        }
    }

    public FaceRecognitionApiClient(Context context) {
        this.context = context;
        this.gson = new Gson();
        this.executorService = Executors.newSingleThreadExecutor();

        // Configure OkHttp client with timeouts
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .writeTimeout(10, TimeUnit.SECONDS)
                .readTimeout(10, TimeUnit.SECONDS)
                .build();
    }

    /**
     * Process image asynchronously to avoid blocking the main thread
     */
    public void processImageAsync(byte[] imageData, long captureTimestamp) {
        executorService.execute(() -> processImage(imageData, captureTimestamp));
    }

    /**
     * Send image to server for face recognition processing
     */
    private void processImage(byte[] imageData, long captureTimestamp) {
        if (imageData == null || imageData.length == 0) {
            Log.e(TAG, "Image data is null or empty");
            return;
        }

        try {
            long requestStartTime = System.currentTimeMillis();
            Log.d(TAG, "[TIMING] Starting HTTP request at: " + requestStartTime + " (+" + (requestStartTime - captureTimestamp) + "ms from capture)");
            String filename = "capture_" + captureTimestamp + ".jpg";
            Log.d(TAG, "Processing image: " + filename);

            // Create multipart request body
            long buildStartTime = System.currentTimeMillis();
            RequestBody requestBody = new MultipartBody.Builder()
                    .setType(MultipartBody.FORM)
                    .addFormDataPart("file", filename,
                            RequestBody.create(imageData, MediaType.parse("image/jpeg")))
                    .build();

            // Build the request
            Request request = new Request.Builder()
                    .url(PROCESS_IMAGE_ENDPOINT)
                    .post(requestBody)
                    .build();
            long buildEndTime = System.currentTimeMillis();
            Log.d(TAG, "[TIMING] Request build took: " + (buildEndTime - buildStartTime) + "ms");

            // Execute the request
            Log.d(TAG, "[TIMING] Sending HTTP POST to server...");
            long networkStartTime = System.currentTimeMillis();
            try (Response response = httpClient.newCall(request).execute()) {
                long networkEndTime = System.currentTimeMillis();
                Log.d(TAG, "[TIMING] *** SERVER RESPONSE RECEIVED at: " + networkEndTime + " ***");
                Log.d(TAG, "[TIMING] *** SERVER PROCESSING TIME: " + (networkEndTime - networkStartTime) + "ms ***");
                Log.d(TAG, "[TIMING] Total time from capture to response: " + (networkEndTime - captureTimestamp) + "ms");
                handleResponse(response, filename, captureTimestamp);
            }

        } catch (IOException e) {
            Log.e(TAG, "Network error processing image data", e);
            sendErrorNotification("Network error: " + e.getMessage());
        } catch (Exception e) {
            Log.e(TAG, "Error processing image data", e);
            sendErrorNotification("Error: " + e.getMessage());
        }
    }

    /**
     * Handle HTTP response from server
     */
    private void handleResponse(Response response, String filename, long captureTimestamp) throws IOException {
        long parseStartTime = System.currentTimeMillis();
        int statusCode = response.code();
        String responseBody = response.body() != null ? response.body().string() : "";

        Log.d(TAG, "Response status: " + statusCode);
        Log.d(TAG, "Response body: " + responseBody);

        if (statusCode == 200) {
            // Parse successful response
            try {
                FaceRecognitionResponse result = gson.fromJson(responseBody, FaceRecognitionResponse.class);
                long parseEndTime = System.currentTimeMillis();
                Log.d(TAG, "[TIMING] JSON parsing took: " + (parseEndTime - parseStartTime) + "ms");
                Log.i(TAG, "Face recognition result: " + result.toString());

                if (result.success) {
                    handleSuccessfulRecognition(result, filename, captureTimestamp);
                } else {
                    Log.w(TAG, "Recognition was not successful: " + result.message);
                    sendErrorNotification("Recognition failed: " + result.message);
                }
            } catch (Exception e) {
                Log.e(TAG, "Error parsing response JSON", e);
                sendErrorNotification("Error parsing response");
            }
        } else if (statusCode == 400) {
            Log.e(TAG, "Bad request - invalid image file");
            sendErrorNotification("Invalid image file");
        } else if (statusCode == 408) {
            Log.e(TAG, "Request timeout - server took too long");
            sendErrorNotification("Server timeout");
        } else if (statusCode == 413) {
            Log.e(TAG, "File too large (max 10MB)");
            sendErrorNotification("File too large");
        } else if (statusCode == 500) {
            Log.e(TAG, "Server error during processing");
            sendErrorNotification("Server error");
        } else {
            Log.e(TAG, "Unexpected status code: " + statusCode);
            sendErrorNotification("Unexpected error: " + statusCode);
        }
    }

    /**
     * Handle successful face recognition result
     */
    private void handleSuccessfulRecognition(FaceRecognitionResponse result, String filename, long captureTimestamp) {
        String displayName;

        if (result.facesDetected == 0) {
            // No faces detected
            displayName = "No known person found!";
            Log.i(TAG, "No faces detected in image");
        } else if (result.personName == null || result.personName.equals("Unknown Person")) {
            // Face detected but not recognized
            displayName = "No known person found!";
            Log.i(TAG, "Face detected but not recognized");
        } else {
            // Person recognized
            displayName = result.personName;
            if (result.relationship != null && !result.relationship.equals("Unknown")) {
                displayName += " (" + result.relationship + ")";
            }
            Log.i(TAG, "Person recognized: " + displayName +
                    " with confidence: " + (result.confidence != null ? result.confidence : "N/A"));
        }

        // Send broadcast notification with recognition result
        long broadcastTime = System.currentTimeMillis();
        Log.d(TAG, "[TIMING] Sending broadcast at: " + broadcastTime + " (+" + (broadcastTime - captureTimestamp) + "ms from capture)");
        sendRecognitionNotification(displayName, result, filename, null);
    }

    /**
     * Send broadcast notification with face recognition result
     */
    private void sendRecognitionNotification(String displayName, FaceRecognitionResponse result, String filename, String thumbnailPath) {
        if (context != null) {
            Intent intent = new Intent(FaceRecognitionBroadcastReceiver.ACTION_FACE_RECOGNIZED);
            intent.putExtra(FaceRecognitionBroadcastReceiver.EXTRA_DISPLAY_NAME, displayName);
            intent.putExtra(FaceRecognitionBroadcastReceiver.EXTRA_PERSON_NAME, result.personName);
            intent.putExtra(FaceRecognitionBroadcastReceiver.EXTRA_RELATIONSHIP, result.relationship);
            intent.putExtra(FaceRecognitionBroadcastReceiver.EXTRA_CONFIDENCE, result.confidence != null ? result.confidence : -1.0);
            intent.putExtra(FaceRecognitionBroadcastReceiver.EXTRA_FACES_DETECTED, result.facesDetected);
            intent.putExtra(FaceRecognitionBroadcastReceiver.EXTRA_FILENAME, filename);
            intent.putExtra(FaceRecognitionBroadcastReceiver.EXTRA_IMAGE_PATH, thumbnailPath);
            context.sendBroadcast(intent);
            Log.d(TAG, "Sent recognition broadcast: " + displayName);
        }
    }

    /**
     * Send error notification
     */
    private void sendErrorNotification(String errorMessage) {
        if (context != null) {
            Intent intent = new Intent(FaceRecognitionBroadcastReceiver.ACTION_FACE_RECOGNIZED);
            intent.putExtra(FaceRecognitionBroadcastReceiver.EXTRA_DISPLAY_NAME, "Error: " + errorMessage);
            intent.putExtra(FaceRecognitionBroadcastReceiver.EXTRA_ERROR, errorMessage);
            context.sendBroadcast(intent);
            Log.d(TAG, "Sent error broadcast: " + errorMessage);
        }
    }

    /**
     * Shutdown the client service
     */
    public void shutdown() {
        if (executorService != null && !executorService.isShutdown()) {
            executorService.shutdown();
        }
    }
}
