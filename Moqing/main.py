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
import subprocess
import threading
import queue
import signal
import platform
from PIL import Image, ImageDraw, ImageFont

# 安装依赖：pip install pygame pillow

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
ACCENT_RED = (255, 80, 80)
SELECTION_COLOR = (55, 85, 115, 80)
COMMENT_COLOR = (87, 96, 110)
TERMINAL_BG = (30, 30, 30)
TERMINAL_TEXT = (220, 220, 220)

# ==================== 字体加载（支持中文）====================
def get_font(size, bold=False, monospace=False):
    """尝试加载支持中文的字体，失败则回退到默认字体"""
    # 常见中文字体名称（按优先级）
    font_names = [
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
        "STHeiti", "WenQuanYi Micro Hei", "Droid Sans Fallback"
    ]
    if monospace:
        # 等宽字体（终端用）
        font_names = [
            "Consolas", "Courier New", "DejaVu Sans Mono",
            "Noto Mono", "WenQuanYi Zen Hei Mono"
        ] + font_names

    for name in font_names:
        try:
            font = pygame.font.SysFont(name, size, bold=bold)
            # 测试是否能渲染中文
            test_surf = font.render("测试", True, (255,255,255))
            if test_surf.get_width() > 0:
                return font
        except:
            continue
    # 回退到默认字体（可能不支持中文但保证运行）
    return pygame.font.Font(None, size)

# 预定义字体
FONT_NORMAL = get_font(24)
FONT_SMALL = get_font(18)
FONT_MONO = get_font(20, monospace=True)  # 终端用等宽字体

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

    # C/C++
    C_KEYWORD = (204, 120, 255)  # Purple
    C_STRING = (174, 219, 127)  # Green
    C_COMMENT = (128, 138, 158)  # Gray
    C_PREPROCESSOR = (206, 145, 90)  # Orange
    C_NUMBER = (181, 142, 240)  # Purple
    C_TYPE = (86, 156, 214)  # Blue
    C_OPERATOR = (255, 153, 102)  # Orange


