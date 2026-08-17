import unittest
import zipfile

import package_release


class ZipReadmeTest(unittest.TestCase):
    def test_keeps_everything_before_the_regenerating_heading(self):
        out = package_release.zip_readme(
            "# Title\n\n## Install\n\nCopy Config.\n\n## Regenerating\n\ncd tools\n"
        )
        self.assertIn("## Install", out)
        self.assertIn("Copy Config.", out)

    def test_drops_build_steps_that_name_files_the_zip_lacks(self):
        out = package_release.zip_readme(
            "# Title\n\n## Regenerating\n\npython build_vrlf_profiles.py --verify\n"
        )
        self.assertNotIn("build_vrlf_profiles.py", out)
        self.assertNotIn("--verify", out)

    def test_points_at_the_repo_instead(self):
        out = package_release.zip_readme("# T\n\n## Regenerating\n\nx\n", repo_url="http://x/y")
        self.assertIn("http://x/y", out)

    def test_a_moved_heading_fails_the_build(self):
        with self.assertRaises(SystemExit):
            package_release.zip_readme("# Title\n\n## Rebuilding\n\ncd tools\n")

    def test_heading_must_start_a_line(self):
        # A mid-sentence mention is not the section, and must not truncate the README.
        with self.assertRaises(SystemExit):
            package_release.zip_readme("# Title\n\nSee ## Regenerating below.\n")


class PayloadTest(unittest.TestCase):
    def test_payload_is_the_two_installable_folders(self):
        rels = [rel for _, rel in package_release.payload_files()]
        self.assertTrue(rels)
        for rel in rels:
            self.assertTrue(
                rel.startswith("Config/") or rel.startswith("GameSettings/"), rel
            )

    def test_ships_no_generator_or_base_templates(self):
        rels = [rel for _, rel in package_release.payload_files()]
        self.assertFalse([r for r in rels if r.endswith(".py")])
        self.assertFalse([r for r in rels if r.startswith("base/")])


class BuildTest(unittest.TestCase):
    def test_zip_has_one_top_level_folder_carrying_readme_and_licence(self):
        import tempfile
        import pathlib

        with tempfile.TemporaryDirectory() as tmp:
            out = package_release.build("v0.0-test", pathlib.Path(tmp))
            with zipfile.ZipFile(out) as z:
                names = z.namelist()
            roots = {n.split("/", 1)[0] for n in names}
            self.assertEqual(roots, {"VRLF-Dolphin-Accuracy-Profiles-v0.0-test"})
            self.assertIn("VRLF-Dolphin-Accuracy-Profiles-v0.0-test/README.md", names)
            self.assertIn("VRLF-Dolphin-Accuracy-Profiles-v0.0-test/LICENSE", names)


if __name__ == "__main__":
    unittest.main()
