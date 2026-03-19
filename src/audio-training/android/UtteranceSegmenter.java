package devkit.blade.vuzix.com.blade_template_app.audiotraining;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.UUID;

public class UtteranceSegmenter {
    private static final double SPEECH_RMS_THRESHOLD = 900.0d;

    private final ByteArrayOutputStream currentUtterance = new ByteArrayOutputStream();
    private long utteranceStartMs = 0L;
    private long lastSpeechMs = 0L;
    private boolean speechActive = false;

    public void appendAudioChunk(AudioTrainingModels.AudioChunk chunk) {
        if (chunk.rms >= SPEECH_RMS_THRESHOLD) {
            if (!speechActive) {
                currentUtterance.reset();
                utteranceStartMs = chunk.timestampMs;
            }
            speechActive = true;
            lastSpeechMs = chunk.timestampMs;
        }

        if (!speechActive) {
            return;
        }

        try {
            currentUtterance.write(chunk.pcmBytes);
        } catch (IOException ignored) {
        }
    }

    public boolean detectSpeechBoundary(long nowMs) {
        if (!speechActive) {
            return false;
        }

        long durationMs = nowMs - utteranceStartMs;
        boolean silenceExpired = nowMs - lastSpeechMs >= AudioTrainingConfig.getSilenceTimeoutMs();
        boolean utteranceTooLong = durationMs >= AudioTrainingConfig.getMaxUtteranceMs();
        return silenceExpired || utteranceTooLong;
    }

    public AudioTrainingModels.UtterancePayload finalizeUtterance() {
        if (!speechActive) {
            reset();
            return null;
        }

        long durationMs = Math.max(0L, lastSpeechMs - utteranceStartMs);
        if (durationMs < AudioTrainingConfig.getMinUtteranceMs()) {
            reset();
            return null;
        }

        AudioTrainingModels.UtterancePayload utterance = new AudioTrainingModels.UtterancePayload();
        utterance.utteranceId = UUID.randomUUID().toString();
        utterance.sourceFileName = utterance.utteranceId + ".wav";
        utterance.startMs = utteranceStartMs;
        utterance.endMs = lastSpeechMs;
        utterance.wavBytes = toWaveBytes(currentUtterance.toByteArray());
        reset();
        return utterance;
    }

    public void reset() {
        currentUtterance.reset();
        utteranceStartMs = 0L;
        lastSpeechMs = 0L;
        speechActive = false;
    }

    private byte[] toWaveBytes(byte[] pcmBytes) {
        int sampleRate = AudioTrainingConfig.getAudioSampleRate();
        int channels = AudioTrainingConfig.getAudioChannels();
        int byteRate = sampleRate * channels * AudioTrainingConfig.getAudioEncodingBytes();

        ByteBuffer header = ByteBuffer.allocate(44);
        header.order(ByteOrder.LITTLE_ENDIAN);
        header.put("RIFF".getBytes());
        header.putInt(36 + pcmBytes.length);
        header.put("WAVE".getBytes());
        header.put("fmt ".getBytes());
        header.putInt(16);
        header.putShort((short) 1);
        header.putShort((short) channels);
        header.putInt(sampleRate);
        header.putInt(byteRate);
        header.putShort((short) (channels * AudioTrainingConfig.getAudioEncodingBytes()));
        header.putShort((short) (AudioTrainingConfig.getAudioEncodingBytes() * 8));
        header.put("data".getBytes());
        header.putInt(pcmBytes.length);

        byte[] wavBytes = new byte[44 + pcmBytes.length];
        System.arraycopy(header.array(), 0, wavBytes, 0, 44);
        System.arraycopy(pcmBytes, 0, wavBytes, 44, pcmBytes.length);
        return wavBytes;
    }
}