class Language(Enum):
    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    HTML = "HTML"
    CSS = "CSS"
    JAVA = "Java"
    C = "C"
    CPP = "C++"
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
        },
        Language.C: {
            'keywords': r'\b(auto|break|case|char|const|continue|default|do|double|else|enum|extern|float|for|goto|if|int|long|register|return|short|signed|sizeof|static|struct|switch|typedef|union|unsigned|void|volatile|while)\b',
            'strings': r'(\".*?\"|\'.*?\')',
            'comments': r'//.*$|/\*[\s\S]*?\*/',
            'preprocessor': r'#\s*(include|define|ifdef|ifndef|endif|pragma|error|warning)\b',
            'numbers': r'\b\d+\b',
            'operators': r'[+\-*/%=<>!&|^~?:]+'
        },
        Language.CPP: {
            'keywords': r'\b(auto|break|case|catch|class|const|constexpr|continue|decltype|default|delete|do|double|else|enum|explicit|export|extern|false|final|float|for|friend|goto|if|inline|int|long|mutable|namespace|new|noexcept|nullptr|operator|private|protected|public|register|reinterpret_cast|return|short|signed|sizeof|static|static_assert|static_cast|struct|switch|template|this|throw|true|try|typedef|typeid|typename|union|unsigned|using|virtual|void|volatile|while)\b',
            'strings': r'(\".*?\"|\'.*?\'|R"[^()]*\(.*?\)")',
            'comments': r'//.*$|/\*[\s\S]*?\*/',
            'preprocessor': r'#\s*(include|define|ifdef|ifndef|endif|pragma|error|warning)\b',
            'numbers': r'\b\d+\b',
            'operators': r'[+\-*/%=<>!&|^~?:]+|::|->|\.\*|->\*'
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
        if re.search(r'#include\s*[<"][^>"]+[>"]|\b(int|void|char|float|double)\s+\w+\s*\(', text):
            if re.search(r'class\s+\w+|\bpublic:\b|\bprivate:\b|\bprotected:\b|std::|::', text):
                return Language.CPP
            else:
                return Language.C

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
            for match in re.finditer(patterns['keywords'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_KEYWORD))
            for match in re.finditer(patterns['strings'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_STRING))
            for match in re.finditer(patterns['comments'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_COMMENT))
            for match in re.finditer(patterns['numbers'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_NUMBER))
            for match in re.finditer(patterns['functions'], line):
                highlights.append((match.span(), SyntaxColors.PYTHON_FUNCTION))
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

        elif language == Language.C:
            for match in re.finditer(patterns['keywords'], line):
                highlights.append((match.span(), SyntaxColors.C_KEYWORD))
            for match in re.finditer(patterns['strings'], line):
                highlights.append((match.span(), SyntaxColors.C_STRING))
            for match in re.finditer(patterns['comments'], line):
                highlights.append((match.span(), SyntaxColors.C_COMMENT))
            for match in re.finditer(patterns['preprocessor'], line):
                highlights.append((match.span(), SyntaxColors.C_PREPROCESSOR))
            for match in re.finditer(patterns['numbers'], line):
                highlights.append((match.span(), SyntaxColors.C_NUMBER))
            for match in re.finditer(patterns['operators'], line):
                highlights.append((match.span(), SyntaxColors.C_OPERATOR))

        elif language == Language.CPP:
            for match in re.finditer(patterns['keywords'], line):
                highlights.append((match.span(), SyntaxColors.C_KEYWORD))
            for match in re.finditer(patterns['strings'], line):
                highlights.append((match.span(), SyntaxColors.C_STRING))
            for match in re.finditer(patterns['comments'], line):
                highlights.append((match.span(), SyntaxColors.C_COMMENT))
            for match in re.finditer(patterns['preprocessor'], line):
                highlights.append((match.span(), SyntaxColors.C_PREPROCESSOR))
            for match in re.finditer(patterns['numbers'], line):
                highlights.append((match.span(), SyntaxColors.C_NUMBER))
            for match in re.finditer(patterns['operators'], line):
                highlights.append((match.span(), SyntaxColors.C_OPERATOR))

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
    """Smooth, ultra-thin cursor with soft outer glow using radial gradient"""

    def __init__(self, x, y, height):
        self.target_x = x
        self.target_y = y
        self.current_x = x
        self.current_y = y
        self.height = height
        self.width = 1  # 超细线
        self.blink_timer = 0
        self.visible = True
        self.speed = 0.3

        # 预计算发光层（提高性能）
        self.glow_layers = []
        for i in range(1, 6):
            alpha = int(30 * math.exp(-i / 1.5))
            self.glow_layers.append((i, alpha))

    def update(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        self.current_x += (self.target_x - self.current_x) * self.speed
        self.current_y += (self.target_y - self.current_y) * self.speed
        self.blink_timer += 1
        if self.blink_timer > 30:
            self.visible = not self.visible
            self.blink_timer = 0

    def draw(self, screen):
        if not self.visible:
            return

        x, y = int(self.current_x), int(self.current_y)

        # 绘制外层发光（更柔和的扩散效果）
        for i, alpha in self.glow_layers:
            # 左右两侧的发光更明显，形成光晕效果
            glow_width = self.width + i * 2
            glow_height = self.height + i * 2

            # 左侧发光
            left_glow = pygame.Rect(x - i, y - i, i * 2, glow_height)
            left_surface = pygame.Surface((left_glow.width, left_glow.height), pygame.SRCALPHA)
            pygame.draw.rect(left_surface, (*ACCENT_BLUE, alpha),
                             (0, 0, left_glow.width, left_glow.height),
                             border_radius=3)
            screen.blit(left_surface, (left_glow.x, left_glow.y))

            # 右侧发光
            right_glow = pygame.Rect(x + self.width - i, y - i, i * 2, glow_height)
            right_surface = pygame.Surface((right_glow.width, right_glow.height), pygame.SRCALPHA)
            pygame.draw.rect(right_surface, (*ACCENT_BLUE, alpha),
                             (0, 0, right_glow.width, right_glow.height),
                             border_radius=3)
            screen.blit(right_surface, (right_glow.x, right_glow.y))

            # 顶部和底部轻微发光
            if i <= 2:  # 只有内层才有顶部底部发光
                top_glow = pygame.Rect(x - 1, y - i, self.width + 2, i)
                top_surface = pygame.Surface((top_glow.width, top_glow.height), pygame.SRCALPHA)
                pygame.draw.rect(top_surface, (*ACCENT_BLUE, alpha // 2),
                                 (0, 0, top_glow.width, top_glow.height))
                screen.blit(top_surface, (top_glow.x, top_glow.y))

                bottom_glow = pygame.Rect(x - 1, y + self.height, self.width + 2, i)
                bottom_surface = pygame.Surface((bottom_glow.width, bottom_glow.height), pygame.SRCALPHA)
                pygame.draw.rect(bottom_surface, (*ACCENT_BLUE, alpha // 2),
                                 (0, 0, bottom_glow.width, bottom_glow.height))
                screen.blit(bottom_surface, (bottom_glow.x, bottom_glow.y))

        # 绘制核心光标（最细的线）
        cursor_rect = pygame.Rect(x, y, self.width, self.height)
        pygame.draw.rect(screen, (255, 255, 255), cursor_rect)  # 纯白色光标

class SmoothGlow:
    """Smooth glow effect using Gaussian-like blur"""
    @staticmethod
    def create_glow_surface(text_surface, glow_color, intensity=1.0, spread=3):
        padding = spread * 4
        width = text_surface.get_width() + padding * 2
        height = text_surface.get_height() + padding * 2
        glow_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for i in range(spread, 0, -1):
            alpha = int(120 * intensity * math.exp(-i / 2))
            scaled = pygame.transform.scale(
                text_surface,
                (int(text_surface.get_width() * (1 + i * 0.15)),
                 int(text_surface.get_height() * (1 + i * 0.15)))
            )
            tinted = scaled.copy()
            tinted.fill((*glow_color[:3], alpha), special_flags=pygame.BLEND_RGBA_MULT)
            x = padding - (scaled.get_width() - text_surface.get_width()) // 2
            y = padding - (scaled.get_height() - text_surface.get_height()) // 2
            glow_surface.blit(tinted, (x, y))
        return glow_surface

class FileManager:
    IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']

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
                ("C files", "*.c"),
                ("C++ files", "*.cpp *.cc *.cxx"),
                ("Header files", "*.h *.hpp"),
                ("Text files", "*.txt"),
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )
        if not file_path:
            return None, None
        ext = Path(file_path).suffix.lower()
        if ext in FileManager.IMAGE_EXTENSIONS:
            return file_path, None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return file_path, content
        except Exception as e:
            print(f"Error opening file: {e}")
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
                    ("C files", "*.c"),
                    ("C++ files", "*.cpp"),
                    ("Header files", "*.h"),
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
        return FileManager.save_file(content, None)


class Terminal:
    """跨平台终端模拟器"""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.lines = [""]
        self.current_line = ""
        self.cursor_pos = 0
        self.history = []
        self.history_index = -1
        self.process = None
        self.output_queue = queue.Queue()
        self.running = False
        self.font = FONT_MONO
        self.line_height = 25
        self.char_width = 10
        self.prompt = "$ " if platform.system() != "Windows" else "> "
        self.current_directory = os.getcwd()
        self.copied_text = ""  # 用于内部剪贴板

    def start(self):
        """启动终端进程"""
        self.running = True
        self.lines = [f"Moqing Terminal [{platform.system()}]"]
        self.lines.append(f"Working directory: {self.current_directory}")
        self.lines.append("Type 'exit' to close terminal")
        self.lines.append("")
        self.current_line = self.prompt

    def execute_command(self, command):
        """执行命令"""
        if not command.strip():
            self.current_line = self.prompt
            return

        # 添加到历史记录
        self.history.append(command)
        self.history_index = len(self.history)

        # 显示命令
        self.lines.append(self.current_line)

        # 处理内置命令
        if command.strip() == "exit":
            self.lines.append("Terminal closed")
            self.running = False
            return
        elif command.strip() == "clear":
            self.lines = [self.lines[0], self.lines[1], self.lines[2], ""]
            self.current_line = self.prompt
            return
        elif command.strip().startswith("cd "):
            self.handle_cd(command[3:].strip())
            self.current_line = self.prompt
            return

        # 执行外部命令
        try:
            # 在不同平台上使用不同的shell
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    cwd=self.current_directory
                )
            else:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    executable="/bin/bash",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    cwd=self.current_directory
                )

            stdout, stderr = process.communicate(timeout=5)

            if stdout:
                for line in stdout.decode('utf-8', errors='ignore').split('\n'):
                    if line:
                        self.lines.append(line)
            if stderr:
                for line in stderr.decode('utf-8', errors='ignore').split('\n'):
                    if line:
                        self.lines.append(f"Error: {line}")

        except subprocess.TimeoutExpired:
            process.kill()
            self.lines.append("Command timed out")
        except Exception as e:
            self.lines.append(f"Error: {str(e)}")

        self.current_line = self.prompt

    def handle_cd(self, path):
        """处理cd命令"""
        try:
            if not path:
                path = str(Path.home())
            new_path = Path(self.current_directory) / path
            new_path = new_path.resolve()
            if new_path.exists() and new_path.is_dir():
                self.current_directory = str(new_path)
                self.prompt = "$ " if platform.system() != "Windows" else "> "
            else:
                self.lines.append(f"Directory not found: {path}")
        except Exception as e:
            self.lines.append(f"Error: {str(e)}")

    def copy_to_clipboard(self):
        """复制当前行或最后输出到剪贴板"""
        if self.lines:
            # 如果有最后输出，复制最后输出；否则复制当前行
            text = self.last_output if self.last_output else self.current_line
            if CLIPBOARD_AVAILABLE:
                try:
                    pygame.scrap.put(pygame.SCRAP_TEXT, text.encode('utf-8'))
                except:
                    pass
            self.copied_text = text
            self.lines.append("[已复制]")

    def paste_from_clipboard(self):
        """从剪贴板粘贴到当前行"""
        pasted = ""
        if CLIPBOARD_AVAILABLE:
            try:
                pasted = pygame.scrap.get(pygame.SCRAP_TEXT).decode('utf-8')
            except:
                pass
        if not pasted and self.copied_text:
            pasted = self.copied_text
        if pasted:
            self.current_line += pasted.replace('\n', ' ').replace('\r', '')

    def send_interrupt(self):
        """向当前运行的子进程发送中断信号 (Ctrl+C)"""
        if self.process and self.process.poll() is None:
            if platform.system() == "Windows":
                # Windows 下用 terminate 模拟
                self.process.terminate()
            else:
                self.process.send_signal(signal.SIGINT)
            self.lines.append("^C")
        else:
            self.lines.append("没有正在运行的进程")

    def handle_key(self, event):
        mods = pygame.key.get_mods()

        # Ctrl+Shift+C 复制
        if event.key == pygame.K_c and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
            self.copy_to_clipboard()
            return

        # Ctrl+Shift+V 粘贴
        if event.key == pygame.K_v and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
            self.paste_from_clipboard()
            return

        # Ctrl+[ 发送中断
        if event.key == pygame.K_LEFTBRACKET and (mods & pygame.KMOD_CTRL):
            self.send_interrupt()
            return
        if event.key == pygame.K_RETURN:
            command = self.current_line[len(self.prompt):]
            self.execute_command(command)
        elif event.key == pygame.K_BACKSPACE:
            if len(self.current_line) > len(self.prompt):
                self.current_line = self.current_line[:-1]
        elif event.key == pygame.K_UP:
            if self.history and self.history_index > 0:
                self.history_index -= 1
                self.current_line = self.prompt + self.history[self.history_index]
        elif event.key == pygame.K_DOWN:
            if self.history and self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.current_line = self.prompt + self.history[self.history_index]
            else:
                self.current_line = self.prompt
        elif event.key == pygame.K_TAB:
            # 简单的tab补全
            self.handle_tab_completion()
        elif event.unicode and event.unicode.isprintable():
            self.current_line += event.unicode

    def handle_tab_completion(self):
        """处理tab补全"""
        current = self.current_line[len(self.prompt):]
        if current.startswith("cd "):
            # 补全目录
            path_part = current[3:].strip()
            try:
                search_path = Path(self.current_directory) / path_part if path_part else Path(self.current_directory)
                parent = search_path.parent if path_part and not search_path.exists() else search_path
                pattern = search_path.name if path_part else ""

                if parent.exists():
                    matches = [p.name for p in parent.iterdir()
                              if p.name.startswith(pattern) and p.is_dir()]
                    if matches:
                        if len(matches) == 1:
                            self.current_line = self.prompt + "cd " + str(Path(path_part).parent / matches[0]) + "/"
            except:
                pass

    def draw(self, screen):
        """绘制终端"""
        # 终端背景
        pygame.draw.rect(screen, TERMINAL_BG, (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

        # 绘制行
        y = 10
        start_line = max(0, len(self.lines) - (WINDOW_HEIGHT // self.line_height) + 2)
        for i in range(start_line, len(self.lines)):
            line = self.lines[i]
            text_surface = self.font.render(line, True, TERMINAL_TEXT)
            screen.blit(text_surface, (10, y))
            y += self.line_height

        # 绘制当前行
        current_surface = self.font.render(self.current_line, True, TERMINAL_TEXT)
        screen.blit(current_surface, (10, y))

        # 绘制光标
        cursor_x = 10 + len(self.current_line) * self.char_width
        if pygame.time.get_ticks() % 1000 < 500:
            pygame.draw.line(screen, TERMINAL_TEXT,
                           (cursor_x, y), (cursor_x, y + self.line_height - 5), 2)


class ImagePreview:
    """图片预览器"""

    def __init__(self):
        self.image = None
        self.image_path = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        self.last_mouse = (0, 0)

    def load_image(self, path):
        """加载图片"""
        try:
            self.image_path = path
            pil_image = Image.open(path)

            # 转换PIL图片为pygame surface
            mode = pil_image.mode
            size = pil_image.size
            data = pil_image.tobytes()

            if mode == 'RGBA':
                self.image = pygame.image.fromstring(data, size, 'RGBA').convert_alpha()
            else:
                self.image = pygame.image.fromstring(data, size, 'RGB').convert()

            self.scale = 1.0
            self.offset_x = 0
            self.offset_y = 0
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False

    def handle_event(self, event):
        """处理鼠标事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键拖拽
                self.dragging = True
                self.last_mouse = event.pos
            elif event.button == 4:  # 滚轮向上 - 放大
                self.scale *= 1.1
            elif event.button == 5:  # 滚轮向下 - 缩小
                self.scale /= 1.1

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                dx = event.pos[0] - self.last_mouse[0]
                dy = event.pos[1] - self.last_mouse[1]
                self.offset_x += dx
                self.offset_y += dy
                self.last_mouse = event.pos

    def draw(self, screen):
        """绘制图片"""
        if not self.image:
            # 显示提示
            font = FONT_NORMAL
            text = font.render("No image loaded", True, TEXT_SECONDARY)
            text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
            screen.blit(text, text_rect)
            return

        # 计算缩放后的尺寸
        scaled_width = int(self.image.get_width() * self.scale)
        scaled_height = int(self.image.get_height() * self.scale)

        if scaled_width > 0 and scaled_height > 0:
            scaled = pygame.transform.scale(self.image, (scaled_width, scaled_height))
            screen.blit(scaled, (self.offset_x, self.offset_y))

        # 显示图片信息
        font = FONT_SMALL
        info = f"Scale: {self.scale:.2f}x | File: {os.path.basename(self.image_path) if self.image_path else 'None'}"
        text = font.render(info, True, TEXT_PRIMARY)
        pygame.draw.rect(screen, BG_SECONDARY, (5, 5, text.get_width() + 10, text.get_height() + 10))
        screen.blit(text, (10, 10))


class EnhancedCodeCompleter(CodeCompleter):
    """增强的代码联想引擎"""

    # C/C++ 关键字
    C_KEYWORDS = [
        'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
        'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
        'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
        'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'
    ]

    CPP_KEYWORDS = [
        'and', 'and_eq', 'asm', 'bitand', 'bitor', 'bool', 'catch', 'class',
        'compl', 'const_cast', 'delete', 'dynamic_cast', 'explicit', 'export',
        'false', 'friend', 'inline', 'mutable', 'namespace', 'new', 'not',
        'not_eq', 'operator', 'or', 'or_eq', 'private', 'protected', 'public',
        'reinterpret_cast', 'static_cast', 'template', 'this', 'throw', 'true',
        'try', 'typeid', 'typename', 'using', 'virtual', 'wchar_t', 'xor', 'xor_eq'
    ]

    # C/C++ 标准库函数
    C_STDLIB = {
        'stdio.h': ['printf', 'scanf', 'fopen', 'fclose', 'fread', 'fwrite', 'fprintf', 'fscanf', 'getchar', 'putchar'],
        'stdlib.h': ['malloc', 'calloc', 'realloc', 'free', 'atoi', 'atof', 'rand', 'srand', 'exit', 'qsort', 'bsearch'],
        'string.h': ['strcpy', 'strncpy', 'strcat', 'strncat', 'strcmp', 'strncmp', 'strlen', 'strchr', 'strrchr', 'strstr'],
        'math.h': ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sqrt', 'pow', 'log', 'log10', 'exp', 'fabs', 'ceil', 'floor'],
        'ctype.h': ['isalpha', 'isdigit', 'isalnum', 'islower', 'isupper', 'tolower', 'toupper', 'isspace'],
        'time.h': ['time', 'clock', 'difftime', 'strftime', 'localtime', 'gmtime'],
        'assert.h': ['assert']
    }

    CPP_STDLIB = {
        'iostream': ['cin', 'cout', 'cerr', 'clog', 'endl', 'ws'],
        'vector': ['push_back', 'pop_back', 'size', 'empty', 'clear', 'begin', 'end', 'insert', 'erase', 'resize'],
        'string': ['length', 'size', 'substr', 'find', 'rfind', 'replace', 'append', 'c_str', 'compare'],
        'map': ['insert', 'erase', 'find', 'count', 'begin', 'end', 'at', 'operator[]'],
        'algorithm': ['sort', 'find', 'reverse', 'copy', 'max', 'min', 'swap', 'binary_search'],
        'memory': ['shared_ptr', 'unique_ptr', 'make_shared', 'make_unique'],
        'fstream': ['ifstream', 'ofstream', 'fstream', 'open', 'close', 'is_open'],
        'sstream': ['stringstream', 'istringstream', 'ostringstream']
    }

    @classmethod
    def get_completions(cls, text, language=Language.PYTHON, context=None):
        """获取增强的代码联想建议"""
        if not text:
            return []

        completions = []

        # 处理模块导入
        if '.' in text:
            module, partial = text.rsplit('.', 1)
            if language == Language.PYTHON and module in cls.COMMON_LIBS:
                completions.extend([f"{module}.{func}" for func in cls.COMMON_LIBS[module]
                                   if func.startswith(partial)])
            elif language == Language.C and module in cls.C_STDLIB:
                completions.extend([f"{module}.{func}" for func in cls.C_STDLIB[module]
                                   if func.startswith(partial)])
            elif language == Language.CPP and module in cls.CPP_STDLIB:
                completions.extend([f"{module}.{func}" for func in cls.CPP_STDLIB[module]
                                   if func.startswith(partial)])

        # 语言特定的联想
        if language == Language.PYTHON:
            # Python 关键词
            completions.extend([kw for kw in cls.PYTHON_KEYWORDS if kw.startswith(text)])
            # Python 内置函数
            completions.extend([b for b in cls.PYTHON_BUILTINS if b.startswith(text)])
            # 常见库名
            completions.extend([lib for lib in cls.COMMON_LIBS.keys() if lib.startswith(text)])

        elif language == Language.C:
            # C 关键词
            completions.extend([kw for kw in cls.C_KEYWORDS if kw.startswith(text)])
            # C 标准库函数
            for lib, funcs in cls.C_STDLIB.items():
                completions.extend([f"{lib}::{func}" for func in funcs if func.startswith(text)])

        elif language == Language.CPP:
            # C++ 关键词
            completions.extend([kw for kw in cls.C_KEYWORDS + cls.CPP_KEYWORDS if kw.startswith(text)])
            # C++ 标准库
            for lib, funcs in cls.CPP_STDLIB.items():
                completions.extend([f"{lib}::{func}" for func in funcs if func.startswith(text)])

        # 上下文感知联想（简化版）
        if context:
            # 根据上下文提供更相关的建议
            if 'include' in context and language in (Language.C, Language.CPP):
                # 头文件联想
                headers = list(cls.C_STDLIB.keys()) + list(cls.CPP_STDLIB.keys())
                completions.extend([f"#include <{h}>" for h in headers if h.startswith(text)])

        return sorted(set(completions))[:15]  # 返回前15个建议


class CodeEditor:
    def __init__(self):
        self.lines = [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.current_language = Language.PYTHON
        self.working_directory = os.getcwd()
        self.current_file = None

        # Text rendering
        self.font = FONT_NORMAL
        self.font_height = 30
        self.line_height = 35
        self.left_margin = 100
        self.top_margin = 60

        # Selection
        self.selection_start = None
        self.selection_end = None
        self.selecting = False
        self.clipboard = ""

        # Enhanced code completion
        self.completion_active = False
        self.completions = []
        self.selected_completion = 0
        self.completion_prefix = ""
        self.completion_context = ""

        # Terminal mode
        self.terminal_mode = False
        self.terminal = Terminal(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Image preview
        self.image_preview_mode = False
        self.image_preview = ImagePreview()

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

        # Search functionality - 修复：添加新变量
        self.search_active = False
        self.search_query = ""
        self.search_results = []
        self.current_search_index = -1
        self.double_shift_time = 0
        self.last_shift_key = None  # 记录最后一次按下的Shift键
        self.search_input_active = False  # 搜索输入模式标志

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

        self.insert_mode = True

    def get_text_width(self, text):
        """返回给定文本的渲染宽度（像素）"""
        if not text:
            return 0
        return self.font.size(text)[0]

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
        # Terminal mode 处理
        if self.terminal_mode:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    self.terminal_mode = False
                    self.show_notification("Exited terminal mode")
                else:
                    self.terminal.handle_key(event)
            return

        # 图片预览模式处理
        if self.image_preview_mode:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.image_preview_mode = False
                self.show_notification("Exited image preview")
            else:
                self.image_preview.handle_event(event)
            return

        # 正常编辑模式处理
        if event.type == pygame.KEYDOWN:
            self.handle_keydown(event)
            self.key_states[event.key] = pygame.time.get_ticks()
        elif event.type == pygame.KEYUP:
            if event.key in self.key_states:
                del self.key_states[event.key]
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
            # 修复：搜索模式下，将文本输入添加到搜索框
            if self.search_active:
                self.search_query += event.text
                self.update_search()
            elif not self.completion_active:
                self.insert_text(event.text)
                self.update_completions()
        elif event.type == pygame.TEXTEDITING:
            self.ime_text = event.text
            self.ime_active = True

    def handle_keydown(self, event):
        """Handle key press events"""
        current_time = pygame.time.get_ticks()
        mods = pygame.key.get_mods()

        # Ctrl+Alt+T 切换终端模式
        if event.key == pygame.K_t and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_ALT):
            self.terminal_mode = not self.terminal_mode
            if self.terminal_mode:
                self.terminal.start()
                self.show_notification("Terminal mode activated (Ctrl+Esc to exit)")
            return

        # File operations
        if event.key == pygame.K_o and mods & pygame.KMOD_CTRL:
            self.open_file()
        elif event.key == pygame.K_s and mods & pygame.KMOD_CTRL:
            if mods & pygame.KMOD_SHIFT:
                self.save_file_as()
            else:
                self.save_file()

        # Copy/Paste shortcuts
        elif event.key == pygame.K_c and mods & pygame.KMOD_CTRL:
            self.copy_selection()
        elif event.key == pygame.K_v and mods & pygame.KMOD_CTRL:
            self.paste_clipboard()
        elif event.key == pygame.K_x and mods & pygame.KMOD_CTRL:
            self.cut_selection()
        elif event.key == pygame.K_a and mods & pygame.KMOD_CTRL:
            self.select_all()

        # Format code
        elif event.key == pygame.K_l and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_ALT):
            self.format_code()

        # Toggle comment
        elif event.key == pygame.K_SLASH and mods & pygame.KMOD_CTRL:
            self.toggle_comment()

        # Double shift search - 修复双击检测
        elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
            # 如果是第一次按下Shift或按下的Shift键与上次不同
            if self.last_shift_key is None or self.last_shift_key != event.key:
                self.last_shift_key = event.key
                self.double_shift_time = current_time
            else:
                # 检查是否是双击（两次按同一个Shift键）
                if current_time - self.double_shift_time < 300:
                    self.start_search()
                self.last_shift_key = None  # 重置，避免连续触发
                self.double_shift_time = 0

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
            elif event.key == pygame.K_BACKSPACE:
                self.handle_backspace()
                self.update_completions()
            return

        # Search handling - 修复搜索模式下的输入问题
        if self.search_active:
            if event.key == pygame.K_RETURN:
                self.find_next()
            elif event.key == pygame.K_ESCAPE:
                self.search_active = False
                self.search_query = ""
                self.search_results = []
                self.search_input_active = False
                # 重新启用文本输入
                pygame.key.start_text_input()
            elif event.key == pygame.K_BACKSPACE:
                if self.search_query:
                    self.search_query = self.search_query[:-1]
                    self.update_search()
            elif event.key == pygame.K_TAB:
                # 允许Tab键切换焦点或保留用于搜索
                pass
            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                # 允许Shift键（但不处理）
                pass
            else:
                # 对于其他按键，让系统处理TEXTINPUT事件
                # 这里不拦截，让TEXTINPUT事件处理
                pass
            return  # 重要：拦截所有按键，但TEXTINPUT会单独处理字符输入

        # 搜索模式下的文本输入由TEXTINPUT事件处理
        # 所以这里不需要处理字符输入

        # Regular editing (非搜索模式)
        if event.key == pygame.K_BACKSPACE:
            self.handle_backspace()
            self.update_completions()
        elif event.key == pygame.K_RETURN:
            self.handle_enter()
            self.update_completions()
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
        """Handle mouse click"""
        if event.button == 2 and pygame.key.get_mods() & pygame.KMOD_CTRL:
            # Ctrl+Middle click - center viewport
            world_x = event.pos[0] + self.viewport_x
            world_y = event.pos[1] + self.viewport_y
            self.viewport_x = world_x - WINDOW_WIDTH // 2
            self.viewport_y = world_y - WINDOW_HEIGHT // 2
            self.show_notification("Viewport centered")
        else:
            # Normal click
            world_x = event.pos[0] + self.viewport_x
            world_y = event.pos[1] + self.viewport_y

            line_idx = int((world_y - self.top_margin) / self.line_height)
            if 0 <= line_idx < len(self.lines):
                self.cursor_y = line_idx
                # 根据点击位置计算字符索引
                line = self.lines[line_idx]
                click_x = world_x - self.left_margin
                total_width = 0
                col = 0
                for i, ch in enumerate(line):
                    ch_width = self.font.size(ch)[0]
                    if total_width + ch_width / 2 > click_x:  # 超过字符中间位置则选中该字符
                        col = i
                        break
                    total_width += ch_width
                    col = i + 1  # 如果循环结束，则位于行末
                self.cursor_x = max(0, min(col, len(self.lines[line_idx])))

                self.selecting = True
                self.selection_start = (self.cursor_y, self.cursor_x)
                self.selection_end = None

    def open_file(self):
        """Open a file"""
        file_path, content = FileManager.open_file()
        if file_path and content is not None:
            # 检查是否为图片文件
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
            if any(file_path.lower().endswith(ext) for ext in image_extensions):
                if self.image_preview.load_image(file_path):
                    self.image_preview_mode = True
                    self.show_notification(f"Previewing image: {os.path.basename(file_path)}")
                return

            # 普通文本文件
            self.lines = content.splitlines()
            if not self.lines:
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
        # 获取当前行和上下文
        line = self.lines[self.cursor_y]

        # 获取当前单词的开始位置
        word_start = self.cursor_x
        while word_start > 0 and (line[word_start - 1].isalnum() or
                                  line[word_start - 1] == '_' or
                                  line[word_start - 1] == '.' or
                                  line[word_start - 1] == ':'):
            word_start -= 1

        # 获取上下文（前两行）
        context_start = max(0, self.cursor_y - 2)
        context = '\n'.join(self.lines[context_start:self.cursor_y + 1])

        if word_start < self.cursor_x:
            self.completion_prefix = line[word_start:self.cursor_x]
            self.completions = EnhancedCodeCompleter.get_completions(
                self.completion_prefix,
                self.current_language,
                context
            )
            self.completion_active = len(self.completions) > 0
            self.selected_completion = 0
        else:
            self.completion_active = False

    def apply_completion(self):
        """Apply selected completion"""
        if self.completions and 0 <= self.selected_completion < len(self.completions):
            completion = self.completions[self.selected_completion]

            # 移除前缀并插入补全
            line = self.lines[self.cursor_y]
            word_start = self.cursor_x
            while word_start > 0 and (line[word_start - 1].isalnum() or
                                      line[word_start - 1] == '_' or
                                      line[word_start - 1] == '.'):
                word_start -= 1

            self.lines[self.cursor_y] = line[:word_start] + completion + line[self.cursor_x:]
            self.cursor_x = word_start + len(completion)
            self.completion_active = False
            self.show_notification(f"Completed: {completion}")

    def handle_key_holding(self):
        """Handle smooth key holding (including search backspace repeat)"""
        current_time = pygame.time.get_ticks()
        for key, press_time in list(self.key_states.items()):
            if current_time - press_time > self.key_repeat_delay:
                if self.completion_active:
                    # 联想导航重复
                    if key == pygame.K_UP:
                        self.selected_completion = max(0, self.selected_completion - 1)
                    elif key == pygame.K_DOWN:
                        self.selected_completion = min(len(self.completions) - 1, self.selected_completion + 1)
                elif self.search_active:
                    # 搜索模式下，退格键重复删除
                    if key == pygame.K_BACKSPACE and self.search_query:
                        self.search_query = self.search_query[:-1]
                        self.update_search()
                else:
                    # 普通编辑模式重复
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
        """Handle mouse drag for selection (adapting to variable-width fonts)"""
        if not self.selecting:
            return

        world_x = pos[0] + self.viewport_x
        world_y = pos[1] + self.viewport_y

        line_idx = int((world_y - self.top_margin) / self.line_height)
        if 0 <= line_idx < len(self.lines):
            line = self.lines[line_idx]
            # 计算点击位置的字符索引
            click_x = world_x - self.left_margin
            total_width = 0
            col = 0
            for i, ch in enumerate(line):
                ch_width = self.font.size(ch)[0]
                # 如果点击位置在字符中间之后，定位到下一个字符
                if total_width + ch_width / 2 > click_x:
                    col = i
                    break
                total_width += ch_width
                col = i + 1  # 如果循环结束，则位于行末
            # 限制列范围
            col = max(0, min(col, len(line)))
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
        """Insert text at cursor position (supports insert/overwrite modes)"""
        if self.selection_start and self.selection_end:
            self.delete_selection()

        line = self.lines[self.cursor_y]
        if self.insert_mode:
            self.lines[self.cursor_y] = line[:self.cursor_x] + text + line[self.cursor_x:]
            self.cursor_x += len(text)
        else:
            replace_len = min(len(text), len(line) - self.cursor_x)
            self.lines[self.cursor_y] = line[:self.cursor_x] + text[:replace_len] + line[self.cursor_x + replace_len:]
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
        """Enhanced language detection including C/C++"""
        full_text = "\n".join(self.lines)

        # C/C++ 检测
        if re.search(r'#include\s*[<"][^>"]+[>"]|\b(int|void|char|float|double)\s+\w+\s*\(', full_text):
            if re.search(r'class\s+\w+|\bpublic:\b|\bprivate:\b|\bprotected:\b|std::|::', full_text):
                self.current_language = Language.CPP
            else:
                self.current_language = Language.C
        else:
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
        """Smooth viewport following"""
        # 获取光标前文本的实际宽度
        prefix = self.lines[self.cursor_y][:self.cursor_x]
        cursor_world_x = self.left_margin + self.get_text_width(prefix)
        cursor_world_y = self.top_margin + self.cursor_y * self.line_height

        target_x = cursor_world_x - WINDOW_WIDTH // 2
        target_y = cursor_world_y - WINDOW_HEIGHT // 2

        self.viewport_x += (target_x - self.viewport_x) * self.viewport_speed
        self.viewport_y += (target_y - self.viewport_y) * self.viewport_speed

    def world_to_screen(self, x, y):
        """Convert world coordinates to screen coordinates"""
        return x - self.viewport_x, y - self.viewport_y

    def draw_selection(self, screen):
        """Draw text selection (supports variable-width fonts)"""
        if not (self.selection_start and self.selection_end):
            return

        start_y, start_x = self.selection_start
        end_y, end_x = self.selection_end

        # Ensure correct order
        if start_y > end_y or (start_y == end_y and start_x > end_x):
            start_y, end_y = end_y, start_y
            start_x, end_x = end_x, start_x

        selection_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

        if start_y == end_y:
            # Single line selection
            line = self.lines[start_y]
            # 计算起始和结束位置的世界坐标（基于前缀宽度）
            prefix_start = line[:start_x]
            prefix_end = line[:end_x]
            world_x1 = self.left_margin + self.get_text_width(prefix_start)
            world_x2 = self.left_margin + self.get_text_width(prefix_end)
            world_y = self.top_margin + start_y * self.line_height

            screen_x1, screen_y = self.world_to_screen(world_x1, world_y)
            screen_x2, _ = self.world_to_screen(world_x2, world_y)

            width = screen_x2 - screen_x1
            if width > 0:
                pygame.draw.rect(selection_surface, SELECTION_COLOR,
                                 (screen_x1, screen_y, width, self.line_height))
        else:
            # Multi-line selection
            # First line: from start_x to end of line
            first_line = self.lines[start_y]
            prefix_first = first_line[:start_x]
            world_x1 = self.left_margin + self.get_text_width(prefix_first)
            world_y1 = self.top_margin + start_y * self.line_height
            screen_x1, screen_y1 = self.world_to_screen(world_x1, world_y1)
            # 第一行高亮到屏幕右边缘
            width_first = WINDOW_WIDTH - screen_x1
            if width_first > 0:
                pygame.draw.rect(selection_surface, SELECTION_COLOR,
                                 (screen_x1, screen_y1, width_first, self.line_height))

            # Middle lines: full lines
            for y in range(start_y + 1, end_y):
                world_y = self.top_margin + y * self.line_height
                screen_y = world_y - self.viewport_y
                pygame.draw.rect(selection_surface, SELECTION_COLOR,
                                 (0, screen_y, WINDOW_WIDTH, self.line_height))

            # Last line: from 0 to end_x
            last_line = self.lines[end_y]
            prefix_last = last_line[:end_x]
            world_x2 = self.left_margin + self.get_text_width(prefix_last)
            world_y2 = self.top_margin + end_y * self.line_height
            screen_x2, screen_y2 = self.world_to_screen(world_x2, world_y2)
            pygame.draw.rect(selection_surface, SELECTION_COLOR,
                             (0, screen_y2, screen_x2, self.line_height))

        screen.blit(selection_surface, (0, 0))

    def draw_completions(self, screen):
        """Draw code completion popup"""
        if not self.completion_active or not self.completions:
            return

        # Calculate popup position
        prefix = self.lines[self.cursor_y][:self.cursor_x]
        cursor_world_x = self.left_margin + self.get_text_width(prefix)
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
            elif completion in EnhancedCodeCompleter.PYTHON_KEYWORDS:
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
            # 为非默认颜色添加发光
            if color != TEXT_PRIMARY:
                glow = SmoothGlow.create_glow_surface(text_surface, color, 0.5, 2)
                screen.blit(glow, (current_x - 2, y - 2))
            screen.blit(text_surface, (current_x, y))
            current_x += text_surface.get_width()

    def draw_search_highlights(self, screen):
        if not self.search_active or not self.search_results:
            return

        for idx, (line_idx, start, end) in enumerate(self.search_results):
            # 计算从行首到起始位置的实际宽度
            prefix = self.lines[line_idx][:start]
            world_x = self.left_margin + self.get_text_width(prefix)
            world_y = self.top_margin + line_idx * self.line_height
            screen_x, screen_y = self.world_to_screen(world_x, world_y)

            # 计算选中文本的实际宽度
            text_segment = self.lines[line_idx][start:end]
            width = self.get_text_width(text_segment)

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

            # Working directory click handling
            if option == "Working Dir" and self.settings_alpha > 200:
                if pygame.mouse.get_pressed()[0]:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if panel_x + 250 < mouse_x < panel_x + 380 and y_pos - 15 < mouse_y < y_pos + 25:
                        self.change_working_directory()

    def change_working_directory(self):
        """Change working directory (go up one level)"""
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
        """Main draw method"""
        if self.terminal_mode:
            self.terminal.draw(screen)
            return

        if self.image_preview_mode:
            screen.fill(BG_PRIMARY)
            self.image_preview.draw(screen)

            # 绘制退出提示
            font = pygame.font.Font(None, 20)
            text = font.render("Press ESC to exit image preview", True, TEXT_SECONDARY)
            screen.blit(text, (10, WINDOW_HEIGHT - 30))
            return

        # 正常编辑模式绘制
        screen.fill(BG_PRIMARY)

        # Update cursor position
        # 获取当前行光标前的文本宽度
        prefix = self.lines[self.cursor_y][:self.cursor_x]
        cursor_world_x = self.left_margin + self.get_text_width(prefix)
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
                if i == self.cursor_y:
                    # 绘制半透明背景
                    highlight_surf = pygame.Surface((WINDOW_WIDTH, self.line_height), pygame.SRCALPHA)
                    highlight_surf.fill((*ACCENT_BLUE, 30))  # 浅蓝色透明
                    screen.blit(highlight_surf, (0, screen_y))
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

        # Draw status bar with mode indicator
        file_name = os.path.basename(self.current_file) if self.current_file else "Untitled"
        mode_text = "TERMINAL MODE (Ctrl+Alt+T)" if self.terminal_mode else "EDIT MODE"
        status_text = f"{file_name} | Language: {self.current_language.value} | Mode: {mode_text} | Line: {self.cursor_y + 1}, Col: {self.cursor_x + 1}"
        status_surface = pygame.font.Font(None, 18).render(status_text, True, TEXT_SECONDARY)
        screen.blit(status_surface, (10, WINDOW_HEIGHT - 25))

    def start_search(self):
        """启动搜索模式"""
        self.search_active = True
        self.search_query = ""
        self.search_results = []
        self.current_search_index = -1
        self.search_input_active = True
        # 确保文本输入已启用
        pygame.key.start_text_input()
        self.show_notification("Search mode activated (type to search, Enter to find next, Esc to exit)")

    def update_search(self):
        """更新搜索结果"""
        self.search_results = []
        if not self.search_query:
            return

        search_lower = self.search_query.lower()
        for i, line in enumerate(self.lines):
            pos = 0
            while True:
                pos = line.lower().find(search_lower, pos)
                if pos == -1:
                    break
                self.search_results.append((i, pos, pos + len(self.search_query)))
                pos += 1

        if self.search_results:
            self.current_search_index = 0
            # 自动跳转到第一个结果
            self.go_to_search_result(0)
        else:
            self.current_search_index = -1

    def go_to_search_result(self, index):
        """跳转到指定的搜索结果"""
        if not self.search_results or index < 0 or index >= len(self.search_results):
            return

        line_idx, start, end = self.search_results[index]
        self.cursor_y = line_idx
        self.cursor_x = start

        # 选中搜索结果
        self.selection_start = (line_idx, start)
        self.selection_end = (line_idx, end)

        # 滚动视图到光标位置
        target_y = line_idx * self.line_height + self.top_margin - WINDOW_HEIGHT // 2
        self.viewport_y = target_y

    def find_next(self):
        """查找下一个"""
        if not self.search_results:
            self.show_notification("No matches found")
            return

        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self.go_to_search_result(self.current_search_index)
        self.show_notification(f"Match {self.current_search_index + 1} of {len(self.search_results)}")


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