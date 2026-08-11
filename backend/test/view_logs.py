#!/usr/bin/env python3
"""
日志查看工具

提供便捷的日志查看功能，包括：
- 查看最新的日志
- 按级别过滤日志
- 按时间范围过滤日志
- 搜索日志内容
- 实时监控日志
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional


class LogViewer:
    """日志查看器"""
    
    def __init__(self, log_dir: str = None):
        """
        初始化日志查看器
        
        Args:
            log_dir: 日志目录路径，默认为 backend/logs
        """
        if log_dir is None:
            # 获取日志目录路径
            backend_dir = Path(__file__).parent
            self.log_dir = backend_dir / "logs"
        else:
            self.log_dir = Path(log_dir)
        
        # 日志文件映射
        self.log_files = {
            'app': self.log_dir / "app.log",
            'error': self.log_dir / "error.log",
            'request': self.log_dir / "request.log",
            'agent': self.log_dir / "agent.log",
            'database': self.log_dir / "database.log",
            'debug': self.log_dir / "debug.log"
        }
    
    def view_log(
        self,
        log_type: str = 'app',
        lines: int = 50,
        level: Optional[str] = None,
        follow: bool = False
    ):
        """
        查看日志
        
        Args:
            log_type: 日志类型（app, error, request, agent, database, debug）
            lines: 显示的行数
            level: 日志级别过滤（INFO, ERROR, DEBUG等）
            follow: 是否实时监控日志
        """
        log_file = self.log_files.get(log_type)
        
        if not log_file or not log_file.exists():
            print(f"❌ 日志文件不存在: {log_file}")
            return
        
        print(f"\n{'='*80}")
        print(f"📋 日志文件: {log_file.name}")
        print(f"{'='*80}\n")
        
        if follow:
            # 实时监控日志
            self._follow_log(log_file, level)
        else:
            # 查看历史日志
            self._read_log(log_file, lines, level)
    
    def _read_log(self, log_file: Path, lines: int, level: Optional[str]):
        """
        读取日志文件
        
        Args:
            log_file: 日志文件路径
            lines: 显示的行数
            level: 日志级别过滤
        """
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                
                # 过滤日志级别
                if level:
                    filtered_lines = [
                        line for line in all_lines
                        if f"[{level}]" in line
                    ]
                else:
                    filtered_lines = all_lines
                
                # 显示最新的N行
                display_lines = filtered_lines[-lines:]
                
                for line in display_lines:
                    print(line.rstrip())
                
                print(f"\n✅ 显示最新 {len(display_lines)} 行日志")
                
        except Exception as e:
            print(f"❌ 读取日志失败: {e}")
    
    def _follow_log(self, log_file: Path, level: Optional[str]):
        """
        实时监控日志
        
        Args:
            log_file: 日志文件路径
            level: 日志级别过滤
        """
        print("🔍 实时监控日志（按 Ctrl+C 退出）...\n")
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                # 跳到文件末尾
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        if level is None or f"[{level}]" in line:
                            print(line.rstrip())
                    else:
                        # 短暂休眠，避免CPU占用过高
                        import time
                        time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n✅ 停止监控")
        except Exception as e:
            print(f"❌ 监控日志失败: {e}")
    
    def search_log(self, keyword: str, log_type: str = 'app'):
        """
        搜索日志内容
        
        Args:
            keyword: 搜索关键词
            log_type: 日志类型
        """
        log_file = self.log_files.get(log_type)
        
        if not log_file or not log_file.exists():
            print(f"❌ 日志文件不存在: {log_file}")
            return
        
        print(f"\n{'='*80}")
        print(f"🔍 搜索关键词: {keyword}")
        print(f"📋 日志文件: {log_file.name}")
        print(f"{'='*80}\n")
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                matches = []
                for line_num, line in enumerate(f, 1):
                    if keyword.lower() in line.lower():
                        matches.append((line_num, line.rstrip()))
                
                if matches:
                    for line_num, line in matches:
                        print(f"[{line_num:05d}] {line}")
                    print(f"\n✅ 找到 {len(matches)} 条匹配记录")
                else:
                    print(f"❌ 未找到匹配记录")
                    
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
    
    def list_logs(self):
        """列出所有日志文件"""
        print(f"\n{'='*80}")
        print(f"📋 日志目录: {self.log_dir}")
        print(f"{'='*80}\n")
        
        if not self.log_dir.exists():
            print(f"❌ 日志目录不存在")
            return
        
        for log_type, log_file in self.log_files.items():
            if log_file.exists():
                size = log_file.stat().st_size
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                print(f"✅ {log_type:10s} - {log_file.name:20s} - {size:>10,} bytes - {mtime}")
            else:
                print(f"❌ {log_type:10s} - {log_file.name:20s} - 不存在")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Agent Backend 日志查看工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 查看最新的50行应用日志
  python view_logs.py app
  
  # 查看最新的100行错误日志
  python view_logs.py error --lines 100
  
  # 查看所有ERROR级别的日志
  python view_logs.py app --level ERROR
  
  # 实时监控应用日志
  python view_logs.py app --follow
  
  # 搜索包含"session"的日志
  python view_logs.py app --search session
  
  # 列出所有日志文件
  python view_logs.py --list
        """
    )
    
    parser.add_argument(
        'log_type',
        nargs='?',
        default='app',
        choices=['app', 'error', 'request', 'agent', 'database', 'debug'],
        help='日志类型（默认: app）'
    )
    
    parser.add_argument(
        '--lines',
        type=int,
        default=50,
        help='显示的行数（默认: 50）'
    )
    
    parser.add_argument(
        '--level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='日志级别过滤'
    )
    
    parser.add_argument(
        '--follow',
        action='store_true',
        help='实时监控日志'
    )
    
    parser.add_argument(
        '--search',
        type=str,
        help='搜索关键词'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有日志文件'
    )
    
    args = parser.parse_args()
    
    viewer = LogViewer()
    
    if args.list:
        viewer.list_logs()
    elif args.search:
        viewer.search_log(args.search, args.log_type)
    else:
        viewer.view_log(args.log_type, args.lines, args.level, args.follow)


if __name__ == "__main__":
    main()