"""الجدول: صحة البيانات، عرض المجموعة، باقي الجدول، مشروع التخرج، الصيغة، الحفظ، الشاشات."""
import re
import unittest
from datetime import datetime

from support import GRAD, PAGE, SUPERVISORS, PageCase, minutes, shown, show, slots, start_of, view


def non_decreasing_per_day(rows):
    """هل أوقات البداية مرتبة تصاعديًا داخل كل يوم؟ (rows: tuples من shown)"""
    last = {}
    for day, *_, rng in rows:
        a = re.match(r"من (\S+) إلى", rng).group(1)
        m = start_of(a + "–" + a)
        if m < last.get(day, -1):
            return False
        last[day] = m
    return True


class TimetableContent(PageCase):
    def test_every_original_slot_is_shown_exactly_once_across_main_and_rest(self):
        want = sorted((d, s, t, p, show(rng)) for _, d, s, t, p, rng in slots("all"))
        for g in (1, 2):
            with self.subTest(group=g):
                pg = self.page(self.context())
                self.choose_group(pg, g)
                pg.click("#toggle")
                self.assertEqual(sorted(shown(pg, "#main") + shown(pg, "#rest")), want)

    def test_group_view_lists_only_that_groups_slots_in_that_groups_time_order(self):
        for g in (1, 2):
            with self.subTest(group=g):
                pg = self.page(self.context())
                self.choose_group(pg, g)
                self.assertEqual(shown(pg), view(g))

    def test_without_a_group_only_a_prompt_is_shown(self):
        pg = self.page(self.context())
        self.assertEqual(shown(pg), [])
        self.assertTrue(pg.locator("#bar").is_hidden())
        self.assertIn("اختر المجموعة", pg.inner_text("#note"))

    def test_rest_button_reveals_then_hides_the_remaining_rows(self):
        pg = self.page(self.context())
        self.choose_group(pg, 1)
        self.assertTrue(pg.locator("#rest").is_hidden())
        self.assertEqual(pg.inner_text("#toggle"), "إظهار باقي الجدول")
        pg.click("#toggle")
        self.assertEqual((len(shown(pg, "#main")), len(shown(pg, "#rest"))), (7, 19))
        self.assertEqual(pg.inner_text("#toggle"), "إخفاء باقي الجدول")
        pg.click("#toggle")
        self.assertTrue(pg.locator("#rest").is_hidden())

    def test_chosen_supervisor_joins_main_schedule_and_leaves_rest(self):
        for sup in SUPERVISORS:
            with self.subTest(supervisor=sup):
                pg = self.page(self.context())
                self.choose_group(pg, 1)
                pg.select_option("#sup", sup)
                pg.click("#toggle")
                main, rest = shown(pg, "#main"), shown(pg, "#rest")
                mine = [r for r in main if r[1] == GRAD]
                self.assertEqual([r[2] for r in mine], [sup])
                self.assertEqual((len(main), len(rest)), (8, 18))
                self.assertNotIn(mine[0], rest)
                self.assertTrue(non_decreasing_per_day(main))


class GraduationProjects(PageCase):
    def test_graduation_tables_have_no_group_column_and_no_unclassified_section(self):
        # انحدار (طلب المستخدم): لا عمود مجموعة ولا «—» في مشروع التخرج، ولا قسم «غير مصنّف»
        pg = self.page(self.context())
        self.choose_group(pg, 1)
        pg.click("#toggle")
        heads = pg.evaluate("""() => [...document.querySelectorAll('#rest h2')].map(h => ({
            title: h.textContent, cols: (() => { let n = h.nextElementSibling; const out = [];
              while (n && n.tagName !== 'H2') { n.querySelectorAll('th').forEach(t => out.push(t.textContent)); n = n.nextElementSibling; }
              return out; })() }))""")
        grad_section = next(h for h in heads if GRAD in h["title"])
        self.assertNotIn("المجموعة", grad_section["cols"])
        self.assertNotIn("غير مصنّف", pg.inner_text("body"))
        pg.click("#gpBtn")
        self.assertEqual(pg.locator('#main td[data-l="المجموعة"]').count(), 0)
        self.assertNotIn("المجموعة", pg.locator("#main th").all_inner_texts())

    def test_graduation_only_view_shows_all_twelve_and_returns_to_the_group_view(self):
        pg = self.page(self.context())
        self.choose_group(pg, 1)
        pg.click("#gpBtn")
        want = sorted((d, s, t, p, show(rng)) for _, d, s, t, p, rng in slots(None))
        self.assertEqual(sorted(shown(pg)), want)
        self.assertEqual(pg.inner_text("#gpBtn"), "العودة للجدول")
        pg.click("#gpBtn")
        self.assertEqual(shown(pg), view(1))


