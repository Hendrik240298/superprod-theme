"""Opt-in network check in a clean browser: python tests/app_smoke.py.

Uses the public web app, NEVER an existing browser/profile or desktop task store.
Set SP_APP_URL to test a separately served app build; screenshots go to test-results/.
"""

import os
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).absolute().parent.parent


class RealAppSmokeTests(unittest.TestCase):
    def test_install_reload_task_states_mobile_and_uninstall(self):
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={'width': 1440, 'height': 960}, color_scheme='dark')
            page.goto(os.environ.get('SP_APP_URL', 'https://app.super-productivity.com'), wait_until='networkidle')
            page.locator('nav-item').filter(has_text='Settings').click()
            page.wait_for_url('**/config**')
            expect(page.get_by_role('button', name='Install theme')).to_be_visible()
            with page.expect_file_chooser() as chooser:
                page.get_by_role('button', name='Install theme').click()
            chooser.value.set_files(str(ROOT / 'todoist-dark.css'))
            page.wait_for_function("getComputedStyle(document.body).getPropertyValue('--td-sidebar').trim() === '#262626'")
            self.assertEqual(page.locator('#custom-theme-stylesheet').count(), 1)
            page.reload(wait_until='networkidle')
            page.wait_for_function("getComputedStyle(document.body).getPropertyValue('--td-sidebar').trim() === '#262626'")
            page.locator('nav-item').filter(has_text='Today').first.click()
            page.wait_for_url('**/tag/TODAY/tasks')
            for title in ['Plan the week', 'Review the project proposal', 'Read a chapter']:
                page.keyboard.press('Shift+A')
                page.locator('add-task-bar textarea').fill(title)
                page.keyboard.press('Enter')
                expect(page.locator('task').filter(has_text=title)).to_be_visible()
                page.keyboard.press('Escape')
            expect(page.locator('task')).to_have_count(3)
            if page.get_by_role('button', name='No thanks', exact=True).count():
                page.get_by_role('button', name='No thanks', exact=True).click()
            expect(page.locator('.cdk-overlay-backdrop')).to_have_count(0)
            page.evaluate('''async () => {
              await Promise.allSettled(document.getAnimations()
                .filter(a => a.effect.getTiming().iterations !== Infinity).map(a => a.finished));
            }''')
            page.mouse.move(1000, 600)
            page.screenshot(path=str(results / 'desktop.png'), animations='disabled')
            self.assertEqual(page.locator('.nav-sidenav').evaluate('(e)=>getComputedStyle(e).backgroundColor'), 'rgb(38, 38, 38)')
            row = page.locator('task').first
            self.assertEqual(row.locator('.done-shape').first.evaluate('(e)=>getComputedStyle(e).rx'), '10px')
            self.assertEqual(row.locator('.done-shape').first.evaluate('(e)=>getComputedStyle(e).opacity'), '0.75')
            # The real completion control must still work after CSS reshaping.
            row.locator('done-toggle').first.click()
            expect(page.locator('task.isDone')).to_have_count(1)
            # Desktop actions and native row menus remain visible/clickable.
            page.locator('task:not(.isDone)').first.click(button='right')
            expect(page.locator('.mat-mdc-menu-panel').first).to_be_visible()
            self.assertEqual(page.locator('.mat-mdc-menu-panel').first.evaluate('(e)=>getComputedStyle(e).backgroundColor'), 'rgb(40, 40, 40)')
            page.screenshot(path=str(results / 'menu.png'), animations='disabled')
            page.keyboard.press('Escape')
            page.set_viewport_size({'width': 390, 'height': 844})
            page.screenshot(path=str(results / 'mobile.png'), animations='disabled')
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)
            page.locator('mobile-bottom-nav button').filter(has=page.locator('mat-icon', has_text='menu')).click()
            drawer = page.locator('.nav-sidenav.mobile')
            expect(drawer).to_be_visible()
            self.assertGreater(drawer.bounding_box()['width'], 200)
            page.screenshot(path=str(results / 'mobile-drawer.png'), animations='disabled')
            page.locator('.mobile-menu-close').click()
            # Return to Settings on desktop; remove the user theme using the UI.
            page.set_viewport_size({'width': 1440, 'height': 960})
            page.locator('nav-item').filter(has_text='Settings').click()
            page.wait_for_url('**/config**')
            expect(page.get_by_role('button', name='Install theme')).to_be_visible()
            print('App version:', page.locator('body').inner_text().split('Super Productivity ')[-1].split('content_copy')[0])
            page.locator('mat-select').first.click()
            page.get_by_role('option').filter(has_text='Todoist Dark').get_by_role('button', name='Remove theme').click()
            expect(page.locator('#custom-theme-stylesheet')).to_have_count(0)
            page.keyboard.press('Escape')
            page.locator('nav-item').filter(has_text='Today').first.click()
            expect(page.locator('task')).to_have_count(3)
            page.reload(wait_until='networkidle')
            expect(page.locator('task')).to_have_count(3)
            expect(page.locator('#custom-theme-stylesheet')).to_have_count(0)
            browser.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
