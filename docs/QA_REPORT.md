# Medmate 1.0 verification report

Verified delivery: KivyMD local prototype Python source. Doctor Community excluded.

## Environment

Python 3.12.14, Kivy 2.3.1, KivyMD 1.2.0, requests 2.32.5, python-dotenv 1.1.1, Pillow 12.3.0, pytest 9.1.1. Linux SDL2/OpenGL with Mesa software rendering. Phone-sized window 390×844; desktop 1100×780. No clinical or real account data used.

## Results

| Check | Result |
|---|---|
| Full suite: `KIVY_HOME=/tmp/medmate-kivy-verified python -m pytest -q` | **35 passed in 29.44 seconds; process exit 0** |
| Data/API/health tests | 26 passed as part of full suite |
| Actual KivyMD widget integration tests | 9 passed as part of full suite |
| Actual main application event loop startup and scheduled stop | `APP_STOPPED_CLEANLY`; process exit 0 |
| `python -m compileall -q main.py medmate tests` | Pass |
| Original Python source parse audit | All 21 original Python files parsed; runtime defects separately documented |
| Secret-pattern scan of deliverable text files | No embedded OpenRouter/OpenAI key found |
| UI render script with disposable synthetic accounts | 13 screenshots generated; process exit 0 |
| Independent code review after fixes | No remaining Important/Critical findings in reviewed fixes |

Tests cover wrong password and wrong mode, registration/email/password validation, salted password hashes, restart persistence, per-account profile/preferences isolation, doctor grants and revocation, private-note isolation, linked-only messaging, actual same-device message delivery, appointment conflict/past-date/participant/status rules, vegan filtering, allergen aliases and unknown allergies, non-diagnostic offline information, API configuration/authentication/rate-limit/timeout/connection/JSON/schema failures, bounded conversation context, profile-sharing field restrictions, UI registration/profile saving, every patient and doctor route, role guards, Back/dialog handling, patient access/visit/message/doctor-note flows, logout widget clearing, stale AI callback rejection, cross-navigation pending requests, stale meal clearing, storage-error feedback, responsive sidebar switch, and a real offline worker-thread reply saving and restoring controls.

## Review corrections

The reviewer reproduced three issues before fixes. Regression tests failed for those issues, then passed after correction:

1. Reopening Assistant could permit concurrent requests or clear history during a pending response. Shared per-session request state now blocks both, and completion refreshes the currently open assistant page. Logout invalidates results.
2. Rejected unknown allergies left old meal results visible. New searches now clear previous results before validation.
3. Some storage errors escaped UI callbacks. Authentication, settings, page construction, assistant persistence, searches/status updates and conversation refresh now handle storage errors; recurring refresh stops on error.

Visual corrections increased text-field contrast and dark-mode action/icon contrast. Screenshots show the actual application, not mockups.

## Environment notes

Initial `xvfb-run` wrapper commands printed passing tests but returned 1. Investigation showed pytest/application themselves returned 0, while the wrapper cleanup failed to kill an Xvfb process that could not bind inside the sandbox. Final checks ran directly using SDL2 graphics and returned 0. This was not hidden or counted as a successful wrapper run.

KivyMD 1.2.0 emits an upstream deprecation notice and its toolbar uses an upstream deprecated property. These do not fail the tested application. The release is deliberately pinned rather than depending on an unpinned master-branch API. Mesa could not write its optional shader cache in the restricted test environment; rendering completed.

## Not verified

- Windows batch scripts on an actual Windows PC, a PyInstaller EXE build, or an Android APK/device build.
- Physical Android keyboard/Back/browser behaviour or mobile storage permissions.
- Live OpenRouter inference, provider credits, available models or clinical correctness of model output. API boundary tests use controlled transport fixtures.
- Remote messaging/sync, doctor credential verification, push notifications, real clinic schedules/bookings, encryption, or production medical compliance. These are not claimed features of this local prototype.
- Browser pages beyond their authoritative source links; the app is not a live feed.

Use fictional test records. Keep local database backups private. Replace the original embedded key at its provider if it belongs to you. Setup, limitations and complete screen instructions are in README.md.
