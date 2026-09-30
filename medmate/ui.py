"""Shared Material widgets and responsive page scaffolding."""
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.gridlayout import MDGridLayout
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp

TEAL=get_color_from_hex('#176B61')
INK=get_color_from_hex('#163D39')
MUTED=get_color_from_hex('#657A75')
BG=get_color_from_hex('#F2F5F1')

def is_dark():
    app=MDApp.get_running_app()
    return bool(app and app.theme_cls.theme_style=='Dark')

def accent():
    return get_color_from_hex('#8ED8C7') if is_dark() else TEAL


def label(text,style='Body1',secondary=False):
    widget=MDLabel(text=text,font_style=style,theme_text_color='Secondary' if secondary else 'Primary',
                   size_hint_y=None,halign='left',valign='middle')
    widget.bind(width=lambda w,v:setattr(w,'text_size',(v,None)),texture_size=lambda w,v:setattr(w,'height',v[1]+dp(4)))
    return widget


def column(spacing=12):
    box=MDBoxLayout(orientation='vertical',spacing=dp(spacing),size_hint_y=None)
    box.bind(minimum_height=box.setter('height'))
    return box


def card(title=None,subtitle=None):
    box=MDCard(orientation='vertical',size_hint_y=None,padding=dp(20),spacing=dp(10),
               radius=[dp(18)],elevation=0,line_color=(.5,.6,.55,.18))
    box.bind(minimum_height=box.setter('height'))
    if title: box.add_widget(label(title,'H6'))
    if subtitle: box.add_widget(label(subtitle,secondary=True))
    return box


def button(text,callback,primary=True,icon=None):
    cls=MDRaisedButton if primary else MDFlatButton
    b=cls(text=text,size_hint_y=None,height=dp(46),font_size=dp(14))
    if primary: b.md_bg_color=TEAL
    else: b.theme_text_color='Custom'; b.text_color=accent()
    b.bind(on_release=lambda *_:callback())
    return b


def field(hint,text='',multiline=False,password=False):
    f=MDTextField(hint_text=hint,text=str(text),mode='rectangle',multiline=multiline,password=password,
                  size_hint_y=None,height=dp(110 if multiline else 64),max_height=dp(160),
                  helper_text_mode='on_error',font_size=dp(16))
    f.text_color_normal=f.text_color_focus=(.9,.95,.92,1) if is_dark() else INK
    f.hint_text_color_normal=(.72,.78,.75,1) if is_dark() else MUTED
    f.hint_text_color_focus=accent()
    return f


def row(*widgets):
    box=MDBoxLayout(spacing=dp(8),size_hint_y=None,height=dp(48))
    for w in widgets: box.add_widget(w)
    return box


class ActionCard(MDCard):
    def __init__(self,title,description,icon,callback,**kwargs):
        super().__init__(orientation='vertical',padding=dp(18),spacing=dp(7),size_hint_y=None,
                         height=dp(170),radius=[dp(18)],elevation=0,ripple_behavior=True,
                         line_color=(.5,.6,.55,.18),**kwargs)
        self.add_widget(MDIcon(icon=icon,theme_text_color='Custom',text_color=accent(),size_hint=(None,None),size=(dp(32),dp(32)),font_size=dp(28)))
        self.add_widget(label(title,'H6'))
        self.add_widget(label(description,'Body2',True))
        self.bind(on_release=lambda *_:callback())


class Page(MDBoxLayout):
    route=''
    title=''
    def __init__(self,app,**kwargs):
        super().__init__(orientation='vertical',**kwargs)
        self.app=app
        scroll=ScrollView(do_scroll_x=False,bar_width=dp(3))
        self.body=column(16)
        self.body.padding=[dp(24),dp(20),dp(24),dp(30)]
        scroll.add_widget(self.body)
        self.add_widget(scroll)
        self.status=label('',secondary=True)
        self.fields={}

    def intro(self,title,subtitle):
        self.body.add_widget(label(title,'H4'))
        self.body.add_widget(label(subtitle,secondary=True))

    def tiles(self,items):
        grid=MDGridLayout(cols=2 if self.app.content_width>=650 else 1,spacing=dp(14),size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        self.bind(width=lambda *_:setattr(grid,'cols',2 if self.width>=650 else 1))
        for title,description,icon,callback in items: grid.add_widget(ActionCard(title,description,icon,callback))
        self.body.add_widget(grid)
        return grid

    def run(self,action,success=None):
        from .store import ValidationError
        import sqlite3
        try:
            result=action()
            if success: self.app.notify(success)
            return result
        except (ValidationError,sqlite3.Error,OSError) as e:
            message=str(e) if isinstance(e,ValidationError) else 'The data could not be saved. Check folder access and try again.'
            self.app.notify(message)
            return None

    def dispose(self):
        pass
