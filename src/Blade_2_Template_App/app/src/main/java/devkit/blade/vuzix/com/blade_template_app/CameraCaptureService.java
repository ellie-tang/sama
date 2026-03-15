package devkit.blade.vuzix.com.blade_template_app;

import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.ImageFormat;
import android.graphics.Matrix;
import android.hardware.camera2.*;
import android.media.Image;
import android.media.ImageReader;
import android.os.Environment;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.util.Log;
import android.util.Size;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.Arrays;
import java.util.Timer;
import java.util.TimerTask;

/**
 * Service for capturing images every 1 seconds and sending to face recognition server
 */
public class CameraCaptureService extends Service {
    private static final String TAG = "CameraCaptureService";
    private static final int CAPTURE_INTERVAL_MS = 1000; // 1 seconds
    
    private CameraManager cameraManager;
    private String cameraId;
    private CameraDevice cameraDevice;
    private CameraCaptureSession captureSession;
    private ImageReader imageReader;
    private Handler backgroundHandler;
    private HandlerThread backgroundThread;
    private Timer captureTimer;
    private FaceRecognitionApiClient apiClient;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "Service created");

        cameraManager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        apiClient = new FaceRecognitionApiClient(this);

        startBackgroundThread();
        initializeCamera();
        startPeriodicCapture();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.d(TAG, "Service started");
        return START_STICKY; // Restart if killed
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        Log.d(TAG, "Service destroyed");
        
        if (captureTimer != null) {
            captureTimer.cancel();
            captureTimer = null;
        }
        
        closeCamera();
        stopBackgroundThread();
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null; // Not a bound service
    }

    private void startBackgroundThread() {
        backgroundThread = new HandlerThread("CameraBackground");
        backgroundThread.start();
        backgroundHandler = new Handler(backgroundThread.getLooper());
    }

    private void stopBackgroundThread() {
        if (backgroundThread != null) {
            backgroundThread.quitSafely();
            try {
                backgroundThread.join();
                backgroundThread = null;
                backgroundHandler = null;
            } catch (InterruptedException e) {
                Log.e(TAG, "Error stopping background thread", e);
            }
        }
    }

    private void initializeCamera() {
        try {
            // Get back-facing camera
            for (String camId : cameraManager.getCameraIdList()) {
                CameraCharacteristics characteristics = cameraManager.getCameraCharacteristics(camId);
                Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
                if (facing != null && facing == CameraCharacteristics.LENS_FACING_BACK) {
                    cameraId = camId;
                    break;
                }
            }

            if (cameraId == null) {
                Log.e(TAG, "No back-facing camera found");
                return;
            }

            // Get optimal camera resolution
            CameraCharacteristics characteristics = cameraManager.getCameraCharacteristics(cameraId);
            Size[] jpegSizes = characteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP)
                    .getOutputSizes(ImageFormat.JPEG);
            
            // Choose a good resolution (not the largest to avoid memory issues)
            Size captureSize = jpegSizes.length > 1 ? jpegSizes[1] : jpegSizes[0];
            Log.d(TAG, "Using capture resolution: " + captureSize.getWidth() + "x" + captureSize.getHeight());
            
            // Setup ImageReader for capturing images
            imageReader = ImageReader.newInstance(captureSize.getWidth(), captureSize.getHeight(), ImageFormat.JPEG, 1);
            imageReader.setOnImageAvailableListener(imageAvailableListener, backgroundHandler);

        } catch (CameraAccessException e) {
            Log.e(TAG, "Camera access exception", e);
        }
    }

    private void openCamera() {
        try {
            cameraManager.openCamera(cameraId, stateCallback, backgroundHandler);
        } catch (CameraAccessException e) {
            Log.e(TAG, "Error opening camera", e);
        } catch (SecurityException e) {
            Log.e(TAG, "Camera permission not granted", e);
        }
    }

    private void closeCamera() {
        if (captureSession != null) {
            captureSession.close();
            captureSession = null;
        }
        if (cameraDevice != null) {
            cameraDevice.close();
            cameraDevice = null;
        }
        if (imageReader != null) {
            imageReader.close();
            imageReader = null;
        }
    }

    private final CameraDevice.StateCallback stateCallback = new CameraDevice.StateCallback() {
        @Override
        public void onOpened(@NonNull CameraDevice camera) {
            Log.d(TAG, "Camera opened");
            cameraDevice = camera;
            createCaptureSession();
        }

        @Override
        public void onDisconnected(@NonNull CameraDevice camera) {
            Log.d(TAG, "Camera disconnected");
            camera.close();
            cameraDevice = null;
        }

        @Override
        public void onError(@NonNull CameraDevice camera, int error) {
            Log.e(TAG, "Camera error: " + error);
            camera.close();
            cameraDevice = null;
        }
    };

    private void createCaptureSession() {
        try {
            cameraDevice.createCaptureSession(Arrays.asList(imageReader.getSurface()),
                    new CameraCaptureSession.StateCallback() {
                        @Override
                        public void onConfigured(@NonNull CameraCaptureSession session) {
                            Log.d(TAG, "Capture session configured");
                            captureSession = session;
                        }

                        @Override
                        public void onConfigureFailed(@NonNull CameraCaptureSession session) {
                            Log.e(TAG, "Capture session configuration failed");
                        }
                    }, backgroundHandler);
        } catch (CameraAccessException e) {
            Log.e(TAG, "Error creating capture session", e);
        }
    }

    private void startPeriodicCapture() {
        captureTimer = new Timer();
        captureTimer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                captureImage();
            }
        }, 2000, CAPTURE_INTERVAL_MS); // Start after 2 seconds, then every 1 seconds
    }

    private void captureImage() {
        if (cameraDevice == null || captureSession == null) {
            Log.w(TAG, "Camera not ready for capture");
            openCamera(); // Try to reopen camera
            return;
        }

        // Capture immediately with continuous auto-focus (no manual trigger needed)
        // This eliminates the 500ms auto-focus delay
        performActualCapture();
    }

    private void triggerAutoFocus() throws CameraAccessException {
        Log.d(TAG, "Triggering auto-focus");
        
        CaptureRequest.Builder focusBuilder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
        focusBuilder.addTarget(imageReader.getSurface());
        
        // Trigger auto-focus
        focusBuilder.set(CaptureRequest.CONTROL_MODE, CameraMetadata.CONTROL_MODE_AUTO);
        focusBuilder.set(CaptureRequest.CONTROL_AF_MODE, CameraMetadata.CONTROL_AF_MODE_AUTO);
        focusBuilder.set(CaptureRequest.CONTROL_AF_TRIGGER, CameraMetadata.CONTROL_AF_TRIGGER_START);
        focusBuilder.set(CaptureRequest.CONTROL_AE_MODE, CameraMetadata.CONTROL_AE_MODE_ON);
        focusBuilder.set(CaptureRequest.CONTROL_AWB_MODE, CameraMetadata.CONTROL_AWB_MODE_AUTO);

        captureSession.capture(focusBuilder.build(), new CameraCaptureSession.CaptureCallback() {
            @Override
            public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                                           @NonNull CaptureRequest request,
                                           @NonNull TotalCaptureResult result) {
                // Check if auto-focus is finished
                Integer afState = result.get(CaptureResult.CONTROL_AF_STATE);
                if (afState != null && 
                    (afState == CaptureResult.CONTROL_AF_STATE_FOCUSED_LOCKED || 
                     afState == CaptureResult.CONTROL_AF_STATE_NOT_FOCUSED_LOCKED)) {
                    Log.d(TAG, "Auto-focus completed, taking picture");
                    // Focus is done, now take the actual picture
                    performActualCapture();
                } else {
                    // Wait a bit more and try capture anyway
                    backgroundHandler.postDelayed(() -> performActualCapture(), 500);
                }
            }

            @Override
            public void onCaptureFailed(@NonNull CameraCaptureSession session,
                                        @NonNull CaptureRequest request,
                                        @NonNull CaptureFailure failure) {
                Log.w(TAG, "Auto-focus failed, capturing anyway");
                performActualCapture();
            }
        }, backgroundHandler);
    }

    private void performActualCapture() {
        try {
            Log.d(TAG, "Performing actual image capture");
            
            CaptureRequest.Builder captureBuilder = cameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
            captureBuilder.addTarget(imageReader.getSurface());
            
            // Configure capture settings for best quality
            captureBuilder.set(CaptureRequest.CONTROL_MODE, CameraMetadata.CONTROL_MODE_AUTO);
            // Use continuous auto-focus for faster captures (no manual trigger needed)
            captureBuilder.set(CaptureRequest.CONTROL_AF_MODE, CameraMetadata.CONTROL_AF_MODE_CONTINUOUS_PICTURE);
            captureBuilder.set(CaptureRequest.CONTROL_AE_MODE, CameraMetadata.CONTROL_AE_MODE_ON);
            captureBuilder.set(CaptureRequest.CONTROL_AWB_MODE, CameraMetadata.CONTROL_AWB_MODE_AUTO);
            
            // Enable optical stabilization if available
            try {
                captureBuilder.set(CaptureRequest.LENS_OPTICAL_STABILIZATION_MODE, 
                        CameraMetadata.LENS_OPTICAL_STABILIZATION_MODE_ON);
            } catch (Exception e) {
                Log.d(TAG, "Optical stabilization not available");
            }
            
            // Set high JPEG quality
            captureBuilder.set(CaptureRequest.JPEG_QUALITY, (byte) 95);

            captureSession.capture(captureBuilder.build(), new CameraCaptureSession.CaptureCallback() {
                @Override
                public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                                               @NonNull CaptureRequest request,
                                               @NonNull TotalCaptureResult result) {
                    Log.d(TAG, "High quality image capture completed");
                }

                @Override
                public void onCaptureFailed(@NonNull CameraCaptureSession session,
                                            @NonNull CaptureRequest request,
                                            @NonNull CaptureFailure failure) {
                    Log.e(TAG, "Image capture failed: " + failure.getReason());
                }
            }, backgroundHandler);

        } catch (CameraAccessException e) {
            Log.e(TAG, "Error performing actual capture", e);
        }
    }

    private final ImageReader.OnImageAvailableListener imageAvailableListener = new ImageReader.OnImageAvailableListener() {
        @Override
        public void onImageAvailable(ImageReader reader) {
            long captureTimestamp = System.currentTimeMillis();
            Log.d(TAG, "═══════════════════════════════════════════════");
            Log.d(TAG, "[TIMING] Image captured at: " + captureTimestamp);

            Image image = null;
            try {
                image = reader.acquireLatestImage();
                if (image != null) {
                    long processingStart = System.currentTimeMillis();
                    byte[] jpegBytes = prepareRotatedImageBytes(image);
                    long processingEnd = System.currentTimeMillis();
                    Log.d(TAG, "[TIMING] Image processing took: " + (processingEnd - processingStart) + "ms");

                    if (jpegBytes != null) {
                        Log.d(TAG, "Prepared in-memory JPEG (" + jpegBytes.length + " bytes)");
                        long sendTimestamp = System.currentTimeMillis();
                        Log.d(TAG, "[TIMING] Sending to API at: " + sendTimestamp + " (+" + (sendTimestamp - captureTimestamp) + "ms from capture)");
                        apiClient.processImageAsync(jpegBytes, captureTimestamp);
                    } else {
                        Log.w(TAG, "Failed to prepare JPEG bytes; skipping upload");
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "Error processing captured image", e);
            } finally {
                if (image != null) {
                    image.close();
                }
            }
        }
    };

    /**
     * Convert captured image into rotated JPEG bytes stored in memory.
     */
    private byte[] prepareRotatedImageBytes(Image image) {
        try {
            Image.Plane[] planes = image.getPlanes();
            ByteBuffer buffer = planes[0].getBuffer();
            byte[] bytes = new byte[buffer.remaining()];
            buffer.get(bytes);

            Bitmap originalBitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
            if (originalBitmap == null) {
                Log.e(TAG, "Failed to decode captured image");
                return null;
            }

            Bitmap rotatedBitmap = rotateImage(originalBitmap, 180);
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            rotatedBitmap.compress(Bitmap.CompressFormat.JPEG, 90, outputStream);
            byte[] jpegBytes = outputStream.toByteArray();
            outputStream.close();

            originalBitmap.recycle();
            rotatedBitmap.recycle();

            return jpegBytes;
        } catch (IOException e) {
            Log.e(TAG, "Error converting image to bytes", e);
            return null;
        } catch (Exception e) {
            Log.e(TAG, "Unexpected error preparing image bytes", e);
            return null;
        }
    }

    private File saveImageToTempFile(Image image) {
        try {
            // Get the JPEG data
            Image.Plane[] planes = image.getPlanes();
            ByteBuffer buffer = planes[0].getBuffer();
            byte[] bytes = new byte[buffer.remaining()];
            buffer.get(bytes);

            // Convert to bitmap for rotation
            Bitmap originalBitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
            if (originalBitmap == null) {
                Log.e(TAG, "Failed to decode image to bitmap");
                return null;
            }

            // Rotate image to correct orientation (180 degrees for Vuzix Blade 2)
            Bitmap rotatedBitmap = rotateImage(originalBitmap, 180);
            
            // Create temporary file
            File tmpDir = new File(getExternalFilesDir(Environment.DIRECTORY_PICTURES), "tmp");
            if (!tmpDir.exists()) {
                tmpDir.mkdirs();
            }

            String filename = "capture_" + System.currentTimeMillis() + ".jpg";
            File tmpFile = new File(tmpDir, filename);

            // Save rotated bitmap to file
            try (FileOutputStream output = new FileOutputStream(tmpFile)) {
                rotatedBitmap.compress(Bitmap.CompressFormat.JPEG, 90, output);
                output.flush();
            }

            // Clean up bitmaps
            originalBitmap.recycle();
            rotatedBitmap.recycle();

            return tmpFile;

        } catch (IOException e) {
            Log.e(TAG, "Error saving image to temp file", e);
            return null;
        } catch (Exception e) {
            Log.e(TAG, "Error processing image", e);
            return null;
        }
    }

    // Thumbnail generation is currently disabled in onImageAvailable, but we keep this helper for future use.
    /**
     * Save both full image and thumbnail
     * @return Array with [0] = full image file, [1] = thumbnail file
     */
    private File[] saveImageAndThumbnail(Image image) {
        try {
            // Get the JPEG data
            Image.Plane[] planes = image.getPlanes();
            ByteBuffer buffer = planes[0].getBuffer();
            byte[] bytes = new byte[buffer.remaining()];
            buffer.get(bytes);

            // Convert to bitmap for rotation
            Bitmap originalBitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
            if (originalBitmap == null) {
                Log.e(TAG, "Failed to decode image to bitmap");
                return null;
            }

            // Rotate image to correct orientation (180 degrees for Vuzix Blade 2)
            Bitmap rotatedBitmap = rotateImage(originalBitmap, 180);

            // Create directories
            File tmpDir = new File(getExternalFilesDir(Environment.DIRECTORY_PICTURES), "tmp");
            File thumbDir = new File(getExternalFilesDir(Environment.DIRECTORY_PICTURES), "thumbnails");
            if (!tmpDir.exists()) tmpDir.mkdirs();
            if (!thumbDir.exists()) thumbDir.mkdirs();

            String timestamp = String.valueOf(System.currentTimeMillis());
            File fullImageFile = new File(tmpDir, "capture_" + timestamp + ".jpg");
            File thumbnailFile = new File(thumbDir, "thumb_" + timestamp + ".jpg");

            // Save full resolution image
            try (FileOutputStream output = new FileOutputStream(fullImageFile)) {
                rotatedBitmap.compress(Bitmap.CompressFormat.JPEG, 90, output);
                output.flush();
            }

            // Create and save thumbnail (120x120 to match ImageView size)
            Bitmap thumbnailBitmap = Bitmap.createScaledBitmap(rotatedBitmap, 120, 120, true);
            try (FileOutputStream output = new FileOutputStream(thumbnailFile)) {
                thumbnailBitmap.compress(Bitmap.CompressFormat.JPEG, 85, output);
                output.flush();
            }

            // Clean up bitmaps
            originalBitmap.recycle();
            rotatedBitmap.recycle();
            thumbnailBitmap.recycle();

            return new File[]{fullImageFile, thumbnailFile};

        } catch (IOException e) {
            Log.e(TAG, "Error saving image and thumbnail", e);
            return null;
        } catch (Exception e) {
            Log.e(TAG, "Error processing image", e);
            return null;
        }
    }

    /**
     * Rotate image by specified degrees
     */
    private Bitmap rotateImage(Bitmap bitmap, int degrees) {
        Matrix matrix = new Matrix();
        matrix.postRotate(degrees);

        try {
            return Bitmap.createBitmap(bitmap, 0, 0, bitmap.getWidth(), bitmap.getHeight(), matrix, true);
        } catch (OutOfMemoryError e) {
            Log.e(TAG, "Out of memory rotating image", e);
            return bitmap; // Return original if rotation fails
        }
    }
}
