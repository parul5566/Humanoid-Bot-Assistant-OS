# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for HumanoidBotAssistant.exe (build on Windows).

Usage (on a Windows 11 machine with Python 3.12+):
    pip install -e . pyinstaller
    pyinstaller packaging/humanoidbot.spec --noconfirm
Output: dist/HumanoidBotAssistant/HumanoidBotAssistant.exe
"""

import sys

block_cipher = None

a = Analysis(
    ["../humanoid_bot/app/main.py"],
    pathex=[".."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "humanoid_bot.ui.main_window",
        "humanoid_bot.ui.avatar.avatar_widget",
        "humanoid_bot.ui.chat.chat_panel",
        "humanoid_bot.ui.system_tray.tray",
        "humanoid_bot.ui.settings.settings_dialog",
        "humanoid_bot.ui.history",
        "humanoid_bot.ui.system_monitor",
        "humanoid_bot.ai.orchestrator",
        "humanoid_bot.ai.planner",
        "humanoid_bot.ai.providers.base",
        "humanoid_bot.tools.registry",
        "humanoid_bot.tools.automation_tools",
        "humanoid_bot.tools.file_tools",
        "humanoid_bot.tools.screen_tools",
        "humanoid_bot.tools.system_tools",
        "humanoid_bot.tools.clipboard_tools",
        "humanoid_bot.tools.notification_tools",
        "humanoid_bot.tools.web_tools",
        "humanoid_bot.security.permissions",
        "humanoid_bot.security.confirmation",
        "humanoid_bot.voice.pipeline",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="HumanoidBotAssistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # windowed app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # place assets/icon.ico here and reference it
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="HumanoidBotAssistant",
)

if sys.platform != "win32":
    # The spec is only meaningful on Windows; keep importable for docs/CI checks.
    pass
