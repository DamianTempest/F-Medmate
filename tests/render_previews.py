"""Render actual KivyMD screens with disposable synthetic data."""
import os
os.environ.setdefault('KIVY_NO_ARGS','1')
os.environ.setdefault('KIVY_NO_CONSOLELOG','1')
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime,timedelta
from main import MedMateApp
from kivy.clock import Clock
from kivy.base import EventLoop
from kivy.core.window import Window

def pump(n=24):
    for _ in range(n): Clock.tick(); EventLoop.idle()

with TemporaryDirectory() as data:
    app=MedMateApp(data_dir=data); app._run_prepare(); pump()
    output=Path('docs/previews').resolve(); output.mkdir(exist_ok=True,parents=True)
    def capture(name):
        pump(); app.root.export_to_png(str(output/(name+'.png')))
        print('RENDERED',name,flush=True)
    capture('welcome-desktop')
    p=app.store.register('patient@example.com','demo-pass123','patient','Ama Mensah')
    d=app.store.register('doctor@example.com','demo-pass123','doctor','Dr. Kofi Owusu','DEMO-001','General practice')
    app.store.save_profile(p['id'],{'age':'24','country':'Ghana','allergies':'peanuts','medical_history':'Demonstration record only','medications':'None recorded'})
    app.store.link_doctor(p['id'],d['id'])
    when=(datetime.now()+timedelta(days=2)).replace(hour=9,minute=30,second=0,microsecond=0).isoformat(timespec='minutes')
    aid=app.store.request_appointment(p['id'],d['id'],when,'Routine wellbeing conversation')
    app.store.update_appointment(d['id'],aid,'accepted')
    app.store.send_message(p['id'],d['id'],'Hello doctor. I have written down my questions for our visit.')
    app.store.send_message(d['id'],p['id'],'Thank you, Ama. Bring your current medicine list as well.')
    app.sign_in(p); capture('patient-dashboard-desktop')
    app.navigate('profile'); capture('patient-profile-desktop')
    app.open_conversation(d['id']); capture('patient-messages-desktop')
    app.navigate('meals'); app.current_page.preference.text='Vegan'; app.current_page.suggest(); capture('meal-ideas-desktop')
    Window.size=(390,844); pump()
    app.navigate('dashboard'); capture('patient-dashboard-phone')
    app.navigate('appointments'); capture('appointments-phone')
    app.navigate('profile'); capture('profile-phone')
    app.navigate('assistant'); capture('assistant-phone')
    app.logout(); app.sign_in(d); capture('doctor-dashboard-phone')
    Window.size=(1100,780); pump(); app.navigate('dashboard'); capture('doctor-dashboard-desktop')
    app.open_patient(p['id']); capture('doctor-record-desktop')
    app.navigate('settings'); app.current_page.theme.text='Dark'; app.current_page.apply_theme(); app.navigate('dashboard'); capture('doctor-dashboard-dark')
    app.stop()
