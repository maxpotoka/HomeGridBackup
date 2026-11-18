[app]
title = HomeGrid Backup
package.name = homegridbackup
package.domain = org.homegrid
source.dir = .
source.include_exts = py,png,jpg,ico,kv,json
source.exclude_dirs = tests, bin, .git, .github, dist_x86, dist_mac, build
version = 1.028
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
