"""التذكيرات من جهة الصفحة. الحد المحاكى: جسر الأندرويد (AndroidBridge) فقط، ونفحص ما تُرسله الصفحة إليه."""
import unittest

from support import PageCase, slots, start_of, GRAD


def calls(pg, kind):
    return [c for c in pg.evaluate("window.__calls") if c[0] == kind]


def last_payload(pg):
    return calls(pg, "set")[-1][1]


def sent(payload):
    return sorted((i["dow"], i["m"], i["s"], i["t"], i["p"]) for i in payload["items"])


def expected_items(group):
    return sorted((1 if d == "الإثنين" else 4, start_of(rng), s, t, p) for _, d, s, t, p, rng in slots(group))


class Reminders(PageCase):
    def test_card_is_hidden_outside_the_android_app(self):
        pg = self.page(self.context(bridge=False))
        self.choose_group(pg, 1)
        self.assertTrue(pg.locator("#rem").is_hidden())

    def test_enabling_sends_one_weekly_item_per_lecture_with_iso_day_and_start_minute(self):
        for g in (1, 2):
            with self.subTest(group=g):
                pg = self.page(self.context(bridge=True))
                self.choose_group(pg, g)
                pg.check("#remOn", force=True)
                payload = last_payload(pg)
                self.assertEqual(payload["lead"], 15)
                self.assertEqual(sent(payload), expected_items(g))

    def test_supervisor_and_lead_time_changes_resend_the_payload(self):
        pg = self.page(self.context(bridge=True))
        self.choose_group(pg, 1)
        pg.check("#remOn", force=True)
        pg.select_option("#sup", "د/ علاء جبر")
        extra = [i for i in last_payload(pg)["items"] if i["s"] == GRAD]
        self.assertEqual([(i["dow"], i["m"], i["t"]) for i in extra], [(1, 13 * 60 + 30, "د/ علاء جبر")])
        pg.select_option("#remLead", "30")
        self.assertEqual(last_payload(pg)["lead"], 30)

    def test_disabling_clears_the_native_reminders(self):
        pg = self.page(self.context(bridge=True))
        self.choose_group(pg, 1)
        pg.check("#remOn", force=True)
        pg.uncheck("#remOn", force=True)
        self.assertEqual(pg.evaluate("window.__calls")[-1][0], "clear")

    def test_blocked_notifications_ask_permission_and_schedule_once_granted(self):
        pg = self.page(self.context(bridge=True, init="window.__notif = false;"))
        self.choose_group(pg, 1)
        pg.check("#remOn", force=True)
        self.assertEqual(len(calls(pg, "request")), 1)
        self.assertEqual(calls(pg, "set"), [])
        self.assertTrue(pg.locator("#remSet").is_visible())
        pg.evaluate("window.__notif = true; window.onNotifPermission(true)")  # ما يفعله التطبيق بعد قبول الإذن
        self.assertEqual(sent(last_payload(pg)), expected_items(1))
        self.assertTrue(pg.locator("#remSet").is_hidden())

    def test_without_a_group_nothing_is_scheduled(self):
        pg = self.page(self.context(bridge=True))
        pg.check("#remOn", force=True)
        self.assertEqual(calls(pg, "set"), [])
        self.assertIn("اختر مجموعتك", pg.inner_text("#remNote"))

    def test_choice_survives_reload_and_is_resent_to_the_app(self):
        pg = self.page(self.context(bridge=True))
        self.choose_group(pg, 1)
        pg.check("#remOn", force=True)
        pg.select_option("#remLead", "30")
        pg.reload()
        self.assertTrue(pg.is_checked("#remOn"))
        self.assertEqual(pg.input_value("#remLead"), "30")
        self.assertEqual(last_payload(pg)["lead"], 30)


if __name__ == "__main__":
    unittest.main()
