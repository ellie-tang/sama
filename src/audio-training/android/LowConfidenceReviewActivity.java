package devkit.blade.vuzix.com.blade_template_app.audiotraining;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;

public class LowConfidenceReviewActivity extends Activity {
    private static final String TAG = "LowConfidenceReview";

    private AudioTrainingApiClient apiClient;
    private String reviewTaskId;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        apiClient = new AudioTrainingApiClient(this);
        reviewTaskId = getIntent().getStringExtra(AudioTrainingBroadcastReceiver.EXTRA_REVIEW_TASK_ID);
        renderReviewTask();
    }

    public void renderReviewTask() {
        Log.i(TAG, "Render review task: " + reviewTaskId + ". Hook this into the Blade HUD review UI.");
    }

    public void submitApprovedLabel() {
        apiClient.submitHumanLabelAsync(reviewTaskId, "approve", null);
        finish();
    }

    public void submitCorrectedLabel(String correctedLabel) {
        apiClient.submitHumanLabelAsync(reviewTaskId, "correct", correctedLabel);
        finish();
    }

    public void discardSample() {
        apiClient.submitHumanLabelAsync(reviewTaskId, "discard", null);
        finish();
    }
}
