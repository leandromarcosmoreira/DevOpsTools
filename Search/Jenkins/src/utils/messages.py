from typing import Dict, Any
from datetime import datetime
from colorama import init, Style, Fore
import sys

init()

class MessageManager:
    COLORS = {
        'info': Fore.BLUE,
        'success': Fore.GREEN,
        'warning': Fore.YELLOW,
        'error': Fore.RED,
        'progress': Fore.CYAN,
        'header': Fore.WHITE + Style.BRIGHT
    }
    
    _start_times = {}
    
    @classmethod
    def _format_message(cls, message: str, msg_type: str = 'info') -> str:
        timestamp = datetime.now().strftime('%H:%M:%S')
        color = cls.COLORS.get(msg_type, '')
        return f"{color}[{timestamp}] {message}{Style.RESET_ALL}"
    
    @classmethod
    def info(cls, message: str):
        print(cls._format_message(message, 'info'), flush=True)
    
    @classmethod
    def success(cls, message: str):
        print(cls._format_message(message, 'success'), flush=True)
    
    @classmethod
    def warning(cls, message: str):
        print(cls._format_message(message, 'warning'), flush=True)
    
    @classmethod
    def error(cls, message: str):
        print(cls._format_message(message, 'error'), flush=True)
    
    @classmethod
    def progress(cls, current: int, total: int, message: str = "Processando", elapsed_seconds: float = None):
        if message not in cls._start_times and current == 1:
            cls._start_times[message] = datetime.now()
        
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current // total)
        bar = '=' * filled_length + '-' * (bar_length - filled_length)
        
        if current == total:
            if elapsed_seconds is None and message in cls._start_times:
                duration = datetime.now() - cls._start_times[message]
                elapsed_seconds = duration.total_seconds()
            
            if elapsed_seconds is not None:
                progress_text = f"\r{cls.COLORS['progress']}[{bar}] {percentage:.1f}% {message}... ({elapsed_seconds:.2f}s){Style.RESET_ALL}"
            else:
                progress_text = f"\r{cls.COLORS['progress']}[{bar}] {percentage:.1f}% {message}...{Style.RESET_ALL}"
            
            if message in cls._start_times:
                del cls._start_times[message]
        else:
            progress_text = f"\r{cls.COLORS['progress']}[{bar}] {percentage:.1f}% {message}...{Style.RESET_ALL}"
        
        sys.stdout.write(progress_text)
        sys.stdout.flush()
        
        if current == total:
            sys.stdout.write('\n')
            sys.stdout.flush()
    
    @classmethod
    def summary(cls, stats: Dict[str, Any]):
        print("\n" + "="*60, flush=True)
        print(cls._format_message("RESUMO DA EXECUÇÃO", 'header'), flush=True)
        print("-"*60, flush=True)
        
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"\n{cls._format_message(key + ':', 'header')}", flush=True)
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, (list, set)):
                        print(cls._format_message(f"  {subkey}:", 'info'), flush=True)
                        for item in sorted(subvalue):
                            print(cls._format_message(f"    - {item}", 'success'), flush=True)
                    else:
                        print(cls._format_message(f"  {subkey}: {subvalue}", 'success'), flush=True)
            elif isinstance(value, (list, set)):
                print(f"\n{cls._format_message(key + ':', 'header')}", flush=True)
                for item in sorted(value):
                    print(cls._format_message(f"  - {item}", 'success'), flush=True)
            else:
                print(cls._format_message(f"{key}: {value}", 'success'), flush=True)
        
        print("\n" + "="*60 + "\n", flush=True)