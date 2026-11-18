"""Smoke tests: every example tastes cleanly in every mode."""
import glob
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TONGUE = os.path.join(HERE, "tongue.py")
EXAMPLES = sorted(glob.glob(os.path.join(HERE, "examples", "*.json")))


def run(*args):
    return subprocess.run([sys.executable, TONGUE, *args], capture_output=True, text=True)


class TongueTests(unittest.TestCase):
    def test_examples_exist(self):
        self.assertGreater(len(EXAMPLES), 3)

    def test_all_mode(self):
        for path in EXAMPLES:
            r = run(path, "all", "room")
            self.assertEqual(r.returncode, 0, msg=f"{path}: {r.stderr}")
            self.assertIn("sweet", r.stdout)

    def test_temperatures(self):
        for temp in ("frozen", "cold", "room", "hot", "scorching"):
            r = run(EXAMPLES[0], "all", temp)
            self.assertEqual(r.returncode, 0, msg=r.stderr)

    def test_drink_dilute(self):
        r = run(os.path.join(HERE, "examples", "dr-pepper.json"), "dilute", "cold")
        self.assertEqual(r.returncode, 0, msg=r.stderr)

    def test_layers(self):
        r = run(os.path.join(HERE, "examples", "warheads.json"), "layers")
        self.assertEqual(r.returncode, 0, msg=r.stderr)

    def test_cookie_dunk(self):
        r = run(os.path.join(HERE, "examples", "chocolate-chip-cookie.json"), "dunk")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("dunk", r.stdout.lower())


if __name__ == "__main__":
    unittest.main()
