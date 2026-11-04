"""الحضور والغياب والتعويض، وتصفير السجل يوميًا. الحدود المحاكاة: الساعة فقط."""
import re
import unittest
from datetime import datetime

from support import JAVA_DIR, PageCase, lecture, stored, summary

MON_10 = datetime(2026, 11, 2, 10, 0)  # الإثنين 10:00 — بدأت محاضرتان فقط من محاضرات المجموعة 1


class AttendanceFlow(PageCase):
    def setUp(self):
        super().setUp()
        self.ctx = self.context()
        self.pg = self.page(self.ctx, MON_10)
        self.choose_group(self.pg, 1)

    def test_remaining_count_tracks_todays_unrecorded_lectures(self):
        pg = self.pg
        self.assertIn("المتبقي اليوم: 4 من 4", summary(pg))
        lecture(pg, 0, 0).locator('[data-act="a"]').click()
        self.assertIn("المتبقي اليوم: 3 من 4", summary(pg))
        lecture(pg, 0, 1).locator('[data-act="m"]').click()
        self.assertIn("المتبقي اليوم: 2 من 4", summary(pg))
        self.assertIn("فاتتني 1", summary(pg))

    def test_recording_unlocks_when_the_lecture_starts_and_only_for_today(self):
        for when, unlocked in [(datetime(2026, 11, 2, 8, 29), False), (datetime(2026, 11, 2, 8, 30), True)]:
            with self.subTest(clock=str(when)):
                pg = self.page(self.ctx, when)
                self.assertEqual(lecture(pg, 0, 0).locator("[data-act]").count() > 0, unlocked)
        pg = self.page(self.ctx, MON_10)
        self.assertIn("ليس اليوم", lecture(pg, 1, 0).inner_text())  # محاضرات الخميس يوم الإثنين
        self.assertEqual(lecture(pg, 1, 0).locator("[data-act]").count(), 0)

    def test_absence_offers_the_other_groups_slot_of_the_same_course(self):
        pg = self.pg
        lecture(pg, 0, 1).locator('[data-act="m"]').click()  # إدارة المشروعات: المجموعة 1 الساعة 9:30
        card = pg.inner_text("#att .mk")
        for part in ["إدارة المشروعات", "المجموعة 2", "من 8:30 إلى 9:30", "مدرج إيزيس"]:
            self.assertIn(part, card)

    def test_absence_counts_as_made_up_only_after_attending_the_alternative(self):
        pg = self.pg
        lecture(pg, 0, 1).locator('[data-act="m"]').click()
        self.assertIn("فائتة لم تُعوَّض: 1", summary(pg))
        self.assertIn("المتبقي اليوم: 3 من 4", summary(pg))
        pg.locator('#att .mk [data-act="k"]').click()
        self.assertIn("فائتة لم تُعوَّض: 0", summary(pg))
        self.assertIn("المتبقي اليوم: 3 من 4", summary(pg))  # التعويض لا يغيّر المتبقي
        self.assertIn("تعويض", lecture(pg, 0, 1).inner_text())

    def test_alternative_unlocks_only_once_it_has_started(self):
        # مالية متقدمة: المجموعة 1 الساعة 8:30، وبديلها (المجموعة 2) الساعة 9:30 في نفس اليوم
        pg = self.page(self.ctx, datetime(2026, 11, 2, 9, 20))
        lecture(pg, 0, 0).locator('[data-act="m"]').click()
        self.assertIn("لم يبدأ بعد", pg.inner_text("#att .mk"))
        self.assertTrue(pg.locator('#att .mk [data-act="k"]').is_disabled())
        pg = self.page(self.ctx, datetime(2026, 11, 2, 9, 35))
        self.assertTrue(pg.locator('#att .mk [data-act="k"]').is_enabled())

    def test_every_available_alternative_is_listed_and_the_chosen_one_is_recorded(self):
        pg = self.pg
        pg.evaluate("E.push({d:0,c:'b',s:'مادة تجريبية',t:'د/ تجربة',p:'قاعة س',"
                    "sl:[[1,'8:30–9:30'],[2,'9:30–10:30'],[2,'11:30–12:30']]}); render();")
        lecture_row = pg.locator("#main tbody tr", has_text="مادة تجريبية")
        lecture_row.locator('[data-act="m"]').click()
        self.assertEqual(pg.locator("#att .mk .alt").count(), 2)
        buttons = pg.locator('#att .mk [data-act="k"]')
        self.assertTrue(buttons.nth(0).is_enabled() and buttons.nth(1).is_disabled())  # 11:30 لم يبدأ
        buttons.nth(0).click()
        self.assertIn("9:30", lecture_row.inner_text())

    def test_graduation_project_absence_has_no_alternative(self):
        pg = self.page(self.ctx, datetime(2026, 11, 2, 14, 0))
        pg.select_option("#sup", "د/ علاء جبر")
        pg.locator("#main tbody tr", has_text="علاء جبر").locator('[data-act="m"]').click()
        self.assertIn("لا يوجد موعد بديل", pg.inner_text("#att .mk"))

    def test_undo_steps_back_one_state_at_a_time(self):
        pg = self.pg
        lecture(pg, 0, 1).locator('[data-act="m"]').click()
        pg.locator('#att .mk [data-act="k"]').click()
        lecture(pg, 0, 1).locator('[data-act="undo"]').click()  # من «تعويض» إلى «فائتة»
        self.assertIn("فائتة لم تُعوَّض: 1", summary(pg))
        pg.locator('#att .mk [data-act="undo"]').click()  # من «فائتة» إلى «لم تُسجَّل»
        self.assertIn("المتبقي اليوم: 4 من 4", summary(pg))
        self.assertEqual(pg.locator("#att .mk").count(), 0)


