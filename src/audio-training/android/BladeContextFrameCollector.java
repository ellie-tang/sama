package devkit.blade.vuzix.com.blade_template_app.audiotraining;

import android.util.Log;

import java.util.UUID;

public class BladeContextFrameCollector {
    private static final String TAG = "BladeContextFrames";
    private static final long FRAME_STALE_MS = 5000L;

    private byte[] latestFrameBytes;
    private long latestFrameTimestampMs;
    private String latestDescription;

    public void startCameraContextCapture() {
        Log.d(TAG, "Context frame collector ready. Wire submitLatestFrame() to the Blade camera pipeline.");
    }

    public void stopCameraContextCapture() {
        latestFrameBytes = null;
        latestFrameTimestampMs = 0L;
        latestDescription = null;
    }

    public synchronized void submitLatestFrame(byte[] jpegBytes, long timestampMs, String description) {
        latestFrameBytes = jpegBytes;
        latestFrameTimestampMs = timestampMs;
        latestDescription = description;
    }

    public synchronized AudioTrainingModels.ContextFrame captureCompanionFrame() {
        if (latestFrameBytes == null) {
            return null;
        }
        long now = System.currentTimeMillis();
        if (now - latestFrameTimestampMs > FRAME_STALE_MS) {
            return null;
        }
        AudioTrainingModels.ContextFrame frame = new AudioTrainingModels.ContextFrame();
        frame.frameId = UUID.randomUUID().toString();
        frame.sourceFileName = frame.frameId + ".jpg";
        frame.timestampMs = latestFrameTimestampMs;
        frame.description = latestDescription != null ? latestDescription : "blade2-camera-context";
        frame.jpegBytes = compressFrameForUpload(latestFrameBytes);
        return frame;
    }

    public byte[] compressFrameForUpload(byte[] jpegBytes) {
        return jpegBytes;
    }
}
