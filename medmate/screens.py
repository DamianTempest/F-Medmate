"""Patient and doctor workflows built from shared KivyMD components."""
from datetime import datetime,timedelta
from pathlib import Path
import json
import random
import threading
import sqlite3
import webbrowser
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDIcon
from kivymd.uix.selectioncontrol import MDSwitch
from .ui import Page,card,column,label,button,field,row,TEAL
from .store import ValidationError
from .health import TIPS,RESOURCES,meal_ideas,symptom_guidance,offline_answer
from .assistant import Assistant,AssistantError


def picker(values,text='Choose one'):
    return Spinner(text=text,values=values,size_hint_y=None,height=dp(48),background_normal='',
                   background_color=TEAL,color=(1,1,1,1),font_size=dp(15))


def readonly(text,height=260):
    return TextInput(text=text,readonly=True,multiline=True,size_hint_y=None,height=dp(height),
                     background_normal='',background_active='',background_color=(0,0,0,0),
                     foreground_color=(.12,.28,.25,1),font_size=dp(16),padding=[dp(10),dp(10)])


class Welcome(Page):
    route='welcome'; title='Medmate'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Your health.\nA little closer.','A simple place for your records, care conversations and everyday wellbeing.')
        hero=card('Welcome to Medmate','Choose your workspace to begin.')
        hero.add_widget(MDIcon(icon='heart-plus-outline',font_size=dp(64),theme_text_color='Custom',text_color=TEAL,
                               size_hint=(None,None),size=(dp(72),dp(72))))
        hero.add_widget(label('Care starts with connection','H5'))
        hero.add_widget(label('Keep your health details organised. Prepare for appointments. Explore Ghanaian meal ideas.',secondary=True))
        self.body.add_widget(hero)
        self.tiles([
            ('I am a patient','My records, appointments and care messages.','account-heart-outline',lambda:app.show_auth('patient')),
            ('I am a doctor','Authorised records, appointments and notes.','stethoscope',lambda:app.show_auth('doctor')),
        ])
        self.body.add_widget(label('LOCAL PROTOTYPE  •  Accounts connect on this device.\nOnline AI is optional. Doctor credentials are self-declared.','Body2',True))


class Auth(Page):
    route='auth'; title='Your account'
    def __init__(self,app):
        super().__init__(app)
        self.signup=app.auth_signup; self.role=app.auth_role
        self.intro(('Create your account' if self.signup else 'Welcome back'),self.role.title()+' workspace · Accounts saved on this device')
        form=card()
        specs=[]
        if self.signup: specs.append(('name','Full name',False))
        specs.extend([('email','Email address',False),('password','Password (at least 8 characters)',True)])
        if self.signup:
            specs.append(('confirm','Confirm password',True))
            if self.role=='doctor': specs.extend([('license','Self-declared license number',False),('specialty','Specialty',False)])
        for key,hint,pw in specs:
            f=field(hint,password=pw); self.fields[key]=f; form.add_widget(f)
        self.status=label('',secondary=True); form.add_widget(self.status)
        form.add_widget(button('Create account' if self.signup else 'Sign in',self.submit))
        form.add_widget(button('Already registered? Sign in' if self.signup else 'New here? Create an account',
                               lambda:app.show_auth(self.role,not self.signup),False))
        form.add_widget(button('Change workspace',lambda:app.navigate('welcome'),False))
        if self.role=='doctor': form.add_widget(label('This prototype does not verify a medical license. Use test records only.','Body2',True))
        self.body.add_widget(form)

    def submit(self):
        try:
            values={k:v.text for k,v in self.fields.items()}
            if self.signup:
                if values['password']!=values['confirm']: raise ValidationError('Passwords do not match.')
                user=self.app.store.register(values['email'],values['password'],self.role,values['name'],values.get('license',''),values.get('specialty',''))
            else: user=self.app.store.login(values['email'],values['password'],self.role)
            self.fields['password'].text=''
            if 'confirm' in self.fields: self.fields['confirm'].text=''
            self.app.sign_in(user)
        except (ValidationError,sqlite3.Error,OSError) as e:
            self.status.text=str(e) if isinstance(e,ValidationError) else 'Account data could not be opened or saved. Check folder access and retry.'


