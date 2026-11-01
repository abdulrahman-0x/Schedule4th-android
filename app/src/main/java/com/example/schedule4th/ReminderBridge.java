package com.example.schedule4th;

import android.webkit.JavascriptInterface;

/** الجسر بين الصفحة والتطبيق: window.AndroidBridge. تُنفَّذ دوالّه على خيط خلفي. */
public class ReminderBridge {
    private final MainActivity act;

    ReminderBridge(MainActivity act) { this.act = act; }

    @JavascriptInterface
    public String status() {
        return "{\"notif\":" + act.notificationsAllowed() + "}";
    }

    @JavascriptInterface
    public void requestPermission() { act.runOnUiThread(act::askNotificationPermission); }

    @JavascriptInterface
    public void openSettings() { act.runOnUiThread(act::openNotificationSettings); }

    @JavascriptInterface
    public void setReminders(String json) { Reminders.replaceAll(act, json); }

    @JavascriptInterface
    public void clearReminders() { Reminders.clearAll(act); }
}
