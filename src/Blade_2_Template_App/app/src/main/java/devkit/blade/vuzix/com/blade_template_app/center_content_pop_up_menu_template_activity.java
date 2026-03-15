package devkit.blade.vuzix.com.blade_template_app;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.WindowManager;
import android.view.ViewGroup;
import android.widget.TextView;
import android.widget.Toast;

import com.vuzix.hud.actionmenu.ActionMenuActivity;
import com.vuzix.hud.actionmenu.DefaultActionMenuItemView;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;


/**
 * Main Template Activity, This application follows the Center Lock style of the Vuzix Camera App.
 * All Navigation buttons are MenuItems and the Rotation is handle by the ActionMenuActivity.
 * The Center of the screen is your normal Layout.
 * This template provide the example to only show the Pop Up Menu ON the Menu Gesture.
 * The only change is changing the return for the method alwaysShowActionMenu to False.
 * For more information on the ActionMenuActivity read the JavaDocs in Android Studio or download the
 * Java docs at:  https://www.vuzix.com/support/Downloads_Drivers
 */
public class center_content_pop_up_menu_template_activity extends ActionMenuActivity {

    private boolean statusState = true;
    private int statusCount = 1;

    private MenuItem HelloMenuItem;
    private MenuItem VuzixMenuItem;
    private MenuItem BladeMenuItem;
    private SwitchMenuItemView switchMenuItemView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setupFullscreen();
        setContentView(R.layout.activity_center_content_template_style);
        maximizeContentRealEstate();

    }

    /**
     *  Main override to create the ACTION MENU. Notice that this is onCreate-ACTION-MENU. Not to be
     *  confuse with onCreate-Option-Menu which will create the basic Android menu that will not
     *  display properly in the small device screen.
     * @param menu Menu to inflate too.
     * @return Return if menu was setup correctly.
     */
    @Override
    protected boolean onCreateActionMenu(Menu menu) {
        super.onCreateActionMenu(menu);
        getMenuInflater().inflate(R.menu.main_menu, menu);

        HelloMenuItem = menu.findItem(R.id.action_menu_hello);
        VuzixMenuItem = menu.findItem(R.id.action_menu_vuzix);
        BladeMenuItem = menu.findItem(R.id.action_menu_blade);
        BladeMenuItem.setActionView(switchMenuItemView = new SwitchMenuItemView(this));
        menu.findItem(R.id.action_menu_lunch_pop_up).setTitle(R.string.showCenterContent);
        updateMenuItems();

        return true;
    }

    /**
     * Override of the ActionMenuActivity. TRUE will tell the system to always show the Action Menu in
     * the position that you ask for. If this is false, the action menu will be hidden and will be
     * presented upon the Menu Option Gesture (1 Finger hold for 1 second.)
     * https://www.vuzix.com/Developer/KnowledgeBase/Detail/65
     */
    //This is only difference that will make the Navigation menu show or just pop up on the Menu Option
    //Gesture.
    @Override
    protected boolean alwaysShowActionMenu() {
        return false;
    }

    /**
     * Override of the ActionMenuActivity. This will tell the BladeOS which item to start at and
     * which one if the default action to start at on activity restarts.
     * @return
     */
    @Override
    protected int getDefaultAction() {
        return 1;
    }

    /**
     * Maintain fullscreen mode when window regains focus
     */
    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            setupFullscreen();
        }
    }

    /**
     * Setup fullscreen mode to use full 480x480 resolution on Blade 2
     */
    private void setupFullscreen() {
        getWindow().setFlags(
                WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN
        );

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                            | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            );
        }
    }

    /**
     * Remove container padding/margins so the layout occupies the full 480x480 area.
     */
    private void maximizeContentRealEstate() {
        View rootContainer = findViewById(R.id.root_container);
        if (rootContainer != null) {
            ViewGroup.LayoutParams params = rootContainer.getLayoutParams();
            if (params instanceof ViewGroup.MarginLayoutParams) {
                ((ViewGroup.MarginLayoutParams) params).setMargins(0, 0, 0, 0);
            }
            rootContainer.setLayoutParams(params);
            rootContainer.setPadding(0, 0, 0, 0);
            ViewCompat.setOnApplyWindowInsetsListener(rootContainer, (v, insets) -> WindowInsetsCompat.CONSUMED);
        }
    }

    private void updateMenuItems() {
        if (HelloMenuItem == null) {
            return;
        }

        VuzixMenuItem.setEnabled(false);
        BladeMenuItem.setEnabled(false);
        switchMenuItemView.setSwitchState(statusState, statusCount);
    }


    //Action Menu Click events
    //This events where register via the XML for the menu definitions.
    public void showHello(MenuItem item){

        showToast(getString(R.string.Hello));
        VuzixMenuItem.setEnabled(true);
        BladeMenuItem.setEnabled(true);
    }

    public void showVuzix(MenuItem item){
        showToast(getString(R.string.Vuzix));
    }

    public void showBlade(MenuItem item){
        showToast(getString(R.string.Blade1));
        statusState = !statusState;
        statusCount++;
        switchMenuItemView.setSwitchState(statusState, statusCount);
    }

    public void showbottomlock(MenuItem item)
    {
        startActivity(new Intent(this, around_content_template_activity.class));
    }

    public void showpopUp(MenuItem item)
    {
        startActivity(new Intent(this, center_content_template_activity.class));
    }


    private void showToast(final String text){

        final Activity activity = this;

        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Toast.makeText(activity, text, Toast.LENGTH_SHORT).show();
            }
        });
    }

    /**
     * Custom Class to allow the view to change on the dynamicly.
     * Notice that we utilize this class on the actual MenuItem for its ActionView class.
     * This will allow us to access internal fields like icon to modify the action view itself.
     * For more information see the Class definition for DefaultActionMenuItemView and for
     * onCreateActionMenu.
     */
    private static class SwitchMenuItemView extends DefaultActionMenuItemView {

        public SwitchMenuItemView(Context context) {
            super(context);
        }

        private void setSwitchState(boolean on, int times) {
            if (on) {
                icon.setImageTintList(getResources().getColorStateList(com.vuzix.hud.actionmenu.R.color.action_menu_item_text_color));
                setIcon(getResources().getDrawable(R.drawable.baseline_perm_device_information_24, getContext().getTheme()));
                setTitle(getResources().getString(R.string.Blade,times));
            } else {
                icon.setImageTintList(getResources().getColorStateList(com.vuzix.hud.actionmenu.R.color.hud_blue));
                setIcon(getResources().getDrawable(R.drawable.baseline_copyright_24,getContext().getTheme()));
                setTitle(getResources().getString(R.string.Blade,times));
            }
        }
    }

}
