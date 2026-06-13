#!/usr/bin/env python3
"""
Adaptive Process Booster (Dynamic Resource Manager) - Advanced Edition
A comprehensive GUI-based application for monitoring and managing process priorities
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import psutil
import threading
import time
import sys
import os
import csv
from datetime import datetime
from collections import deque
import json


# Priority levels mapping
PRIORITY_LEVELS = {
    'Windows': {
        'Realtime': psutil.REALTIME_PRIORITY_CLASS,
        'High': psutil.HIGH_PRIORITY_CLASS,
        'Above Normal': psutil.ABOVE_NORMAL_PRIORITY_CLASS,
        'Normal': psutil.NORMAL_PRIORITY_CLASS,
        'Below Normal': psutil.BELOW_NORMAL_PRIORITY_CLASS,
        'Low': psutil.IDLE_PRIORITY_CLASS
    },
    'Linux': {
        'Very High': -10,
        'High': -5,
        'Above Normal': -2,
        'Normal': 0,
        'Below Normal': 5,
        'Low': 10
    }
}


def boost_process_priority(pid, priority_level='High'):
    """
    Boost the priority of a process based on the operating system.
    
    Args:
        pid (int): Process ID to boost
        priority_level (str): Priority level name
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        process = psutil.Process(pid)
        
        if sys.platform == 'win32':
            priority_map = PRIORITY_LEVELS['Windows']
            if priority_level in priority_map:
                process.nice(priority_map[priority_level])
            else:
                process.nice(psutil.HIGH_PRIORITY_CLASS)
        else:
            priority_map = PRIORITY_LEVELS['Linux']
            if priority_level in priority_map:
                process.nice(priority_map[priority_level])
            else:
                process.nice(-5)
        
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False
    except Exception:
        return False


def kill_process(pid):
    """
    Terminate a process.
    
    Args:
        pid (int): Process ID to kill
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        process = psutil.Process(pid)
        process.terminate()
        time.sleep(0.5)
        if process.is_running():
            process.kill()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    except Exception:
        return False


def calculate_score(cpu_percent, ram_percent):
    """
    Calculate dynamic score based on CPU and RAM usage.
    
    Args:
        cpu_percent (float): CPU usage percentage
        ram_percent (float): RAM usage percentage
        
    Returns:
        float: Calculated score
    """
    score = 0.6 * cpu_percent + 0.4 * ram_percent
    return score


def get_process_details(pid):
    """
    Get detailed information about a process.
    
    Args:
        pid (int): Process ID
        
    Returns:
        dict: Process details or None if error
    """
    try:
        process = psutil.Process(pid)
        with process.oneshot():
            return {
                'pid': pid,
                'name': process.name(),
                'status': process.status(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'memory_info': process.memory_info(),
                'num_threads': process.num_threads(),
                'create_time': datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
                'exe': process.exe() if hasattr(process, 'exe') else 'N/A',
                'cwd': process.cwd() if hasattr(process, 'cwd') else 'N/A',
                'cmdline': ' '.join(process.cmdline()) if process.cmdline() else 'N/A',
                'username': process.username() if hasattr(process, 'username') else 'N/A',
                'nice': process.nice() if hasattr(process, 'nice') else 'N/A'
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None
    except Exception:
        return None


def monitor_processes(gui_app):
    """
    Continuously monitor processes and update GUI.
    Also performs automatic priority boosting for high-score processes.
    
    Args:
        gui_app: Reference to the GUI application instance
    """
    while gui_app.monitoring_active:
        try:
            processes_data = []
            system_cpu = psutil.cpu_percent(interval=0.1)
            system_memory = psutil.virtual_memory()
            # Get disk usage - use C: on Windows, / on Linux/Mac
            disk_path = 'C:\\' if sys.platform == 'win32' else '/'
            try:
                system_disk = psutil.disk_usage(disk_path)
            except:
                # Fallback if disk path fails
                system_disk = type('obj', (object,), {
                    'percent': 0,
                    'total': 0,
                    'used': 0,
                    'free': 0
                })()
            
            # Update system stats
            gui_app.root.after(0, gui_app.update_system_stats, {
                'cpu': system_cpu,
                'memory_percent': system_memory.percent,
                'memory_total': system_memory.total,
                'memory_used': system_memory.used,
                'memory_available': system_memory.available,
                'disk_percent': system_disk.percent,
                'disk_total': system_disk.total,
                'disk_used': system_disk.used,
                'disk_free': system_disk.free
            })
            
            # Get all running processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    pid = proc_info['pid']
                    name = proc_info['name'] or 'N/A'
                    cpu_percent = proc_info['cpu_percent'] or 0.0
                    ram_percent = proc_info['memory_percent'] or 0.0
                    status = proc_info.get('status', 'unknown')
                    
                    # Calculate dynamic score
                    score = calculate_score(cpu_percent, ram_percent)
                    
                    # Auto-boost if enabled and score > threshold
                    if gui_app.auto_boost_enabled and score > gui_app.auto_boost_threshold:
                        try:
                            boost_process_priority(pid, gui_app.auto_boost_level)
                            gui_app.log_action(f"Auto-boosted PID {pid} ({name}) - Score: {score:.2f}")
                        except:
                            pass
                    
                    processes_data.append({
                        'pid': pid,
                        'name': name,
                        'cpu': cpu_percent,
                        'ram': ram_percent,
                        'score': score,
                        'status': status
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception:
                    continue
            
            # Update GUI in thread-safe manner
            gui_app.root.after(0, gui_app.update_process_list, processes_data)
            
            # Wait 1 second before next refresh
            time.sleep(1)
            
        except Exception:
            time.sleep(1)
            continue


class ProcessDetailsWindow:
    """Window to display detailed process information."""
    
    def __init__(self, parent, pid):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Process Details - PID {pid}")
        self.window.geometry("600x500")
        self.window.resizable(True, True)
        
        details = get_process_details(pid)
        if not details:
            tk.Label(self.window, text="Unable to retrieve process details.", fg="red").pack(pady=20)
            return
        
        # Create scrollable text widget
        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Format and insert details
        info_text = f"""
