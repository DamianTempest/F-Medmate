# Medmate 1.0 — KivyMD local prototype

A complete local patient–doctor companion. Patient and doctor accounts use the **same device and database**. No server or API key is needed for accounts, profiles, access permissions, appointments, messages, private doctor notes, Ghanaian meal ideas, or the offline information library.

**Doctor mode has no Community page.** Its home actions are Patients, Appointments, Messages, and Research & news.

## Start on Windows (beginner steps)

1. Install **64-bit Python 3.12** from https://www.python.org/downloads/. Include the Python launcher (`py`) and select “Add Python to PATH”. Python 3.12 is the tested version for this delivery.
2. Extract this ZIP completely. Do not run files from inside the ZIP window.
3. Open the extracted `Medmate` folder and double-click **setup_windows.bat**. Internet is required to download dependencies. Wait until it says “Setup complete”.
4. Double-click **run_windows.bat**. Keep the console open while using the app. If there is a startup error, the window stays open so you can copy it.
5. Choose Patient or Doctor. Select “New here? Create an account”. Enter a name, email and password with at least eight characters. Doctor accounts also enter a self-declared license number; the app does not verify it.

If `py -3.12` is not found, install Python 3.12 with its launcher and retry. Do not reuse the virtual environment from the old ZIP; it was tied to another PC. A fresh `.venv` is created for this copy.

### Start in a terminal (Windows)

