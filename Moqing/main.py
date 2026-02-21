import pygame
import sys
import re
from enum import Enum
import math
import os
from pathlib import Path
import keyword
import builtins
from collections import deque
import pygame.locals as pl
from tkinter import filedialog, Tk
import tkinter as tk

# Initialize Pygame
pygame.init()

# Initialize clipboard safely
try:
    pygame.scrap.init()
    CLIPBOARD_AVAILABLE = True
except:
    CLIPBOARD_AVAILABLE = False
    print("Warning: Clipboard system not available - using internal clipboard only")

# Window settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Moqing Editor - Professional Edition")
clock = pygame.time.Clock()

# Hide the main tkinter window
root = tk.Tk()
root.withdraw()

# Colors - Professional Dark Theme
BG_PRIMARY = (18, 18, 22)
BG_SECONDARY = (28, 28, 34)
BG_TERTIARY = (38, 38, 44)
TEXT_PRIMARY = (220, 220, 240)
TEXT_SECONDARY = (160, 160, 180)
ACCENT_BLUE = (86, 156, 214)
ACCENT_GREEN = (106, 190, 140)
ACCENT_ORANGE = (206, 145, 90)
ACCENT_PURPLE = (197, 134, 192)
ACCENT_YELLOW = (220, 220, 170)
ACCENT_CYAN = (78, 201, 176)
SELECTION_COLOR = (55, 85, 115, 80)
COMMENT_COLOR = (87, 96, 110)


# Syntax colors by language
class SyntaxColors:
    # Python
    PYTHON_KEYWORD = (255, 119, 153)  # Pink
    PYTHON_STRING = (174, 219, 127)  # Green
    PYTHON_COMMENT = (143, 151, 164)  # Gray
    PYTHON_FUNCTION = (97, 175, 239)  # Blue
    PYTHON_CLASS = (229, 192, 123)  # Gold
    PYTHON_NUMBER = (181, 142, 240)  # Purple
    PYTHON_OPERATOR = (255, 153, 102)  # Orange

    # JavaScript
    JS_KEYWORD = (255, 89, 153)  # Pink
    JS_STRING = (158, 227, 99)  # Green
    JS_COMMENT = (128, 138, 158)  # Gray
    JS_FUNCTION = (87, 173, 255)  # Blue
    JS_NUMBER = (189, 147, 249)  # Purple
    JS_OPERATOR = (255, 153, 102)  # Orange

    # HTML/CSS
    HTML_TAG = (255, 123, 114)  # Coral
    HTML_ATTR = (165, 214, 167)  # Mint
    CSS_PROPERTY = (173, 216, 255)  # Light blue
    CSS_VALUE = (255, 215, 140)  # Peach

    # Java
    JAVA_KEYWORD = (204, 120, 255)  # Purple
    JAVA_STRING = (174, 219, 127)  # Green
    JAVA_COMMENT = (128, 138, 158)  # Gray
    JAVA_ANNOTATION = (108, 188, 230)  # Cyan


class Language(Enum):
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    HTML = "HTML"
    CSS = "CSS"
    JAVA = "Java"
    UNKNOWN = "Unknown"


