package com.example.schedule4th;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

/** يفحص LectureTime كما هو في التطبيق، على JVM: بداية الأسبوع في عدة لغات، والتوقيت الصيفي في مصر. */
public class LectureTimeCheck {
    static final TimeZone TZ = TimeZone.getTimeZone("Africa/Cairo");
    static int fails = 0, checks = 0;

    static SimpleDateFormat fmt() {
        SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.ROOT);
        f.setTimeZone(TZ);
        return f;
    }

    static void expectStart(String name, int isoDay, int minutes, int lead, String after, String expected) throws Exception {
        long got = LectureTime.nextStart(LectureTime.toCalendarDow(isoDay), minutes, lead, fmt().parse(after).getTime());
        checks++;
        String actual = fmt().format(new Date(got));
        if (!actual.equals(expected)) {
            fails++;
            System.out.println("FAIL [" + Locale.getDefault() + "] " + name + ": got " + actual + ", expected " + expected);
        }
    }

    public static void main(String[] args) throws Exception {
        TimeZone.setDefault(TZ);
        Locale[] weekStarts = {Locale.US, new Locale("ar", "EG"), Locale.FRANCE, new Locale("ar", "SA")}; // الأحد/السبت/الإثنين
        for (Locale l : weekStarts) {
            Locale.setDefault(l);
            expectStart("Sunday before Monday", 1, 510, 15, "2026-11-01 12:00", "2026-11-02 08:30");
            expectStart("same day, trigger still ahead", 1, 510, 15, "2026-11-02 08:10", "2026-11-02 08:30");
            expectStart("after the trigger -> next week", 1, 510, 15, "2026-11-02 08:20", "2026-11-09 08:30");
            expectStart("exactly at the trigger -> next week", 1, 510, 15, "2026-11-02 08:15", "2026-11-09 08:30");
            expectStart("Friday -> next Thursday", 4, 750, 15, "2026-11-06 10:00", "2026-11-12 12:30");
            expectStart("one-hour lead already passed", 4, 630, 60, "2026-11-05 09:35", "2026-11-12 10:30");
            expectStart("1:30 pm lecture", 1, 810, 30, "2026-11-02 12:00", "2026-11-02 13:30");
            expectStart("Saturday -> Thursday", 4, 510, 15, "2026-11-07 09:00", "2026-11-12 08:30");
            expectStart("day before the DST change", 4, 630, 15, "2026-10-28 12:00", "2026-10-29 10:30");
            expectStart("wall clock kept after DST change", 4, 630, 15, "2026-10-29 11:00", "2026-11-05 10:30");
        }
        int[][] dayMap = {{1, Calendar.MONDAY}, {4, Calendar.THURSDAY}, {7, Calendar.SUNDAY}, {0, -1}, {8, -1}};
        for (int[] m : dayMap) {
            checks++;
            if (LectureTime.toCalendarDow(m[0]) != m[1]) { fails++; System.out.println("FAIL toCalendarDow(" + m[0] + ")"); }
        }
        System.out.println("checks: " + checks + ", failures: " + fails);
        System.exit(fails == 0 ? 0 : 1);
    }
}
