[app]
title = SPACE-JET
package.name = spacejet
package.domain = org.test
source.dir = .
source.filename = game.py
source.include_exts = py,png,jpg,kv,atlas,wav,mp3

version = 0.1
requirements = python3,pygame

orientation = landscape
fullscreen = 1

android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
