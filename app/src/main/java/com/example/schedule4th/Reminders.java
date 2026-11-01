package com.example.schedule4th;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/** جدولة التذكيرات الأسبوعية وإظهار الإشعارات. الإعدادات محفوظة في SharedPreferences. */
final class Reminders {
    private static final String PREFS = "reminders";
    private static final String KEY = "config"; // {"lead":15,"items":[{"dow":1,"m":510,"s":"..","t":"..","p":"..","tm":".."}]}
    private static final String CHANNEL = "lectures";

    private Reminders() {}

    private static JSONObject config(Context ctx) {
        String s = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY, null);
        if (s == null) return null;
        try { return new JSONObject(s); } catch (JSONException e) { return null; }
    }

    static void replaceAll(Context ctx, String json) {
        try { new JSONObject(json); } catch (JSONException e) { return; }
        // إلغاء واسع أولًا: يشمل أي منبّه قديم من إعداد سابق (حتى لو كان عدد عناصره أكبر)
        cancelRange(ctx, MAX_SLOTS);
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY, json).apply();
        scheduleAll(ctx);
    }

    static void clearAll(Context ctx) {
        cancelRange(ctx, MAX_SLOTS);
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().remove(KEY).apply();
    }

    /** أقصى عدد تذكيرات ممكن (محاضرات المجموعة + مشروع التخرج) — سقف عند الإلغاء الواسع. */
    private static final int MAX_SLOTS = 64;

    /**
     * إلغاء كل المنبّهات الممكنة بغض النظر عن الإعدادات المحفوظة.
     * يُستخدم قبل الحفظ الجديد حتى لا تبقى منبّهات من إعداد سابق (مجموعة/مشرف آخر)
     * بأرقام أكبر من عدد العناصر الجديد.
     */
    private static void cancelRange(Context ctx, int count) {
        AlarmManager am = ctx.getSystemService(AlarmManager.class);
        for (int i = 0; i < count; i++) {
            Intent in = new Intent(ctx, ReminderReceiver.class);
            PendingIntent p = PendingIntent.getBroadcast(ctx, i, in,
                    PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
            if (p != null) { am.cancel(p); p.cancel(); }
        }
    }

    static void scheduleAll(Context ctx) {
        JSONObject cfg = config(ctx);
        JSONArray items = cfg == null ? null : cfg.optJSONArray("items");
        if (items == null) return;
        int lead = cfg.optInt("lead", 15);
        long now = System.currentTimeMillis();
        for (int i = 0; i < items.length(); i++) scheduleOne(ctx, i, items.optJSONObject(i), lead, now);
    }

    private static void scheduleOne(Context ctx, int i, JSONObject it, int lead, long after) {
        if (it == null) return;
        int dow = LectureTime.toCalendarDow(it.optInt("dow", 0));
        int m = it.optInt("m", -1);
        if (dow < 0 || m < 0) return;
        long start = LectureTime.nextStart(dow, m, lead, after);
        long trigger = start - lead * 60000L;
        AlarmManager am = ctx.getSystemService(AlarmManager.class);
        Intent in = new Intent(ctx, ReminderReceiver.class).putExtra("i", i).putExtra("start", start);
        PendingIntent p = PendingIntent.getBroadcast(ctx, i, in,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        boolean exact = true;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) exact = am.canScheduleExactAlarms();
        try {
            if (exact) am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, p);
            else am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, p);
        } catch (SecurityException e) {
            am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, trigger, p);
        }
    }

    /** عند وصول المنبّه: أظهر الإشعار (إن لم تبدأ المحاضرة) ثم جدول موعد الأسبوع القادم. */
    static void onAlarm(Context ctx, int i, long start) {
        JSONObject cfg = config(ctx);
        JSONArray items = cfg == null ? null : cfg.optJSONArray("items");
        JSONObject it = (items == null || i < 0) ? null : items.optJSONObject(i);
        if (it == null) return;
        int lead = cfg.optInt("lead", 15);
        long now = System.currentTimeMillis();
        if (start == 0L || now <= start) notifyLecture(ctx, i, it, lead, start);
        // الجدولة التالية تبدأ من لحظة الإشعار نفسها (start) لا من "الآن"،
        // حتى لا يُحسب أسبوع إضافي لو تأخّر استلام المنبّه (وضع Doze مثلًا).
        long after = start > 0 ? start : now;
        scheduleOne(ctx, i, it, lead, after);
    }

    private static void notifyLecture(Context ctx, int i, JSONObject it, int lead, long start) {
        NotificationManager nm = ctx.getSystemService(NotificationManager.class);
        NotificationChannel ch = new NotificationChannel(CHANNEL, "تذكير المحاضرات", NotificationManager.IMPORTANCE_HIGH);
        ch.setDescription("تنبيه قبل بداية كل محاضرة");
        nm.createNotificationChannel(ch);

        Intent open = new Intent(ctx, MainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent tap = PendingIntent.getActivity(ctx, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        String place = it.optString("p"), doctor = it.optString("t"), time = it.optString("tm");
        Notification n = new Notification.Builder(ctx, CHANNEL)
                .setSmallIcon(R.drawable.ic_stat_lecture)
                .setContentTitle(it.optString("s"))
                .setContentText("تبدأ بعد " + leadText(lead) + " – " + place)
                .setStyle(new Notification.BigTextStyle().bigText(doctor + "\n" + time + " – " + place))
                .setContentIntent(tap)
                .setAutoCancel(true)
                .setCategory(Notification.CATEGORY_REMINDER)
                .setWhen(start > 0 ? start : System.currentTimeMillis())
                .setShowWhen(true)
                .build();
        nm.notify(1000 + i, n);
    }

    private static String leadText(int n) {
        return n == 60 ? "ساعة" : (n <= 10 ? n + " دقائق" : n + " دقيقة");
    }
}
