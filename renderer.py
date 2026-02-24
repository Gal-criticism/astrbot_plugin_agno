"""
Markdown 渲染器模块
支持三种渲染方式：
1. AstrBot html_renderer (需要 AstrBot 服务)
2. Local (本地渲染)
3. Plain (纯文本，不渲染)

使用方式：
    通过配置 render_mode 参数切换：
    - "astrbot": 使用 AstrBot 内置渲染服务
    - "local": 使用本地 weasyprint 渲染
    - "plain": 纯文本输出
"""
from pathlib import Path
from typing import Optional


class MarkdownRenderer:
    def __init__(self, render_mode: str = "astrbot", render_threshold: int = 200):
        """
        初始化渲染器
        
        Args:
            render_mode: 渲染模式 ("astrbot", "local", "plain")
            render_threshold: 超过此长度使用图片渲染，0 表示始终使用图片
        """
        self.resources_dir = Path(__file__).parent / "resources"
        self.template_dir = self.resources_dir / "template"
        self.render_mode = render_mode
        self.render_threshold = render_threshold

    async def initialize(self):
        """初始化渲染器"""
        pass

    def should_render(self, content: str) -> bool:
        """判断是否需要渲染为图片"""
        if self.render_mode == "plain":
            return False
        if self.render_threshold == 0:
            return True
        return len(content) > self.render_threshold

    async def render(self, markdown_content: str, title: str = "结果") -> str:
        """
        渲染 markdown 为图片 URL 或 base64
        
        Args:
            markdown_content: markdown 内容
            title: 标题
            
        Returns:
            图片 URL 或 base64
        """
        if self.render_mode == "astrbot":
            return await self._render_astrbot(markdown_content, title)
        elif self.render_mode == "local":
            return await self._render_local(markdown_content, title)
        else:
            return markdown_content  # plain 模式直接返回原始内容

    async def _render_astrbot(self, markdown_content: str, title: str) -> str:
        """使用 AstrBot html_renderer 渲染"""
        from astrbot.api import html_renderer, logger
        
        # 读取模板
        template_path = self.template_dir / "markdown_template.html"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
        else:
            # 使用内置模板
            template_content = _DEFAULT_TEMPLATE
        
        # 将 markdown 转换为 HTML
        html_content = self._markdown_to_html(markdown_content)
        
        # 渲染模板
        url = await html_renderer.render_custom_template(
            template_content,
            {"content": html_content, "title": title, "font": ""},
            True,
            {"type": "jpeg", "quality": 85}
        )
        return url

    async def _render_local(self, markdown_content: str, title: str) -> str:
        """使用本地库渲染 (markdown2 + weasyprint)"""
        import base64
        from weasyprint import HTML
        
        # 转换为 HTML
        html_body = self._markdown_to_html(markdown_content)
        
        # 完整 HTML 文档
        full_html = self._wrap_html(html_body, title)
        
        # 渲染为 PDF
        pdf_bytes = HTML(string=full_html).write_pdf()
        
        # 转换为 base64
        return f"base64://{base64.b64encode(pdf_bytes).decode()}"

    def _markdown_to_html(self, markdown: str) -> str:
        """将 markdown 转换为简单 HTML"""
        import re
        
        # 转义 HTML 特殊字符
        markdown = (markdown
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))
        
        lines = markdown.split("\n")
        html_lines = []
        in_code_block = False
        in_list = False
        
        for line in lines:
            line = line.rstrip()
            
            # 代码块
            if line.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    html_lines.append('<pre><code>')
                else:
                    in_code_block = False
                    html_lines.append('</code></pre>')
                continue
            
            if in_code_block:
                html_lines.append(line)
                continue
            
            # 标题
            if line.startswith("### "):
                html_lines.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith("## "):
                html_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith("# "):
                html_lines.append(f'<h1>{line[2:]}</h1>')
            # 列表
            elif line.startswith("- ") or line.startswith("* "):
                if not in_list:
                    in_list = True
                    html_lines.append('<ul>')
                html_lines.append(f'<li>{line[2:]}</li>')
            # 分割线
            elif line == "---" or line == "***":
                html_lines.append('<hr>')
            # 空行
            elif not line:
                if in_list:
                    in_list = False
                    html_lines.append('</ul>')
                html_lines.append('<br>')
            # 普通段落（检测粗体和斜体）
            else:
                if in_list:
                    in_list = False
                    html_lines.append('</ul>')
                # 处理粗体 **text**
                line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                # 处理行内代码 `code`
                line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
                # 处理链接 [text](url)
                line = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', line)
                html_lines.append(f'<p>{line}</p>')
        
        if in_list:
            html_lines.append('</ul>')
            
        return "\n".join(html_lines)

    def _wrap_html(self, body: str, title: str) -> str:
        """包装为完整 HTML 文档"""
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
            background: #fff;
            color: #333;
            line-height: 1.6;
        }}
        h1, h2, h3 {{ color: #1a1a1a; margin-top: 1.5em; }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', monospace;
        }}
        pre {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 5px 0; }}
        hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
        a {{ color: #0066cc; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {body}
</body>
</html>'''


# 全局单例
_renderer: Optional[MarkdownRenderer] = None


def get_renderer() -> MarkdownRenderer:
    global _renderer
    if _renderer is None:
        _renderer = MarkdownRenderer()
    return _renderer


# 默认模板（当模板文件不存在时使用）
_DEFAULT_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
        }
        .content {
            padding: 24px;
            line-height: 1.7;
        }
        h1, h2, h3 { color: #1a1a1a; margin: 1em 0 0.5em; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
        pre { background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; overflow-x: auto; }
        pre code { background: none; color: inherit; padding: 0; }
        ul, ol { padding-left: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>{{ title }}</h1></div>
        <div class="content">{{ content }}</div>
    </div>
</body>
</html>'''
