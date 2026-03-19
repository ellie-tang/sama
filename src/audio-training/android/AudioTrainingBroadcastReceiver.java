package devkit.blade.vuzix.com.blade_template_app.audiotraining;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

public class AudioTrainingBroadcastReceiver extends BroadcastReceiver {
    public static final String ACTION_AUDIO_TRAINING_UPDATE =
            "devkit.blade.vuzix.com.blade_template_app.audiotraining.UPDATE";
    public static final String ACTION_AUDIO_TRAINING_ERROR =
            "devkit.blade.vuzix.com.blade_template_app.audiotraining.ERROR";
    public static final String EXTRA_STATUS = "extra_status";
    public static final String EXTRA_MESSAGE = "extra_message";
    public static final String EXTRA_REVIEW_TASK_ID = "extra_review_task_id";
    public static final String EXTRA_CONFIDENCE = "extra_confidence";

    private static final String TAG = "AudioTrainingReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || intent.getAction() == null) {
            return;
        }
        if (ACTION_AUDIO_TRAINING_UPDATE.equals(intent.getAction())) {
            double confidence = intent.getDoubleExtra(EXTRA_CONFIDENCE, 0d);
            String reviewTaskId = intent.getStringExtra(EXTRA_REVIEW_TASK_ID);
            if (reviewTaskId != null && confidence < AudioTrainingConfig.getLowConfidenceThreshold()) {
                dispatchReviewNeeded(context, reviewTaskId);
            } else {
                dispatchDatasetSaved(intent.getStringExtra(EXTRA_STATUS));
            }
        } else if (ACTION_AUDIO_TRAINING_ERROR.equals(intent.getAction())) {
            Log.e(TAG, "Audio training error: " + intent.getStringExtra(EXTRA_MESSAGE));
        }
    }

    public void dispatchReviewNeeded(Context context, String reviewTaskId) {
        Intent reviewIntent = new Intent(context, LowConfidenceReviewActivity.class);
        reviewIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        reviewIntent.putExtra(EXTRA_REVIEW_TASK_ID, reviewTaskId);
        context.startActivity(reviewIntent);
    }

    public void dispatchDatasetSaved(String status) {
        Log.i(TAG, "Audio training pipeline update: " + status);
    }
}
