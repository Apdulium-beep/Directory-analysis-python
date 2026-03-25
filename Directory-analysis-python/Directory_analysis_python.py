import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from collections import defaultdict

#Расширенная карта типов файлов
FILE_TYPES = {
    '.doc': 'Word 97-2003', '.docx': 'Word Document', 
    '.xls': 'Excel 97-2003', '.xlsx': 'Excel Spreadsheet',
    '.ppt': 'PowerPoint 97-2003', '.pptx': 'PowerPoint',
    '.pdf': 'PDF Document', '.txt': 'Text File', '.rtf': 'Rich Text',
    '.iso': 'ISO Image', '.img': 'Disk Image', '.vhd': 'Virtual Disk',
    '.zip': 'ZIP Archive', '.rar': 'RAR Archive', '.7z': '7-Zip',
    '.tar': 'TAR Archive', '.gz': 'GZip', '.bz2': 'BZip2',
    '.jpg': 'JPEG Image', '.jpeg': 'JPEG Image', '.png': 'PNG Image',
    '.gif': 'GIF Image', '.bmp': 'Bitmap', '.tiff': 'TIFF Image',
    '.webp': 'WebP Image', '.svg': 'SVG Vector',
    '.mp4': 'MP4 Video', '.avi': 'AVI Video', '.mkv': 'MKV Video',
    '.mp3': 'MP3 Audio', '.wav': 'WAV Audio', '.flac': 'FLAC Audio',
    '.exe': 'Executable', '.dll': 'Dynamic Library', '.py': 'Python Script',
    '.js': 'JavaScript', '.html': 'HTML', '.css': 'CSS',
}

def get_file_type(filename):
    ext = Path(filename).suffix.lower()
    return FILE_TYPES.get(ext, f"Файл ({ext[1:].upper()})")

current_directory = os.getcwd()

def analyze_directory():
    global current_directory
    
    try:
        files = [f for f in os.listdir(current_directory) 
                if os.path.isfile(os.path.join(current_directory, f))]
    except PermissionError:
        messagebox.showerror("Ошибка", "Нет доступа к папке!")
        return
    
#Очищаем таблицу
    for item in tree.get_children():
        tree.delete(item)
    
    files_by_size = defaultdict(list)
    for filename in sorted(files):
        filepath = os.path.join(current_directory, filename)
        try:
            size = os.path.getsize(filepath)
        except (OSError, PermissionError):
            continue
        
        file_type = get_file_type(filename)
        files_by_size[size].append((filename, file_type))
    
#Заполняем таблицу
    for size in sorted(files_by_size):
        count = len(files_by_size[size])
        for filename, file_type in files_by_size[size]:
            tree.insert("", "end", values=(filename, f"{size:,}", file_type, f"[{count}]"))

def select_directory():
    global current_directory
    new_dir = filedialog.askdirectory(initialdir=current_directory, title="Выберите папку")
    if new_dir:
        current_directory = new_dir
        path_label.config(text=f"📍 Директория: {current_directory}")
        analyze_directory()

def sort_column(column, reverse=False):
    data = [(tree.set(child, column), child) for child in tree.get_children()]
    
    if column == "Размер":
        data.sort(key=lambda x: int(x[0].replace(',', '')), reverse=reverse)
    elif column == "Группа":
        data.sort(key=lambda x: int(x[0][1:x[0].find(' ')]), reverse=reverse)
    else:
        data.sort(reverse=reverse)
    
    for index, (val, child) in enumerate(data):
        tree.move(child, '', index)
    
    tree.heading(column, command=lambda: sort_column(column, not reverse))

#ИНТЕРФЕЙС
root = tk.Tk()
root.title("Анализатор файлов Pro")
root.geometry("1100x650")

#Заголовок
tk.Label(root, text="🔍 Анализатор файлов (Word, ISO, архивы, видео...)", 
         font=("Arial", 13, "bold")).pack(pady=15)

#Таблица
columns = ("Название", "Размер", "Тип", "Группа")
tree = ttk.Treeview(root, columns=columns, show="headings", height=25)
tree.heading("Название", text="📄 Название", command=lambda: sort_column("Название"))
tree.heading("Размер", text="📏 Размер", command=lambda: sort_column("Размер"))
tree.heading("Тип", text="📋 Тип файла", command=lambda: sort_column("Тип"))
tree.heading("Группа", text="🔗 Дубликаты", command=lambda: sort_column("Группа"))
tree.column("Название", width=450)
tree.column("Размер", width=140)
tree.column("Тип", width=300)
tree.column("Группа", width=150)
tree.pack(pady=10, padx=15, fill="both", expand=True)

#КНОПКИ 
button_frame = tk.Frame(root)
button_frame.pack(pady=15)

select_btn = tk.Button(button_frame, text="📁 Выбрать папку", 
                      command=select_directory, bg="#2196F3", fg="white", 
                      font=("Arial", 11, "bold"), width=16, height=2)
select_btn.pack(side=tk.LEFT, padx=10)

update_btn = tk.Button(button_frame, text="🔄 Обновить", 
                      command=analyze_directory, bg="#4CAF50", fg="white", 
                      font=("Arial", 11), width=14, height=2)
update_btn.pack(side=tk.LEFT, padx=10)


path_label = tk.Label(root, text=f"📍 Директория: {current_directory}", 
                     font=("Arial", 10), anchor="w", justify="left", 
                     relief="sunken", bd=1, bg="#f0f0f0")
path_label.pack(pady=10, padx=15, fill="x")


analyze_directory()
root.mainloop()
