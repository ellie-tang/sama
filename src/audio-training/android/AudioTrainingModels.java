package devkit.blade.vuzix.com.blade_template_app.audiotraining;

import com.google.gson.annotations.SerializedName;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class AudioTrainingModels {
    private AudioTrainingModels() {
    }

    public static class AudioChunk {
        public final byte[] pcmBytes;
        public final long timestampMs;
        public final double rms;

        public AudioChunk(byte[] pcmBytes, long timestampMs, double rms) {
            this.pcmBytes = pcmBytes;
            this.timestampMs = timestampMs;
            this.rms = rms;
        }
    }

    public static class ContextFrame {
        @SerializedName("frame_id")
        public String frameId;

        @SerializedName("source_file_name")
        public String sourceFileName;

        @SerializedName("timestamp_ms")
        public long timestampMs;

        @SerializedName("description")
        public String description;

        public byte[] jpegBytes;
    }

    public static class UtterancePayload {
        @SerializedName("utterance_id")
        public String utteranceId;

        @SerializedName("source_file_name")
        public String sourceFileName;

        @SerializedName("start_ms")
        public long startMs;

        @SerializedName("end_ms")
        public long endMs;

        @SerializedName("speaker_tag")
        public String speakerTag = "wearer";

        @SerializedName("transcript_hint")
        public String transcriptHint;

        @SerializedName("asr_confidence_hint")
        public Double asrConfidenceHint;

        public byte[] wavBytes;
    }

    public static class ConversationWindow {
        @SerializedName("conversation_id")
        public String conversationId;

        @SerializedName("device_id")
        public String deviceId;

        @SerializedName("captured_at")
        public String capturedAtIso;

        @SerializedName("utterances")
        public List<UtterancePayload> utterances = new ArrayList<>();

        @SerializedName("context_frames")
        public List<ContextFrame> contextFrames = new ArrayList<>();

        @SerializedName("preferred_target_utterance_id")
        public String preferredTargetUtteranceId;

        @SerializedName("metadata")
        public Map<String, Object> metadata = new HashMap<>();
    }

    public static class LabelDecision {
        @SerializedName("labelable")
        public boolean labelable;

        @SerializedName("canonical_label")
        public String canonicalLabel;

        @SerializedName("confidence")
        public double confidence;

        @SerializedName("reason")
        public String reason;

        @SerializedName("needs_human_review")
        public boolean needsHumanReview;

        @SerializedName("discard")
        public boolean discard;
    }

    public static class ReviewTask {
        @SerializedName("review_task_id")
        public String reviewTaskId;

        @SerializedName("conversation_id")
        public String conversationId;

        @SerializedName("target_utterance_id")
        public String targetUtteranceId;

        @SerializedName("target_audio_path")
        public String targetAudioPath;

        @SerializedName("proposed_label")
        public String proposedLabel;

        @SerializedName("decision_confidence")
        public double decisionConfidence;

        @SerializedName("reason")
        public String reason;
    }

    public static class IngestResponse {
        @SerializedName("success")
        public boolean success;

        @SerializedName("status")
        public String status;

        @SerializedName("conversation_id")
        public String conversationId;

        @SerializedName("target_utterance_id")
        public String targetUtteranceId;

        @SerializedName("decision")
        public LabelDecision decision;

        @SerializedName("dataset_sample_id")
        public String datasetSampleId;

        @SerializedName("review_task_id")
        public String reviewTaskId;

        @SerializedName("message")
        public String message;
    }
}