class Dashboard(Page):
    route='dashboard'; title='Your workspace'
    def __init__(self,app):
        super().__init__(app)
        parts=app.user['name'].split()
        name=parts[1] if len(parts)>1 and parts[0].lower().rstrip('.') in ('dr','doctor') else parts[0]
        self.intro('Hello, '+name+'.','Your '+app.user['role']+' workspace · '+datetime.now().strftime('%A, %d %B'))
        appointments=app.store.appointments(app.user['id'])
        active=[a for a in appointments if a['status'] in ('requested','accepted')]
        hero=card('A clearer view of your care',f'{len(active)} active appointment'+('s' if len(active)!=1 else ''))
        future=sorted([a for a in active if a['when_at']>datetime.now().isoformat(timespec='minutes')],key=lambda a:a['when_at'])
        if future:
            a=future[0]
            hero.add_widget(label('Next: '+a['when_at'].replace('T',' at ')+' · '+a['status'].title(),'Body1'))
            hero.add_widget(label(a['patient_name'] if app.user['role']=='doctor' else a['doctor_name'],secondary=True))
            hero.add_widget(button('View appointments',lambda:app.navigate('appointments'),False))
        else:
            hero.add_widget(label('Everything starts with a connection. Your saved visits will appear here.',secondary=True))
            hero.add_widget(button('View patients' if app.user['role']=='doctor' else 'Find a doctor on this device',lambda:app.navigate('patients' if app.user['role']=='doctor' else 'care')))
        self.body.add_widget(hero)
        if app.user['role']=='doctor':
            items=[('My patients','Open records shared with you.','account-group-outline','patients'),('Appointments','Review requests and manage visits.','calendar-month-outline','appointments'),('Messages','Continue a care conversation.','message-text-outline','messages'),('Research & news','Authoritative resources in your browser.','microscope','resources')]
        else:
            items=[('My care','Link a doctor and arrange a visit.','heart-outline','care'),('Health assistant','Offline information or optional online AI.','chat-processing-outline','assistant'),('Meal ideas','Ghanaian meals with ingredient lists.','food-apple-outline','meals'),('Symptom guidance','Prepare concerns for a clinician.','clipboard-pulse-outline','symptoms')]
        self.tiles([(a,b,c,lambda r=d:app.navigate(r)) for a,b,c,d in items])
        tip=card('A small step for today',random.choice(TIPS)); self.body.add_widget(tip)
        self.body.add_widget(row(button('My profile',lambda:app.navigate('profile'),False),button('Settings',lambda:app.navigate('settings'),False)))


class Profile(Page):
    route='profile'; title='My profile'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Your details, in one place.','Update your profile. It stays saved when you sign out.')
        data=app.store.profile(app.user['id'])
        form=card('Personal details')
        specs=[('name','Full name',False),('age','Age (optional)',False),('country','Country',False)]
        if app.user['role']=='doctor': specs.extend([('license_number','Self-declared license number',False),('specialty','Specialty',False)])
        else: specs.extend([('medical_history','Medical history',True),('medications','Current medications',True),('allergies','Allergies (comma-separated)',True),('activities','Activities and wellbeing notes',True)])
        for key,hint,multi in specs:
            f=field(hint,data.get(key,''),multi)
            if key=='age': f.input_filter='int'
            self.fields[key]=f; form.add_widget(f)
        form.add_widget(button('Save profile',self.save)); self.body.add_widget(form)
        self.body.add_widget(label('Only doctors you link in My care can open your patient record.','Body2',True) if app.user['role']=='patient' else label('License details are not verified by this prototype.','Body2',True))

    def save(self):
        def action():
            self.app.store.save_profile(self.app.user['id'],{k:v.text for k,v in self.fields.items()})
            self.app.user=self.app.store.user(self.app.user['id']); self.app.chrome()
        self.run(action,'Profile saved.')


