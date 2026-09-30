"""Real KivyMD integration tests; run with a graphics display (xvfb-run on Linux)."""
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import pytest
os.environ.setdefault('KIVY_NO_ARGS','1')
os.environ.setdefault('KIVY_NO_CONSOLELOG','1')
from main import MedMateApp
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.core.window import Window

def pump(n=12):
    for _ in range(n): Clock.tick(); EventLoop.idle()

@pytest.fixture(scope='module')
def app(tmp_path_factory):
    a=MedMateApp(data_dir=tmp_path_factory.mktemp('ui'))
    a._run_prepare()
    pump()
    yield a
    a.stop()

def test_authentication_ui_and_patient_profile(app):
    app.show_auth('patient',True)
    page=app.current_page
    page.fields['name'].text='UI Patient'
    page.fields['email'].text='ui@example.com'
    page.fields['password'].text='testpass123'
    page.fields['confirm'].text='testpass123'
    page.submit()
    pump()
    assert app.user['role']=='patient'
    assert app.route=='dashboard'
    app.navigate('profile')
    app.current_page.fields['age'].text='23'
    app.current_page.fields['allergies'].text='fish'
    app.current_page.save()
    assert app.store.profile(app.user['id'])['allergies']=='fish'
    app.close_dialog(); pump(4)
    app.navigate('settings')
    app.back()
    assert app.route=='profile'

def test_all_patient_routes_render_and_doctor_routes_are_guarded(app):
    for route in ('dashboard','care','appointments','messages','assistant','meals','symptoms','resources','profile','settings','about'):
        app.navigate(route); pump(3)
        assert app.route==route
        assert app.current_page.width>0
    app.navigate('patients')
    assert app.route=='about'

def test_same_device_link_appointment_message_and_doctor_record(app):
    p=app.user['id']
    d=app.store.register('ui-doc@example.com','testpass123','doctor','UI Doctor','TEST-UI','General practice')['id']
    app.navigate('care')
    app.current_page.grant(d)
    app.navigate('appointments')
    page=app.current_page
    page.doctor_id=d
    page.fields['date'].text=(datetime.now()+timedelta(days=3)).strftime('%Y-%m-%d')
    page.fields['time'].text='10:30'
    page.fields['reason'].text='UI check up'
    page.request()
    assert len(app.store.appointments(p))==1
    app.open_conversation(d)
    app.current_page.message_input.text='Hello from UI'
    app.current_page.send()
    assert app.store.messages(d,p)[0]['text']=='Hello from UI'
    app.logout()
    assert app.user is None
    app.sign_in(app.store.login('ui-doc@example.com','testpass123','doctor'))
    for route in ('dashboard','patients','appointments','messages','resources','profile','settings','about'):
        app.navigate(route); pump(3)
        assert app.route==route
    app.open_patient(p)
    assert 'fish' in app.current_page.record['allergies']
    app.current_page.note_input.text='Test note'
    app.current_page.save_note()
    assert app.store.notes(d,p)[0]['text']=='Test note'
    aid=app.store.appointments(d)[0]['id']
    app.navigate('appointments'); app.current_page.change_status(aid,'accepted')
    assert app.store.appointments(d)[0]['status']=='accepted'
    app.logout()
    assert app.current_page.route=='welcome'
    assert len(app.manager.screens)==1

def test_stale_ai_result_is_ignored_after_logout(app):
    app.sign_in(app.store.login('ui@example.com','testpass123','patient'))
    app.navigate('assistant')
    page=app.current_page; session=app.session_id; uid=app.user['id']
    app.logout()
    page.finish_response(session,uid,'Sensitive stale answer',None)
    assert app.store.assistant_history(uid)==[]

def test_phone_and_desktop_layout_switches(app):
    app.sign_in(app.store.login('ui@example.com','testpass123','patient'))
    Window.size=(390,844); pump()
    assert app.sidebar.width==0
    Window.size=(1100,780); pump()
    assert app.sidebar.width>100

def test_pending_assistant_survives_navigation_without_overlapping_requests(app):
    app.sign_in(app.store.register('async@example.com','testpass123','patient','Async Tester'))
    app.navigate('assistant')
    old=app.current_page
    session=app.session_id; uid=app.user['id']
    # Simulate the UI after dispatch; no external API required.
    old.busy=True
    app.assistant_pending.add((session,uid))
    app.navigate('dashboard'); app.navigate('assistant')
    assert app.current_page.send_btn.disabled
    assert app.current_page.busy
    old.finish_response(session,uid,'A completed response',None)
    assert not app.current_page.send_btn.disabled
    assert 'A completed response' in app.current_page.transcript.text

def test_invalid_allergy_clears_previous_suggestions(app):
    app.sign_in(app.store.register('allergy@example.com','testpass123','patient','Allergy Tester'))
    app.navigate('meals'); page=app.current_page
    page.suggest(); assert page.list.children
    page.allergies.text='mango'; page.suggest()
    assert not page.list.children
    app.close_dialog()

def test_storage_failure_in_settings_does_not_escape_callback(app,monkeypatch):
    import sqlite3
    app.navigate('settings'); page=app.current_page
    def fail(*args,**kwargs): raise sqlite3.OperationalError('database is locked')
    with monkeypatch.context() as m:
        m.setattr(app.store,'save_preferences',fail)
        page.apply_theme()
        assert app.dialog is not None
    app.close_dialog()

def test_offline_assistant_thread_saves_reply_and_restores_controls(app):
    app.sign_in(app.store.register('offline@example.com','testpass123','patient','Offline Tester'))
    app.navigate('assistant'); page=app.current_page
    page.message_input.text='Tell me about meals'
    page.send()
    assert page.message_input.text==''
    for _ in range(30):
        pump(1)
        if not page.busy: break
    assert not page.busy
    assert not page.send_btn.disabled
    history=app.store.assistant_history(app.user['id'])
    assert [m['role'] for m in history]==['user','assistant']
    assert 'Offline information library' in history[-1]['text']
    page.clear(); assert app.dialog is not None
    app.close_dialog()
    assert len(app.store.assistant_history(app.user['id']))==2