```powershell
cd "C:\path\to\Medmate"
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

### Linux / macOS source run

Use Python 3.12 and a normal graphical desktop. On Linux install SDL/OpenGL system libraries if requested by Kivy.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

## Try the complete care workflow

Use fictional test records. No demo credentials or personal health data are shipped.

1. Create a **Doctor** account; fill its name, self-declared license and specialty. Sign out using the top-right logout icon.
2. Create a **Patient** account. Open **My profile** and save details, history, medicines and allergies.
3. Open **My care**. Search for the doctor account you created. Press **Grant record access**. This gives that doctor access to the complete patient profile, enables messaging, and permits visit requests.
4. Open **Appointments**, choose the doctor, enter a future date (`YYYY-MM-DD`), time (`HH:MM`, 24-hour), and reason. Press **Request appointment**.
5. Send a message from **Messages**. This is saved to the recipient's local account; it is not sent to another device or clinic.
6. Sign out and sign in as the doctor. Open the patient record, add a private note, read/reply to the message, and accept the requested visit. An accepted visit can be marked Complete.
7. Return to the patient account. The reply and updated appointment status appear. Removing doctor access cancels active visits and prevents further record access or messages. Existing message history remains available to both participants.

Appointment requests reserve a doctor/time slot while requested or accepted. Cancelled/completed slots can be used again. Date and time follow the device's local clock. The app does not enforce a clinic schedule, notify a real hospital, or send remote reminders.

## Screen guide

| Screen | What you can do |
|---|---|
| Welcome / account | Choose mode, register, sign in, or change workspace. |
| Patient home | See active/next appointments and open My care, assistant, meals or symptoms. |
| Doctor home | Open authorised patients, appointments, messages or external research/news resources. |
| Profile | Save your own details. Patient health information is shared only through explicit doctor links. |
| My care | Search local doctor accounts, grant access, message or remove access. |
| My patients | Search patients who granted this doctor account access. |
| Patient record | Read shared fields; save doctor-only notes. |
| Appointments | Request, accept, complete or cancel, subject to role and status. Active/all filters include visit history. |
| Messages / conversation | Search contacts, send/reply, refresh, and select message text to copy. Open conversations refresh every three seconds. |
| Health assistant | Use the honest offline information library, or opt into configured Online AI; retry failed requests or clear saved history. |
| Meal ideas | Choose a dietary preference and review Ghanaian preparation ideas, ingredients and allergens. Unsupported allergies stop suggestions until reviewed. |
| Symptom guidance | Enter concerns and see general next-step information. It does not diagnose, assess individual urgency or prescribe. |
| Resources | Open WHO information/news, PubMed research and NHS symptom sources in your browser. No fabricated live news feed. |
| Settings | Light/dark theme, AI opt-in, optional profile sharing, local data folder, legacy import and About. |

On wide windows the sidebar is visible. On narrow windows a four-action bottom bar appears. Longer forms scroll. The top-left Back button and Escape/Android Back return through navigation history; if a dialog is open, Back closes it first. From Home, Back offers Sign out rather than immediately exiting.

## Optional Online AI

The offline library is a small collection of general information; **it is not an offline language model**. GPT-2 experiments and automatic model downloads from the old project are removed from the runnable app.

To enable open-ended online responses:

1. Obtain your own OpenRouter API key and an available model identifier from https://openrouter.ai/.
2. Copy `.env.example` to `.env` in the same folder as `main.py`.
3. Fill `OPENROUTER_API_KEY` and `OPENROUTER_MODEL`. Never share the `.env` file.
4. Restart Medmate. In Settings enable **Use Online AI** and save.
5. Optional: enable **Include health profile with AI requests**. This sends age, history, medicines and allergies. Automatic context excludes names, license numbers and contact details; anything you type in the question or conversation still goes to the provider.

Online requests send your question and up to 12 prior conversation entries to OpenRouter/model providers. API usage can cost money and depends on provider availability. A ChatGPT subscription does not supply an OpenRouter key or credits. No API key is stored in the database. Without configuration, keep Online AI off. Timeouts, rate limits, authentication and malformed responses have useful retry messages. Requests run off the UI thread; logout invalidates pending results.

This delivery tests the API boundary with controlled responses, including failures. **No live paid AI request was performed.**

## Your data and the old project

The application creates `medmate.db` in Kivy's application user-data folder. Settings shows the exact path. On Windows this is normally below `%APPDATA%`. Set `MEDMATE_DATA_DIR` to an absolute folder before launch to override it. Both roles must use the same folder for the local prototype workflow.

Close every running Medmate instance before copying the database for backup. Keep the backup private. Do not overwrite your only backup when upgrading. Reinstalling source does not erase the normal user-data folder.

The original login did not persist real accounts, so create new accounts. To keep an old profile, retain your own `data/user_profile.json`, sign in to the correct patient account, and use **Settings → Import legacy profile**, entering the file's full path. Review the confirmation before importing. This delivery does not contain the old user's personal profile or the exposed API key. If the old key was yours, revoke/rotate it with OpenRouter.

The database is not encrypted. Doctor credentials are not verified. This is a development prototype for test records, not a deployed medical service. Do not rely on it for emergencies, diagnosis, prescriptions, real clinic bookings or clinical data security.

## Run the tests

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The UI tests need a working graphical display. On a Linux server:

```sh
KIVY_HOME=/tmp/medmate-kivy-tests xvfb-run -a python -m pytest -q
```

Pure data/API tests can run without graphics:

```sh
python -m pytest tests/test_store.py tests/test_health.py tests/test_assistant.py -q
```

Actual UI screenshots are in `docs/previews`. Render new synthetic previews from the project folder with `PYTHONPATH=. python tests/render_previews.py` (PowerShell: set `$env:PYTHONPATH = "."` first).

## Android and Windows packaging

`buildozer.spec` is updated for KivyMD, requests, SSL, arm64, portrait layout and internet permission. Build on a supported Linux/WSL environment using Buildozer/python-for-android tooling and Android SDK/NDK. Start with `buildozer android debug`. The local record database is outside packaged source; Android backup is disabled. Android's treatment of browser intents, keyboards and physical Back needs device testing.

For a Windows folder build, install PyInstaller and run `python -m PyInstaller --clean main.spec` on Windows. It collects KivyMD data/fonts. `.env` is deliberately not included; use environment variables for optional AI in a packaged build.

**No Android APK or Windows EXE was built or device-tested in this delivery.** The verified deliverable is the Python source application. See `docs/QA_REPORT.md` for the exact checks and limitations.

## Source layout

- `main.py`: application shell, responsive navigation, theme and session lifecycle.
- `medmate/store.py`: SQLite accounts, profiles, permissions, visits and conversations.
- `medmate/ui.py`: shared KivyMD widgets and page layout.
- `medmate/screens.py`: patient and doctor workflows.
- `medmate/health.py`: conservative offline information, meal metadata and source links.
- `medmate/assistant.py`: optional OpenRouter client and error handling.
- `tests/`: behaviour and actual-widget integration tests; disposable screenshot data.
- `docs/SOURCE_AUDIT.md`: original-code findings and what replaced them.
