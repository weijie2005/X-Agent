"""
PDF 导出服务

使用 Playwright 无头浏览器渲染生成 PDF。
"""
import logging
import os
import tempfile
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class PDFExporter:
    """
    PDF 导出器
    
    使用 Playwright 无头浏览器渲染生成 PDF。
    """
    
    def __init__(self):
        """初始化 PDF 导出器"""
        self.browser = None
        self.playwright = None
        logger.info("Initialized PDFExporter")
    
    async def init_browser(self):
        """
        初始化浏览器
        
        延迟初始化，只在需要时启动浏览器。
        """
        if self.browser is None:
            try:
                from playwright.async_api import async_playwright
                
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=True)
                
                logger.info("Browser initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize browser: {e}")
                raise
    
    async def export_chat_to_pdf(
        self,
        messages: List[Dict[str, Any]],
        session_id: str,
        output_path: str
    ) -> str:
        """
        导出聊天记录到 PDF
        
        Args:
            messages: 消息列表
            session_id: 会话 ID
            output_path: 输出路径
        
        Returns:
            PDF 文件路径
        """
        try:
            # 初始化浏览器
            await self.init_browser()
            
            # 生成 HTML
            html_content = self._generate_html(messages, session_id)
            
            # 保存临时 HTML 文件
            html_path = output_path.replace('.pdf', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 使用 Playwright 渲染 PDF
            page = await self.browser.new_page()
            
            try:
                # 加载 HTML
                await page.goto(f'file://{html_path}')
                
                # 等待页面加载完成
                await page.wait_for_load_state('networkidle')
                
                # 等待图表渲染
                await asyncio.sleep(2)
                
                # 生成 PDF
                await page.pdf(
                    path=output_path,
                    format='A4',
                    print_background=True,
                    margin={
                        'top': '20px',
                        'right': '20px',
                        'bottom': '20px',
                        'left': '20px'
                    }
                )
                
                logger.info(f"PDF exported successfully: {output_path}")
                
                return output_path
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"Failed to export PDF: {e}")
            raise
    
    def _generate_html(
        self,
        messages: List[Dict[str, Any]],
        session_id: str
    ) -> str:
        """
        生成 HTML 内容
        
        Args:
            messages: 消息列表
            session_id: 会话 ID
        
        Returns:
            HTML 内容
        """
        # HTML 模板
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Export - {session_id}</title>
    <style>
        {styles}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Agent Chatbot Export</h1>
        <div class="meta">
            <p><strong>Session ID:</strong> {session_id}</p>
            <p><strong>Export Time:</strong> {export_time}</p>
        </div>
        
        <div class="messages">
            {messages_html}
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js"></script>
    <script>
        // 初始化 Mermaid
        mermaid.initialize({ startOnLoad: true });
        
        // 渲染 ECharts
        document.addEventListener('DOMContentLoaded', function() {
            const echartsElements = document.querySelectorAll('.echarts-chart');
            echartsElements.forEach((element, index) => {
                try {
                    const config = JSON.parse(element.getAttribute('data-config'));
                    const chart = echarts.init(element);
                    chart.setOption(config);
                } catch (error) {
                    console.error('ECharts render error:', error);
                }
            });
        });
    </script>