class SyntaxHighlighter:
    """Professional syntax highlighting with language detection"""

    # Language patterns
    PATTERNS = {
        Language.PYTHON: {
            'keywords': r'\b(def|class|if|else|elif|for|while|return|import|from|as|try|except|finally|with|lambda|yield|async|await|True|False|None|and|or|not|is|in|global|nonlocal|assert|break|continue|pass|raise|del)\b',
            'strings': r'(\".*?\"|\'.*?\')',
            'comments': r'#.*$',
            'decorators': r'@\w+',
            'numbers': r'\b\d+\b',
            'functions': r'\b\w+(?=\()',
            'classes': r'\b[A-Z][a-zA-Z0-9]*\b',
            'operators': r'[+\-*/%=<>!&|^~]+'
        },
        Language.JAVASCRIPT: {
            'keywords': r'\b(function|const|let|var|if|else|for|while|return|import|export|from|default|class|extends|super|this|new|try|catch|finally|throw|switch|case|break|continue|typeof|instanceof|void|delete|in|of|yield|async|await|Promise|true|false|null|undefined)\b',
            'strings': r'(\".*?\"|\'.*?\'|`.*?`)',
            'comments': r'//.*$|/\*[\s\S]*?\*/',
            'numbers': r'\b\d+\b',
            'functions': r'\b\w+(?=\()',
            'operators': r'[+\-*/%=<>!&|^~?:]+'
        },
        Language.HTML: {
            'tags': r'</?[a-z][a-z0-9]*[^>]*>',
            'attributes': r'\b[a-z-]+(?==)',
            'strings': r'(\".*?\"|\'.*?\')',
            'comments': r'<!--[\s\S]*?-->'
        },
        Language.CSS: {
            'properties': r'[a-z-]+(?=\s*:)',
            'values': r':\s*[^;]+',
            'selectors': r'[.#]?[a-zA-Z][a-zA-Z0-9_-]*\s*[{,]',
            'comments': r'/\*[\s\S]*?\*/'
        },
        Language.JAVA: {
            'keywords': r'\b(public|private|protected|class|interface|enum|extends|implements|static|final|abstract|synchronized|volatile|transient|native|strictfp|if|else|for|while|do|switch|case|default|break|continue|return|throw|throws|try|catch|finally|import|package|new|this|super|instanceof|true|false|null|void|int|float|double|boolean|char|byte|short|long|String)\b',
            'strings': r'(\".*?\"|\'.*?\')',
            'comments': r'//.*$|/\*[\s\S]*?\*/',
            'annotations': r'@\w+',
            'numbers': r'\b\d+\b',
            'operators': r'[+\-*/%=<>!&|^~]+'
        }
    }

    @classmethod
    def detect_language(cls, text):
        """Intelligently detect programming language from text"""
        if not text:
            return Language.PYTHON

        # Strong indicators
        if re.search(r'^\s*@\w+|\s*def\s+\w+\s*\(', text, re.MULTILINE):
            return Language.PYTHON
        if re.search(r'^\s*function\s+\w+\(|const\s+\w+\s*=\s*\(|=>', text, re.MULTILINE):
            return Language.JAVASCRIPT
        if re.search(r'<html|<div|<span|<body', text, re.IGNORECASE):
            return Language.HTML
        if re.search(r'{[^}]*:[^;]*;|\.[a-zA-Z][^{]*\{', text):
            return Language.CSS
        if re.search(r'public\s+class|private\s+\w+|void\s+\w+\(', text):
            return Language.JAVA

        return Language.PYTHON  # Default

    @classmethod
    def highlight_line(cls, line, language):
        """Apply syntax highlighting to a line of code"""
        if language == Language.UNKNOWN:
            language = cls.detect_language(line)

        if language not in cls.PATTERNS:
            return [((0, len(line)), TEXT_PRIMARY)]

        patterns = cls.PATTERNS[language]
        highlights = []

        # Apply language-specific highlighting
        if language == Language.PYTHON:
            # Keywords
            for match in re.finditer(patterns['keywords'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_KEYWORD))
            # Strings
            for match in re.finditer(patterns['strings'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_STRING))
            # Comments
            for match in re.finditer(patterns['comments'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_COMMENT))
            # Numbers
            for match in re.finditer(patterns['numbers'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_NUMBER))
            # Functions
            for match in re.finditer(patterns['functions'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_FUNCTION))
            # Operators
            for match in re.finditer(patterns['operators'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_OPERATOR))

        elif language == Language.JAVASCRIPT:
            for match in re.finditer(patterns['keywords'], line):
                highlights.append((match.span(), SyntaxColors.JS_KEYWORD))
            for match in re.finditer(patterns['strings'], line):
                highlights.append((match.span(), SyntaxColors.JS_STRING))
            for match in re.finditer(patterns['comments'], line):
                highlights.append((match.span(), SyntaxColors.JS_COMMENT))
            for match in re.finditer(patterns['numbers'], line):
                highlights.append((match.span(), SyntaxColors.JS_NUMBER))
            for match in re.finditer(patterns['functions'], line):
                highlights.append((match.span(), SyntaxColors.JS_FUNCTION))

        elif language == Language.HTML:
            for match in re.finditer(patterns['tags'], line):
                highlights.append((match.span(), SyntaxColors.HTML_TAG))
            for match in re.finditer(patterns['attributes'], line):
                highlights.append((match.span(), SyntaxColors.HTML_ATTR))
            for match in re.finditer(patterns['strings'], line):
                highlights.append((match.span(), SyntaxColors.JS_STRING))

        elif language == Language.CSS:
            for match in re.finditer(patterns['properties'], line):
                highlights.append((match.span(), SyntaxColors.CSS_PROPERTY))
            for match in re.finditer(patterns['values'], line):
                highlights.append((match.span(), SyntaxColors.CSS_VALUE))

        elif language == Language.JAVA:
            for match in re.finditer(patterns['keywords'], line):
                highlights.append((match.span(), SyntaxColors.JAVA_KEYWORD))
            for match in re.finditer(patterns['strings'], line):
                highlights.append((match.span(), SyntaxColors.JAVA_STRING))
            for match in re.finditer(patterns['comments'], line):
                highlights.append((match.span(), SyntaxColors.JAVA_COMMENT))
            for match in re.finditer(patterns['annotations'], line):
                highlights.append((match.span(), SyntaxColors.JAVA_ANNOTATION))

        # Sort by position and merge
        highlights.sort(key=lambda x: x[0][0])

        # Fill gaps with default color
        result = []
        pos = 0
        for (start, end), color in highlights:
            if start > pos:
                result.append(((pos, start), TEXT_PRIMARY))
            result.append(((start, end), color))
            pos = end
        if pos < len(line):
            result.append(((pos, len(line)), TEXT_PRIMARY))

        return result


class CodeCompleter:
    """Intelligent code completion engine"""

    # Python built-in keywords and functions
    PYTHON_KEYWORDS = keyword.kwlist
    PYTHON_BUILTINS = dir(builtins)

    # Common libraries and their functions
    COMMON_LIBS = {
        'os': ['listdir', 'path', 'getcwd', 'chdir', 'mkdir', 'remove', 'rename', 'walk'],
        'sys': ['argv', 'path', 'exit', 'version', 'platform'],
        're': ['match', 'search', 'findall', 'sub', 'split', 'compile'],
        'json': ['load', 'loads', 'dump', 'dumps'],
        'math': ['sin', 'cos', 'tan', 'sqrt', 'pow', 'log', 'pi', 'e'],
        'random': ['randint', 'choice', 'shuffle', 'random', 'uniform'],
        'datetime': ['datetime', 'date', 'time', 'timedelta'],
        'pygame': ['init', 'display', 'draw', 'event', 'image', 'mixer', 'font'],
        'numpy': ['array', 'zeros', 'ones', 'linspace', 'reshape'],
        'pandas': ['DataFrame', 'Series', 'read_csv', 'to_csv']
    }

    @classmethod
    def get_completions(cls, text, language=Language.PYTHON):
        """Get code completions based on current text"""
        if not text:
            return []

        completions = []

        # Handle module imports
        if '.' in text:
            module, partial = text.rsplit('.', 1)
            if module in cls.COMMON_LIBS:
                completions.extend([f"{module}.{func}" for func in cls.COMMON_LIBS[module]
                                    if func.startswith(partial)])

        # Handle Python completions
        if language == Language.PYTHON:
            # Keywords
            completions.extend([kw for kw in cls.PYTHON_KEYWORDS if kw.startswith(text)])

            # Builtins
            completions.extend([b for b in cls.PYTHON_BUILTINS if b.startswith(text)])

            # Common library names
            completions.extend([lib for lib in cls.COMMON_LIBS.keys() if lib.startswith(text)])

        return sorted(set(completions))[:10]  # Return top 10 completions