class Care(Page):
    route='care'; title='My care'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Choose your care connection.','Doctor accounts on this device · Grant access before requesting a visit or sending messages.')
        self.body.add_widget(row(button('Appointments',lambda:app.navigate('appointments')),button('Messages',lambda:app.navigate('messages'),False)))
        self.search=field('Search by doctor name or specialty'); self.body.add_widget(self.search)
        self.list=column(); self.body.add_widget(self.list)
        self.search.bind(text=lambda *_:self.run(self.populate))
        self.populate()

    def populate(self):
        self.list.clear_widgets()
        doctors=self.app.store.doctors(); linked={d['id'] for d in self.app.store.linked_doctors(self.app.user['id'])}
        q=self.search.text.lower()
        doctors=[d for d in doctors if q in (d['name']+' '+d['specialty']).lower()]
        if not doctors: self.list.add_widget(card('No doctor accounts found','Create a doctor account from the welcome screen, then sign back in as a patient.'))
        for d in doctors:
            connected=d['id'] in linked
            box=card(d['name'],(d['specialty'] or 'Specialty not provided')+' · Self-declared credentials')
            if connected:
                box.add_widget(label('Access granted · Record and messaging enabled',secondary=True))
                box.add_widget(row(button('Message',lambda uid=d['id']:self.app.open_conversation(uid)),button('Remove access',lambda uid=d['id']:self.revoke(uid),False)))
            else: box.add_widget(button('Grant record access',lambda uid=d['id']:self.grant(uid)))
            self.list.add_widget(box)

    def grant(self,doctor):
        def action():
            self.app.store.link_doctor(self.app.user['id'],doctor)
            self.populate()
        self.run(action)

    def revoke(self,doctor):
        def remove():
            def action():
                self.app.store.unlink_doctor(self.app.user['id'],doctor); self.populate()
            self.run(action)
        self.app.confirm('Remove doctor access?','This doctor loses access to your record and future messages. Active appointments are cancelled. Existing messages remain in history.',remove,'Remove')


class Patients(Page):
    route='patients'; title='My patients'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Care, organised.','Only patients who granted your account access appear here.')
        self.search=field('Search patient name'); self.body.add_widget(self.search)
        self.list=column(); self.body.add_widget(self.list)
        self.search.bind(text=lambda *_:self.run(self.populate)); self.populate()

    def populate(self):
        self.list.clear_widgets()
        patients=[p for p in self.app.store.patients(self.app.user['id']) if self.search.text.lower() in p['name'].lower()]
        if not patients: self.list.add_widget(card('No patients to show','A patient must link your doctor account in My care.'))
        for p in patients:
            box=card(p['name'],'Record access granted on this device')
            box.add_widget(row(button('Open record',lambda uid=p['id']:self.app.open_patient(uid)),button('Message',lambda uid=p['id']:self.app.open_conversation(uid),False)))
            self.list.add_widget(box)


class PatientRecord(Page):
    route='patient_record'; title='Patient record'
    def __init__(self,app):
        super().__init__(app)
        self.record={}
        try:
            self.record=app.store.patient_record(app.user['id'],app.patient_id)
        except ValidationError as e:
            self.body.add_widget(card('Record unavailable',str(e))); return
        self.intro(self.record['name'],'Shared patient record · Read only')
        box=card('Health details')
        for k in ('age','country','medical_history','medications','allergies','activities'):
            box.add_widget(label(k.replace('_',' ').title(),'Subtitle2'))
            box.add_widget(label(self.record.get(k) or 'Not provided',secondary=True))
        self.body.add_widget(box)
        self.body.add_widget(button('Message patient',lambda:app.open_conversation(app.patient_id),False))
        notes=card('Your private notes','These notes are visible only to your doctor account.')
        self.note_input=field('Add a visit note',multiline=True); notes.add_widget(self.note_input)
        notes.add_widget(button('Save note',self.save_note)); self.body.add_widget(notes)
        self.notes_list=column(); self.body.add_widget(self.notes_list); self.populate_notes()

    def populate_notes(self):
        self.notes_list.clear_widgets()
        for n in self.app.store.notes(self.app.user['id'],self.app.patient_id): self.notes_list.add_widget(card(n['created'].replace('T',' '),n['text']))

    def save_note(self):
        def action():
            self.app.store.save_note(self.app.user['id'],self.app.patient_id,self.note_input.text)
            self.note_input.text=''; self.populate_notes()
        self.run(action,'Private note saved.')


