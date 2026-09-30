"""SQLite persistence and access rules for the same-device prototype."""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import hashlib
import hmac
import json
import re
import secrets
import sqlite3

class ValidationError(ValueError):
    """A user-facing validation or permission failure."""

PROFILE_FIELDS = ('name','age','country','medical_history','medications','allergies','activities','specialty','license_number')
DEFAULT_PREFS = {'theme':'Light','diet':'Omnivore','share_ai':False,'online_ai':False}

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL, salt TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('patient','doctor')),
                name TEXT NOT NULL, profile TEXT NOT NULL, preferences TEXT NOT NULL DEFAULT '{}');
            CREATE TABLE IF NOT EXISTS links (
                patient INTEGER REFERENCES users(id), doctor INTEGER REFERENCES users(id),
                PRIMARY KEY(patient,doctor));
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY, sender INTEGER REFERENCES users(id),
                recipient INTEGER REFERENCES users(id), text TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY, patient INTEGER REFERENCES users(id), doctor INTEGER REFERENCES users(id),
                when_at TEXT NOT NULL, reason TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'requested');
            CREATE UNIQUE INDEX IF NOT EXISTS active_doctor_slot ON appointments(doctor,when_at)
                WHERE status IN ('requested','accepted');
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY, doctor INTEGER REFERENCES users(id), patient INTEGER REFERENCES users(id),
                text TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS assistant_messages (
                id INTEGER PRIMARY KEY, uid INTEGER REFERENCES users(id), role TEXT NOT NULL,
                text TEXT NOT NULL, created TEXT NOT NULL);
            ''')

    @contextmanager
    def connection(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

    @staticmethod
    def _hash(password, salt):
        return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 260000).hex()

    @staticmethod
    def _text(value, label, limit=4000, required=False):
        if not isinstance(value,str): raise ValidationError(f'{label} must be text.')
        value=value.strip()
        if required and not value: raise ValidationError(f'Enter {label.lower()}.')
        if len(value)>limit: raise ValidationError(f'{label} is too long (maximum {limit} characters).')
        return value

    def register(self,email,password,role,name,license_number='',specialty=''):
        email=self._text(email,'Email',254,True).lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email): raise ValidationError('Enter a valid email address.')
        if role not in ('patient','doctor'): raise ValidationError('Choose Patient or Doctor.')
        if not isinstance(password,str) or not 8<=len(password)<=128: raise ValidationError('Use a password with 8 to 128 characters.')
        name=self._text(name,'Name',100,True)
        license_number=self._text(license_number,'License number',100,role=='doctor')
        specialty=self._text(specialty,'Specialty',100)
        profile={k:'' for k in PROFILE_FIELDS}
        profile.update(name=name,country='Ghana',license_number=license_number,specialty=specialty)
        salt=secrets.token_hex(16)
        with self.connection() as c:
            try:
                cur=c.execute('INSERT INTO users(email,password_hash,salt,role,name,profile) VALUES (?,?,?,?,?,?)',
                              (email,self._hash(password,salt),salt,role,name,json.dumps(profile)))
            except sqlite3.IntegrityError as e: raise ValidationError('An account with this email already exists.') from e
            uid=cur.lastrowid
        return self.user(uid)

    def login(self,email,password,role):
        with self.connection() as c:
            row=c.execute('SELECT * FROM users WHERE email=?',(str(email).strip().lower(),)).fetchone()
        # Equal work for absent accounts; never reveal whether an email exists.
        salt=row['salt'] if row else '0'*32
        digest=self._hash(str(password),salt)
        if not row or not hmac.compare_digest(digest,row['password_hash']) or row['role']!=role:
            raise ValidationError('Email, password, or selected mode is incorrect.')
        return self.user(row['id'])

    def user(self,uid):
        with self.connection() as c:
            r=c.execute('SELECT id,email,role,name FROM users WHERE id=?',(uid,)).fetchone()
        if not r: raise ValidationError('Account was not found. Sign in again.')
        return dict(r)

    def profile(self,uid):
        with self.connection() as c:
            row=c.execute('SELECT profile FROM users WHERE id=?',(uid,)).fetchone()
        if not row: raise ValidationError('Account was not found.')
        return json.loads(row['profile'])

    def save_profile(self,uid,data):
        user=self.user(uid)
        current=self.profile(uid)
        for k,v in data.items():
            if k in PROFILE_FIELDS: current[k]=self._text(v,k.replace('_',' ').title(),100 if k in ('name','age','country','license_number','specialty') else 4000)
        if not current['name']: raise ValidationError('Enter your name.')
        age=current['age']
        if age and (not age.isdigit() or not 1<=int(age)<=120): raise ValidationError('Age must be a whole number from 1 to 120, or left blank.')
        if user['role']=='doctor' and not current['license_number']: raise ValidationError('Enter your self-declared license number.')
        with self.connection() as c:
            c.execute('UPDATE users SET name=?,profile=? WHERE id=?',(current['name'],json.dumps(current),uid))

    def preferences(self,uid):
        self.user(uid)
        with self.connection() as c: r=c.execute('SELECT preferences FROM users WHERE id=?',(uid,)).fetchone()
        return {**DEFAULT_PREFS,**json.loads(r['preferences'])}

    def save_preferences(self,uid,data):
        prefs=self.preferences(uid)
        for key,value in data.items():
            if key=='theme' and value not in ('Light','Dark'): raise ValidationError('Choose Light or Dark theme.')
            if key=='diet' and value not in ('Omnivore','Vegetarian','Vegan','Pescatarian'): raise ValidationError('Choose a listed dietary preference.')
            if key in ('share_ai','online_ai') and type(value) is not bool: raise ValidationError('Preference must be on or off.')
            if key in DEFAULT_PREFS: prefs[key]=value
        with self.connection() as c: c.execute('UPDATE users SET preferences=? WHERE id=?',(json.dumps(prefs),uid))

    def doctors(self):
        with self.connection() as c: rows=c.execute("SELECT id,name,profile FROM users WHERE role='doctor' ORDER BY name").fetchall()
        return [{'id':r['id'],'name':r['name'],'specialty':json.loads(r['profile'])['specialty']} for r in rows]

    def linked_doctors(self,patient):
        self._role(patient,'patient')
        with self.connection() as c: rows=c.execute('SELECT u.id,u.name FROM links l JOIN users u ON u.id=l.doctor WHERE l.patient=? ORDER BY u.name',(patient,)).fetchall()
        return [dict(r) for r in rows]

    def _role(self,uid,role):
        if self.user(uid)['role']!=role: raise ValidationError('This action is unavailable in your mode.')

    def _linked(self,c,patient,doctor):
        if not c.execute('SELECT 1 FROM links WHERE patient=? AND doctor=?',(patient,doctor)).fetchone():
            raise ValidationError('The patient must grant this doctor access first.')

    def link_doctor(self,patient,doctor):
        self._role(patient,'patient'); self._role(doctor,'doctor')
        with self.connection() as c: c.execute('INSERT OR IGNORE INTO links VALUES (?,?)',(patient,doctor))

    def unlink_doctor(self,patient,doctor):
        self._role(patient,'patient')
        with self.connection() as c:
            c.execute('DELETE FROM links WHERE patient=? AND doctor=?',(patient,doctor))
            c.execute("UPDATE appointments SET status='cancelled' WHERE patient=? AND doctor=? AND status IN ('requested','accepted')",(patient,doctor))

    def patients(self,doctor):
        self._role(doctor,'doctor')
        with self.connection() as c: rows=c.execute('SELECT u.id,u.name FROM links l JOIN users u ON u.id=l.patient WHERE l.doctor=? ORDER BY u.name',(doctor,)).fetchall()
        return [dict(r) for r in rows]

    def patient_record(self,doctor,patient):
        self._role(doctor,'doctor')
        with self.connection() as c:
            self._linked(c,patient,doctor)
            row=c.execute('SELECT profile FROM users WHERE id=?',(patient,)).fetchone()
        return json.loads(row['profile'])

    def _pair(self,sender,recipient):
        a=self.user(sender); b=self.user(recipient)
        if a['role']==b['role']: raise ValidationError('Choose a patient–doctor conversation.')
        return (sender,recipient) if a['role']=='patient' else (recipient,sender)

    def send_message(self,sender,recipient,text):
        text=self._text(text,'Message',4000,True)
        patient,doctor=self._pair(sender,recipient)
        with self.connection() as c:
            self._linked(c,patient,doctor)
            c.execute('INSERT INTO messages(sender,recipient,text,created) VALUES (?,?,?,?)',
                      (sender,recipient,text,datetime.now().isoformat(timespec='seconds')))

    def messages(self,uid,other):
        self.user(uid); self.user(other)
        with self.connection() as c:
            rows=c.execute('SELECT * FROM messages WHERE (sender=? AND recipient=?) OR (sender=? AND recipient=?) ORDER BY id',(uid,other,other,uid)).fetchall()
        return [dict(r) for r in rows]

    def contacts(self,uid):
        user=self.user(uid)
        linked=self.linked_doctors(uid) if user['role']=='patient' else self.patients(uid)
        with self.connection() as c:
            rows=c.execute('''SELECT DISTINCT u.id,u.name FROM users u JOIN messages m
                ON u.id=CASE WHEN m.sender=? THEN m.recipient ELSE m.sender END
                WHERE m.sender=? OR m.recipient=? ORDER BY u.name''',(uid,uid,uid)).fetchall()
        return sorted({r['id']:dict(r) for r in [*rows,*linked]}.values(),key=lambda x:x['name'].lower())

    def request_appointment(self,patient,doctor,when,reason):
        self._role(patient,'patient'); self._role(doctor,'doctor')
        reason=self._text(reason,'Reason for visit',1000,True)
        try: at=datetime.fromisoformat(when)
        except (ValueError,TypeError): raise ValidationError('Use date YYYY-MM-DD and time HH:MM.')
        if at.tzinfo or at.second or at.microsecond: raise ValidationError('Use local date and time to the nearest minute.')
        if at<=datetime.now(): raise ValidationError('Choose a future date and time.')
        when=at.isoformat(timespec='minutes')
        with self.connection() as c:
            self._linked(c,patient,doctor)
            try:
                cur=c.execute('INSERT INTO appointments(patient,doctor,when_at,reason) VALUES (?,?,?,?)',(patient,doctor,when,reason))
            except sqlite3.IntegrityError as e: raise ValidationError('This doctor already has a request at that time. Choose another time.') from e
            return cur.lastrowid

    def appointments(self,uid):
        self.user(uid)
        with self.connection() as c:
            rows=c.execute('''SELECT a.*,p.name patient_name,d.name doctor_name FROM appointments a
                JOIN users p ON p.id=a.patient JOIN users d ON d.id=a.doctor
                WHERE a.patient=? OR a.doctor=? ORDER BY a.when_at DESC,a.id DESC''',(uid,uid)).fetchall()
        return [dict(r) for r in rows]

    def update_appointment(self,uid,aid,status):
        with self.connection() as c:
            row=c.execute('SELECT * FROM appointments WHERE id=?',(aid,)).fetchone()
            if not row or uid not in (row['patient'],row['doctor']): raise ValidationError('You cannot change this appointment.')
            if row['status'] not in ('requested','accepted'): raise ValidationError('This appointment is already closed.')
            allowed=('cancelled',) if uid==row['patient'] else (('accepted','cancelled') if row['status']=='requested' else ('completed','cancelled'))
            if status not in allowed: raise ValidationError('This status change is unavailable.')
            self._linked(c,row['patient'],row['doctor'])
            c.execute('UPDATE appointments SET status=? WHERE id=?',(status,aid))

    def notes(self,doctor,patient):
        self._role(doctor,'doctor')
        with self.connection() as c:
            self._linked(c,patient,doctor)
            rows=c.execute('SELECT * FROM notes WHERE doctor=? AND patient=? ORDER BY id DESC',(doctor,patient)).fetchall()
        return [dict(r) for r in rows]

    def save_note(self,doctor,patient,text):
        self._role(doctor,'doctor')
        text=self._text(text,'Note',4000,True)
        with self.connection() as c:
            self._linked(c,patient,doctor)
            c.execute('INSERT INTO notes(doctor,patient,text,created) VALUES (?,?,?,?)',(doctor,patient,text,datetime.now().isoformat(timespec='seconds')))

    def assistant_history(self,uid):
        self.user(uid)
        with self.connection() as c: rows=c.execute('SELECT role,text,created FROM assistant_messages WHERE uid=? ORDER BY id',(uid,)).fetchall()
        return [dict(r) for r in rows]

    def add_assistant_message(self,uid,role,text):
        self.user(uid)
        if role not in ('user','assistant'): raise ValidationError('Invalid message role.')
        text=self._text(text,'Message',16000,True)
        with self.connection() as c: c.execute('INSERT INTO assistant_messages(uid,role,text,created) VALUES (?,?,?,?)',(uid,role,text,datetime.now().isoformat(timespec='seconds')))

    def clear_assistant_history(self,uid):
        self.user(uid)
        with self.connection() as c: c.execute('DELETE FROM assistant_messages WHERE uid=?',(uid,))
