package devkit.blade.vuzix.com.blade_template_app.audiotraining;

import android.content.Context;
import android.content.Intent;
import android.util.Log;

import com.google.gson.Gson;

import java.io.IOException;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class AudioTrainingApiClient {
    private static final String TAG = "AudioTrainingApi";
    private static final MediaType MEDIA_TYPE_WAV = MediaType.parse("audio/wav");
    private static final MediaType MEDIA_TYPE_JPEG = MediaType.parse("image/jpeg");

    private final Context context;
    private final Gson gson = new Gson();
    private final OkHttpClient httpClient;
    private final ExecutorService executorService = Executors.newSingleThreadExecutor();

    public AudioTrainingApiClient(Context context) {
        this.context = context;
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .build();
    }

    public void uploadConversationWindowAsync(AudioTrainingModels.ConversationWindow window) {
        executorService.execute(() -> uploadConversationWindow(window));
    }

    public void submitHumanLabelAsync(String reviewTaskId, String decision, String correctedLabel) {
        executorService.execute(() -> submitHumanLabel(reviewTaskId, decision, correctedLabel));
    }

    public void pollReviewStatusAsync() {
        executorService.execute(() -> {
            Request request = new Request.Builder()
                    .url(AudioTrainingConfig.getServerBaseUrl() + "/reviews")
                    .get()
                    .build();
            try (Response response = httpClient.newCall(request).execute()) {
                Log.d(TAG, "Review queue polled: " + response.code());
            } catch (IOException e) {
                Log.e(TAG, "Failed to poll review queue", e);
            }
        });
    }

    public void handleIngestResponse(AudioTrainingModels.IngestResponse response) {
        Intent intent = new Intent(AudioTrainingBroadcastReceiver.ACTION_AUDIO_TRAINING_UPDATE);
        intent.putExtra(AudioTrainingBroadcastReceiver.EXTRA_STATUS, response.status);
        intent.putExtra(AudioTrainingBroadcastReceiver.EXTRA_MESSAGE, response.message);
        intent.putExtra(AudioTrainingBroadcastReceiver.EXTRA_REVIEW_TASK_ID, response.reviewTaskId);
        intent.putExtra(AudioTrainingBroadcastReceiver.EXTRA_CONFIDENCE,
                response.decision != null ? response.decision.confidence : 0d);
        context.sendBroadcast(intent);
    }

    private void uploadConversationWindow(AudioTrainingModels.ConversationWindow window) {
        String payloadJson = gson.toJson(window);
        MultipartBody.Builder builder = new MultipartBody.Builder().setType(MultipartBody.FORM);
        builder.addFormDataPart("payload_json", payloadJson);

        for (AudioTrainingModels.UtterancePayload utterance : window.utterances) {
            builder.addFormDataPart(
                    "audio_files",
                    utterance.sourceFileName,
                    RequestBody.create(utterance.wavBytes, MEDIA_TYPE_WAV)
            );
        }

        for (AudioTrainingModels.ContextFrame frame : window.contextFrames) {
            if (frame.jpegBytes == null) {
                continue;
            }
            builder.addFormDataPart(
                    "context_frames",
                    frame.sourceFileName,
                    RequestBody.create(frame.jpegBytes, MEDIA_TYPE_JPEG)
            );
        }

        Request request = new Request.Builder()
                .url(AudioTrainingConfig.getServerBaseUrl() + "/ingest")
                .post(builder.build())
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            if (response.body() == null) {
                throw new IOException("Empty response body");
            }
            String body = response.body().string();
            AudioTrainingModels.IngestResponse ingestResponse = gson.fromJson(body, AudioTrainingModels.IngestResponse.class);
            handleIngestResponse(ingestResponse);
        } catch (Exception e) {
            Log.e(TAG, "Failed to upload conversation window", e);
            Intent intent = new Intent(AudioTrainingBroadcastReceiver.ACTION_AUDIO_TRAINING_ERROR);
            intent.putExtra(AudioTrainingBroadcastReceiver.EXTRA_MESSAGE, e.getMessage());
            context.sendBroadcast(intent);
        }
    }

    private void submitHumanLabel(String reviewTaskId, String decision, String correctedLabel) {
        HumanReviewDecision payload = new HumanReviewDecision();
        payload.decision = decision;
        payload.correctedLabel = correctedLabel;
        payload.reviewer = "blade2";
        String json = gson.toJson(payload);
        Request request = new Request.Builder()
                .url(AudioTrainingConfig.getServerBaseUrl() + "/reviews/" + reviewTaskId)
                .post(RequestBody.create(json, MediaType.parse("application/json")))
                .build();
        try (Response response = httpClient.newCall(request).execute()) {
            Log.d(TAG, "Review submitted: " + response.code());
        } catch (IOException e) {
            Log.e(TAG, "Failed to submit review", e);
        }
    }

    private static class HumanReviewDecision {
        String decision;
        String correctedLabel;
        String reviewer;
    }
}
