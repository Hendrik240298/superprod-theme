"""Offline computed-style regressions, not a substitute for actual app testing."""

from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).absolute().parent.parent


class BrowserThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.page = self.browser.new_page(viewport={'width': 1280, 'height': 900})
        self.page.set_content((ROOT / 'tests/fixtures/app.html').read_text())
        self.style = self.page.add_style_tag(path=str(ROOT / 'todoist-dark.css'))

    def tearDown(self):
        self.page.close()

    def css(self, selector, property_name):
        return self.page.locator(selector).first.evaluate(
            '(element, name) => getComputedStyle(element).getPropertyValue(name).trim()', property_name)

    def test_todoist_canvas_sidebar_selection_and_system_typography(self):
        self.assertEqual(self.css('body', 'background-color'), 'rgb(31, 31, 31)')
        self.assertEqual(self.css('.nav-sidenav', 'background-color'), 'rgb(38, 38, 38)')
        self.assertEqual(self.css('.nav-link.active', 'background-color'), 'rgb(71, 37, 37)')
        self.assertEqual(self.css('.nav-link.active', 'color'), 'rgb(240, 127, 117)')
        self.assertIn('system-ui', self.css('body', 'font-family'))
        self.assertNotIn('Open Sans', self.css('body', 'font-family'))
        self.assertEqual(self.css('.mat-icon', 'font-family'), '"Material Icons"')

    def test_flat_row_hover_is_local_and_never_overwrites_selection_or_tracking(self):
        box = '#parent > swipe-block > .inner-wrapper > .inner-wrapper > .box'
        child_box = '#child > swipe-block > .inner-wrapper > .inner-wrapper > .box'
        self.assertEqual(self.css(box, 'background-color'), 'rgba(0, 0, 0, 0)')
        self.page.locator('#parent .display-value').first.hover()
        self.assertEqual(self.css(box, 'background-color'), 'rgb(43, 43, 43)')
        self.assertEqual(self.css(child_box, 'background-color'), 'rgba(0, 0, 0, 0)')
        self.page.locator('#child').hover()
        self.assertEqual(self.css(box, 'background-color'), 'rgba(0, 0, 0, 0)')
        self.assertEqual(self.css(child_box, 'background-color'), 'rgb(43, 43, 43)')
        self.page.locator('#parent .display-value').first.hover()
        for state, colour in [('isSelected', 'rgb(48, 48, 48)'),
                              ('isCurrent', 'rgb(53, 42, 41)'),
                              ('isMultiSelected', 'rgb(71, 37, 37)')]:
            self.page.locator('#parent').evaluate('(el, state) => el.className = state', state)
            self.assertEqual(self.css(box, 'background-color'), colour)
        self.assertEqual(self.css(box, 'outline-style'), 'solid')

    def test_circular_completion_control_preserves_hit_area_and_keyboard_focus(self):
        self.assertEqual(self.css('.done-shape', 'rx'), '10px')
        self.assertGreaterEqual(self.page.locator('done-toggle').bounding_box()['width'], 36)
        self.page.keyboard.press('Tab')
        self.assertEqual(self.css(':focus', 'outline-style'), 'solid')
        self.assertEqual(self.css(':focus', 'outline-color'), 'rgb(240, 127, 117)')
        self.page.locator('#parent').focus()
        box = '#parent > swipe-block > .inner-wrapper > .inner-wrapper > .box'
        self.assertEqual(self.css(box, 'outline-style'), 'solid')
        self.assertEqual(self.css(box, 'outline-color'), 'rgb(240, 127, 117)')
        self.page.locator('done-toggle').evaluate("el => el.classList.add('is-done')")
        self.assertEqual(self.css('.done-shape', 'fill'), 'rgb(179, 179, 179)')

    def test_overlays_inputs_and_primary_actions_share_the_dark_surfaces(self):
        self.page.evaluate('''() => {
          const overlay = document.createElement('div');
          overlay.className = 'cdk-overlay-container';
          overlay.innerHTML = '<div class="mat-mdc-menu-panel"><button class="mat-mdc-menu-item">Schedule</button></div><div class="mat-mdc-dialog-surface" role="dialog">Task details</div>';
          document.body.append(overlay);
        }''')
        for selector in ['.mat-mdc-menu-panel', '.mat-mdc-dialog-surface']:
            self.assertEqual(self.css(selector, 'background-color'), 'rgb(40, 40, 40)')
            self.assertEqual(self.css(selector, 'color'), 'rgb(238, 238, 238)')
        self.assertEqual(self.css('.mat-mdc-unelevated-button', 'background-color'), 'rgb(201, 60, 57)')
        self.assertEqual(self.css('body', '--input-bg'), '#242424')
        self.assertEqual(self.css('.tag', 'color'), 'rgb(141, 212, 162)')

    def test_material_accent_palette_does_not_fall_back_to_default_pink(self):
        self.page.evaluate('''() => {
          const indicator = document.createElement('div');
          indicator.id = 'accent-indicator';
          indicator.style.backgroundColor = 'var(--palette-accent-500, #ff4081)';
          document.body.append(indicator);
        }''')
        self.assertEqual(self.css('#accent-indicator', 'background-color'), 'rgb(201, 60, 57)')

    def test_readable_column_and_touch_rows_without_mobile_overflow(self):
        self.assertLessEqual(self.page.locator('.task-list-wrapper').bounding_box()['width'], 840)
        self.page.set_viewport_size({'width': 375, 'height': 812})
        self.assertGreaterEqual(self.page.locator('#other .first-line').bounding_box()['height'], 44)
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 375)
        self.assertEqual(self.css('magic-side-nav', 'transform'), 'none')
        self.assertEqual(self.css('magic-side-nav', 'filter'), 'none')
        self.assertNotIn('paint', self.css('magic-side-nav', 'contain'))

    def test_reduced_motion_disables_host_token_animations(self):
        self.page.emulate_media(reduced_motion='reduce')
        self.assertEqual(self.css('body', '--transition-duration-s'), '0ms')
        self.assertEqual(self.css('body', '--transition-duration-m'), '0ms')

    def test_light_mode_is_untouched_and_removing_stylesheet_restores_defaults(self):
        self.page.locator('body').evaluate("el => el.classList.remove('isDarkTheme')")
        self.assertEqual(self.css('body', 'background-color'), 'rgb(248, 248, 247)')
        self.assertIn('Open Sans', self.css('body', 'font-family'))
        self.page.locator('body').evaluate("el => el.classList.add('isDarkTheme')")
        self.style.evaluate('el => el.remove()')
        self.assertEqual(self.css('body', 'background-color'), 'rgb(19, 19, 20)')
        self.assertEqual(self.css('.done-shape', 'rx'), '5.5px')

    def test_text_and_action_labels_meet_aa_contrast(self):
        def luminance(hex_colour):
            channels = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
            return sum(c * w for c, w in zip(linear, (0.2126, 0.7152, 0.0722)))

        for foreground, background in [('--ink', '--surface-1'), ('--ink-muted', '--td-sidebar'),
                                       ('--td-accent-strong', '--td-selected')]:
            values = sorted([luminance(self.css('body', foreground)), luminance(self.css('body', background))])
            self.assertGreaterEqual((values[1] + 0.05) / (values[0] + 0.05), 4.5)
        self.assertGreaterEqual((1.0 + 0.05) / (luminance(self.css('body', '--td-button')) + 0.05), 4.5)


if __name__ == '__main__':
    unittest.main()
