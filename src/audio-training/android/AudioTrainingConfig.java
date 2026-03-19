package devkit.blade.vuzix.com.blade_template_app.audiotraining;

public final class AudioTrainingConfig {
    private static final String SERVER_HOST = "192.168.1.201";
    private static final int SERVER_PORT = 8010;
    private static final String BASE_URL = "http://" + SERVER_HOST + ":" + SERVER_PORT + "/audio-training";

    private static final int AUDIO_SAMPLE_RATE = 16000;
    private static final int AUDIO_CHANNELS = 1;
    private static final int AUDIO_ENCODING_BYTES = 2;
    private static final int PCM_READ_SIZE = 2048;
    private static final int MAX_UTTERANCE_MS = 8000;
    private static final int MIN_UTTERANCE_MS = 500;
    private static final int SILENCE_TIMEOUT_MS = 1200;
    private static final int CONVERSATION_GAP_MS = 4000;
    private static final double LOW_CONFIDENCE_THRESHOLD = 0.82d;

    private AudioTrainingConfig() {
    }

    public static String getServerBaseUrl() {
        return BASE_URL;
    }

    public static int getAudioSampleRate() {
        return AUDIO_SAMPLE_RATE;
    }

    public static int getAudioChannels() {
        return AUDIO_CHANNELS;
    }

    public static int getAudioEncodingBytes() {
        return AUDIO_ENCODING_BYTES;
    }

    public static int getPcmReadSize() {
        return PCM_READ_SIZE;
    }

    public static int getMaxUtteranceMs() {
        return MAX_UTTERANCE_MS;
    }

    public static int getMinUtteranceMs() {
        return MIN_UTTERANCE_MS;
    }

    public static int getSilenceTimeoutMs() {
        return SILENCE_TIMEOUT_MS;
    }

    public static int getConversationGapMs() {
        return CONVERSATION_GAP_MS;
    }

    public static double getLowConfidenceThreshold() {
        return LOW_CONFIDENCE_THRESHOLD;
    }
}
