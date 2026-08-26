[app]
title = SPACE-JET
package.name = spacejet
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav
version = 0.1
requirements = python3,kivy

orientation = portrait
osx.kivy_version = 2.0.0

fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
