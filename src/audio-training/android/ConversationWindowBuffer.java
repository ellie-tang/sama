package devkit.blade.vuzix.com.blade_template_app.audiotraining;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

public class ConversationWindowBuffer {
    private final List<AudioTrainingModels.UtterancePayload> utterances = new ArrayList<>();
    private final List<AudioTrainingModels.ContextFrame> contextFrames = new ArrayList<>();
    private long lastUtteranceEndMs = 0L;

    public void appendUtterance(AudioTrainingModels.UtterancePayload utterance) {
        utterances.add(utterance);
        lastUtteranceEndMs = utterance.endMs;
    }

    public void appendContextFrame(AudioTrainingModels.ContextFrame frame) {
        if (frame != null) {
            contextFrames.add(frame);
        }
    }

    public boolean shouldCloseConversationWindow(long nowMs) {
        return !utterances.isEmpty() && nowMs - lastUtteranceEndMs >= AudioTrainingConfig.getConversationGapMs();
    }

    public AudioTrainingModels.ConversationWindow buildConversationWindow() {
        if (utterances.isEmpty()) {
            return null;
        }

        AudioTrainingModels.ConversationWindow window = new AudioTrainingModels.ConversationWindow();
        window.conversationId = UUID.randomUUID().toString();
        window.deviceId = "vuzix-blade-2";
        window.capturedAtIso = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX", Locale.US).format(new Date());
        window.utterances.addAll(utterances);
        window.contextFrames.addAll(contextFrames);
        window.preferredTargetUtteranceId = utterances.get(0).utteranceId;
        window.metadata.put("collector", "BladeAudioCaptureService");
        window.metadata.put("audio_sample_rate", AudioTrainingConfig.getAudioSampleRate());
        return window;
    }

    public void clearExpiredWindow() {
        utterances.clear();
        contextFrames.clear();
        lastUtteranceEndMs = 0L;
    }
}