class SmoothCursor:
    """Smooth, thin cursor with animation"""

    def __init__(self, x, y, height):
        self.target_x = x
        self.target_y = y
        self.current_x = x
        self.current_y = y
        self.height = height
        self.width = 2  # Thin cursor
        self.alpha = 255
        self.blink_timer = 0
        self.visible = True
        self.speed = 0.3

    def update(self, target_x, target_y):
        """Smooth cursor movement"""
        self.target_x = target_x
        self.target_y = target_y

        # Smooth interpolation
        self.current_x += (self.target_x - self.current_x) * self.speed
        self.current_y += (self.target_y - self.current_y) * self.speed

        # Blinking
        self.blink_timer += 1
        if self.blink_timer > 30:
            self.visible = not self.visible
            self.blink_timer = 0

    def draw(self, screen):
        """Draw smooth thin cursor"""
        if not self.visible:
            return

        # Main cursor (thin)
        cursor_rect = pygame.Rect(
            int(self.current_x),
            int(self.current_y),
            self.width,
            self.height
        )

        # Subtle glow
        for i in range(3, 0, -1):
            alpha = int(20 * math.exp(-i))
            glow_rect = cursor_rect.inflate(i * 2, i)
            pygame.draw.rect(screen, (*ACCENT_BLUE, alpha), glow_rect)

        # Main cursor
        pygame.draw.rect(screen, ACCENT_BLUE, cursor_rect)