class DailyReset(PageCase):
    def record_monday(self, ctx, sup=None):
        pg = self.page(ctx, MON_10)
        self.choose_group(pg, 1)
        if sup:
            pg.select_option("#sup", sup)
        lecture(pg, 0, 0).locator('[data-act="a"]').click()
        lecture(pg, 0, 1).locator('[data-act="m"]').click()
        return pg

    def test_records_persist_within_the_same_day(self):
        ctx = self.context()
        self.record_monday(ctx)
        pg = self.page(ctx, datetime(2026, 11, 2, 23, 59))
        self.assertIn("حضرت 1", summary(pg))
        self.assertEqual(pg.locator("#att .mk").count(), 1)

    def test_a_new_day_starts_clean_but_keeps_schedule_group_and_supervisor(self):
        cases = [
            (datetime(2026, 11, 3, 0, 5), "لا محاضرات اليوم"),        # الثلاثاء
            (datetime(2026, 11, 5, 9, 0), "المتبقي اليوم: 4 من 4"),    # الخميس (3 محاضرات + مشروع نهى أحمد)
            (datetime(2026, 11, 9, 9, 0), "المتبقي اليوم: 4 من 4"),    # الإثنين التالي
        ]
        for when, expected in cases:
            with self.subTest(clock=str(when)):
                ctx = self.context()
                before = len(self.record_monday(ctx, "د/ نهى أحمد").locator("#main tbody tr").all())
                pg = self.page(ctx, when)
                self.assertIn(expected, summary(pg))
                self.assertEqual(pg.locator("#att .mk").count(), 0)
                self.assertEqual(stored(pg, "att"), "{}")
                self.assertEqual(len(pg.locator("#main tbody tr").all()), before)
                self.assertTrue(pg.is_checked('input[value="1"]'))
                self.assertEqual(pg.input_value("#sup"), "د/ نهى أحمد")

    def test_midnight_with_the_page_open_clears_the_record(self):
        pg = self.page(self.context(), datetime(2026, 11, 2, 23, 58))
        self.choose_group(pg, 1)
        lecture(pg, 0, 0).locator('[data-act="a"]').click()
        lecture(pg, 0, 1).locator('[data-act="m"]').click()
        pg.clock.run_for(180000)  # ثلاث دقائق: يعبر منتصف الليل ويعمل المؤقّت
        self.assertIn("لا محاضرات اليوم", summary(pg))
        self.assertEqual(pg.locator("#att .mk").count(), 0)

    def test_the_apps_resume_hook_refreshes_the_page_after_midnight_in_the_background(self):
        # انحدار: onResume ينادي window.tick() فإن لم تكن الدالة عامة لم يحدث أي تحديث عند الرجوع للتطبيق.
        # نشغّل نص الجافا نفسه كما هو (مأخوذ من MainActivity) بدل افتراض اسمه.
        main = (JAVA_DIR / "MainActivity.java").read_text("utf-8")
        script = re.search(r'evaluateJavascript\("(window\.tick[^"]*)"', main).group(1)
        pg = self.page(self.context(), datetime(2026, 11, 2, 23, 59))
        self.choose_group(pg, 1)
        lecture(pg, 0, 0).locator('[data-act="a"]').click()
        pg.clock.set_system_time(datetime(2026, 11, 3, 0, 0, 10))  # مرّ الوقت والتطبيق في الخلفية: لم يعمل أي مؤقّت
        self.assertIn("المتبقي اليوم", summary(pg))  # ما زالت الصفحة القديمة معروضة
        pg.evaluate(script)
        self.assertIn("لا محاضرات اليوم", summary(pg))
        self.assertEqual(stored(pg, "att"), "{}")

    def test_stale_button_clicked_after_midnight_records_nothing(self):
        pg = self.page(self.context(), datetime(2026, 11, 2, 23, 59))
        self.choose_group(pg, 1)
        pg.clock.set_system_time(datetime(2026, 11, 3, 0, 0, 10))  # لم يعمل المؤقّت بعد
        lecture(pg, 0, 0).locator('[data-act="a"]').click()
        self.assertEqual(stored(pg, "att"), "{}")

    def test_weekly_records_from_the_old_version_are_discarded(self):
        legacy = ('localStorage.setItem("grp","1");localStorage.setItem("att",JSON.stringify('
                  '{"2026-11-02":{"0|8:30–9:30|إدارة مالية متقدمة|د/ هيكل عبدة":"m"}}))')
        pg = self.page(self.context(init=legacy), MON_10)
        self.assertIn("المتبقي اليوم: 4 من 4", summary(pg))
        self.assertEqual(pg.locator("#att .mk").count(), 0)


if __name__ == "__main__":
    unittest.main()
