"""Offline stylesheet contract tests. Run with: python -m unittest discover -s tests -v."""

from pathlib import Path
import unittest

import tinycss2


ROOT = Path(__file__).absolute().parent.parent
THEME = ROOT / 'todoist-dark.css'


class ThemeContractTests(unittest.TestCase):
    def test_dark_palette_is_declared_on_body_not_inherited_from_root(self):
        self.assertTrue(THEME.is_file(), 'Installable todoist-dark.css is missing')
        rules = tinycss2.parse_stylesheet(THEME.read_text(), skip_whitespace=True, skip_comments=True)
        declarations = {}
        for rule in rules:
            if rule.type == 'qualified-rule' and tinycss2.serialize(rule.prelude).strip() == 'body.isDarkTheme':
                declarations.update({d.name: tinycss2.serialize(d.value).strip()
                                     for d in tinycss2.parse_declaration_list(rule.content)
                                     if d.type == 'declaration'})
        for name, value in {
            '--surface-0': '#191919', '--surface-1': '#1f1f1f',
            '--surface-2': '#282828', '--surface-3': '#333333', '--surface-4': '#3d3d3d',
            '--ink': '#eeeeee', '--ink-strong': '#ffffff', '--ink-muted': '#b3b3b3',
            '--ink-on-channel': '255, 255, 255', '--separator': '#363636',
            '--divider': '#3d3d3d', '--scrim': 'rgba(0, 0, 0, 0.6)',
        }.items():
            with self.subTest(token=name):
                self.assertEqual(declarations.get(name), value)

    def test_standalone_stylesheet_has_no_assets_or_hidden_controls(self):
        css = THEME.read_text()
        self.assertLess(len(css.encode()), 500 * 1024)
        self.assertNotRegex(css, r'(?i)(?:url|src|image|image-set)\s*\(|@import|@font-face')
        self.assertNotRegex(css, r'(?i)display\s*:\s*none|visibility\s*:\s*hidden|pointer-events\s*:\s*none')

    def test_css_parses_and_all_rules_are_dark_mode_scoped(self):
        def check_rules(rules):
            for rule in rules:
                self.assertNotEqual(rule.type, 'error', str(rule))
                if rule.type == 'at-rule':
                    self.assertEqual(rule.lower_at_keyword, 'media')
                    check_rules(tinycss2.parse_rule_list(rule.content, skip_comments=True, skip_whitespace=True))
                elif rule.type == 'qualified-rule':
                    self.assertTrue(tinycss2.serialize(rule.prelude).strip().startswith('body.isDarkTheme'))
                    for declaration in tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True):
                        self.assertEqual(declaration.type, 'declaration', str(declaration))
        check_rules(tinycss2.parse_stylesheet(THEME.read_text(), skip_comments=True, skip_whitespace=True))


if __name__ == '__main__':
    unittest.main()