class Appointments(Page):
    route='appointments'; title='Appointments'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Make space for your care.','Requests and confirmations are local to this device. They are not bookings with a real clinic.')
        self.doctor_id=None
        if app.user['role']=='patient':
            doctors=app.store.linked_doctors(app.user['id'])
            form=card('Request a visit','Date and time use this device’s local timezone.')
            if doctors:
                choices={f"{d['name']} · #{d['id']}":d['id'] for d in doctors}
                select=picker(tuple(choices),next(iter(choices)))
                self.doctor_id=choices[select.text]
                select.bind(text=lambda _,value:setattr(self,'doctor_id',choices[value])); form.add_widget(select)
                for key,hint,value,multi in [('date','Date (YYYY-MM-DD)',(datetime.now()+timedelta(days=1)).strftime('%Y-%m-%d'),False),('time','Time (HH:MM, 24-hour)','09:00',False),('reason','Reason for visit','',True)]:
                    f=field(hint,value,multi); self.fields[key]=f; form.add_widget(f)
                form.add_widget(button('Request appointment',self.request))
            else:
                form.add_widget(label('Link a doctor in My care first.',secondary=True)); form.add_widget(button('Open My care',lambda:app.navigate('care')))
            self.body.add_widget(form)
        self.filter=picker(('Active visits','All visits'),'Active visits'); self.filter.bind(text=lambda *_:self.run(self.populate))
        self.body.add_widget(self.filter)
        self.list=column(); self.body.add_widget(self.list); self.populate()

    def request(self):
        def action():
            if not self.doctor_id: raise ValidationError('Choose a doctor first.')
            at=self.fields['date'].text.strip()+'T'+self.fields['time'].text.strip()
            self.app.store.request_appointment(self.app.user['id'],self.doctor_id,at,self.fields['reason'].text)
            self.fields['reason'].text=''; self.populate()
        self.run(action,'Appointment requested. The doctor account can review it on this device.')

    def populate(self):
        self.list.clear_widgets()
        visits=self.app.store.appointments(self.app.user['id'])
        if self.filter.text=='Active visits': visits=[a for a in visits if a['status'] in ('requested','accepted')]
        if not visits: self.list.add_widget(card('No visits to show','Your appointment requests will appear here.'))
        for a in visits:
            other=a['doctor_name'] if self.app.user['role']=='patient' else a['patient_name']
            box=card(a['when_at'].replace('T',' at '),other+' · '+a['status'].title())
            box.add_widget(label(a['reason']))
            if a['status'] in ('requested','accepted'):
                controls=[]
                if self.app.user['role']=='doctor':
                    status='accepted' if a['status']=='requested' else 'completed'
                    controls.append(button('Accept' if status=='accepted' else 'Complete',lambda aid=a['id'],s=status:self.change_status(aid,s)))
                controls.append(button('Cancel visit',lambda aid=a['id']:self.cancel(aid),False))
                box.add_widget(row(*controls))
            self.list.add_widget(box)

    def change_status(self,aid,status):
        def action():
            self.app.store.update_appointment(self.app.user['id'],aid,status); self.populate()
        self.run(action)

    def cancel(self,aid): self.app.confirm('Cancel this visit?','The appointment will move to your history.',lambda:self.change_status(aid,'cancelled'),'Cancel visit')


