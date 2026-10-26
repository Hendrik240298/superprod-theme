# Design references and compatibility

Checked **2026-10-26**.

## Todoist

- [Todoist app](https://app.todoist.com/?theme=dark), public authentication surface,
  app version marker **11889**. Read its computed dark-mode design variables in a
  clean browser; no account, credentials or personal data were used.
- [Theme help](https://www.todoist.com/help/articles/change-color-themes-zD0N5K).

Observed tokens (not marketing-site colours):

| Role | Todoist dark value | Theme adaptation |
| --- | --- | --- |
| Base primary | `#1f1f1f` | Main canvas |
| Base secondary | `#262626` | Sidebar / side panels |
| Raised primary | `#282828` | Cards / menus / dialogs |
| Raised secondary | `#333333` | Higher surfaces |
| Raised tertiary / divider | `#3d3d3d` | Dividers; row hairlines softened to `#363636` |
| Primary text | `#ffffff` | Headings; task text softened to `#eeeeee` |
| Secondary text | `#cccccc` | Navigation; helper text uses `#b3b3b3` |
| Accent text | `#e26a60` | Accent |
| Selected navigation | `#472525` / `#f07f75` | Selection fill / label |
| Accent fill | `#de4c4a` | Darkened to `#c93c39` for AA white-label contrast |

The reference is the public dark-mode token set, **not** an authenticated screenshot
of every Todoist view. Layout/spacing are an independent approximation. No Doist
CSS implementation, logo, proprietary font or other assets are bundled.

## Super Productivity

Pinned target: **v19.2.0**, commit
`466a426700e7402f8628bc80ce499d3de6160dbb`.

- [Theming contract](https://github.com/super-productivity/super-productivity/blob/v19.2.0/docs/theming-contract.md)
- [CSS variables](https://github.com/super-productivity/super-productivity/blob/v19.2.0/src/styles/_css-variables.scss)
- [Installer validator](https://github.com/super-productivity/super-productivity/blob/v19.2.0/src/app/core/theme/validate-theme-css.util.ts)
- [Task states / box ownership](https://github.com/super-productivity/super-productivity/blob/v19.2.0/src/app/features/tasks/task/_task-base.scss)
- [Completion-control SVG](https://github.com/super-productivity/super-productivity/blob/v19.2.0/src/app/ui/done-toggle/done-toggle.component.html)
- [Mobile sidebar containment warning](https://github.com/super-productivity/super-productivity/blob/v19.2.0/src/app/core-ui/magic-side-nav/magic-side-nav.component.scss)
- [Iframe theme bridge](https://github.com/super-productivity/super-productivity/blob/v19.2.0/src/app/plugins/util/plugin-iframe.util.ts)

Public tokens live on `body`, not just `:root`. Installed CSS must contain the
required surface/ink tokens and cannot fetch external assets. This theme declares
all required/recommended tokens on `body.isDarkTheme`; the original validator was
run against the complete stylesheet and accepted it without warnings.

Component-level adaptations are deliberately narrow:

- The existing completion SVG rect gets circular geometry; the real control and
  its semantics remain. Selectors account for Angular's emulated encapsulation.
- Hover targets the owning task's `.box` through direct children. Hovering a parent
  never recolours every subtask, and selection/current states take precedence.
- The sidebar host gets no transform/filter/containment or forced width, avoiding
  the mobile drawer's zero-width containing-block trap.
- Material overlays receive dark surface tokens plus scoped background fallbacks.
- The theme does not inject styles into plugin iframes. Kanban compatibility uses
  only the host's supported colour/font variable injection; iframe layout was not
  end-to-end tested.

Real UI checks used **19.3.1WB** at
[app.super-productivity.com](https://app.super-productivity.com), in an ephemeral
Chromium context. The offline HTML fixture is only a cascade/DOM regression model;
it is not presented as the actual application. Desktop Electron validation remains
manual; no user configuration or native task store was accessed.
