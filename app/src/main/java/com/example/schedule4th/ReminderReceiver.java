package com.example.schedule4th;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class ReminderReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        Reminders.onAlarm(ctx, intent.getIntExtra("i", -1), intent.getLongExtra("start", 0L));
    }
}
