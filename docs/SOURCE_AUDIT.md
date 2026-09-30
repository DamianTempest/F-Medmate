# Original Medmate source review and upgrade mapping

The uploaded archive contained 21 Python source files, three KV files, a Python screen fragment with an unusual filename, an authentication prototype in `login.txt`, image assets, Windows virtual-environment files, build caches, and an unrelated OWN-TEK water-project letter saved with an RTF extension despite containing DOCX bytes. Dependencies and build output were not treated as authored application code.

## Application entry and navigation

`main.py` combined duplicated imports/classes, account forms, symptom logic, meal data, local chat placeholders and screen registration. `medmate.kv` declared a second root ScreenManager and mismatched screen names. Doctor links targeted Community/Research/News names absent from the Python manager; patient links included missing chat.2/chat.3 screens. Some widgets had no behaviour or IDs expected by callbacks. Two profile images were absent. The AI hub was created both by Python and KV and a button called a nonexistent method. Account forms only validated text before marking login successful. Doctor forms did not use an actual authentication store.

Replacement: one MDApp shell, one managed active page, explicit role routes, actual saved accounts and profile storage, shared KivyMD styling, consistent Back navigation. No missing background/photo dependencies. Community omitted as instructed.

## AI, profiles and meals

`AI_ChatBox.py` was an alternate healthcare-only application. `screens/chat_screen.py` scheduled synchronous network work through Clock, still blocking the interface. `screens/profile_screen.py` and its duplicate fragment shared one JSON file for every user. `screens/dietician_screen.py` loaded stale preferences, never called its own save method in the suggestion flow, blocked during API work, and its failure handler called a nonexistent message function. `ai_response.py` and `ask_dietician.py` embedded an API key, omitted timeouts and returned unchecked API JSON.

Replacement: account-specific SQLite profile/preferences, separate API service with environment-only credentials and HTTP/schema/timeout handling, worker-thread requests and UI/session-safe completion, copied/selectable local history, explicit profile sharing. The exposed original key is not included; its owner should revoke or rotate it.

`Dieti.py` and the meal implementation in `main.py` had duplicated recipe databases. Vegetarian meals included fish; keto/paleo categories included incompatible starch/grain preparations. Allergy comparison used raw untrimmed tokens and ingredient literals. `Edit.py` included an older app variant and attempted `.lower()` on meal dictionaries during filtering.

Replacement: one honest meal-idea catalogue, explicit preparation variants and ingredients, vegetarian/vegan/pescatarian/omnivore matching, allergen alias handling and refusal for unknown allergies. No diagnosis, drug recommendations or claims that a real meal is allergen-free.

## Other experiments

| Original file(s) | Purpose / finding | Result |
|---|---|---|
| `Edit.py` | Earlier monolithic application with overlapping names and dead screens | Consolidated into current workflows. |
| `Chat_2.py` | Separate Tkinter GPT-2 chat; depends on absent local model | Removed from runnable app. Offline library labelled honestly. |
| `gpt2.py`, `health_gpt2.py`, `preload_model.py` | Download general GPT-2 on import, not a clinical model | No automatic model downloads. Optional online client only. |
| `server.py`, `bac_end.py` | Duplicate Flask keyword symptom mapping with debug server | Core app no longer requires port 5000 or a server. Symptom page supplies non-diagnostic next-step information. |
| `smpth0ms.py` | Separate Kivy symptom client with blocking localhost request | Integrated into the patient tool without a server. |
| `sms.py`, `sms_server.py` | Kivy/Flask tips experiments; substring health flags, not SMS delivery | Replaced with integrated general-information library and tips. |
| `bace.py` | Echo-style Flask chat stub | Real same-device account conversations; no invented replies. |
| `f.py` | Popup demonstration | Consistent Material dialogs. |
| `import streamlit as st.py` | Separate Streamlit echo demonstration | Removed from runtime. |
| `c.kv`, `c2.kv` | Duplicate input/response layouts with no matching complete runtime | Replaced by profile/tool forms. |
| `Profilescreen.screenmanager import Scree` | Duplicate Python profile fragment | One profile implementation. |
| `login.txt` | Flask login stub; raw SHA256 hash incompatible with Werkzeug check; fake token | Actual salted password hashes and role-aware account checks. |
| `main.spec` | PyInstaller configuration omitted KV/assets | KivyMD collection configuration supplied; target-platform binary build untested. |
| `buildozer.spec` | Unpinned KivyMD master branch and absent API client dependencies | Pinned Kivy/KivyMD, client/SSL dependencies and clean source exclusions; Android build untested. |

All 21 original Python files parsed successfully during the audit. Parsing alone did not prove their runtime behaviour. The replacement application has behaviour and actual-widget integration tests; see QA_REPORT.md.

The clean delivery omits old personal profile data, embedded keys, .git metadata, virtual environments, caches, compiled build output, unused image assets and the unrelated letter. The original upload was available during the review; legacy profile import is explicit and account-specific.