class Messages(Page):
    route='messages'; title='Messages'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Continue the conversation.','Messages are exchanged between accounts on this device. No remote delivery or automatic doctor replies.')
        self.body.add_widget(button('Refresh conversations',lambda:self.run(self.populate),False))
        self.search=field('Search conversation'); self.body.add_widget(self.search)
        self.list=column(); self.body.add_widget(self.list)
        self.search.bind(text=lambda *_:self.run(self.populate)); self.populate()

    def populate(self):
        self.list.clear_widgets()
        contacts=[p for p in self.app.store.contacts(self.app.user['id']) if self.search.text.lower() in p['name'].lower()]
        if not contacts: self.list.add_widget(card('No conversations yet','Link a doctor in My care, or wait for a patient to grant your doctor account access.'))
        for p in contacts:
            history=self.app.store.messages(self.app.user['id'],p['id'])
            preview=history[-1]['text'][:160] if history else 'Start a conversation'
            box=card(p['name'],preview); box.add_widget(button('Open conversation',lambda uid=p['id']:self.app.open_conversation(uid),False)); self.list.add_widget(box)


class Conversation(Page):
    route='conversation'; title='Conversation'
    def __init__(self,app):
        super().__init__(app)
        # Chat uses the full remaining page; composer stays reachable.
        self.clear_widgets()
        layout=MDBoxLayout(orientation='vertical',padding=dp(18),spacing=dp(10)); self.add_widget(layout)
        other=app.store.user(app.other_id)
        layout.add_widget(label(other['name'],'H5'))
        layout.add_widget(label('Same-device conversation · Select text to copy','Caption',True))
        self.transcript=readonly('',300); self.transcript.size_hint_y=1
        self.transcript.foreground_color=(.83,.91,.87,1) if app.theme_cls.theme_style=='Dark' else (.12,.28,.25,1)
        layout.add_widget(self.transcript)
        self.message_input=field('Write a message'); layout.add_widget(self.message_input)
        self.message_input.bind(on_text_validate=lambda *_:self.send())
        layout.add_widget(row(button('Send message',self.send),button('Refresh',lambda:self.run(self.populate),False)))
        self.populate()
        self.refresh_event=Clock.schedule_interval(self.refresh,3)

    def refresh(self,_):
        try: self.populate()
        except (ValidationError,sqlite3.Error,OSError):
            self.refresh_event.cancel()
            self.app.notify('The conversation could not refresh. Check data folder access, then reopen it.')

    def populate(self):
        if not self.app.user: return
        text='\n\n'.join(('You' if m['sender']==self.app.user['id'] else self.app.store.user(m['sender'])['name'])+' · '+m['created'].replace('T',' ')+'\n'+m['text'] for m in self.app.store.messages(self.app.user['id'],self.app.other_id))
        if text!=self.transcript.text: self.transcript.text=text or 'No messages yet.'; self.transcript.cursor=(0,len(self.transcript._lines)-1)

    def send(self):
        def action():
            self.app.store.send_message(self.app.user['id'],self.app.other_id,self.message_input.text)
            self.message_input.text=''; self.populate()
        self.run(action)

    def dispose(self):
        if hasattr(self,'refresh_event'): self.refresh_event.cancel()


