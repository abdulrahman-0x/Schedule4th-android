"""فحوصات ثابتة لمشروع الأندرويد (لا تحتاج SDK): ما يكسر البناء أو يعطّل التذكيرات بصمت."""
import re
import shutil
import subprocess
import unittest
import xml.etree.ElementTree as ET

from support import JAVA_DIR, PAGE, ROOT, PageCase

RES = ROOT / "app/src/main/res"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
ANDROID = "{http://schemas.android.com/apk/res/android}"


def manifest():
    return ET.parse(MANIFEST).getroot()


def java_sources():
    return sorted(JAVA_DIR.glob("*.java"))


class ProjectFiles(unittest.TestCase):
    def test_all_xml_files_are_well_formed(self):
        for f in [MANIFEST, *RES.rglob("*.xml")]:
            with self.subTest(file=str(f.relative_to(ROOT))):
                ET.parse(f)

    def test_every_referenced_resource_exists(self):
        defined = set()
        for f in RES.rglob("*"):
            kind = f.parent.name.split("-")[0]
            if f.is_file() and kind in ("drawable", "mipmap"):
                defined.add((kind, f.stem))
            if f.is_file() and kind == "values":
                defined |= {(el.tag, el.get("name")) for el in ET.parse(f).getroot()}
        refs = set()
        for f in [MANIFEST, *RES.rglob("*.xml")]:
            refs |= {(k, n) for k, n in re.findall(r"@(drawable|mipmap|string|color|style)/([\w.]+)", f.read_text("utf-8"))}
        for f in java_sources():
            refs |= {(k, n) for k, n in re.findall(r"\bR\.(drawable|mipmap|string|color)\.(\w+)", f.read_text("utf-8"))}
        self.assertEqual(sorted(refs - defined), [])

    def test_the_signing_keystore_gradle_points_to_is_committed(self):
        # مفتاح التوقيع الثابت يجعل كل بناء على GitHub يُثبَّت فوق السابق. فقدانه أو تجاهله في git يكسر البناء.
        gradle = (ROOT / "app/build.gradle.kts").read_text("utf-8")
        keystores = re.findall(r'storeFile\s*=\s*file\("([^"]+)"\)', gradle)
        self.assertTrue(keystores, "لا يوجد storeFile في build.gradle.kts")
        ignored = (ROOT / ".gitignore").read_text("utf-8")
        for name in keystores:
            with self.subTest(keystore=name):
                self.assertGreater((ROOT / "app" / name).stat().st_size, 0)
                self.assertNotIn("keystore", ignored)

    @unittest.skipUnless(shutil.which("java"), "JDK غير متاح")
    def test_java_sources_have_no_syntax_errors(self):
        # فحص صيغة فقط، ليس بناءً: الربط مع Android يحتاج SDK
        done = subprocess.run(["java", str(ROOT / "tests/java/ParseOnly.java"), *map(str, java_sources())],
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


class Manifest(unittest.TestCase):
    def test_declares_the_permissions_reminders_need_and_no_internet(self):
        perms = {p.get(ANDROID + "name").split(".")[-1] for p in manifest().iter("uses-permission")}
        self.assertTrue({"POST_NOTIFICATIONS", "USE_EXACT_ALARM", "RECEIVE_BOOT_COMPLETED"} <= perms)
        self.assertNotIn("INTERNET", perms)  # التطبيق يعمل بلا إنترنت

    def test_every_android_component_class_is_registered_and_every_registered_class_exists(self):
        declared = {c.get(ANDROID + "name").lstrip(".") for tag in ("activity", "receiver", "service") for c in manifest().iter(tag)}
        defined = {f.stem for f in java_sources()
                   if re.search(r"extends\s+(Activity|BroadcastReceiver|Service)\b", f.read_text("utf-8"))}
        self.assertEqual(declared, defined)

    def test_components_with_intent_filters_declare_exported_explicitly(self):
        # من أندرويد 12 يرفض البناء أي مكوّن له intent-filter بدون android:exported
        for tag in ("activity", "receiver", "service"):
            for c in manifest().iter(tag):
                if c.find("intent-filter") is not None:
                    with self.subTest(component=c.get(ANDROID + "name")):
                        self.assertIsNotNone(c.get(ANDROID + "exported"))


class PageToAppContract(unittest.TestCase):
    """الصفحة والتطبيق يتخاطبان بأسماء نصية: خطأ إملائي واحد يعطّل الميزة بصمت."""

    def test_page_only_calls_bridge_methods_the_app_exposes(self):
        page = PAGE.read_text("utf-8")
        bridge = (JAVA_DIR / "ReminderBridge.java").read_text("utf-8")
        exposed = set(re.findall(r"@JavascriptInterface\s+public\s+\w+\s+(\w+)\(", bridge))
        called = set(re.findall(r"\bAB\.(\w+)\(", page))
        self.assertTrue(called, "لم تُعثر على أي نداء للجسر")
        self.assertEqual(sorted(called - exposed), [])

    def test_app_loads_the_page_it_actually_ships(self):
        main = (JAVA_DIR / "MainActivity.java").read_text("utf-8")
        entry = re.search(r'START_URL\s*=\s*".*?/assets/([\w.]+)"', main).group(1)
        self.assertTrue((ROOT / "app/src/main/assets" / entry).is_file())


class AppToPageContract(PageCase):
    """ما ينادي عليه التطبيق داخل الصفحة يجب أن يكون دالة حقيقية على window وقت التشغيل.
    النداء من الجافا بصيغة `window.x && window.x()` يفشل بصمت إن كانت الدالة محلية أو غير موجودة،
    وفحص النص (regex) لا يكشف ذلك لأنه ينجح حتى لو كانت الدالة داخل IIFE."""

    def test_every_function_the_app_calls_exists_on_window_at_runtime(self):
        names = set(re.findall(r"window\.(\w+)", (JAVA_DIR / "MainActivity.java").read_text("utf-8")))
        self.assertTrue(names)
        pg = self.page(self.context(bridge=True))  # بعض الدوال تُعرَّف داخل التطبيق فقط (عند وجود الجسر)
        for name in sorted(names):
            with self.subTest(function=name):
                self.assertEqual(pg.evaluate(f"typeof window.{name}"), "function")


if __name__ == "__main__":
    unittest.main()