</body>
</html>
        """
        
        # CSS 样式
        styles = """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        h1 {
            color: #1890ff;
            border-bottom: 2px solid #1890ff;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .meta {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 30px;
        }
        
        .meta p {
            margin: 5px 0;
        }
        
        .messages {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .message {
            display: flex;
            gap: 15px;
        }
        
        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }
        
        .message.user .message-avatar {
            background: #1890ff;
        }
        
        .message.assistant .message-avatar {
            background: #52c41a;
        }
        
        .message-content {
            flex: 1;
            padding: 15px;
            border-radius: 8px;
            background: #f9f9f9;
        }
        
        .message.user .message-content {
            background: #e3f2fd;
        }
        
        .message-content h1, .message-content h2, .message-content h3 {
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        
        .message-content p {
            margin-bottom: 1em;
        }
        
        .message-content ul, .message-content ol {
            margin-left: 2em;
            margin-bottom: 1em;
        }
        
        .message-content table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1em;
        }
        
        .message-content th, .message-content td {
            border: 1px solid #e8e8e8;
            padding: 8px 12px;
            text-align: left;
        }
        
        .message-content th {
            background: #f5f5f5;
            font-weight: 600;
        }
        
        .message-content pre {
            background: #f5f5f5;
            padding: 12px;
            border-radius: 4px;
            overflow-x: auto;
            margin-bottom: 1em;
        }
        
        .message-content code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        
        .mermaid-chart {
            text-align: center;
            margin: 1em 0;
        }
        
        .echarts-chart {
            width: 100%;
            height: 400px;
            margin: 1em 0;
        }
        
        @media print {
            body {
                background: white;
            }
            
            .container {
                box-shadow: none;
            }
        }
        """
        
        # 生成消息 HTML
        messages_html = ""
        for message in messages:
            role = message.get('role', 'assistant')
            content = message.get('content', '')
            
            # 渲染 Markdown（简化版）
            rendered_content = self._render_markdown(content)
            
            messages_html += f"""
            <div class="message {role}">
                <div class="message-avatar">
                    { '👤' if role == 'user' else '🤖' }
                </div>
                <div class="message-content">
                    {rendered_content}
                </div>
            </div>
            """
        
        # 填充模板
        html_content = html_template.format(
            session_id=session_id,
            export_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            styles=styles,
            messages_html=messages_html
        )
        
        return html_content
    
    def _render_markdown(self, content: str) -> str:
        """
        渲染 Markdown 内容（简化版）
        
        Args:
            content: Markdown 内容
        
        Returns:
            HTML 内容
        """
        import re
        
        # 简化的 Markdown 渲染
        # 在实际应用中应该使用 marked.js 或其他库
        
        # 处理代码块
        content = re.sub(
            r'```(\w+)\n(.*?)\n```',
            r'<pre><code class="language-\1">\2</code></pre>',
            content,
            flags=re.DOTALL
        )
        
        # 处理 Mermaid 图表
        content = re.sub(
            r'<pre><code class="language-mermaid">(.*?)</code></pre>',
            r'<div class="mermaid-chart"><div class="mermaid">\1</div></div>',
            content,
            flags=re.DOTALL
        )
        
        # 处理 ECharts 图表
        content = re.sub(
            r'<pre><code class="language-echarts">(.*?)</code></pre>',
            r'<div class="echarts-chart" data-config="\1"></div>',
            content,
            flags=re.DOTALL
        )
        
        # 处理标题
        content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        
        # 处理列表
        content = re.sub(r'^- (.*?)$', r'<li>\1</li>', content, flags=re.MULTILINE)
        content = re.sub(r'(<li>.*?</li>\n?)+', r'<ul>\g<0></ul>', content)
        
        # 处理段落
        paragraphs = content.split('\n\n')
        rendered = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph and not paragraph.startswith('<'):
                rendered.append(f'<p>{paragraph}</p>')
            else:
                rendered.append(paragraph)
        
        return '\n'.join(rendered)
    
    async def close(self):
        """
        关闭浏览器
        """
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        
        logger.info("Browser closed")


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test():
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

Python 是一种高级编程语言。

## 特点

- 简单易学
- 开源免费
- 跨平台

## 示例代码

```python
print("Hello, World!")
```

## 流程图

```mermaid
graph TD
    A[开始] --> B[处理]
    B --> C[结束]
```

## 统计图表

```echarts
{
  "title": {"text": "Python 使用统计"},
  "xAxis": {"data": ["2020", "2021", "2022", "2023"]},
  "yAxis": {},
  "series": [{"type": "bar", "data": [100, 200, 300, 400]}]
}
```
                """
            }
        ]
        
        # 导出 PDF
        output_path = "/tmp/test_chat.pdf"
        await exporter.export_chat_to_pdf(messages, "test_session", output_path)
        
        print(f"PDF exported to: {output_path}")
        
        # 关闭浏览器
        await exporter.close()
    
    asyncio.run(test())