"""Run with python main.py. Core features need no server or AI credentials."""
from pathlib import Path
import os
import sqlite3
os.environ.setdefault('KIVY_NO_ARGS','1')
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / '.env')
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from medmate.store import Store
from medmate.ui import label, button, TEAL, BG, column, accent

class MedMateApp(MDApp):
    def __init__(self,data_dir=None,**kwargs):
        super().__init__(**kwargs)
        self._data_dir=data_dir
        self.user=None
        self.session_id=0
        self.assistant_pending=set()
        self.assistant_failures={}
        self.route='welcome'
        self.history=[]
        self.dialog=None
        self.other_id=None
        self.patient_id=None
        self.current_page=None
        self.title='Medmate'

    def build(self):
        self.theme_cls.primary_palette='Teal'
        self.theme_cls.primary_hue='700'
        self.theme_cls.theme_style='Light'
        self.theme_cls.material_style='M3'
        if platform not in ('android','ios'): Window.size=(1100,780)
        Window.minimum_width=360; Window.minimum_height=600
        Window.softinput_mode='below_target'
        self.store=Store(Path(self._data_dir or os.getenv('MEDMATE_DATA_DIR') or self.user_data_dir)/'medmate.db')
        self.root_layout=MDBoxLayout(orientation='horizontal')
        self.sidebar=MDBoxLayout(orientation='vertical',size_hint_x=None,width=0,padding=dp(16),spacing=dp(10),md_bg_color=TEAL)
        self.root_layout.add_widget(self.sidebar)
        self.content=MDBoxLayout(orientation='vertical')
        self.toolbar=MDTopAppBar(title='Medmate',elevation=0,md_bg_color=BG,specific_text_color=TEAL)
        self.content.add_widget(self.toolbar)
        self.manager=ScreenManager(transition=NoTransition())
        self.content.add_widget(self.manager)
        self.bottom=MDBoxLayout(size_hint_y=None,height=0,spacing=dp(2),padding=[dp(6),0])
        self.content.add_widget(self.bottom)
        self.root_layout.add_widget(self.content)
        Window.bind(on_keyboard=self.on_key,size=self.resize)
        self.render('welcome')
        return self.root_layout

    @property
    def content_width(self): return Window.width-(dp(224) if Window.width>=dp(850) and self.user else 0)

    def resize(self,*_):
        wide=Window.width>=dp(850) and self.user is not None
        self.sidebar.width=dp(224) if wide else 0
        self.sidebar.opacity=1 if wide else 0
        self.sidebar.disabled=not wide
        self.bottom.height=dp(68) if self.user and not wide else 0
        self.bottom.opacity=1 if self.user and not wide else 0
        self.bottom.disabled=not (self.user and not wide)

    def nav_items(self):
        if not self.user: return []
        if self.user['role']=='doctor': return [('dashboard','Home','view-dashboard-outline'),('patients','Patients','account-group-outline'),('appointments','Visits','calendar-month-outline'),('messages','Messages','message-outline')]
        return [('dashboard','Home','view-dashboard-outline'),('care','My care','heart-outline'),('messages','Messages','message-outline'),('profile','Profile','account-outline')]

    def chrome(self):
        self.sidebar.clear_widgets(); self.bottom.clear_widgets()
        self.sidebar.add_widget(label('MEDMATE','H5'))
        self.sidebar.children[0].theme_text_color='Custom'; self.sidebar.children[0].text_color=(1,1,1,1)
        tagline=label('CARE, CLOSE TO YOU','Caption'); tagline.theme_text_color='Custom'; tagline.text_color=(.73,.9,.84,1)
        self.sidebar.add_widget(tagline)
        if self.user:
            who=label(self.user['name']+'\n'+self.user['role'].title()+' workspace','Body2')
            who.theme_text_color='Custom'; who.text_color=(1,1,1,1)
            self.sidebar.add_widget(who)
        for route,text,icon in self.nav_items():
            b=MDFlatButton(text=text,size_hint_x=1,height=dp(48),theme_text_color='Custom',text_color=(1,1,1,1),
                           md_bg_color=(1,1,1,.14) if self.route==route else (1,1,1,0))
            b.bind(on_release=lambda _,r=route:self.navigate(r))
            self.sidebar.add_widget(b)
            group=MDBoxLayout(orientation='vertical')
            ib=MDIconButton(icon=icon,pos_hint={'center_x':.5},theme_text_color='Custom',text_color=accent())
            ib.bind(on_release=lambda _,r=route:self.navigate(r))
            group.add_widget(ib)
            cap=label(text,'Caption'); cap.halign='center'; cap.height=dp(18)
            group.add_widget(cap); self.bottom.add_widget(group)
        if self.user:
            for route,text in [('resources','Resources'),('settings','Settings')]:
                b=MDFlatButton(text=text,size_hint_x=1,theme_text_color='Custom',text_color=(1,1,1,1))
                b.bind(on_release=lambda _,r=route:self.navigate(r)); self.sidebar.add_widget(b)
            self.sidebar.add_widget(MDBoxLayout())
            self.sidebar.add_widget(label('LOCAL PROTOTYPE','Caption'))
            self.sidebar.children[0].theme_text_color='Custom'; self.sidebar.children[0].text_color=(.73,.9,.84,1)
        self.toolbar.left_action_items=[['arrow-left',lambda *_:self.back()]] if self.route not in ('welcome','dashboard') else []
        self.toolbar.right_action_items=[['cog-outline',lambda *_:self.navigate('settings')],['logout',lambda *_:self.confirm_logout()]] if self.user else []
        self.toolbar.title=self.current_page.title or 'Medmate'
        dark=self.theme_cls.theme_style=='Dark'
        bg=(.075,.115,.11,1) if dark else BG
        self.root_layout.md_bg_color=bg; self.toolbar.md_bg_color=bg
        self.toolbar.specific_text_color=(.75,.92,.86,1) if dark else TEAL
        self.resize()

    def render(self,route):
        from medmate.screens import PAGES
        from medmate.store import ValidationError
        try:
            page=PAGES[route](self)
        except (ValidationError,sqlite3.Error,OSError) as e:
            if self.current_page:
                self.notify(str(e) if isinstance(e,ValidationError) else 'This page could not load its saved data. Check folder access and try again.')
                return
            raise
        if self.current_page: self.current_page.dispose()
        self.manager.clear_widgets()
        self.route=route
        self.current_page=page
        screen=Screen(name=route); screen.add_widget(self.current_page)
        self.manager.add_widget(screen); self.manager.current=route
        self.chrome()

    def navigate(self,route,remember=True):
        from medmate.screens import PAGES
        if route not in PAGES: self.notify('This page is unavailable.'); return
        if not self.user and route not in ('welcome','auth'): return
        if self.user:
            doctor_only={'patients','patient_record'}
            patient_only={'care','meals','symptoms'}
            if (route in doctor_only and self.user['role']!='doctor') or (route in patient_only and self.user['role']!='patient'):
                self.notify('This page is unavailable in your mode.'); return
        if remember and route!=self.route: self.history.append(self.route)
        self.render(route)

    def show_auth(self,role,signup=False):
        self.auth_role=role; self.auth_signup=signup
        self.navigate('auth')

    def sign_in(self,user):
        theme=self.store.preferences(user['id'])['theme']
        self.session_id+=1; self.user=user; self.history=[]
        self.assistant_pending.clear(); self.assistant_failures.clear()
        self.theme_cls.theme_style=theme
        self.render('dashboard')

    def logout(self):
        self.session_id+=1
        self.assistant_pending.clear(); self.assistant_failures.clear()
        if self.dialog: self.dialog.dismiss(); self.dialog=None
        self.user=None; self.history=[]; self.other_id=None; self.patient_id=None
        self.theme_cls.theme_style='Light'
        self.render('welcome')

    def confirm_logout(self): self.confirm('Sign out?','Your records remain saved on this device.',self.logout,'Sign out')

    def back(self):
        if self.dialog:
            self.dialog.dismiss(); self.dialog=None; return
        if self.history:
            self.render(self.history.pop())
        elif self.user and self.route!='dashboard': self.render('dashboard')
        elif self.user: self.confirm_logout()
        elif self.route!='welcome': self.render('welcome')

    def on_key(self,window,key,*_):
        if key==27: self.back(); return True
        return False

    def notify(self,text):
        if self.dialog: self.dialog.dismiss()
        self.dialog=MDDialog(title='Medmate',text=text,buttons=[button('OK',self.close_dialog,False)])
        self.dialog.bind(on_dismiss=lambda *_:setattr(self,'dialog',None))
        self.dialog.open()

    def close_dialog(self):
        if self.dialog: self.dialog.dismiss()

    def confirm(self,title,text,action,action_label='Confirm'):
        if self.dialog: self.dialog.dismiss()
        def proceed():
            self.close_dialog(); action()
        self.dialog=MDDialog(title=title,text=text,buttons=[button('Cancel',self.close_dialog,False),button(action_label,proceed)])
        self.dialog.bind(on_dismiss=lambda *_:setattr(self,'dialog',None)); self.dialog.open()

    def open_conversation(self,other):
        self.other_id=other; self.navigate('conversation')

    def open_patient(self,patient):
        self.patient_id=patient; self.navigate('patient_record')

    def on_stop(self):
        if self.current_page: self.current_page.dispose()
        Window.unbind(on_keyboard=self.on_key,size=self.resize)

if __name__=='__main__':
    MedMateApp().run()
