# Building the Windows executable

These steps must run on a **Windows 11 machine** (an .exe cannot be produced
from Linux/macOS).

## 1. Prepare the environment

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,windows,voice,vision,browser]" pyinstaller
```

## 2. Verify the app runs from source

```powershell
python -m humanoid_bot.app.main
```

## 3. Build the executable

```powershell
pyinstaller packaging\humanoidbot.spec --noconfirm
```

Output lands in `dist\HumanoidBotAssistant\HumanoidBotAssistant.exe`.

## 4. Build the installer (optional)

Install [Inno Setup 6](https://jrsoftware.org/isinfo.php), then:

```powershell
iscc packaging\installer.iss
```

`packaging\dist\HumanoidBotAssistant-Setup.exe` installs with desktop and
Start Menu shortcuts and an optional start-with-Windows task.

## Notes

- `console=False` in the spec keeps the app windowless.
- Optional extras (`windows`, `voice`, `vision`, `browser`) enable real
  automation (pywinauto/pyautogui), local speech (faster-whisper/pyttsx3),
  OCR (pytesseract + Tesseract binary on PATH), and browser automation
  (Playwright: run `playwright install` once).
- Without the extras the app still runs: fake backends keep every feature
  importable and the UI functional.
