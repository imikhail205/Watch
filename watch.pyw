import winreg
import time
import tkinter as tk
import ctypes
import ctypes.wintypes

# 🛡️ ФИКС DPI-МАСШТАБИРОВАНИЯ (Решает проблему улета мышки и прыжков координат)
try:
    # Заставляем Windows отдавать Python реальные физические пиксели без искажений масштаба
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per Monitor DPI Aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware() # Резервный вариант для старых Windows
    except Exception:
        pass

# Путь в реестре HKEY_CURRENT_USER
REG_KEY_PATH = r"SOFTWARE\Nikon\Camera Control Pro\2.0\FileNaming"

def update_time():
    """Обновляет время на экране каждую секунду"""
    current_time = time.strftime("%H:%M")
    label.config(text=current_time)
    root.after(1000, update_time)

def get_saved_coordinates():
    """Считывает сохраненные координаты окна из реестра"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
            x, _ = winreg.QueryValueEx(key, "ClockX")
            y, _ = winreg.QueryValueEx(key, "ClockY")
            return int(x), int(y)
    except Exception:
        return None

def save_coordinates(x, y):
    """Сохраняет текущие координаты окна в реестр, автоматически создавая папки, если их нет"""
    try:
        # CreateKeyEx открывает существующий ключ или создаёт всю цепочку папок
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "ClockX", 0, winreg.REG_SZ, str(x))
            winreg.SetValueEx(key, "ClockY", 0, winreg.REG_SZ, str(y))
    except Exception:
        pass

# --- Универсальный Drag & Drop для любых конфигураций мониторов ---
def start_drag(event):
    global start_x, start_y
    # Точные координаты клика относительно верхнего левого угла самого окна
    start_x = event.x
    start_y = event.y

def drag_window(event):
    # Глобальные координаты мыши на экране МИНУС смещение клика внутри окна
    x = event.x_root - start_x
    y = event.y_root - start_y
    
    # Шаблон '+%d+%d' в Tkinter отлично переваривает отрицательные числа (получается + -1200 -> -1200)
    root.wm_geometry(f"+{x}+{y}")

def stop_drag(event):
    """Срабатывает при отпускании мыши и сохраняет точные физические координаты окна"""
    try:
        # Получаем дескриптор окна Tkinter для Windows
        hwnd = int(root.wm_frame(), 16)
        rect = ctypes.wintypes.RECT()
        # Запрашиваем честные экранные координаты у Win32 API, обходя баги winfo_x()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        save_coordinates(rect.left, rect.top)
    except Exception:
        # Запасной вариант, если Win32 API не вернул данные
        save_coordinates(root.winfo_x(), root.winfo_y())

def safe_exit(event=None):
    root.destroy()

# --- Инициализация графического интерфейса ---
root = tk.Tk()
root.overrideredirect(True)
root.wm_attributes("-topmost", True)
root.wm_attributes("-alpha", 0.7) 
root.config(bg="#1A1A1A") 

label = tk.Label(
    root, 
    text="", 
    font=("Arial", 72, "bold"), 
    fg="#FFFFFF",               
    bg="#1A1A1A"
)
label.pack(expand=True, fill="both", padx=20, pady=5)

# Привязка событий для перетаскивания и сохранения
label.bind("<Button-1>", start_drag)
label.bind("<B1-Motion>", drag_window)
label.bind("<ButtonRelease-1>", stop_drag)

root.bind("<Alt-F4>", safe_exit)
root.protocol("WM_DELETE_WINDOW", safe_exit)

update_time()

# Принудительно рассчитываем размеры интерфейса, чтобы окно не схлопывалось
root.update_idletasks()
widget_real_width = root.winfo_reqwidth()
widget_real_height = root.winfo_reqheight()

# Задаем фиксированный размер окну
root.wm_geometry(f"{widget_real_width}x{widget_real_height}")

# 📍 ПОЗИЦИОНИРОВАНИЕ ИЗ РЕЕСТРА ИЛИ РАСЧЕТ В УГОЛ
saved_pos = get_saved_coordinates()
if saved_pos:
    x, y = saved_pos
    # Перемещаем окно в сохраненные координаты (включая отрицательные знаки)
    root.wm_geometry(f"+{x}+{y}")
else:
    # Дефолтное положение: правый верхний угол главного монитора
    screen_width = root.winfo_screenwidth()
    init_x = screen_width - widget_real_width - 40
    init_y = 40
    root.wm_geometry(f"+{init_x}+{init_y}")

root.mainloop()