class HealthAssistant(Page):
    route='assistant'; title='Health assistant'
    def __init__(self,app):
        super().__init__(app)
        self.clear_widgets()
        request=(app.session_id,app.user['id'])
        self.busy=request in app.assistant_pending
        self.last_failed=app.assistant_failures.get(request)
        layout=MDBoxLayout(orientation='vertical',padding=dp(18),spacing=dp(10)); self.add_widget(layout)
        prefs=app.store.preferences(app.user['id']); self.online=prefs['online_ai']
        layout.add_widget(label('Ask, learn, prepare.','H5'))
        layout.add_widget(label('Online AI · OpenRouter' if self.online else 'Offline information library · Not AI','Body2',True))
        self.transcript=readonly('',300); self.transcript.size_hint_y=1
        self.transcript.foreground_color=(.83,.91,.87,1) if app.theme_cls.theme_style=='Dark' else (.12,.28,.25,1)
        layout.add_widget(self.transcript)
        self.status=label('General information; personal health concerns need a clinician.','Caption',True); layout.add_widget(self.status)
        self.message_input=field('Ask a general health question'); layout.add_widget(self.message_input)
        self.send_btn=button('Send',self.send)
        self.send_btn.disabled=self.busy
        self.retry_btn=button('Retry',self.retry,False); self.retry_btn.disabled=self.busy or not self.last_failed
        if self.busy: self.status.text='A response is still being prepared. You can browse other pages.'
        layout.add_widget(row(self.send_btn,self.retry_btn,button('Settings',lambda:app.navigate('settings'),False)))
        layout.add_widget(button('Clear saved conversation',self.clear,False)); self.populate()

    def populate(self):
        self.transcript.text='\n\n'.join(('You' if m['role']=='user' else 'Medmate')+'\n'+m['text'] for m in self.app.store.assistant_history(self.app.user['id'])) or 'Try asking about meals, sleep, or preparing for an appointment.'
        self.transcript.cursor=(0,len(self.transcript._lines)-1)

    def send(self):
        if self.busy: return
        message=self.message_input.text.strip()
        if not message: self.app.notify('Enter a question first.'); return
        if len(message)>4000: self.app.notify('Keep your question under 4000 characters.'); return
        self.last_failed=None; self.start(message,save_user=True)

    def retry(self):
        if self.last_failed and not self.busy: self.start(self.last_failed,save_user=False)

    def start(self,message,save_user):
        uid=self.app.user['id']; session=self.app.session_id
        request=(session,uid)
        if request in self.app.assistant_pending: return
        self.busy=True; self.send_btn.disabled=True; self.retry_btn.disabled=True
        try:
            history=self.app.store.assistant_history(uid)
            prefs=self.app.store.preferences(uid)
            profile=self.app.store.profile(uid) if prefs['share_ai'] else None
            if not save_user and history and history[-1]['role']=='user': history=history[:-1]
            if save_user: self.app.store.add_assistant_message(uid,'user',message)
            self.populate()
        except (ValidationError,sqlite3.Error,OSError):
            self.busy=False; self.send_btn.disabled=False
            self.status.text='Your message could not be saved. Check data folder access and try again.'
            return
        self.app.assistant_pending.add(request)
        self.app.assistant_failures.pop(request,None)
        self.message_input.text=''
        online=prefs['online_ai']
        self.status.text='Waiting for Online AI…' if online else 'Opening offline information…'
        def work():
            try:
                answer=Assistant().reply(message,history,profile) if online else offline_answer(message)
                error=None
            except (AssistantError,ValidationError) as e: answer=None; error=str(e)
            except Exception: answer=None; error='The assistant could not complete the request. Try again.'
            Clock.schedule_once(lambda _:self.finish_response(session,uid,answer,error,message))
        threading.Thread(target=work,daemon=True).start()

    def finish_response(self,session,uid,answer,error,message=''):
        if session!=self.app.session_id or not self.app.user or self.app.user['id']!=uid: return
        request=(session,uid)
        self.app.assistant_pending.discard(request)
        self.busy=False
        try:
            if answer: self.app.store.add_assistant_message(uid,'assistant',answer)
        except (ValidationError,sqlite3.Error,OSError):
            error='The response could not be saved. Check data folder access and retry.'
        if error: self.app.assistant_failures[request]=message
        else: self.app.assistant_failures.pop(request,None)
        page=self.app.current_page
        if not isinstance(page,HealthAssistant): return
        page.busy=False; page.send_btn.disabled=False
        if error:
            page.last_failed=message; page.retry_btn.disabled=False; page.status.text=error
        else:
            page.last_failed=None; page.retry_btn.disabled=True; page.status.text='Saved to your local conversation.'
        page.run(page.populate)

    def clear(self):
        if self.busy: self.app.notify('Wait for the current response before clearing the conversation.'); return
        def action():
            def save():
                self.app.store.clear_assistant_history(self.app.user['id'])
                self.app.assistant_failures.pop((self.app.session_id,self.app.user['id']),None)
                self.last_failed=None; self.retry_btn.disabled=True; self.populate()
            self.run(save)
        self.app.confirm('Clear this conversation?','Saved assistant messages for your account will be deleted.',action,'Clear')


