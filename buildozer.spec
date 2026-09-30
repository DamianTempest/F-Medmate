[app]
title = Medmate
package.name = medmate
package.domain = org.owntek
source.dir = .
source.include_exts = py,kv,png,jpg,atlas,ttf,json
source.exclude_dirs = .venv,venv,tests,docs,.git,__pycache__,build,dist
source.exclude_patterns = .env,*.db,*.sqlite,*.pyc
version = 1.0.0
requirements = python3,kivy==2.3.1,kivymd==1.2.0,pillow,requests,python-dotenv,openssl
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 35
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = False
[buildozer]
log_level = 2
warn_on_root = 1
