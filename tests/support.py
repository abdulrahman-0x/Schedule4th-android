"""أدوات مشتركة. الحدود المحاكاة الوحيدة: ساعة المتصفح (Playwright clock) وجسر الأندرويد (AndroidBridge).
كل شيء آخر (منطق الصفحة، التخزين، العرض) حقيقي."""
import os
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PAGE = Path(os.environ.get("SCHEDULE_PAGE", ROOT / "app/src/main/assets/index.html"))
JAVA_DIR = ROOT / "app/src/main/java/com/example/schedule4th"

MOCK_BRIDGE = """
window.__calls = []; window.__notif = true;
window.AndroidBridge = {
  status: () => JSON.stringify({notif: window.__notif}),
  requestPermission: () => window.__calls.push(['request']),
  openSettings: () => window.__calls.push(['settings']),
  setReminders: j => window.__calls.push(['set', JSON.parse(j)]),
  clearReminders: () => window.__calls.push(['clear'])
};"""

MON, THU, GRAD = "الإثنين", "الخميس", "مشروع التخرج"
# الجدول الأصلي كما كتبه المستخدم، مستقل عن بيانات الصفحة: (يوم، مادة، دكتور، مكان، {مجموعة: "بداية–نهاية"})
# المجموعة None = موعد بلا مجموعة (مشروع التخرج)
ORIGINAL = [
    (MON, "إدارة المشروعات", "د/ سعد شاهين", "مدرج إيزيس", {2: "8:30–9:30", 1: "9:30–10:30"}),
    (MON, "إدارة مالية متقدمة", "د/ هيكل عبدة", "قاعة توفيق الحكيم", {1: "8:30–9:30", 2: "9:30–10:30"}),
    (MON, "الأساليب الكمية واتخاذ القرار", "د/ نور الدين", "قاعة عباس العقاد", {1: "10:30–11:30", 2: "11:30–12:30"}),
    (MON, "إدارة المحافظ المالية والمشتقات", "د/ هيكل عبدة", "قاعة توفيق الحكيم", {2: "10:30–11:30", 1: "11:30–12:30"}),
    (MON, GRAD, "د/ عبد الحكيم", "قاعة توفيق الحكيم", {None: "12:30–2:30"}),
    (THU, "الأساليب الكمية واتخاذ القرار – سكشن", "د/ إسلام محمد", "قاعة طه حسين", {1: "8:30–9:30", 2: "9:30–10:30"}),
    (THU, "مبادئ المالية العامة – سكشن", "أ/ فاطمة جمعة", "قاعة أحمد زويل", {2: "8:30–9:30", 1: "9:30–10:30"}),
    (THU, GRAD, "أ.د/ السيد متولي", "قاعة نجيب محفوظ", {None: "8:30–10:30"}),
    (THU, "مبادئ المالية العامة", "د/ رشا مصطفى", "قاعة عباس العقاد", {1: "10:30–11:30", 2: "11:30–12:30"}),
    (THU, GRAD, "د/ رشا مصطفى", "قاعة نجيب محفوظ", {None: "12:30–2:30"}),
    (THU, GRAD, "د/ نهى أحمد", "قاعة طه حسين", {None: "12:30–2:30"}),
    (THU, GRAD, "د/ مروة عاصم", "قاعة عباس العقاد", {None: "12:30–2:30"}),
    (MON, GRAD, "د/ سعد شاهين", "قاعة أحمد زويل", {None: "1:30–3:30"}),
    (MON, GRAD, "د/ علاء جبر", "قاعة عباس العقاد", {None: "1:30–3:30"}),
    (MON, GRAD, "د/ هيكل عبدة", "قاعة مجدي يعقوب", {None: "1:30–3:30"}),
    (THU, GRAD, "د/ سميه رمضان", "قاعة مجدي يعقوب", {None: "8:30–10:30"}),
    (THU, GRAD, "د/ رشدى فاروق", "قاعة مجدي يعقوب", {None: "10:30–12:30"}),
    (THU, GRAD, "د/ أحمد يونس", "قاعة أحمد زويل", {None: "10:30–12:30"}),
    (THU, GRAD, "د/ علاء عوض", "قاعة توفيق الحكيم", {None: "10:30–12:30"}),
]
SUPERVISORS = [t for (_, s, t, _, _) in ORIGINAL if s == GRAD]
DAY_IDX = {MON: 0, THU: 1}