class Meals(Page):
    route='meals'; title='Meal ideas'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Familiar food. Fresh ideas.','Ghanaian preparation ideas, with ingredients you can review.')
        prefs=app.store.preferences(app.user['id']); profile=app.store.profile(app.user['id'])
        form=card('Your preferences','These are meal ideas, not a therapeutic diet plan. Check labels, preparation and cross-contact for allergies.')
        self.preference=picker(('Omnivore','Vegetarian','Vegan','Pescatarian'),prefs['diet']); form.add_widget(self.preference)
        self.allergies=field('Allergies (comma-separated)',profile['allergies']); form.add_widget(self.allergies)
        form.add_widget(label('Recognised: peanuts/groundnuts, nuts, fish, eggs, milk/dairy, soy, wheat/gluten, shellfish, sesame.','Caption',True))
        form.add_widget(button('Find meal ideas',self.suggest)); self.body.add_widget(form)
        self.list=column(); self.body.add_widget(self.list)

    def suggest(self):
        self.list.clear_widgets()
        def action():
            meals=meal_ideas(self.preference.text,self.allergies.text)
            self.app.store.save_preferences(self.app.user['id'],{'diet':self.preference.text})
            self.list.clear_widgets()
            if not meals: self.list.add_widget(card('No matching ideas','Ask a dietitian to review alternatives.'))
            for m in meals:
                box=card(m['name'],m['diet']+' preparation')
                box.add_widget(label('Ingredients: '+', '.join(m['ingredients'])))
                box.add_widget(label(m['method'],secondary=True))
                box.add_widget(label('Declared allergens: '+(', '.join(m['allergens']) or 'None in this ingredient list — check actual ingredients and preparation.'),'Caption',True))
                self.list.add_widget(box)
        self.run(action)


class Symptoms(Page):
    route='symptoms'; title='Symptom guidance'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Prepare for the right conversation.','Record what you are experiencing and organise what to tell a clinician.')
        form=card('Your concerns','This tool does not diagnose or prescribe. For life-threatening symptoms, seek emergency care now.')
        self.input=field('Describe symptoms and when they started',multiline=True); form.add_widget(self.input)
        form.add_widget(button('Show next-step information',self.show_guidance)); self.body.add_widget(form)
        self.result=card(); self.body.add_widget(self.result)

    def show_guidance(self):
        def action():
            text=symptom_guidance(self.input.text)
            self.result.clear_widgets(); self.result.add_widget(label(text))
            self.result.add_widget(button('Arrange a local visit',lambda:self.app.navigate('appointments'),False))
            self.result.add_widget(button('Open NHS source',lambda:webbrowser.open('https://www.nhs.uk/symptoms/chest-pain/'),False))
        self.run(action)


class Resources(Page):
    route='resources'; title='Resources'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Read from trusted sources.','Research, health information and news · Links open in your browser and require internet.')
        self.tiles([(title,desc,icon,lambda url=url:webbrowser.open(url)) for title,desc,url,icon in RESOURCES])
        self.body.add_widget(label('Medmate does not supply a live news feed. Publication dates and content belong to each source.','Body2',True))


