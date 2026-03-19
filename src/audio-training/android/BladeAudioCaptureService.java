package devkit.blade.vuzix.com.blade_template_app.audiotraining;

import android.Manifest;
import android.app.Service;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.IBinder;
import android.util.Log;

import androidx.annotation.Nullable;
import androidx.core.content.ContextCompat;

public class BladeAudioCaptureService extends Service {
    private static final String TAG = "BladeAudioCapture";

    private AudioRecord audioRecord;
    private Thread captureThread;
    private volatile boolean running = false;

    private final UtteranceSegmenter utteranceSegmenter = new UtteranceSegmenter();
    private final ConversationWindowBuffer conversationBuffer = new ConversationWindowBuffer();
    private BladeContextFrameCollector frameCollector;
    private AudioTrainingApiClient apiClient;

    @Override
    public void onCreate() {
        super.onCreate();
        frameCollector = new BladeContextFrameCollector();
        frameCollector.startCameraContextCapture();
        apiClient = new AudioTrainingApiClient(this);
        initializeRecorder();
        startCaptureLoop();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        stopCaptureLoop();
        if (frameCollector != null) {
            frameCollector.stopCameraContextCapture();
        }
        super.onDestroy();
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    public void startCaptureLoop() {
        if (audioRecord == null || running) {
            return;
        }
        running = true;
        audioRecord.startRecording();
        captureThread = new Thread(this::captureAudioLoop, "BladeAudioCaptureThread");
        captureThread.start();
    }

    public void stopCaptureLoop() {
        running = false;
        if (captureThread != null) {
            captureThread.interrupt();
            captureThread = null;
        }
        if (audioRecord != null) {
            audioRecord.stop();
            audioRecord.release();
            audioRecord = null;
        }
    }

    public void initializeRecorder() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            Log.e(TAG, "RECORD_AUDIO permission is not granted.");
            return;
        }

        int minBufferSize = AudioRecord.getMinBufferSize(
                AudioTrainingConfig.getAudioSampleRate(),
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT
        );
        int bufferSize = Math.max(minBufferSize, AudioTrainingConfig.getPcmReadSize() * 2);
        audioRecord = new AudioRecord(
                MediaRecorder.AudioSource.MIC,
                AudioTrainingConfig.getAudioSampleRate(),
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                bufferSize
        );
    }

    public byte[] readPcmChunk() {
        if (audioRecord == null) {
            return null;
        }
        byte[] buffer = new byte[AudioTrainingConfig.getPcmReadSize()];
        int bytesRead = audioRecord.read(buffer, 0, buffer.length);
        if (bytesRead <= 0) {
            return null;
        }
        if (bytesRead == buffer.length) {
            return buffer;
        }
        byte[] exact = new byte[bytesRead];
        System.arraycopy(buffer, 0, exact, 0, bytesRead);
        return exact;
    }

    public AudioTrainingModels.UtterancePayload flushCurrentUtterance() {
        AudioTrainingModels.UtterancePayload utterance = utteranceSegmenter.finalizeUtterance();
        if (utterance != null) {
            AudioTrainingModels.ContextFrame frame = frameCollector.captureCompanionFrame();
            conversationBuffer.appendUtterance(utterance);
            conversationBuffer.appendContextFrame(frame);
        }
        return utterance;
    }

    public void handleVoiceActivityState(long nowMs) {
        if (utteranceSegmenter.detectSpeechBoundary(nowMs)) {
            flushCurrentUtterance();
        }
        if (conversationBuffer.shouldCloseConversationWindow(nowMs)) {
            AudioTrainingModels.ConversationWindow window = conversationBuffer.buildConversationWindow();
            if (window != null) {
                apiClient.uploadConversationWindowAsync(window);
            }
            conversationBuffer.clearExpiredWindow();
        }
    }

    private void captureAudioLoop() {
        while (running && !Thread.currentThread().isInterrupted()) {
            byte[] pcm = readPcmChunk();
            long nowMs = System.currentTimeMillis();
            if (pcm != null) {
                AudioTrainingModels.AudioChunk chunk = new AudioTrainingModels.AudioChunk(
                        pcm,
                        nowMs,
                        calculateRms(pcm)
                );
                utteranceSegmenter.appendAudioChunk(chunk);
            }
            handleVoiceActivityState(nowMs);
        }
    }

    private double calculateRms(byte[] pcmBytes) {
        if (pcmBytes.length < 2) {
            return 0d;
        }
        long sum = 0L;
        int sampleCount = pcmBytes.length / 2;
        for (int i = 0; i < pcmBytes.length - 1; i += 2) {
            short sample = (short) ((pcmBytes[i + 1] << 8) | (pcmBytes[i] & 0xff));
            sum += (long) sample * sample;
        }
        return Math.sqrt((double) sum / Math.max(sampleCount, 1));
    }
}
