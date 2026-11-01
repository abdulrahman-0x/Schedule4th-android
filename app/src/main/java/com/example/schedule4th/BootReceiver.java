package com.example.schedule4th;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** يعيد جدولة المنبّهات بعد إعادة تشغيل الجهاز أو تحديث التطبيق (المنبّهات تُمسح في الحالتين). */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        Reminders.scheduleAll(ctx);
    }
}
