#Библиотеки
import os
import csv
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from collections import defaultdict
##################################################################################

#Функции
def get_size_string(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
##################################################################################
def get_file_extension(file_path):
    """Возвращает расширение файла (.txt, .apk, .py и т.д.)."""
    if file_path.is_dir():
        return "📁 папка"
    
    ext = Path(file_path).suffix.lower()
    if not ext:  # Нет расширения
        return "❓ без расширения"
    
    return ext.upper()  # .txt → .TXT
##################################################################################
def get_hierarchy_symbol(level):
    """Генерирует символы иерархии для отображения вложенности"""
    if level == 0:
        return ""
    symbols = ["│   "] * (level - 1) + ["├── "]
    return "".join(symbols)
##################################################################################
def main():
    root = tk.Tk()
    app = DirectoryAnalyzer(root)
    root.mainloop()
##################################################################################

#Классы
class DuplicatesWindow:
    def __init__(self, parent, duplicates_data):
        self.window = tk.Toplevel(parent)
        self.window.title("🔍 Дубликаты по размеру")
        self.window.geometry("1400x700")
        self.window.minsize(1200, 600)
        
        self.duplicates_data = duplicates_data
        self.sort_column = 'size'  # Текущая колонка сортировки
        self.sort_reverse = True   # Направление сортировки
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Заголовок со статистикой
        stats_frame = ttk.LabelFrame(main_frame, text="📊 Статистика дубликатов", padding="10")
        stats_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        total_dups = sum(len(files) for files in self.duplicates_data.values() if len(files) > 1)
        groups_count = len([group for group in self.duplicates_data.values() if len(group) > 1])
        
        stats_text = f"Найдено {groups_count} групп дубликатов, всего {total_dups} файлов"
        ttk.Label(stats_frame, text=stats_text, font=('Arial', 11, 'bold')).pack()
        
        #  Кнопки сортировки
        sort_frame = ttk.Frame(main_frame)
        sort_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        ttk.Button(sort_frame, text="📊 По размеру ↓", command=lambda: self.sort_table('size')).pack(side=tk.LEFT, padx=2)
        ttk.Button(sort_frame, text="📁 По пути", command=lambda: self.sort_table('path')).pack(side=tk.LEFT, padx=2)
        ttk.Button(sort_frame, text="📄 По имени", command=lambda: self.sort_table('name')).pack(side=tk.LEFT, padx=2)
        ttk.Button(sort_frame, text="🔤 По расширению", command=lambda: self.sort_table('extension')).pack(side=tk.LEFT, padx=2)
        
        #  НОВАЯ СТРУКТУРА ТАБЛИЦЫ
        table_frame = ttk.Frame(main_frame)
        table_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.table = ttk.Treeview(table_frame, 
                                 columns=('name', 'path', 'extension', 'size', 'count'),
                                 show='headings', 
                                 yscrollcommand=scroll_y.set, 
                                 xscrollcommand=scroll_x.set)
        scroll_y.config(command=self.table.yview)
        scroll_x.config(command=self.table.xview)
        self.table.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        #  Привязка клика по заголовкам для сортировки
        self.table.heading('name', text='📄 Название', command=lambda: self.sort_table('name'))
        self.table.heading('path', text='📁 Путь', command=lambda: self.sort_table('path'))
        self.table.heading('extension', text='🔤 Расширение', command=lambda: self.sort_table('extension'))
        self.table.heading('size', text='📊 Размер', command=lambda: self.sort_table('size'))
        self.table.heading('count', text='🔢 Количество', command=lambda: self.sort_table('count'))
        
        self.setup_table_columns()
        self.populate_table()
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))
        
        ttk.Button(btn_frame, text="💾 Экспорт CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Обновить", command=self.refresh_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Закрыть", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
    
    def setup_table_columns(self):
        self.table.column('name', width=300, minwidth=250)
        self.table.column('path', width=500, minwidth=400)
        self.table.column('extension', width=120, minwidth=100)
        self.table.column('size', width=130, minwidth=110, anchor=tk.CENTER)
        self.table.column('count', width=100, minwidth=80, anchor=tk.CENTER)
    
    def sort_key(self, row_data, col):
        """Функция для получения ключа сортировки"""
        name, path, extension, size_str, count_str = row_data
        
        if col == 'name':
            return name.lower()
        elif col == 'path':
            return path.lower()
        elif col == 'extension':
            return extension.lower()
        elif col == 'size':
            # Конвертируем размер обратно в байты для числовой сортировки
            size_bytes = float(size_str.split()[0]) * (1024 ** ['B','KB','MB','GB','TB','PB'].index(size_str.split()[1]))
            return size_bytes
        elif col == 'count':
            return int(count_str)
        return row_data
    
    def sort_table(self, column):
        """Сортировка таблицы по колонке"""
        self.sort_column = column
        self.sort_reverse = not self.sort_reverse if column == self.sort_column else True
        
        # Получаем все данные
        items = [(self.table.item(item)['values'], item) for item in self.table.get_children('')]
        
        # Сортируем
        items.sort(key=lambda x: self.sort_key(x[0], column), reverse=self.sort_reverse)
        
        # Очищаем таблицу
        for item in self.table.get_children():
            self.table.delete(item)
        
        # Вставляем отсортированные данные
        for values, _ in items:
            self.table.insert('', 'end', values=values)
        
        # Обновляем заголовок (стрелка сортировки)
        direction = " ↓" if self.sort_reverse else " ↑"
        headings = {
            'name': f'📄 Название{direction}',
            'path': f'📁 Путь{direction}',
            'extension': f'🔤 Расширение{direction}',
            'size': f'📊 Размер{direction}',
            'count': f'🔢 Количество{direction}'
        }
        self.table.heading(column, text=headings[column])
    
    def populate_table(self):
        """Заполнение таблицы данными"""
        for size_bytes, files in sorted(self.duplicates_data.items(), key=lambda x: x[0], reverse=True):
            if len(files) > 1:
                size_str = get_size_string(size_bytes)
                count = len(files)
                
                for file_path in files:
                    self.table.insert('', 'end', values=(
                        file_path.name,
                        str(file_path.parent),
                        get_file_extension(file_path),
                        size_str,
                        count
                    ))
    
    def refresh_table(self):
        """Обновление таблицы (перезаполнение с текущей сортировкой)"""
        # Сохраняем текущую сортировку
        current_sort = self.sort_column, self.sort_reverse
        
        # Очищаем и перезаполняем
        for item in self.table.get_children():
            self.table.delete(item)
        self.populate_table()
        
        # Применяем сортировку
        self.sort_table(current_sort[0])
    
    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialname=f"duplicates_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Название', 'Путь', 'Расширение', 'Размер', 'Количество'])
                    
                    # Экспортируем отсортированные данные из таблицы
                    items = [(self.table.item(item)['values']) for item in self.table.get_children('')]
                    writer.writerows(items)
                    
                messagebox.showinfo("Успех", f"Экспортировано в:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{str(e)}")
####################################################################################################################################################################

class DirectoryAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 Анализатор Директорий v2.7 - Иерархия + Дубликаты + СОРТИРОВКА")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        self.table_data = []
        self.tree_data = []
        self.duplicates_data = None
        
        self.setup_ui()
        self.root.update_idletasks()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        top_frame = ttk.LabelFrame(main_frame, text="🔍 Настройки анализа", padding="10")
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        top_frame.columnconfigure(1, weight=1)
        
        ttk.Label(top_frame, text="📂 Путь к директории:", font=('Arial', 11, 'bold')).grid(row=0, column=0, padx=(0, 10), pady=5, sticky=tk.W)
        
        self.path_var = tk.StringVar(value=os.getcwd())
        path_entry = ttk.Entry(top_frame, textvariable=self.path_var, font=('Arial', 10))
        path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        
        ttk.Button(top_frame, text="📁 Выбрать", command=self.select_directory).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(top_frame, text="🔍 АНАЛИЗИРОВАТЬ", command=self.start_analysis, 
                  style="Accent.TButton", width=15).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(top_frame, text="🔍 Подсчитать дубликаты", command=self.find_duplicates, 
                  style="Accent.TButton", width=20).grid(row=0, column=4, padx=(10, 0), pady=5)
        
        self.progress = ttk.Progressbar(top_frame, mode='indeterminate')
        self.progress.grid(row=0, column=5, padx=(10, 0), pady=5, sticky=(tk.W, tk.E))
        
        notebook_frame = ttk.Frame(main_frame)
        notebook_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        notebook_frame.columnconfigure(0, weight=1)
        notebook_frame.rowconfigure(0, weight=1)
        
        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 🌳 ДЕРЕВО
        self.tree_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tree_frame, text="🌳 Дерево")
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)
        
        tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL)
        tree_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.tree = ttk.Treeview(self.tree_frame, columns=('size', 'ext'), show='tree headings',
                                yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_x.config(command=self.tree.xview)
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.tree.heading('#0', text='Название')
        self.tree.heading('size', text='Размер')
        self.tree.heading('ext', text='Расширение')
        self.tree.column('#0', width=400, minwidth=300)
        self.tree.column('size', width=150, minwidth=120)
        self.tree.column('ext', width=120, minwidth=100)
        
        # 📊 ТАБЛИЦА
        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text="📊 Таблица")
        self.table_frame.columnconfigure(0, weight=1)
        self.table_frame.rowconfigure(0, weight=1)
        
        table_scroll_y = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL)
        table_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        table_scroll_x = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL)
        table_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.table = ttk.Treeview(self.table_frame, columns=('type', 'name', 'desc', 'size', 'extension'), 
                                 show='headings', yscrollcommand=table_scroll_y.set, xscrollcommand=table_scroll_x.set)
        table_scroll_y.config(command=self.table.yview)
        table_scroll_x.config(command=self.table.xview)
        self.table.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.setup_table_columns()
        
        bottom_frame = ttk.LabelFrame(main_frame, text="⚡ Управление", padding="8")
        bottom_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(15, 0))
        bottom_frame.columnconfigure(2, weight=1)
        
        ttk.Button(bottom_frame, text="💾 Экспорт CSV", command=self.export_csv).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(bottom_frame, text="🔄 Очистить", command=self.clear_results).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(bottom_frame, text="❓ О программе", command=self.show_about).grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
        
        self.status_var = tk.StringVar(value="Готов к анализу")
        status_frame = ttk.Frame(bottom_frame)
        status_frame.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(20, 5))
        status_frame.columnconfigure(0, weight=1)
        ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def setup_table_columns(self):
        self.table.heading('type', text='Тип')
        self.table.heading('name', text='Название')
        self.table.heading('desc', text='Описание')
        self.table.heading('size', text='Размер')
        self.table.heading('extension', text='Расширение')
        
        self.table.column('type', width=100, minwidth=80, anchor=tk.CENTER)
        self.table.column('name', width=350, minwidth=250)
        self.table.column('desc', width=180, minwidth=150)
        self.table.column('size', width=150, minwidth=120, anchor=tk.CENTER)
        self.table.column('extension', width=120, minwidth=100)
    
    def select_directory(self):
        path = filedialog.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)
    
    def start_analysis(self):
        path = self.path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("Ошибка", "Выберите существующую директорию!")
            return
        
        self.clear_results()
        self.progress.start()
        self.status_var.set("Анализирую...")
        self.root.update()
        
        thread = threading.Thread(target=self.analyze_directory, args=(path,))
        thread.daemon = True
        thread.start()
    
    def find_duplicates(self):
        """🔍 Подсчет дубликатов по размеру"""
        if self.duplicates_data is None:
            messagebox.showwarning("Предупреждение", "Сначала выполните анализ директории!")
            return
        
        # Проверяем, есть ли дубликаты
        dup_count = sum(1 for files in self.duplicates_data.values() if len(files) > 1)
        if dup_count == 0:
            messagebox.showinfo("Инфо", "Дубликаты не найдены!")
            return
        
        DuplicatesWindow(self.root, self.duplicates_data)
    
    def analyze_directory(self, path):
        try:
            self.table_data = []
            self.tree_data = []
            self.duplicates_data = defaultdict(list)
            
            self.recursive_analyze(Path(path), self.table_data, self.tree_data, self.duplicates_data, 0)
            self.root.after(0, self.update_results)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка анализа: {str(e)}"))
        finally:
            self.root.after(0, self.analysis_complete)
    
    def recursive_analyze(self, path_obj, table_data, tree_data, duplicates_data, level):
        try:
            prefix = get_hierarchy_symbol(level)
            
            if not path_obj.exists():
                table_data.append([f"{prefix}❌", str(path_obj), "НЕ СУЩЕСТВУЕТ", "-", "-"])
                return
            
            if path_obj.is_file():
                size = path_obj.stat().st_size
                extension = get_file_extension(path_obj)
                
                # СОБИРАЕМ ДУБЛИКАТЫ
                duplicates_data[size].append(path_obj)
                
                table_data.append([
                    f"{prefix}📄",
                    path_obj.name,
                    "Файл",
                    get_size_string(size),
                    extension
                ])
                tree_data.append((f"{prefix}{path_obj.name}", get_size_string(size), extension))
                return
            
            if path_obj.is_dir():
                try:
                    total_size = sum(f.stat().st_size for f in path_obj.rglob('*') if f.is_file())
                    item_count = len(list(path_obj.iterdir()))
                    
                    extension = get_file_extension(path_obj)
                    
                    table_data.append([
                        f"{prefix}📁",
                        path_obj.name,
                        f"Папка ({item_count} elem.)",
                        get_size_string(total_size),
                        extension
                    ])
                    
                    tree_data.append((f"{prefix}{path_obj.name}", get_size_string(total_size), extension))
                    

                    items = sorted(path_obj.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
                    for item in items:
                        self.recursive_analyze(item, table_data, tree_data, duplicates_data, level + 1)
                        
                except PermissionError:
                    table_data.append([f"{prefix}❌", path_obj.name, "Нет доступа", "-", "❌"])
                    
        except Exception:
            table_data.append([f"{prefix}❌", str(path_obj), "Ошибка доступа", "-", "❌"])
    
    def update_results(self):
        for row in self.table_data:
            self.table.insert('', 'end', values=row)
        
        for name, size, extension in self.tree_data:
            self.tree.insert('', 'end', text=name, values=(size, extension))
    
    def analysis_complete(self):
        self.progress.stop()
        dup_count = sum(1 for files in self.duplicates_data.values() if len(files) > 1)
        self.status_var.set(f"Анализ завершен: {len(self.table_data)} элементов, {dup_count} групп дубликатов")
    
    def export_csv(self):
        if not self.table_data:
            messagebox.showwarning("Предупреждение", "Нет данных для экспорта!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialname=f"dir_extensions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Тип', 'Название', 'Описание', 'Размер', 'Расширение'])
                    writer.writerows(self.table_data)
                messagebox.showinfo("Успех", f"Экспортировано в:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{str(e)}")
    
    def clear_results(self):
        for item in self.table.get_children():
            self.table.delete(item)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.table_data = []
        self.tree_data = []
        self.duplicates_data = None
        self.status_var.set("Результаты очищены")
    
    def show_about(self):
        messagebox.showinfo("О программе", 
                           "📁 Анализатор Директорий v2.7\n\n"
                           "✨ Новое в v2.7:\n"
                           "• Символы иерархии ├── │\n"
                           "• Четкое отображение вложенности\n\n"
                           "✨ v2.6:\n"
                           "• 🔄 Полная сортировка дубликатов\n"
                           "• 📊 По размеру (численно)\n"
                           "• 📁 По пути, имени, расширению\n"
                           "• 📈 Визуальные индикаторы ↑↓\n"
                           "• .APK, .TXT, .PY, .JPG и т.д.\n"
                           "• 📁 папка для директорий\n\n"
                           "✨ v2.0 - v2.5:\n"
                           "• Создание интерфейса\n\n"
                           "✨ v1.0:\n"
                           "• 📁 Анализатор Директорий v1.0 (Консольный вариант)\n\n"
                           "Python 3.6+\nCreate by apdulium")


#Код)
if __name__ == "__main__":
    main()