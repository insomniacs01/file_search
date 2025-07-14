import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import platform
import string


class FileSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("全盘文件搜索工具")
        self.root.geometry("900x700")

        self.searching = False
        self.search_thread = None
        self.stop_search = False

        self.create_widgets()
        self.available_drives = self.get_available_drives()
        self.update_drive_list()

    def get_available_drives(self):
        drives = []
        if platform.system() == 'Windows':
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
        else:
            drives = ['/']
        return drives

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 搜索设置
        search_frame = ttk.LabelFrame(main_frame, text="搜索设置", padding="10")
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(search_frame, text="搜索名称:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.search_entry.bind('<Return>', lambda e: self.start_search())

        self.case_sensitive_var = tk.BooleanVar(value=False)
        self.case_sensitive_check = ttk.Checkbutton(
            search_frame,
            text="区分大小写",
            variable=self.case_sensitive_var
        )
        self.case_sensitive_check.grid(row=0, column=2, padx=10)

        # 盘符选择
        drive_frame = ttk.LabelFrame(main_frame, text="选择搜索位置", padding="10")
        drive_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.select_all_var = tk.BooleanVar(value=True)
        self.select_all_check = ttk.Checkbutton(
            drive_frame,
            text="全选",
            variable=self.select_all_var,
            command=self.toggle_all_drives
        )
        self.select_all_check.grid(row=0, column=0, sticky=tk.W, padx=5)

        self.drives_frame = ttk.Frame(drive_frame)
        self.drives_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        self.drive_vars = {}

        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.search_button = ttk.Button(
            button_frame,
            text="开始搜索",
            command=self.start_search,
            width=20
        )
        self.search_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="停止搜索",
            command=self.stop_search_action,
            state=tk.DISABLED,
            width=20
        )
        self.stop_button.grid(row=0, column=1, padx=5)

        self.clear_button = ttk.Button(
            button_frame,
            text="清空结果",
            command=self.clear_results,
            width=20
        )
        self.clear_button.grid(row=0, column=2, padx=5)

        # 进度显示
        self.progress_var = tk.StringVar(value="准备就绪")
        self.progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=300
        )
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 结果显示
        result_frame = ttk.LabelFrame(main_frame, text="搜索结果", padding="10")
        result_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            width=100,
            height=20,
            wrap=tk.WORD
        )
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.result_text.tag_configure("folder", foreground="blue", font=("Arial", 10, "bold"))
        self.result_text.tag_configure("file", foreground="green")
        self.result_text.tag_configure("header", font=("Arial", 12, "bold"))
        self.result_text.tag_configure("summary", foreground="red", font=("Arial", 11, "bold"))

        # 统计信息
        self.stats_var = tk.StringVar(value="文件夹: 0 | 文件: 0 | 已扫描: 0")
        self.stats_label = ttk.Label(main_frame, textvariable=self.stats_var)
        self.stats_label.grid(row=6, column=0, columnspan=2, pady=5)

        # 设置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

    def update_drive_list(self):
        for widget in self.drives_frame.winfo_children():
            widget.destroy()

        self.drive_vars.clear()

        row = 0
        col = 0
        for drive in self.available_drives:
            var = tk.BooleanVar(value=True)
            self.drive_vars[drive] = var

            label = f"{drive} (本地磁盘)"

            check = ttk.Checkbutton(
                self.drives_frame,
                text=label,
                variable=var,
                command=self.update_select_all_state
            )
            check.grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)

            col += 1
            if col > 3:
                col = 0
                row += 1

    def toggle_all_drives(self):
        select_all = self.select_all_var.get()
        for var in self.drive_vars.values():
            var.set(select_all)

    def update_select_all_state(self):
        all_selected = all(var.get() for var in self.drive_vars.values())
        self.select_all_var.set(all_selected)

    def start_search(self):
        if self.searching:
            messagebox.showwarning("警告", "搜索正在进行中！")
            return

        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showwarning("警告", "请输入搜索关键词！")
            return

        selected_drives = [drive for drive, var in self.drive_vars.items() if var.get()]
        if not selected_drives:
            messagebox.showwarning("警告", "请至少选择一个搜索位置！")
            return

        self.clear_results()

        self.search_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.searching = True
        self.stop_search = False

        self.progress_bar.start(10)

        self.search_thread = threading.Thread(
            target=self.search_files,
            args=(search_term, selected_drives, self.case_sensitive_var.get())
        )
        self.search_thread.daemon = True
        self.search_thread.start()

    def search_files(self, search_term, drives, case_sensitive):
        found_folders = []
        found_files = []
        total_scanned = 0

        if not case_sensitive:
            search_term = search_term.lower()

        start_time = time.time()

        for drive in drives:
            if self.stop_search:
                break

            self.update_progress(f"正在搜索 {drive}...")

            try:
                for dirpath, dirnames, filenames in os.walk(drive):
                    if self.stop_search:
                        break

                    total_scanned += 1

                    for dirname in dirnames:
                        check_name = dirname.lower() if not case_sensitive else dirname
                        if search_term in check_name:
                            full_path = os.path.join(dirpath, dirname)
                            found_folders.append(full_path)
                            self.add_result(f"[文件夹] {full_path}\n", "folder")

                    for filename in filenames:
                        check_name = filename.lower() if not case_sensitive else filename
                        if search_term in check_name:
                            full_path = os.path.join(dirpath, filename)
                            found_files.append(full_path)

                            try:
                                size = os.path.getsize(full_path)
                                size_str = self.format_file_size(size)
                                self.add_result(f"[文件] {full_path} ({size_str})\n", "file")
                            except:
                                self.add_result(f"[文件] {full_path}\n", "file")

                    if total_scanned % 100 == 0:
                        self.update_stats(len(found_folders), len(found_files), total_scanned)
                        self.update_progress(f"正在搜索 {drive} - 已扫描 {total_scanned} 个目录...")

            except PermissionError:
                continue
            except Exception as e:
                self.add_result(f"错误: {str(e)}\n", "error")

        elapsed_time = time.time() - start_time
        self.search_complete(len(found_folders), len(found_files), total_scanned, elapsed_time)

    def format_file_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def add_result(self, text, tag=None):
        self.root.after(0, self._add_result, text, tag)

    def _add_result(self, text, tag):
        self.result_text.insert(tk.END, text, tag)
        self.result_text.see(tk.END)

    def update_progress(self, message):
        self.root.after(0, self.progress_var.set, message)

    def update_stats(self, folders, files, scanned):
        stats = f"文件夹: {folders} | 文件: {files} | 已扫描: {scanned}"
        self.root.after(0, self.stats_var.set, stats)

    def search_complete(self, folders, files, scanned, elapsed_time):
        self.root.after(0, self._search_complete, folders, files, scanned, elapsed_time)

    def _search_complete(self, folders, files, scanned, elapsed_time):
        self.progress_bar.stop()

        summary = f"\n{'=' * 60}\n"
        summary += f"搜索完成！\n"
        summary += f"找到 {folders} 个文件夹，{files} 个文件\n"
        summary += f"共扫描 {scanned} 个目录\n"
        summary += f"用时: {elapsed_time:.2f} 秒\n"
        summary += f"{'=' * 60}\n"

        self.result_text.insert(tk.END, summary, "summary")
        self.result_text.see(tk.END)

        self.progress_var.set("搜索完成")
        self.update_stats(folders, files, scanned)

        self.search_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.searching = False

        if self.stop_search:
            messagebox.showinfo("提示", "搜索已停止")
        else:
            messagebox.showinfo("完成", f"搜索完成！找到 {folders} 个文件夹，{files} 个文件")

    def stop_search_action(self):
        if self.searching:
            self.stop_search = True
            self.progress_var.set("正在停止搜索...")

    def clear_results(self):
        self.result_text.delete(1.0, tk.END)
        self.stats_var.set("文件夹: 0 | 文件: 0 | 已扫描: 0")
        self.progress_var.set("准备就绪")


def main():
    root = tk.Tk()
    app = FileSearchGUI(root)

    try:
        root.iconbitmap(default='search.ico')
    except:
        pass

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == "__main__":
    main()