class Settings(Page):
    route='settings'; title='Settings'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Make Medmate yours.','Appearance, assistant preferences and local data.')
        prefs=app.store.preferences(app.user['id'])
        look=card('Appearance')
        self.theme=picker(('Light','Dark'),prefs['theme']); look.add_widget(self.theme)
        look.add_widget(button('Apply theme',self.apply_theme)); self.body.add_widget(look)
        ai=card('Optional Online AI','Requires your own OpenRouter key and model. API usage may have a cost.')
        ai.add_widget(label('Configuration: '+('Ready' if Assistant().configured else 'Not configured · see README and .env.example'),secondary=True))
        self.online=MDSwitch(active=prefs['online_ai']); self.share=MDSwitch(active=prefs['share_ai'])
        ai.add_widget(row(label('Use Online AI'),self.online))
        ai.add_widget(row(label('Include health profile with AI requests'),self.share))
        ai.add_widget(label('Online requests send your question and recent assistant conversation to OpenRouter and its model provider. Profile sharing also includes age, history, medications and allergies. Names and contact details are excluded from automatic profile context.','Caption',True))
        ai.add_widget(button('Save assistant preferences',self.save_ai)); self.body.add_widget(ai)
        data=card('Local data','Use test data. This prototype stores health records locally without database encryption. Protect your device and backups.')
        data.add_widget(label('Data folder: '+str(app.store.path.parent),'Caption',True))
        if app.user['role']=='patient':
            self.legacy_path=field('Legacy user_profile.json path (optional)'); data.add_widget(self.legacy_path)
            data.add_widget(button('Import legacy profile',self.import_legacy,False))
        data.add_widget(button('About Medmate',lambda:app.navigate('about'),False)); self.body.add_widget(data)

    def apply_theme(self):
        def action():
            self.app.store.save_preferences(self.app.user['id'],{'theme':self.theme.text})
            self.app.theme_cls.theme_style=self.theme.text
            self.app.render('settings')
        self.run(action)

    def save_ai(self):
        if self.online.active and not Assistant().configured:
            self.app.notify('Add your own OPENROUTER_API_KEY and OPENROUTER_MODEL to .env, restart Medmate, then enable Online AI.'); return
        self.run(lambda:self.app.store.save_preferences(self.app.user['id'],{'online_ai':bool(self.online.active),'share_ai':bool(self.share.active)}),'Assistant preferences saved.')

    def import_legacy(self):
        def action():
            path=Path(self.legacy_path.text.strip()).expanduser()
            if not self.legacy_path.text.strip(): raise ValidationError('Enter the path to your old user_profile.json file.')
            if not path.is_file() or path.stat().st_size>100000: raise ValidationError('Choose a JSON profile file smaller than 100 KB.')
            try: data=json.loads(path.read_text(encoding='utf-8'))
            except (ValueError,UnicodeError): raise ValidationError('This file is not a valid JSON profile.')
            if not isinstance(data,dict): raise ValidationError('The JSON profile must contain an object.')
            cleaned={k:str(data[k]) for k in ('name','age','country','medical_history','medications','allergies','activities') if k in data and data[k] is not None}
            if not cleaned: raise ValidationError('No supported profile fields were found.')
            self.app.confirm('Import into your profile?','This will replace the listed fields in your current patient profile. Import only your own data.',
                lambda:self.run(lambda:self.app.store.save_profile(self.app.user['id'],cleaned),'Legacy profile imported.'),'Import')
        self.run(action)


class About(Page):
    route='about'; title='About Medmate'
    def __init__(self,app):
        super().__init__(app)
        self.intro('Medmate','Version 1.0.0 · Local prototype')
        self.body.add_widget(card('Care, close to you','A patient–doctor health companion with saved profiles, appointments, conversations and everyday information.'))
        self.body.add_widget(card('What works locally','Accounts, records, access permissions, private doctor notes, messages, appointments, meal ideas and the offline information library.'))
        self.body.add_widget(card('What requires internet','External research/news links and optional configured Online AI. Accounts and messages do not sync across devices.'))
        self.body.add_widget(card('Prototype boundaries','Doctor licenses are self-declared. This is not an emergency service or a clinically validated diagnostic tool. Health data is local and unencrypted. Use test records.'))

PAGES={'welcome':Welcome,'auth':Auth,'dashboard':Dashboard,'profile':Profile,'care':Care,'patients':Patients,
       'patient_record':PatientRecord,'appointments':Appointments,'messages':Messages,'conversation':Conversation,
       'assistant':HealthAssistant,'meals':Meals,'symptoms':Symptoms,'resources':Resources,'settings':Settings,'about':About}