class TimeFormat(PageCase):
    def test_every_time_range_reads_from_start_to_end_in_arabic(self):
        # انحدار (طلب المستخدم): «من 8:30 إلى 9:30» وليس 9:30–8:30 بالعكس
        pg = self.page(self.context())
        self.choose_group(pg, 2)
        pg.click("#toggle")
        times = [r[4] for r in shown(pg, "#main") + shown(pg, "#rest")]
        self.assertEqual(len(times), 26)
        for t in times:
            m = re.fullmatch(r"من (\d{1,2}:\d{2}) إلى (\d{1,2}:\d{2})", t)
            self.assertIsNotNone(m, t)
            self.assertLess(minutes(m.group(1)), minutes(m.group(2)), f"البداية يجب أن تسبق النهاية: {t}")


class SavedChoices(PageCase):
    def test_group_supervisor_and_theme_survive_a_reload(self):
        pg = self.page(self.context())
        self.choose_group(pg, 2)
        pg.select_option("#sup", "د/ نهى أحمد")
        pg.click("#theme")
        before = shown(pg)
        pg.reload()
        self.assertTrue(pg.is_checked('input[value="2"]'))
        self.assertEqual(pg.input_value("#sup"), "د/ نهى أحمد")
        self.assertEqual(pg.evaluate("document.documentElement.dataset.theme"), "dark")
        self.assertEqual(shown(pg), before)

    def test_first_visit_follows_the_system_dark_mode(self):
        for scheme in ("dark", "light"):
            with self.subTest(scheme=scheme):
                pg = self.page(self.context(color_scheme=scheme))
                self.assertEqual(pg.evaluate("document.documentElement.dataset.theme"), scheme)


class NextLectureCard(PageCase):
    def test_card_follows_the_device_clock(self):
        cases = [  # (الوقت، أجزاء النص المتوقعة)
            (datetime(2026, 11, 2, 9, 0), ["جارية الآن", "إدارة مالية متقدمة", "من 8:30 إلى 9:30"]),
            (datetime(2026, 11, 2, 8, 0), ["المحاضرة القادمة", "اليوم", "إدارة مالية متقدمة"]),
            (datetime(2026, 11, 1, 12, 0), ["غدًا", "إدارة مالية متقدمة"]),
            (datetime(2026, 11, 2, 13, 0), ["يوم الخميس", "الأساليب الكمية واتخاذ القرار – سكشن"]),
            (datetime(2026, 11, 4, 10, 0), ["غدًا", "الأساليب الكمية واتخاذ القرار – سكشن"]),  # الأربعاء: الخميس غدًا
            (datetime(2026, 11, 6, 10, 0), ["يوم الإثنين", "إدارة مالية متقدمة"]),
        ]
        ctx = self.context()
        self.choose_group(self.page(ctx), 1)
        for when, parts in cases:
            with self.subTest(clock=str(when)):
                card = self.page(ctx, when).inner_text("#next")
                for part in parts:
                    self.assertIn(part, card)


class ResponsiveLayout(PageCase):
    def test_day_tabs_exist_on_phones_only_and_switch_the_visible_day(self):
        day = lambda pg, d: pg.locator(f'#main .day[data-d="{d}"]').is_visible()
        phone = self.context(width=375, height=800)
        pg = self.page(phone, datetime(2026, 11, 3, 10, 0))  # الثلاثاء: اليوم الافتراضي الخميس
        self.choose_group(pg, 1)
        self.assertTrue(pg.locator("#tabs").is_visible())
        self.assertEqual((day(pg, 0), day(pg, 1)), (False, True))
        pg.click('#tabs button[data-day="0"]')
        self.assertEqual((day(pg, 0), day(pg, 1)), (True, False))
        desk = self.page(self.context(), datetime(2026, 11, 3, 10, 0))
        self.choose_group(desk, 1)
        self.assertTrue(desk.locator("#tabs").is_hidden())
        self.assertEqual((day(desk, 0), day(desk, 1)), (True, True))

    def test_phone_layout_never_scrolls_horizontally(self):
        scroll = lambda pg: pg.evaluate("document.documentElement.scrollWidth > innerWidth")
        pg = self.page(self.context(width=375, height=800), datetime(2026, 11, 2, 10, 0))
        self.choose_group(pg, 1)
        steps = {
            "group view": lambda: None,
            "rest open": lambda: pg.click("#toggle"),
            "supervisor row": lambda: pg.select_option("#sup", "د/ علاء جبر"),
            "absent lecture with make-up card": lambda: pg.locator('#main .day[data-d="0"] tbody tr').nth(1).locator('[data-act="m"]').click(),
            "graduation only": lambda: pg.click("#gpBtn"),
        }
        for name, act in steps.items():
            with self.subTest(state=name):
                act()
                self.assertFalse(scroll(pg))


class Offline(PageCase):
    def test_page_makes_no_network_requests(self):
        ctx = self.context()
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: self.js_errors.append(str(e)))
        urls = []
        pg.on("request", lambda r: urls.append(r.url))
        pg.goto(PAGE.as_uri())
        self.choose_group(pg, 1)
        self.assertEqual([u for u in urls if not u.startswith("file:")], [])


if __name__ == "__main__":
    unittest.main()