PROCESS DETAILS
{'='*60}

PID:                 {details['pid']}
Name:                {details['name']}
Status:              {details['status']}
CPU Usage:           {details['cpu_percent']:.2f}%
Memory Usage:        {details['memory_percent']:.2f}%
Memory (RSS):        {details['memory_info'].rss / (1024*1024):.2f} MB
Memory (VMS):        {details['memory_info'].vms / (1024*1024):.2f} MB
Threads:             {details['num_threads']}
Created:             {details['create_time']}
Priority (Nice):     {details['nice']}
Username:            {details['username']}

Executable Path:
{details['exe']}

Working Directory:
{details['cwd']}

Command Line:
{details['cmdline']}
"""
        
        text_widget.insert("1.0", info_text)
        text_widget.config(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


class SettingsWindow:
    """Window for application settings with enhanced styling."""
    
    def __init__(self, parent, app):
        self.app = app
        self.window = tk.Toplevel(parent)
        self.window.title("⚙️ Settings - Adaptive Process Booster")
        self.window.geometry("550x450")
        self.window.resizable(False, False)
        self.window.configure(bg=app.colors['bg'])
        
        # Header
        header_frame = ttk.Frame(self.window, style='Toolbar.TFrame')
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        title_label = ttk.Label(header_frame, 
                                text="Application Settings", 
                                style='Title.TLabel')
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Main frame
        frame = ttk.Frame(self.window, style='Card.TFrame', padding="25")
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Auto-boost settings card
        settings_card = ttk.LabelFrame(frame, text="⚡ Auto-Boost Settings", 
                                      padding=20, style='Card.TFrame')
        settings_card.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Enable checkbox
        self.auto_boost_var = tk.BooleanVar(value=app.auto_boost_enabled)
        check_frame = ttk.Frame(settings_card, style='Card.TFrame')
        check_frame.pack(fill=tk.X, pady=10)
        
        ttk.Checkbutton(check_frame, text="Enable Auto-Boost", 
                       variable=self.auto_boost_var,
                       font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W)
        
        # Threshold setting
        threshold_frame = ttk.Frame(settings_card, style='Card.TFrame')
        threshold_frame.pack(fill=tk.X, pady=15)
        
        ttk.Label(threshold_frame, text="Auto-Boost Threshold (Score):", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        self.threshold_var = tk.StringVar(value=str(app.auto_boost_threshold))
        threshold_entry = ttk.Entry(threshold_frame, textvariable=self.threshold_var, 
                                    width=25, font=('Segoe UI', 10))
        threshold_entry.pack(anchor=tk.W, pady=5)
        
        # Priority level setting
        priority_frame = ttk.Frame(settings_card, style='Card.TFrame')
        priority_frame.pack(fill=tk.X, pady=15)
        
        ttk.Label(priority_frame, text="Auto-Boost Priority Level:", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        priority_map = PRIORITY_LEVELS['Windows'] if sys.platform == 'win32' else PRIORITY_LEVELS['Linux']
        self.priority_var = tk.StringVar(value=app.auto_boost_level)
        priority_combo = ttk.Combobox(priority_frame, textvariable=self.priority_var, 
                                     values=list(priority_map.keys()), 
                                     state='readonly', width=25, font=('Segoe UI', 10))
        priority_combo.pack(anchor=tk.W, pady=5)
        
        # Buttons with enhanced styling
        button_frame = ttk.Frame(frame, style='Card.TFrame')
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="💾 Save", 
                  command=self.save_settings,
                  style='Success.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="❌ Cancel", 
                  command=self.window.destroy,
                  style='Danger.TButton').pack(side=tk.LEFT, padx=10)
    
    def save_settings(self):
        """Save settings and update application."""
        try:
            self.app.auto_boost_enabled = self.auto_boost_var.get()
            self.app.auto_boost_threshold = float(self.threshold_var.get())
            self.app.auto_boost_level = self.priority_var.get()
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid threshold value. Please enter a number.")


class AdaptiveProcessBooster:
    """
    Main GUI application class for Adaptive Process Booster - Advanced Edition
    """
    
    def __init__(self, root):
        """
        Initialize the GUI application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Adaptive Process Booster - Advanced Edition")
        self.root.geometry("1400x800")
        self.root.resizable(True, True)
        
        # Modern color scheme
        self.colors = {
            'primary': '#2E86AB',      # Blue
            'secondary': '#06A77D',     # Green
            'accent': '#F18F01',        # Orange
            'danger': '#E74C3C',        # Red
            'success': '#27AE60',       # Green
            'warning': '#F39C12',      # Yellow
            'dark': '#2C3E50',         # Dark gray
            'light': '#ECF0F1',        # Light gray
            'bg': '#FFFFFF',            # White
            'card': '#F8F9FA'           # Card background
        }
        
        # Application state
        self.monitoring_active = True
        self.monitoring_thread = None
        self.selected_pid = None
        self.pause_updates = False
        
        # Settings
        self.auto_boost_enabled = False
        self.auto_boost_threshold = 50.0
        self.auto_boost_level = 'High'
        
        # History and logging
        self.action_history = deque(maxlen=100)
        self.process_history = {}
        
        # System stats history for graphs
        self.cpu_history = deque(maxlen=60)
        self.memory_history = deque(maxlen=60)
        
        # Search/filter
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        
        # Setup modern styling
        self.setup_styles()
        
        # Setup GUI
        self.setup_gui()
        self.start_monitoring()
    
    def setup_styles(self):
        """Setup modern ttk styles for enhanced appearance."""
        style = ttk.Style()
        
        # Try to use a modern theme
        try:
            style.theme_use('clam')  # Modern theme
        except:
            style.theme_use('default')
        
        # Configure styles
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       foreground=self.colors['dark'],
                       background=self.colors['bg'])
        
        style.configure('Heading.TLabel',
                       font=('Segoe UI', 12, 'bold'),
                       foreground=self.colors['primary'],
                       background=self.colors['bg'])
        
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       foreground='white',
                       background=self.colors['primary'],
                       padding=10)
        
        style.map('Primary.TButton',
                 background=[('active', '#1E6A8E'), ('pressed', '#155A7A')])
        
        style.configure('Success.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       foreground='white',
                       background=self.colors['success'],
                       padding=10)
        
        style.map('Success.TButton',
                 background=[('active', '#229954'), ('pressed', '#1E8449')])
        
        style.configure('Danger.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       foreground='white',
                       background=self.colors['danger'],
                       padding=10)
        
        style.map('Danger.TButton',
                 background=[('active', '#C0392B'), ('pressed', '#A93226')])
        
        style.configure('Card.TFrame',
                       background=self.colors['card'],
                       relief='flat',
                       borderwidth=1)
        
        style.configure('Toolbar.TFrame',
                       background=self.colors['light'],
                       relief='flat')
        
        # Enhanced Notebook style
        style.configure('TNotebook',
                      background=self.colors['bg'],
                      borderwidth=0)
        
        style.configure('TNotebook.Tab',
                       font=('Segoe UI', 10, 'bold'),
                       padding=[20, 10],
                       background=self.colors['light'],
                       foreground=self.colors['dark'])
        
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['primary']),
                           ('active', '#D5DBDB')],
                 foreground=[('selected', 'white'),
                           ('active', self.colors['dark'])])
        
        # Enhanced Treeview
        style.configure('Treeview',
                       font=('Segoe UI', 9),
                       rowheight=25,
                       background='white',
                       foreground=self.colors['dark'],
                       fieldbackground='white')
        
        style.configure('Treeview.Heading',
                       font=('Segoe UI', 10, 'bold'),
                       background=self.colors['primary'],
                       foreground='white',
                       relief='flat')
        
        style.map('Treeview',
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', 'white')])
        
        # Enhanced Entry
        style.configure('TEntry',
                       font=('Segoe UI', 10),
                       fieldbackground='white',
                       borderwidth=2,
                       relief='solid',
                       padding=5)
        
        style.map('TEntry',
                 bordercolor=[('focus', self.colors['primary'])])
        
        # Enhanced Combobox
        style.configure('TCombobox',
                       font=('Segoe UI', 10),
                       fieldbackground='white',
                       borderwidth=2,
                       padding=5)
        
        # Enhanced Progressbar - use default style, update colors dynamically
        style.configure('TProgressbar',
                       background=self.colors['primary'],
                       troughcolor=self.colors['light'],
                       borderwidth=0,
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'])
        
        # Set root background
        self.root.configure(bg=self.colors['bg'])
    
    def setup_gui(self):
        """Setup all GUI components with advanced features."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Process Monitor
        self.setup_process_tab()
        
        # Tab 2: System Resources
        self.setup_system_tab()
        
        # Tab 3: History & Logs
        self.setup_history_tab()
        
        # Menu bar
        self.setup_menu()
    
    def setup_menu(self):
        """Setup menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export to CSV...", command=self.export_to_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Settings", command=self.open_settings)
        tools_menu.add_command(label="Clear History", command=self.clear_history)
    
    def setup_process_tab(self):
        """Setup the main process monitoring tab."""
        process_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(process_frame, text="📊 Process Monitor")
        
        # Header section with title
        header_frame = ttk.Frame(process_frame, style='Toolbar.TFrame')
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        title_label = ttk.Label(header_frame, 
                                text="Process Management Dashboard", 
                                style='Title.TLabel')
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Top toolbar with enhanced styling
        toolbar = ttk.Frame(process_frame, style='Toolbar.TFrame')
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        # Search section
        search_frame = ttk.Frame(toolbar, style='Toolbar.TFrame')
        search_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(search_frame, text="🔍 Search:", 
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, 
                                width=35, font=('Segoe UI', 10))
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Sort section
        sort_frame = ttk.Frame(toolbar, style='Toolbar.TFrame')
        sort_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        ttk.Label(sort_frame, text="📈 Sort by:", 
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.sort_var = tk.StringVar(value="Score")
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var, 
                                 values=["Score", "CPU %", "RAM %", "PID", "Name"], 
                                 state='readonly', width=18, font=('Segoe UI', 10))
        sort_combo.pack(side=tk.LEFT, padx=5)
        sort_combo.bind('<<ComboboxSelected>>', lambda e: self.update_process_list(self.last_process_data))
        
        # Filter section
        filter_frame = ttk.Frame(toolbar, style='Toolbar.TFrame')
        filter_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        ttk.Label(filter_frame, text="🔽 Filter:", 
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                   values=["All", "High CPU (>50%)", "High RAM (>50%)", "High Score (>50)"], 
                                   state='readonly', width=18, font=('Segoe UI', 10))
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.update_process_list(self.last_process_data))
        
        # Treeview frame
        tree_frame = ttk.Frame(process_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview
        columns = ('PID', 'Process Name', 'CPU %', 'RAM %', 'Score', 'Status')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=25)
        
        # Configure columns
        self.tree.heading('PID', text='PID', command=lambda: self.sort_column('PID'))
        self.tree.heading('Process Name', text='Process Name', command=lambda: self.sort_column('Process Name'))
        self.tree.heading('CPU %', text='CPU %', command=lambda: self.sort_column('CPU %'))
        self.tree.heading('RAM %', text='RAM %', command=lambda: self.sort_column('RAM %'))
        self.tree.heading('Score', text='Score', command=lambda: self.sort_column('Score'))
        self.tree.heading('Status', text='Status')
        
        self.tree.column('PID', width=80, anchor='center')
        self.tree.column('Process Name', width=300, anchor='w')
        self.tree.column('CPU %', width=100, anchor='center')
        self.tree.column('RAM %', width=100, anchor='center')
        self.tree.column('Score', width=100, anchor='center')
        self.tree.column('Status', width=100, anchor='center')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_process_select)
        self.tree.bind('<Button-1>', self.on_tree_click)
        self.tree.bind('<Button-3>', self.show_context_menu)
        self.tree.bind('<Double-Button-1>', self.on_double_click)
        
        # Button frame with enhanced styling
        button_frame = ttk.Frame(process_frame, style='Card.TFrame')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Action buttons with modern styling
        button_container = ttk.Frame(button_frame, style='Card.TFrame')
        button_container.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.boost_button = ttk.Button(button_container, 
                                       text="⚡ Boost Process", 
                                       command=self.boost_selected_process, 
                                       state='disabled',
                                       style='Primary.TButton')
        self.boost_button.pack(side=tk.LEFT, padx=5)
        
        details_btn = ttk.Button(button_container, 
                                text="ℹ️ View Details", 
                                command=self.view_process_details, 
                                state='disabled',
                                style='Success.TButton')
        details_btn.pack(side=tk.LEFT, padx=5)
        self.details_button = details_btn
        
        kill_btn = ttk.Button(button_container, 
                            text="🗑️ Kill Process", 
                            command=self.kill_selected_process, 
                            state='disabled',
                            style='Danger.TButton')
        kill_btn.pack(side=tk.LEFT, padx=5)
        self.kill_button = kill_btn
        
        # Status label with enhanced styling
        status_frame = ttk.Frame(button_frame, style='Card.TFrame')
        status_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        status_icon = ttk.Label(status_frame, text="📊", font=('Segoe UI', 12))
        status_icon.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(status_frame, 
                                     text="Status: Ready | Select a process", 
                                     font=('Segoe UI', 10, 'bold'),
                                     foreground=self.colors['dark'])
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Store last process data for filtering/sorting
        self.last_process_data = []
        self.sort_reverse = False
    
    def setup_system_tab(self):
        """Setup system resources monitoring tab with enhanced visuals."""
        system_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(system_frame, text="💻 System Resources")
        
        # Header
        header_frame = ttk.Frame(system_frame, style='Toolbar.TFrame')
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        title_label = ttk.Label(header_frame, 
                                text="System Resource Monitor", 
                                style='Title.TLabel')
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Main container with cards
        main_container = ttk.Frame(system_frame, style='Card.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # CPU Card
        cpu_card = ttk.LabelFrame(main_container, text="🖥️ CPU Usage", 
                                 padding=15, style='Card.TFrame')
        cpu_card.pack(fill=tk.X, pady=10)
        
        cpu_top = ttk.Frame(cpu_card, style='Card.TFrame')
        cpu_top.pack(fill=tk.X, pady=5)
        
        ttk.Label(cpu_top, text="CPU Usage:", 
                 font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        self.cpu_label = ttk.Label(cpu_top, text="0.0%", 
                                 font=('Segoe UI', 14, 'bold'),
                                 foreground=self.colors['primary'])
        self.cpu_label.pack(side=tk.LEFT, padx=10)
        
        self.cpu_progress = ttk.Progressbar(cpu_card, length=600, mode='determinate')
        self.cpu_progress.pack(fill=tk.X, pady=10, padx=5)
        
        # Memory Card
        mem_card = ttk.LabelFrame(main_container, text="💾 Memory Usage", 
                                  padding=15, style='Card.TFrame')
        mem_card.pack(fill=tk.X, pady=10)
        
        mem_top = ttk.Frame(mem_card, style='Card.TFrame')
        mem_top.pack(fill=tk.X, pady=5)
        
        ttk.Label(mem_top, text="Memory Usage:", 
                 font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        self.mem_label = ttk.Label(mem_top, text="0.0% (0 GB / 0 GB)", 
                                  font=('Segoe UI', 12, 'bold'),
                                  foreground=self.colors['secondary'])
        self.mem_label.pack(side=tk.LEFT, padx=10)
        
        self.mem_progress = ttk.Progressbar(mem_card, length=600, mode='determinate')
        self.mem_progress.pack(fill=tk.X, pady=10, padx=5)
        
        # Disk Card
        disk_card = ttk.LabelFrame(main_container, text="💿 Disk Usage", 
                                   padding=15, style='Card.TFrame')
        disk_card.pack(fill=tk.X, pady=10)
        
        disk_top = ttk.Frame(disk_card, style='Card.TFrame')
        disk_top.pack(fill=tk.X, pady=5)
        
        ttk.Label(disk_top, text="Disk Usage:", 
                 font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        self.disk_label = ttk.Label(disk_top, text="0.0% (0 GB / 0 GB)", 
                                    font=('Segoe UI', 12, 'bold'),
                                    foreground=self.colors['accent'])
        self.disk_label.pack(side=tk.LEFT, padx=10)
        
        self.disk_progress = ttk.Progressbar(disk_card, length=600, mode='determinate')
        self.disk_progress.pack(fill=tk.X, pady=10, padx=5)
        
        # Process Count Card
        proc_card = ttk.LabelFrame(main_container, text="📋 Process Information", 
                                   padding=15, style='Card.TFrame')
        proc_card.pack(fill=tk.X, pady=10)
        
        proc_frame = ttk.Frame(proc_card, style='Card.TFrame')
        proc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(proc_frame, text="Running Processes:", 
                 font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        self.proc_count_label = ttk.Label(proc_frame, text="0", 
                                          font=('Segoe UI', 16, 'bold'),
                                          foreground=self.colors['dark'])
        self.proc_count_label.pack(side=tk.LEFT, padx=10)
    
    def setup_history_tab(self):
        """Setup history and logs tab with enhanced styling."""
        history_frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(history_frame, text="📜 History & Logs")
        
        # Header
        header_frame = ttk.Frame(history_frame, style='Toolbar.TFrame')
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        title_label = ttk.Label(header_frame, 
                                text="Action History & Logs", 
                                style='Title.TLabel')
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # History text widget with enhanced styling
        text_frame = ttk.Frame(history_frame, style='Card.TFrame', padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.history_text = tk.Text(text_frame, wrap=tk.WORD, 
                                   font=("Consolas", 10),
                                   bg='#F8F9FA',
                                   fg=self.colors['dark'],
                                   insertbackground=self.colors['primary'],
                                   selectbackground=self.colors['primary'],
                                   selectforeground='white',
                                   relief='flat',
                                   borderwidth=2,
                                   padx=10,
                                   pady=10)
        history_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", 
                                         command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons with enhanced styling
        button_frame = ttk.Frame(history_frame, style='Card.TFrame', padding="10")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="🗑️ Clear History", 
                  command=self.clear_history,
                  style='Danger.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="💾 Export Logs", 
                  command=self.export_logs,
                  style='Success.TButton').pack(side=tk.LEFT, padx=10)
    
    def on_search_change(self, *args):
        """Handle search text change."""
        if hasattr(self, 'last_process_data'):
            self.update_process_list(self.last_process_data)
    
    def sort_column(self, column):
        """Sort treeview by column."""
        self.sort_reverse = not self.sort_reverse
        if hasattr(self, 'last_process_data'):
            self.update_process_list(self.last_process_data)
    
    def on_tree_click(self, event):
        """Pause updates during user interaction."""
        self.pause_updates = True
        self.root.after(500, lambda: setattr(self, 'pause_updates', False))
    
    def show_context_menu(self, event):
        """Show right-click context menu."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="View Details", command=self.view_process_details)
            menu.add_command(label="Boost Process", command=self.boost_selected_process)
            menu.add_separator()
            menu.add_command(label="Kill Process", command=self.kill_selected_process)
            menu.post(event.x_root, event.y_root)
    
    def on_double_click(self, event):
        """Handle double-click to view details."""
        self.view_process_details()
    
    def on_process_select(self, event):
        """Handle process selection."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            if values:
                self.selected_pid = int(values[0])
                self.boost_button.config(state='normal')
                self.details_button.config(state='normal')
                self.kill_button.config(state='normal')
                self.status_label.config(text=f"Status: Process {self.selected_pid} selected")
        else:
            self.selected_pid = None
            self.boost_button.config(state='disabled')
            self.details_button.config(state='disabled')
            self.kill_button.config(state='disabled')
            self.status_label.config(text="Status: No process selected")
    
    def boost_selected_process(self):
        """Boost selected process with priority selection."""
        if self.selected_pid is None:
            messagebox.showwarning("No Selection", "Please select a process first.")
            return
        
        # Priority selection dialog
        priority_map = PRIORITY_LEVELS['Windows'] if sys.platform == 'win32' else PRIORITY_LEVELS['Linux']
        priority = simpledialog.askstring("Priority Level", f"Select priority level:\n{', '.join(priority_map.keys())}\n\nEnter priority (default: High):")
        
        if priority is None:
            return
        
        if priority not in priority_map:
            priority = 'High'
        
        try:
            success = boost_process_priority(self.selected_pid, priority)
            if success:
                messagebox.showinfo("Success", f"Process {self.selected_pid} priority set to {priority}!")
                self.log_action(f"Boosted PID {self.selected_pid} to {priority} priority")
                self.status_label.config(text=f"Status: Process {self.selected_pid} boosted to {priority}")
            else:
                messagebox.showerror("Error", f"Failed to boost process {self.selected_pid}.")
                self.log_action(f"Failed to boost PID {self.selected_pid}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def view_process_details(self):
        """Open process details window."""
        if self.selected_pid is None:
            messagebox.showwarning("No Selection", "Please select a process first.")
            return
        ProcessDetailsWindow(self.root, self.selected_pid)
    
    def kill_selected_process(self):
        """Kill selected process with confirmation."""
        if self.selected_pid is None:
            messagebox.showwarning("No Selection", "Please select a process first.")
            return
        
        if not messagebox.askyesno("Confirm", f"Are you sure you want to kill process {self.selected_pid}?"):
            return
        
        try:
            success = kill_process(self.selected_pid)
            if success:
                messagebox.showinfo("Success", f"Process {self.selected_pid} terminated.")
                self.log_action(f"Killed PID {self.selected_pid}")
                self.status_label.config(text=f"Status: Process {self.selected_pid} terminated")
            else:
                messagebox.showerror("Error", f"Failed to kill process {self.selected_pid}.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def update_process_list(self, processes_data):
        """Update process list with filtering and sorting."""
        if self.pause_updates:
            return
        
        self.last_process_data = processes_data.copy()
        selected_pid_before = self.selected_pid
        scroll_position = self.tree.yview()
        
        # Apply search filter
        search_text = self.search_var.get().lower()
        if search_text:
            processes_data = [p for p in processes_data if search_text in p['name'].lower() or search_text in str(p['pid'])]
        
        # Apply filter
        filter_type = self.filter_var.get()
        if filter_type == "High CPU (>50%)":
            processes_data = [p for p in processes_data if p['cpu'] > 50]
        elif filter_type == "High RAM (>50%)":
            processes_data = [p for p in processes_data if p['ram'] > 50]
        elif filter_type == "High Score (>50)":
            processes_data = [p for p in processes_data if p['score'] > 50]
        
        # Sort
        sort_by = self.sort_var.get()
        reverse = self.sort_reverse if sort_by != "Score" else True
        if sort_by == "Score":
            processes_data.sort(key=lambda x: x['score'], reverse=reverse)
        elif sort_by == "CPU %":
            processes_data.sort(key=lambda x: x['cpu'], reverse=reverse)
        elif sort_by == "RAM %":
            processes_data.sort(key=lambda x: x['ram'], reverse=reverse)
        elif sort_by == "PID":
            processes_data.sort(key=lambda x: x['pid'], reverse=reverse)
        elif sort_by == "Name":
            processes_data.sort(key=lambda x: x['name'].lower(), reverse=reverse)
        
        # Clear and repopulate
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        selected_item_id = None
        for proc in processes_data:
            pid = proc['pid']
            name = proc['name']
            cpu = f"{proc['cpu']:.2f}"
            ram = f"{proc['ram']:.2f}"
            score = f"{proc['score']:.2f}"
            status = proc.get('status', 'unknown')
            
            item_id = self.tree.insert('', 'end', values=(pid, name, cpu, ram, score, status))
            
            if selected_pid_before is not None and pid == selected_pid_before:
                selected_item_id = item_id
        
        if selected_item_id:
            self.tree.selection_set(selected_item_id)
            self.tree.see(selected_item_id)
        elif selected_pid_before is not None:
            self.selected_pid = None
            self.boost_button.config(state='disabled')
            self.details_button.config(state='disabled')
            self.kill_button.config(state='disabled')
        
        if selected_item_id is None:
            try:
                self.tree.yview_moveto(scroll_position[0])
            except:
                pass
    
    def update_system_stats(self, stats):
        """Update system statistics display with dynamic colors."""
        try:
            # CPU with dynamic color
            cpu_percent = stats['cpu']
            self.cpu_label.config(text=f"{cpu_percent:.1f}%")
            self.cpu_progress['value'] = cpu_percent
            
            # Change CPU label color based on usage
            if cpu_percent > 80:
                cpu_color = self.colors['danger']
            elif cpu_percent > 50:
                cpu_color = self.colors['warning']
            else:
                cpu_color = self.colors['success']
            
            self.cpu_label.config(foreground=cpu_color)
            self.cpu_history.append(cpu_percent)
            
            # Memory with dynamic color
            mem_percent = stats['memory_percent']
            mem_used_gb = stats['memory_used'] / (1024**3)
            mem_total_gb = stats['memory_total'] / (1024**3)
            self.mem_label.config(text=f"{mem_percent:.1f}% ({mem_used_gb:.2f} GB / {mem_total_gb:.2f} GB)")
            self.mem_progress['value'] = mem_percent
            
            # Change Memory label color based on usage
            if mem_percent > 80:
                mem_color = self.colors['danger']
            elif mem_percent > 50:
                mem_color = self.colors['warning']
            else:
                mem_color = self.colors['secondary']
            
            self.mem_label.config(foreground=mem_color)
            self.memory_history.append(mem_percent)
            
            # Disk with dynamic color
            disk_percent = stats['disk_percent']
            disk_used_gb = stats['disk_used'] / (1024**3)
            disk_total_gb = stats['disk_total'] / (1024**3)
            self.disk_label.config(text=f"{disk_percent:.1f}% ({disk_used_gb:.2f} GB / {disk_total_gb:.2f} GB)")
            self.disk_progress['value'] = disk_percent
            
            # Change Disk label color based on usage
            if disk_percent > 80:
                disk_color = self.colors['danger']
            elif disk_percent > 50:
                disk_color = self.colors['warning']
            else:
                disk_color = self.colors['accent']
            
            self.disk_label.config(foreground=disk_color)
            
            # Process count
            if hasattr(self, 'last_process_data'):
                self.proc_count_label.config(text=str(len(self.last_process_data)))
        except Exception as e:
            # Fallback to basic update if styling fails
            try:
                cpu_percent = stats.get('cpu', 0)
                mem_percent = stats.get('memory_percent', 0)
                disk_percent = stats.get('disk_percent', 0)
                
                self.cpu_label.config(text=f"{cpu_percent:.1f}%")
                self.cpu_progress['value'] = cpu_percent
                
                mem_used_gb = stats.get('memory_used', 0) / (1024**3)
                mem_total_gb = stats.get('memory_total', 0) / (1024**3)
                self.mem_label.config(text=f"{mem_percent:.1f}% ({mem_used_gb:.2f} GB / {mem_total_gb:.2f} GB)")
                self.mem_progress['value'] = mem_percent
                
                disk_used_gb = stats.get('disk_used', 0) / (1024**3)
                disk_total_gb = stats.get('disk_total', 0) / (1024**3)
                self.disk_label.config(text=f"{disk_percent:.1f}% ({disk_used_gb:.2f} GB / {disk_total_gb:.2f} GB)")
                self.disk_progress['value'] = disk_percent
            except:
                pass
    
    def log_action(self, message):
        """Log an action to history."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.action_history.append(log_entry)
        
        # Update history tab
        if hasattr(self, 'history_text'):
            self.history_text.insert(tk.END, log_entry)
            self.history_text.see(tk.END)
    
    def clear_history(self):
        """Clear action history."""
        if messagebox.askyesno("Confirm", "Clear all history?"):
            self.action_history.clear()
            if hasattr(self, 'history_text'):
                self.history_text.delete("1.0", tk.END)
    
    def export_to_csv(self):
        """Export process list to CSV file."""
        if not hasattr(self, 'last_process_data') or not self.last_process_data:
            messagebox.showwarning("No Data", "No process data to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['PID', 'Process Name', 'CPU %', 'RAM %', 'Score', 'Status'])
                    for proc in self.last_process_data:
                        writer.writerow([
                            proc['pid'],
                            proc['name'],
                            f"{proc['cpu']:.2f}",
                            f"{proc['ram']:.2f}",
                            f"{proc['score']:.2f}",
                            proc.get('status', 'unknown')
                        ])
                messagebox.showinfo("Success", f"Data exported to {filename}")
                self.log_action(f"Exported process data to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def export_logs(self):
        """Export logs to text file."""
        if not self.action_history:
            messagebox.showwarning("No Logs", "No logs to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.writelines(self.action_history)
                messagebox.showinfo("Success", f"Logs exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def open_settings(self):
        """Open settings window."""
        SettingsWindow(self.root, self)
    
    def start_monitoring(self):
        """Start background monitoring thread."""
        self.monitoring_thread = threading.Thread(target=monitor_processes, args=(self,), daemon=True)
        self.monitoring_thread.start()
        self.log_action("Application started - Monitoring active")
    
    def on_closing(self):
        """Handle window closing."""
        self.monitoring_active = False
        self.log_action("Application closed")
        self.root.destroy()


def main():
    """Main entry point."""
    if sys.platform == 'win32':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print("Warning: Running without administrator privileges.")
                print("Some processes may not be boostable.")
        except:
            pass
    
    root = tk.Tk()
    app = AdaptiveProcessBooster(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
