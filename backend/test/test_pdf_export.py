#!/usr/bin/env python3
"""
测试 PDF 导出功能
"""
import sys
import os
import asyncio
from pathlib import Path

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)
current_directory = os.path.dirname(script_path)
backend_dir = Path(current_directory).parent

# 添加项目路径到 Python 路径
sys.path.insert(0, str(backend_dir))

from app.services.pdf_exporter import PDFExporter


async def test_pdf_export():
    """测试 PDF 导出"""
    print("=" * 80)
    print("PDF 导出功能测试")
    print("=" * 80)
    
    # 创建导出器
    exporter = PDFExporter()
    
    # 测试消息
    messages = [
        {
            "role": "user",
            "content": "你好，请介绍一下 Python"
        },
        {
            "role": "assistant",
            "content": """
# Python 简介

Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。

## 特点

- 简单易学
- 开源免费
- 跨平台
- 丰富的库

## 应用领域

| 领域 | 说明 | 示例 |
|------|------|------|
| Web 开发 | Django, Flask | 网站开发 |
| 数据科学 | NumPy, Pandas | 数据分析 |
| 人工智能 | TensorFlow, PyTorch | 机器学习 |

## 示例代码

```python
def hello_world():
    print("Hello, World!")

hello_world()
```

## 流程图

```mermaid
graph TD
    A[开始] --> B[编写代码]
    B --> C[运行程序]
    C --> D{成功?}
    D -->|是| E[完成]
    D -->|否| F[调试]
    F --> B
```

## 统计图表

```echarts
{
  "title": {"text": "Python 使用趋势"},
  "xAxis": {"data": ["2020", "2021", "2022", "2023", "2024"]},
  "yAxis": {},
  "series": [{
    "type": "line",
    "data": [100, 150, 200, 300, 400],
    "smooth": true
  }]
}
```

## 柱状图

```echarts
{
  "title": {"text": "编程语言排名"},
  "xAxis": {"data": ["Python", "Java", "JavaScript", "C++", "Go"]},
  "yAxis": {},
  "series": [{
    "type": "bar",
    "data": [100, 90, 85, 80, 70]
  }]
}
```

## 饼图

```echarts
{
  "title": {"text": "Python 应用分布"},
  "series": [{
    "type": "pie",
    "data": [
      {"value": 40, "name": "Web 开发"},
      {"value": 30, "name": "数据科学"},
      {"value": 20, "name": "人工智能"},
      {"value": 10, "name": "其他"}
    ]
  }]
}
```
            """
        }
    ]
    
    # 导出 PDF
    output_path = "/tmp/test_chat_export.pdf"
    
    print(f"\n【测试】导出 PDF 到: {output_path}")
    print("-" * 80)
    
    try:
        await exporter.export_chat_to_pdf(
            messages=messages,
            session_id="test_session_001",
            output_path=output_path
        )
        
        print(f"✅ PDF 导出成功!")
        print(f"   文件路径: {output_path}")
        
        # 检查文件是否存在
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"   文件大小: {file_size} 字节")
        else:
            print(f"❌ 文件不存在!")
        
    except Exception as e:
        print(f"❌ PDF 导出失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭浏览器
        await exporter.close()
    
    print("\n" + "=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_pdf_export())