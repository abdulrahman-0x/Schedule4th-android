"""حساب موعد التذكير القادم (LectureTime) على JVM، بنفس كود التطبيق بدون Android."""
import shutil
import subprocess
import tempfile
import unittest

from support import JAVA_DIR, ROOT

JAVAC = ["java", "-m", "jdk.compiler/com.sun.tools.javac.Main"]


@unittest.skipUnless(shutil.which("java"), "JDK غير متاح")
class LectureTimeOnJvm(unittest.TestCase):
    def test_next_reminder_is_correct_for_every_week_start_and_the_egypt_dst_change(self):
        with tempfile.TemporaryDirectory() as out:
            compiled = subprocess.run(
                JAVAC + ["-d", out, str(JAVA_DIR / "LectureTime.java"), str(ROOT / "tests/java/LectureTimeCheck.java")],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            ran = subprocess.run(["java", "-cp", out, "com.example.schedule4th.LectureTimeCheck"],
                                 capture_output=True, text=True, timeout=120)
            self.assertEqual(ran.returncode, 0, ran.stdout)


if __name__ == "__main__":
    unittest.main()
