package com.example.schedule4th;

import java.util.Calendar;

/** حسابات التوقيت فقط، بدون أي اعتماد على Android (قابلة للاختبار على JVM). */
final class LectureTime {
    private LectureTime() {}

    /** من رقم اليوم ISO (الإثنين=1 ... الأحد=7) إلى ثابت Calendar، أو -1 إن كان غير صالح. */
    static int toCalendarDow(int iso) {
        return (iso >= 1 && iso <= 7) ? (iso % 7) + 1 : -1;
    }

    /** أقرب بداية محاضرة (بالمللي ثانية) يقع تذكيرها بعد اللحظة after. */
    static long nextStart(int calDow, int minutes, int leadMin, long after) {
        Calendar c = Calendar.getInstance();
        c.setTimeInMillis(after);
        c.set(Calendar.DAY_OF_WEEK, calDow);
        c.set(Calendar.HOUR_OF_DAY, minutes / 60);
        c.set(Calendar.MINUTE, minutes % 60);
        c.set(Calendar.SECOND, 0);
        c.set(Calendar.MILLISECOND, 0);
        while (c.getTimeInMillis() - leadMin * 60000L <= after) c.add(Calendar.DAY_OF_YEAR, 7);
        return c.getTimeInMillis();
    }
}