class FileManager:
    """Handle file operations"""

    @staticmethod
    def open_file():
        """Open file dialog and read file"""
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Python files", "*.py"),
                ("JavaScript files", "*.js"),
                ("HTML files", "*.html *.htm"),
                ("CSS files", "*.css"),
                ("Java files", "*.java"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return file_path, content
            except Exception as e:
                print(f"Error opening file: {e}")
                return None, None
        return None, None

    @staticmethod
    def save_file(content, current_file=None):
        """Save file dialog"""
        if current_file:
            file_path = current_file
        else:
            file_path = filedialog.asksaveasfilename(
                title="Save File",
                defaultextension=".txt",
                filetypes=[
                    ("Python files", "*.py"),
                    ("JavaScript files", "*.js"),
                    ("HTML files", "*.html"),
                    ("CSS files", "*.css"),
                    ("Java files", "*.java"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return file_path
            except Exception as e:
                print(f"Error saving file: {e}")
                return None
        return None

    @staticmethod
    def save_as_file(content):
        """Save as dialog"""
        return FileManager.save_file(content, None)


class CodeEditor:
    def __init__(self):
        self.lines = [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.current_language = Language.PYTHON
        self.working_directory = os.getcwd()
        self.current_file = None  # Track current file path

        # Text rendering
        self.font = pygame.font.Font(None, 24)
        self.font_height = 30
        self.char_width = 12
        self.line_height = 35
        self.left_margin = 100
        self.top_margin = 60

        # Selection
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.clipboard = ""

        # Code completion
        self.completion_active = False
        self.completions = []
        self.selected_completion = 0
        self.completion_prefix = ""

        # Input method (IME) support
        self.ime_text = ""
        self.ime_active = False
        pygame.key.start_text_input()
        pygame.key.set_text_input_rect(pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

        # Smooth cursor
        cursor_x = self.left_margin
        cursor_y = self.top_margin
        self.cursor = SmoothCursor(cursor_x, cursor_y, self.font_height)

        # Key states for smooth holding
        self.key_states = {}
        self.key_repeat_delay = 200
        self.key_repeat_interval = 30
        self.last_key_time = 0

        # Search functionality
        self.search_active = False
        self.search_query = ""
        self.search_results = []
        self.current_search_index = -1
        self.double_shift_time = 0

        # Viewport
        self.viewport_x = 0
        self.viewport_y = 0
        self.viewport_speed = 0.1

        # Settings panel
        self.settings_visible = False
        self.settings_alpha = 0
        self.settings_options = [
            ("Language", [lang.value for lang in Language]),
            ("Font Size", ["16", "20", "24", "28", "32"]),
            ("Theme", ["Dark", "Light"]),
            ("Working Dir", [self.working_directory]),
            ("Auto Save", ["On", "Off"])
        ]
        self.selected_setting = 0

        # Notification system
        self.notification = None
        self.notification_timer = 0

    def show_notification(self, message, duration=2000):
        """Show a temporary notification"""
        self.notification = message
        self.notification_timer = pygame.time.get_ticks() + duration

    def safe_copy_to_clipboard(self, text):
        """Safely copy text to clipboard with error handling"""
        if CLIPBOARD_AVAILABLE:
            try:
                pygame.scrap.put(pygame.SCRAP_TEXT, text.encode())
                return True
            except:
                # Fall back to internal clipboard
                self.clipboard = text
                return False
        else:
            # Use internal clipboard
            self.clipboard = text
            return False

    def safe_paste_from_clipboard(self):
        """Safely paste text from clipboard with error handling"""
        if CLIPBOARD_AVAILABLE:
            try:
                return pygame.scrap.get(pygame.SCRAP_TEXT).decode()
            except:
                return self.clipboard
        else:
            return self.clipboard

    def handle_event(self, event):
        """Handle input events"""
        if event.type == pygame.KEYDOWN:
            self.handle_keydown(event)
            self.key_states[event.key] = pygame.time.get_ticks()

        elif event.type == pygame.KEYUP:
            if event.key in self.key_states:
                del self.key_states[event.key]
            # Clear completion on escape
            if event.key == pygame.K_ESCAPE:
                self.completion_active = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse_click(event)

        elif event.type == pygame.MOUSEMOTION:
            if self.selecting:
                self.handle_mouse_drag(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            self.selecting = False

        elif event.type == pygame.TEXTINPUT:
            # Handle IME text input
            if not self.search_active:
                self.insert_text(event.text)
                self.update_completions()

        elif event.type == pygame.TEXTEDITING:
            # Handle IME composition
            self.ime_text = event.text
            self.ime_active = True

    def handle_keydown(self, event):
        """Handle key press events"""
        current_time = pygame.time.get_ticks()

        # File operations (Ctrl+O, Ctrl+S)
        if event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.open_file()
        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                self.save_file_as()  # Ctrl+Shift+S = Save As
            else:
                self.save_file()  # Ctrl+S = Save

        # Copy/Paste shortcuts
        elif event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.copy_selection()
        elif event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.paste_clipboard()
        elif event.key == pygame.K_x and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.cut_selection()
        elif event.key == pygame.K_a and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.select_all()

        # Format code (Ctrl+Alt+L)
        elif event.key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_CTRL) and (
                pygame.key.get_mods() & pygame.KMOD_ALT):
            self.format_code()

        # Toggle comment (Ctrl+/)
        elif event.key == pygame.K_SLASH and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.toggle_comment()

        # Double shift detection
        elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
            if current_time - self.double_shift_time < 300:
                self.start_search()
            self.double_shift_time = current_time

        # Settings toggle
        elif event.key == pygame.K_F1:
            self.settings_visible = not self.settings_visible

        # Page Up/Down
        elif event.key == pygame.K_PAGEUP:
            self.page_up()
        elif event.key == pygame.K_PAGEDOWN:
            self.page_down()

        # Completion navigation
        elif self.completion_active:
            if event.key == pygame.K_UP:
                self.selected_completion = max(0, self.selected_completion - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_completion = min(len(self.completions) - 1, self.selected_completion + 1)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_TAB:
                self.apply_completion()
            return

        # Search handling
        if self.search_active:
            if event.key == pygame.K_RETURN:
                self.find_next()
            elif event.key == pygame.K_ESCAPE:
                self.search_active = False
                self.search_query = ""
            elif event.key == pygame.K_BACKSPACE:
                self.search_query = self.search_query[:-1]
                self.update_search()
            return

        # Regular editing
        if event.key == pygame.K_BACKSPACE:
            self.handle_backspace()
        elif event.key == pygame.K_RETURN:
            self.handle_enter()
        elif event.key == pygame.K_TAB:
            if self.completion_active:
                self.apply_completion()
            else:
                self.insert_text("    ")
        elif event.key == pygame.K_LEFT:
            self.move_cursor_left()
            self.completion_active = False
        elif event.key == pygame.K_RIGHT:
            self.move_cursor_right()
            self.completion_active = False
        elif event.key == pygame.K_UP:
            self.move_cursor_up()
            self.completion_active = False
        elif event.key == pygame.K_DOWN:
            self.move_cursor_down()
            self.completion_active = False

        # Detect language after each change
        self.detect_language()

    def handle_mouse_click(self, event):
        """Handle mouse click including Ctrl+Middle button"""
        if event.button == 2 and pygame.key.get_mods() & pygame.KMOD_CTRL:  # Ctrl+Middle click
            # Set viewport center to clicked position
            world_x = event.pos[0] + self.viewport_x
            world_y = event.pos[1] + self.viewport_y

            # Immediately set viewport to center on clicked position
            self.viewport_x = world_x - WINDOW_WIDTH // 2
            self.viewport_y = world_y - WINDOW_HEIGHT // 2
            self.show_notification("Viewport centered")
        else:
            # Normal mouse click handling
            world_x = event.pos[0] + self.viewport_x
            world_y = event.pos[1] + self.viewport_y

            line_idx = int((world_y - self.top_margin) / self.line_height)
            if 0 <= line_idx < len(self.lines):
                self.cursor_y = line_idx
                col = int((world_x - self.left_margin) / self.char_width)
                self.cursor_x = max(0, min(col, len(self.lines[line_idx])))

                # Start selection
                self.selecting = True
                self.selection_start = (self.cursor_y, self.cursor_x)
                self.selection_end = None

    def open_file(self):
        """Open a file"""
        file_path, content = FileManager.open_file()
        if file_path and content is not None:
            self.lines = content.splitlines()
            if not self.lines:  # Ensure at least one line
                self.lines = [""]
            self.current_file = file_path
            self.cursor_x = 0
            self.cursor_y = 0
            self.working_directory = str(Path(file_path).parent)
            self.detect_language()
            self.show_notification(f"Opened: {os.path.basename(file_path)}")

    def save_file(self):
        """Save current file"""
        content = "\n".join(self.lines)
        file_path = FileManager.save_file(content, self.current_file)
        if file_path:
            self.current_file = file_path
            self.show_notification(f"Saved: {os.path.basename(file_path)}")

    def save_file_as(self):
        """Save as new file"""
        content = "\n".join(self.lines)
        file_path = FileManager.save_as_file(content)
        if file_path:
            self.current_file = file_path
            self.show_notification(f"Saved as: {os.path.basename(file_path)}")

    def copy_selection(self):
        """Copy selected text to clipboard"""
        if self.selection_start and self.selection_end:
            selected = self.get_selected_text()
            if selected:
                success = self.safe_copy_to_clipboard(selected)
                if success:
                    self.show_notification("Copied to system clipboard")
                else:
                    self.show_notification("Copied to internal clipboard")

    def cut_selection(self):
        """Cut selected text to clipboard"""
        if self.selection_start and self.selection_end:
            selected = self.get_selected_text()
            if selected:
                success = self.safe_copy_to_clipboard(selected)
                self.delete_selection()
                if success:
                    self.show_notification("Cut to system clipboard")
                else:
                    self.show_notification("Cut to internal clipboard")

    def paste_clipboard(self):
        """Paste text from clipboard"""
        text = self.safe_paste_from_clipboard()
        if text:
            self.insert_text(text)
            if CLIPBOARD_AVAILABLE:
                self.show_notification("Pasted from system clipboard")
            else:
                self.show_notification("Pasted from internal clipboard")

    def select_all(self):
        """Select all text"""
        if self.lines:
            self.selection_start = (0, 0)
            self.selection_end = (len(self.lines) - 1, len(self.lines[-1]))
            self.show_notification("Selected all")

    def get_selected_text(self):
        """Get currently selected text"""
        if not (self.selection_start and self.selection_end):
            return ""

        start_y, start_x = self.selection_start
        end_y, end_x = self.selection_end

        # Ensure correct order
        if start_y > end_y or (start_y == end_y and start_x > end_x):
            start_y, end_y = end_y, start_y
            start_x, end_x = end_x, start_x

        if start_y == end_y:
            return self.lines[start_y][start_x:end_x]

        lines = []
        # First line
        lines.append(self.lines[start_y][start_x:])
        # Middle lines
        for y in range(start_y + 1, end_y):
            lines.append(self.lines[y])
        # Last line
        lines.append(self.lines[end_y][:end_x])

        return "\n".join(lines)

    def delete_selection(self):
        """Delete selected text"""
        if not (self.selection_start and self.selection_end):
            return

        start_y, start_x = self.selection_start
        end_y, end_x = self.selection_end

        # Ensure correct order
        if start_y > end_y or (start_y == end_y and start_x > end_x):
            start_y, end_y = end_y, start_y
            start_x, end_x = end_x, start_x

        if start_y == end_y:
            # Same line
            line = self.lines[start_y]
            self.lines[start_y] = line[:start_x] + line[end_x:]
            self.cursor_x, self.cursor_y = start_x, start_y
        else:
            # Different lines
            first_part = self.lines[start_y][:start_x]
            last_part = self.lines[end_y][end_x:]
            self.lines[start_y] = first_part + last_part

            # Remove lines in between
            del self.lines[start_y + 1:end_y + 1]
            self.cursor_x, self.cursor_y = start_x, start_y

        self.selection_start = None
        self.selection_end = None

    def format_code(self):
        """Format code (Ctrl+Alt+L)"""
        # Simple formatting: ensure proper indentation
        formatted_lines = []
        indent_level = 0

        for line in self.lines:
            stripped = line.lstrip()
            if stripped:
                # Decrease indent for closing brackets/statements
                if stripped.startswith(('}', ')', ']', 'return', 'break', 'continue')):
                    indent_level = max(0, indent_level - 1)

                # Add proper indentation
                formatted_lines.append('    ' * indent_level + stripped)

                # Increase indent for opening brackets/statements
                if stripped.endswith((':', '{', '(', '[')):
                    indent_level += 1
            else:
                formatted_lines.append('')

        self.lines = formatted_lines
        self.show_notification("Code formatted")

    def toggle_comment(self):
        """Toggle comment on selected lines"""
        if self.selection_start and self.selection_end:
            start_y = min(self.selection_start[0], self.selection_end[0])
            end_y = max(self.selection_start[0], self.selection_end[0])

            for y in range(start_y, end_y + 1):
                line = self.lines[y]
                if line.lstrip().startswith('#'):
                    # Uncomment
                    self.lines[y] = line.replace('#', '', 1).lstrip()
                else:
                    # Comment
                    self.lines[y] = '# ' + line
            self.show_notification("Comments toggled")

    def update_completions(self):
        """Update code completion suggestions"""
        # Get current word at cursor
        line = self.lines[self.cursor_y]
        word_start = self.cursor_x

        while word_start > 0 and (
                line[word_start - 1].isalnum() or line[word_start - 1] == '_' or line[word_start - 1] == '.'):
            word_start -= 1

        if word_start < self.cursor_x:
            self.completion_prefix = line[word_start:self.cursor_x]
            self.completions = CodeCompleter.get_completions(self.completion_prefix, self.current_language)
            self.completion_active = len(self.completions) > 0
            self.selected_completion = 0
        else:
            self.completion_active = False

    def apply_completion(self):
        """Apply selected completion"""
        if self.completions and 0 <= self.selected_completion < len(self.completions):
            completion = self.completions[self.selected_completion]

            # Remove prefix and insert completion
            line = self.lines[self.cursor_y]
            word_start = self.cursor_x
            while word_start > 0 and (
                    line[word_start - 1].isalnum() or line[word_start - 1] == '_' or line[word_start - 1] == '.'):
                word_start -= 1

            self.lines[self.cursor_y] = line[:word_start] + completion + line[self.cursor_x:]
            self.cursor_x = word_start + len(completion)
            self.completion_active = False

    def handle_key_holding(self):
        """Handle smooth key holding"""
        current_time = pygame.time.get_ticks()

        for key, press_time in list(self.key_states.items()):
            if current_time - press_time > self.key_repeat_delay:
                if key == pygame.K_LEFT:
                    self.move_cursor_left()
                elif key == pygame.K_RIGHT:
                    self.move_cursor_right()
                elif key == pygame.K_UP:
                    self.move_cursor_up()
                elif key == pygame.K_DOWN:
                    self.move_cursor_down()
                elif key == pygame.K_BACKSPACE:
                    self.handle_backspace()
                elif key == pygame.K_RETURN:
                    self.handle_enter()
                elif key == pygame.K_PAGEUP:
                    self.page_up()
                elif key == pygame.K_PAGEDOWN:
                    self.page_down()

    def handle_mouse_drag(self, pos):
        """Handle mouse drag for selection"""
        if self.selecting:
            world_x = pos[0] + self.viewport_x
            world_y = pos[1] + self.viewport_y

            line_idx = int((world_y - self.top_margin) / self.line_height)
            if 0 <= line_idx < len(self.lines):
                col = int((world_x - self.left_margin) / self.char_width)
                col = max(0, min(col, len(self.lines[line_idx])))
                self.selection_end = (line_idx, col)

    def handle_backspace(self):
        if self.selection_start and self.selection_end:
            self.delete_selection()
        elif self.cursor_x > 0:
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x - 1] + line[self.cursor_x:]
            self.cursor_x -= 1
        elif self.cursor_y > 0:
            prev_line = self.lines[self.cursor_y - 1]
            curr_line = self.lines[self.cursor_y]
            self.lines[self.cursor_y - 1] = prev_line + curr_line
            self.lines.pop(self.cursor_y)
            self.cursor_y -= 1
            self.cursor_x = len(prev_line)

    def handle_enter(self):
        """Handle enter key with auto-indent"""
        curr_line = self.lines[self.cursor_y]

        # Calculate indentation
        indent = ""
        match = re.match(r'^(\s*)', curr_line)
        if match:
            indent = match.group(1)

        # Check if line ends with colon (Python) or brace (other languages)
        if curr_line.rstrip().endswith(':'):
            indent += "    "

        new_line = curr_line[self.cursor_x:]
        self.lines[self.cursor_y] = curr_line[:self.cursor_x]
        self.lines.insert(self.cursor_y + 1, indent + new_line)
        self.cursor_y += 1
        self.cursor_x = len(indent)

    def insert_text(self, text):
        """Insert text at cursor position"""
        if self.selection_start and self.selection_end:
            self.delete_selection()

        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x] + text + line[self.cursor_x:]
        self.cursor_x += len(text)

    def page_up(self):
        lines_per_page = WINDOW_HEIGHT // self.line_height
        for _ in range(lines_per_page):
            self.move_cursor_up()
        self.viewport_y -= WINDOW_HEIGHT * 0.8

    def page_down(self):
        lines_per_page = WINDOW_HEIGHT // self.line_height
        for _ in range(lines_per_page):
            self.move_cursor_down()
        self.viewport_y += WINDOW_HEIGHT * 0.8

    def move_cursor_left(self):
        if self.cursor_x > 0:
            self.cursor_x -= 1
        elif self.cursor_y > 0:
            self.cursor_y -= 1
            self.cursor_x = len(self.lines[self.cursor_y])

    def move_cursor_right(self):
        if self.cursor_x < len(self.lines[self.cursor_y]):
            self.cursor_x += 1
        elif self.cursor_y < len(self.lines) - 1:
            self.cursor_y += 1
            self.cursor_x = 0

    def move_cursor_up(self):
        if self.cursor_y > 0:
            self.cursor_y -= 1
            self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))

    def move_cursor_down(self):
        if self.cursor_y < len(self.lines) - 1:
            self.cursor_y += 1
            self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))

    def detect_language(self):
        """Auto-detect language from content"""
        full_text = "\n".join(self.lines)
        self.current_language = SyntaxHighlighter.detect_language(full_text)

    def start_search(self):
        self.search_active = True
        self.search_query = ""
        self.search_results = []
        self.current_search_index = -1

    def update_search(self):
        self.search_results = []
        if not self.search_query:
            return

        for i, line in enumerate(self.lines):
            pos = 0
            while True:
                pos = line.lower().find(self.search_query.lower(), pos)
                if pos == -1:
                    break
                self.search_results.append((i, pos, pos + len(self.search_query)))
                pos += 1

        self.current_search_index = 0 if self.search_results else -1

    def find_next(self):
        if not self.search_results:
            return

        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        line_idx, start, end = self.search_results[self.current_search_index]

        self.cursor_y = line_idx
        self.cursor_x = start

        target_y = line_idx * self.line_height + self.top_margin - WINDOW_HEIGHT // 2
        self.viewport_y = target_y

    def update_viewport(self):
        cursor_world_x = self.left_margin + self.cursor_x * self.char_width
        cursor_world_y = self.top_margin + self.cursor_y * self.line_height

        target_x = cursor_world_x - WINDOW_WIDTH // 2
        target_y = cursor_world_y - WINDOW_HEIGHT // 2

        self.viewport_x += (target_x - self.viewport_x) * self.viewport_speed
        self.viewport_y += (target_y - self.viewport_y) * self.viewport_speed

    def world_to_screen(self, x, y):
        return x - self.viewport_x, y - self.viewport_y

    def draw_selection(self, screen):
        """Draw text selection"""
        if not (self.selection_start and self.selection_end):
            return

        start_y, start_x = self.selection_start
        end_y, end_x = self.selection_end

        # Ensure correct order
        if start_y > end_y or (start_y == end_y and start_x > end_x):
            start_y, end_y = end_y, start_y
            start_x, end_x = end_x, start_x

        # Create selection surface
        selection_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

        if start_y == end_y:
            # Single line selection
            world_x1 = self.left_margin + start_x * self.char_width
            world_y = self.top_margin + start_y * self.line_height
            screen_x1, screen_y = self.world_to_screen(world_x1, world_y)

            world_x2 = self.left_margin + end_x * self.char_width
            screen_x2, _ = self.world_to_screen(world_x2, world_y)

            width = screen_x2 - screen_x1
            if width > 0:
                pygame.draw.rect(selection_surface, SELECTION_COLOR,
                                 (screen_x1, screen_y, width, self.line_height))
        else:
            # Multi-line selection
            # First line
            world_x1 = self.left_margin + start_x * self.char_width
            world_y1 = self.top_margin + start_y * self.line_height
            screen_x1, screen_y1 = self.world_to_screen(world_x1, world_y1)
            screen_x2 = WINDOW_WIDTH
            width = screen_x2 - screen_x1
            if width > 0:
                pygame.draw.rect(selection_surface, SELECTION_COLOR,
                                 (screen_x1, screen_y1, width, self.line_height))

            # Middle lines
            for y in range(start_y + 1, end_y):
                world_y = self.top_margin + y * self.line_height
                screen_y = world_y - self.viewport_y
                pygame.draw.rect(selection_surface, SELECTION_COLOR,
                                 (0, screen_y, WINDOW_WIDTH, self.line_height))

            # Last line
            world_y2 = self.top_margin + end_y * self.line_height
            screen_y2 = world_y2 - self.viewport_y
            world_x2 = self.left_margin + end_x * self.char_width
            screen_x2, _ = self.world_to_screen(world_x2, world_y2)
            pygame.draw.rect(selection_surface, SELECTION_COLOR,
                             (0, screen_y2, screen_x2, self.line_height))

        screen.blit(selection_surface, (0, 0))

    def draw_completions(self, screen):
        """Draw code completion popup"""
        if not self.completion_active or not self.completions:
            return

        # Calculate popup position
        cursor_world_x = self.left_margin + self.cursor_x * self.char_width
        cursor_world_y = self.top_margin + self.cursor_y * self.line_height
        screen_x, screen_y = self.world_to_screen(cursor_world_x, cursor_world_y + self.line_height)

        # Popup dimensions
        popup_width = 300
        item_height = 25
        popup_height = len(self.completions) * item_height + 10
        popup_x = min(screen_x, WINDOW_WIDTH - popup_width - 10)
        popup_y = min(screen_y, WINDOW_HEIGHT - popup_height - 10)

        # Draw popup background
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        pygame.draw.rect(popup_surface, (*BG_TERTIARY, 240),
                         (0, 0, popup_width, popup_height), border_radius=5)

        # Draw border
        pygame.draw.rect(popup_surface, ACCENT_BLUE,
                         (0, 0, popup_width, popup_height), 1, border_radius=5)

        screen.blit(popup_surface, (popup_x, popup_y))

        # Draw completions
        for i, completion in enumerate(self.completions):
            y = popup_y + 5 + i * item_height

            # Highlight selected item
            if i == self.selected_completion:
                pygame.draw.rect(screen, (*ACCENT_BLUE, 60),
                                 (popup_x + 2, y - 2, popup_width - 4, item_height),
                                 border_radius=3)

            # Draw completion text
            text_surface = self.font.render(completion, True, TEXT_PRIMARY)
            screen.blit(text_surface, (popup_x + 10, y))

            # Draw completion type indicator
            if '.' in completion:
                type_text = "member"
            elif completion in CodeCompleter.PYTHON_KEYWORDS:
                type_text = "keyword"
            else:
                type_text = "function"

            type_surface = pygame.font.Font(None, 16).render(type_text, True, TEXT_SECONDARY)
            screen.blit(type_surface, (popup_x + popup_width - 70, y + 2))

    def draw_line_numbers(self, screen):
        start_line = max(0, int(self.viewport_y / self.line_height))
        end_line = min(len(self.lines),
                       int((self.viewport_y + WINDOW_HEIGHT) / self.line_height) + 2)

        for i in range(start_line, end_line):
            world_y = self.top_margin + i * self.line_height
            screen_y = world_y - self.viewport_y

            if 0 <= screen_y <= WINDOW_HEIGHT:
                num_text = str(i + 1)
                num_surface = pygame.font.Font(None, 18).render(num_text, True, TEXT_SECONDARY)
                screen.blit(num_surface, (20, screen_y + 5))

    def draw_text_with_highlight(self, screen, text, x, y, language):
        if not text:
            return

        highlights = SyntaxHighlighter.highlight_line(text, language)

        current_x = x
        for (start, end), color in highlights:
            if start >= len(text) or end > len(text):
                continue

            segment = text[start:end]
            if not segment:
                continue

            text_surface = self.font.render(segment, True, color)
            screen.blit(text_surface, (current_x, y))
            current_x += text_surface.get_width()

    def draw_search_highlights(self, screen):
        if not self.search_active or not self.search_results:
            return

        for idx, (line_idx, start, end) in enumerate(self.search_results):
            world_x = self.left_margin + start * self.char_width
            world_y = self.top_margin + line_idx * self.line_height
            screen_x, screen_y = self.world_to_screen(world_x, world_y)

            width = (end - start) * self.char_width

            if idx == self.current_search_index:
                color = (*ACCENT_ORANGE, 100)
            else:
                color = (*ACCENT_YELLOW, 40)

            highlight_rect = pygame.Rect(screen_x - 2, screen_y - 2,
                                         width + 4, self.font_height + 4)
            pygame.draw.rect(screen, color, highlight_rect, border_radius=3)

    def draw_settings(self, screen):
        if not self.settings_visible and self.settings_alpha <= 0:
            return

        if self.settings_visible:
            self.settings_alpha = min(255, self.settings_alpha + 15)
        else:
            self.settings_alpha = max(0, self.settings_alpha - 15)

        panel_width = 400
        panel_height = 500
        panel_x = WINDOW_WIDTH - panel_width - 20
        panel_y = 20

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (*BG_SECONDARY, self.settings_alpha),
                         (0, 0, panel_width, panel_height), border_radius=10)
        screen.blit(panel_surface, (panel_x, panel_y))

        # Draw options
        title_font = pygame.font.Font(None, 32)
        title = title_font.render("Settings", True, TEXT_PRIMARY)
        screen.blit(title, (panel_x + 20, panel_y + 20))

        for i, (option, values) in enumerate(self.settings_options):
            y_pos = panel_y + 80 + i * 60

            name_font = pygame.font.Font(None, 24)
            name_surface = name_font.render(option, True, TEXT_SECONDARY)
            screen.blit(name_surface, (panel_x + 30, y_pos))

            value_font = pygame.font.Font(None, 28)
            if option == "Language":
                value = self.current_language.value
            elif option == "Working Dir":
                value = os.path.basename(self.working_directory)
            else:
                value = values[0]

            value_surface = value_font.render(value, True, ACCENT_BLUE)
            screen.blit(value_surface, (panel_x + 250, y_pos))

            # Working directory click handling (simplified)
            if option == "Working Dir" and self.settings_alpha > 200:
                if pygame.mouse.get_pressed()[0]:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if panel_x + 250 < mouse_x < panel_x + 380 and y_pos - 15 < mouse_y < y_pos + 25:
                        self.change_working_directory()

    def change_working_directory(self):
        """Change working directory (simplified - just go up one level)"""
        self.working_directory = str(Path(self.working_directory).parent)
        self.settings_options[3] = ("Working Dir", [self.working_directory])
        self.show_notification(f"Working dir: {os.path.basename(self.working_directory)}")

    def draw_search_bar(self, screen):
        if not self.search_active:
            return

        bar_width = 400
        bar_height = 50
        bar_x = (WINDOW_WIDTH - bar_width) // 2
        bar_y = 20

        bar_surface = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
        pygame.draw.rect(bar_surface, (*BG_TERTIARY, 240),
                         (0, 0, bar_width, bar_height), border_radius=8)
        screen.blit(bar_surface, (bar_x, bar_y))

        icon = pygame.font.Font(None, 30).render("🔍", True, TEXT_SECONDARY)
        screen.blit(icon, (bar_x + 15, bar_y + 12))

        display_text = self.search_query if self.search_query else "Search..."
        color = TEXT_PRIMARY if self.search_query else TEXT_SECONDARY
        text_surface = self.font.render(display_text, True, color)
        screen.blit(text_surface, (bar_x + 50, bar_y + 15))

        if self.search_results:
            count_text = f"{self.current_search_index + 1}/{len(self.search_results)}"
            count_surface = pygame.font.Font(None, 20).render(count_text, True, ACCENT_GREEN)
            screen.blit(count_surface, (bar_x + bar_width - 60, bar_y + 17))

    def draw_notification(self, screen):
        """Draw notification message"""
        if self.notification:
            current_time = pygame.time.get_ticks()
            if current_time < self.notification_timer:
                # Calculate opacity (fade out near end)
                time_left = self.notification_timer - current_time
                alpha = min(255, int(255 * time_left / 500)) if time_left < 500 else 255

                # Draw notification background
                notif_surface = pygame.font.Font(None, 24).render(self.notification, True, TEXT_PRIMARY)
                padding = 15
                width = notif_surface.get_width() + padding * 2
                height = notif_surface.get_height() + padding * 2

                bg_surface = pygame.Surface((width, height), pygame.SRCALPHA)
                pygame.draw.rect(bg_surface, (*BG_SECONDARY, alpha),
                                 (0, 0, width, height), border_radius=5)
                pygame.draw.rect(bg_surface, (*ACCENT_BLUE, alpha),
                                 (0, 0, width, height), 1, border_radius=5)

                # Position in top center
                x = (WINDOW_WIDTH - width) // 2
                y = 80

                screen.blit(bg_surface, (x, y))
                screen.blit(notif_surface, (x + padding, y + padding))
            else:
                self.notification = None

    def draw(self, screen):
        screen.fill(BG_PRIMARY)

        # Update cursor position
        cursor_world_x = self.left_margin + self.cursor_x * self.char_width
        cursor_world_y = self.top_margin + self.cursor_y * self.line_height + 2
        screen_cursor_x, screen_cursor_y = self.world_to_screen(cursor_world_x, cursor_world_y)
        self.cursor.update(screen_cursor_x, screen_cursor_y)

        # Draw visible lines
        start_line = max(0, int(self.viewport_y / self.line_height))
        end_line = min(len(self.lines),
                       int((self.viewport_y + WINDOW_HEIGHT) / self.line_height) + 2)

        for i in range(start_line, end_line):
            world_y = self.top_margin + i * self.line_height
            screen_y = world_y - self.viewport_y

            if -50 <= screen_y <= WINDOW_HEIGHT + 50:
                self.draw_text_with_highlight(
                    screen,
                    self.lines[i],
                    self.left_margin - self.viewport_x,
                    screen_y,
                    self.current_language
                )

        # Draw overlays
        self.draw_selection(screen)
        self.draw_line_numbers(screen)
        self.draw_search_highlights(screen)
        self.draw_completions(screen)
        self.cursor.draw(screen)
        self.draw_search_bar(screen)
        self.draw_settings(screen)
        self.draw_notification(screen)

        # Draw status bar
        file_name = os.path.basename(self.current_file) if self.current_file else "Untitled"
        status_text = f"{file_name} | Language: {self.current_language.value} | Line: {self.cursor_y + 1}, Col: {self.cursor_x + 1} | Ctrl+O: Open, Ctrl+S: Save"
        status_surface = pygame.font.Font(None, 18).render(status_text, True, TEXT_SECONDARY)
        screen.blit(status_surface, (10, WINDOW_HEIGHT - 25))


def main():
    """Main loop"""
    editor = CodeEditor()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type in (pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN,
                                pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP,
                                pygame.TEXTINPUT, pygame.TEXTEDITING):
                editor.handle_event(event)

        editor.handle_key_holding()
        editor.update_viewport()
        editor.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()