# Medmate local prototype design

User-approved direction: local prototype first, KivyMD, no Community in doctor mode. The user authorised completing the design and implementation in this session.

## Outcome
A runnable desktop application that retains the patient/doctor health companion concept and supports real local account workflows. No cloud server, paid AI, or external login is required for core use. Android-friendly layouts and a maintained Buildozer configuration are included; an APK is not claimed without a device build.

## Design
Kivy 2.3.1 and KivyMD 1.2.0, pinned stable compatible APIs. A muted teal identity, warm off-white canvas, rounded cards, generous spacing, large touch targets, visible field labels, consistent toolbar and four primary navigation actions. Responsive card columns on wide windows, single columns on phones. Scroll all long forms. Back closes dialogs or returns to the prior screen; logout clears private widgets/history. Light/dark preference per account.

## Workflows
Patient: account creation/login, dashboard, edit profile (age, country, history, medicines, allergies, activities), choose a doctor account on this device and grant record access, request/cancel appointments, messages, assistant, meal ideas, symptom guidance, resources, settings/about.
Doctor: account creation/login with self-declared license and specialty (not verified), dashboard, authorised patients and private notes, appointment accept/complete/cancel, messages, research/news source links, own profile, settings/about. No Community screen.
Messages are delivered between linked accounts using the same local database, never falsely labelled as remotely sent. No invented doctor replies. Doctor profile access and messaging require the patient link; unlink revokes access and future messages. Existing conversation history remains available to its participants.
Appointments validate future date/time, avoid doctor double booking and expose participant-only updates. Patient can cancel; doctor can accept/complete/cancel. Completed/cancelled requests are terminal.

## Persistence and errors
SQLite with foreign keys, salted PBKDF2 password hashes, role checks, parameterised queries, per-account profiles/preferences, conversations/appointments, and doctor-only notes. Preserve legacy JSON through an explicit import action into the signed-in patient account; never silently assign the legacy person's data. Keep database outside installed source in application user-data directory. Friendly validation messages; rollback failed mutations. Do not ship old data, embedded credentials, environments or build output.

## Health tools
Offline assistant is explicitly a small general-information library, not an LLM. Symptom page records a user's concerns and prompts clinical review, never diagnoses or suggests medicines. Emergency examples point to authoritative resources. Meal database shows ingredients, declared allergens, and preference matching; unsupported or unrecognised allergies cause a refusal to claim suitability. No therapeutic meal plans or inaccurate keto/paleo labels. Online AI is optional OpenRouter, configured through environment only. Timeouts and HTTP/schema errors are mapped to clear UI status. Worker threads do requests; Clock callbacks update UI. No profile sent unless the user explicitly enables it; requests contain a bounded prior conversation and only relevant fields. Late callbacks cannot leak across logout/account changes. Keep failed requests retryable.

## Resources, distribution and evidence
Research/news are honest external authoritative resource links, not fabricated live feeds. Include README, Windows setup/start scripts, pinned requirements, clean Buildozer and PyInstaller specifications, migration notes, source audit, test report, screenshots. Unit/integration tests exercise account persistence/isolation, access revocation, appointments, message delivery, meal filtering, API failures, and UI navigation/forms. Verify real KivyMD rendering at phone and desktop sizes. External AI and Android/Windows packaged binaries require their own runtime validation and must be reported as untested if unavailable.