def minutes(clock):
    h, m = (int(x) for x in clock.split(":"))
    return (h + 12 if h < 7 else h) * 60 + m  # الساعات 1–6 بعد الظهر


def start_of(rng):
    return minutes(rng.split("–")[0])


def show(rng):
    a, b = rng.split("–")
    return f"من {a} إلى {b}"


def slots(group="all"):
    """[(فهرس الأصل، يوم، مادة، دكتور، مكان، وقت)] لكل موعد مطابق."""
    return [(i, d, s, t, p, rng) for i, (d, s, t, p, sl) in enumerate(ORIGINAL)
            for g, rng in sl.items() if group == "all" or g == group]


def view(group):
    """مواعيد المجموعة كما يجب أن تظهر: اليوم ثم وقت المجموعة، وعند التساوي الترتيب الأصلي."""
    rows = sorted(slots(group), key=lambda r: (DAY_IDX[r[1]], start_of(r[5]), r[0]))
    return [(d, s, t, p, show(rng)) for _, d, s, t, p, rng in rows]


ROWS_JS = """sel => [...document.querySelectorAll(sel + ' .day')].flatMap(d =>
  [...d.querySelectorAll('tbody tr')].map(r => {
    const c = l => { const e = r.querySelector('td[data-l="' + l + '"]'); return e ? e.textContent.trim() : null; };
    return {day: d.querySelector('h3').textContent.replace('يوم', '').trim(),
            subject: r.cells[0].querySelector('b').textContent.trim(),
            doctor: r.cells[0].querySelector('small').textContent.trim(),
            place: c('المكان'), time: c('الوقت'), group: c('المجموعة')};
  }))"""


def shown(pg, sel="#main"):
    """الصفوف المعروضة كما هي: [(يوم، مادة، دكتور، مكان، وقت)]."""
    return [(r["day"], r["subject"], r["doctor"], r["place"], r["time"]) for r in pg.evaluate(ROWS_JS, sel)]


def lecture(pg, day, i):
    """صف المحاضرة رقم i في جدول اليوم day (0 الإثنين، 1 الخميس) داخل العرض الرئيسي."""
    return pg.locator(f'#main .day[data-d="{day}"] tbody tr').nth(i)


def summary(pg):
    return pg.locator("#att .sum").inner_text()


def stored(pg, key):
    return pg.evaluate("k => localStorage.getItem(k)", key)


class PageCase(unittest.TestCase):
    """متصفح Chromium واحد للفئة، وسياق (تخزين) معزول لكل اختبار. أي خطأ JavaScript يُفشل الاختبار."""

    @classmethod
    def setUpClass(cls):
        cls._pw = sync_playwright().start()
        cls.browser = cls._pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls._pw.stop()

    def setUp(self):
        self.js_errors = []

    def tearDown(self):
        self.assertEqual(self.js_errors, [], "JavaScript errors on the page")

    def context(self, width=1100, height=900, bridge=False, init=None, **options):
        ctx = self.browser.new_context(viewport={"width": width, "height": height}, **options)
        self.addCleanup(ctx.close)
        if bridge:
            ctx.add_init_script(MOCK_BRIDGE)
        if init:
            ctx.add_init_script(init)
        return ctx

    def page(self, ctx, when=None):
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: self.js_errors.append(str(e)))
        if when:
            pg.clock.install(time=when)
        pg.goto(PAGE.as_uri())
        return pg

    @staticmethod
    def choose_group(pg, group):
        pg.check(f'input[value="{group}"]', force=True)
