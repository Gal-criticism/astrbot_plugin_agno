"""
Markdown 渲染器模块
支持两种渲染方式：
1. Local (本地渲染，使用 playwright)
2. Plain (纯文本，不渲染)

使用方式：
    通过配置 render_mode 参数切换：
    - "local": 使用本地 playwright 渲染
    - "plain": 纯文本输出
"""
from pathlib import Path
from typing import Optional
import asyncio


class MarkdownRenderer:
    def __init__(self, render_mode: str = "plain", render_threshold: int = 200):
        """
        初始化渲染器
        
        Args:
            render_mode: 渲染模式 ("local", "plain")
            render_threshold: 超过此长度使用图片渲染，0 表示始终使用图片
        """
        self.resources_dir = Path(__file__).parent / "resources"
        self.template_dir = self.resources_dir / "template"
        self.render_mode = render_mode
        self.render_threshold = render_threshold
        self._temp_image_path: Optional[Path] = None
        self._playwright_browser = None
        self._playwright_context = None

    async def initialize(self):
        """初始化渲染器"""
        if self.render_mode == "local":
            await self._init_playwright()

    async def _init_playwright(self):
        """初始化 playwright 浏览器"""
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        # 使用 webkit（缓存已有）
        self._playwright_browser = await playwright.chromium.launch()
        self._playwright_context = await self._playwright_browser.new_context(
            viewport={"width": 800, "height": 600}
        )

    def should_render(self, content: str) -> bool:
        """判断是否需要渲染为图片"""
        if self.render_mode == "plain":
            return False
        if self.render_threshold == 0:
            return True
        return len(content) > self.render_threshold

    async def render(self, markdown_content: str, title: str = "结果") -> str:
        """
        渲染 markdown 为图片
        
        Args:
            markdown_content: markdown 内容
            title: 标题
            
        Returns:
            base64 编码的图片或原始内容
        """
        if self.render_mode == "local":
            return await self._render_local(markdown_content, title)
        else:
            return markdown_content  # plain 模式直接返回原始内容

    async def _render_local(self, markdown_content: str, title: str) -> str:
        """使用 playwright 本地渲染"""
        import tempfile
        import uuid
        import base64
        import asyncio

        if not self._playwright_browser:
            await self._init_playwright()

        # 清理之前的临时文件
        if self._temp_image_path and self._temp_image_path.exists():
            try:
                self._temp_image_path.unlink()
            except OSError:
                pass

        # 转换为 HTML
        html_body = self._markdown_to_html(markdown_content)
        
        # 完整 HTML 文档
        full_html = self._wrap_html(html_body, title)

        # 创建新页面并渲染
        page = await self._playwright_context.new_page()
        await page.set_content(full_html, wait_until="networkidle")
        
        # 等待内容渲染完成
        await asyncio.sleep(0.5)
        
        # 截图
        png_bytes = await page.screenshot(type="jpeg", quality=85)
        await page.close()
        
        # 保存为临时文件（使用唯一文件名）
        temp_dir = Path(tempfile.gettempdir()) / "astrbot_agno"
        temp_dir.mkdir(exist_ok=True)
        self._temp_image_path = temp_dir / f"render_{uuid.uuid4().hex[:8]}.jpg"
        
        with open(self._temp_image_path, "wb") as f:
            f.write(png_bytes)
        
        # 返回 base64 编码的图片
        base64_img = base64.b64encode(png_bytes).decode("utf-8")
        return f"base64://{base64_img}"

    def cleanup(self):
        """清理临时文件和浏览器"""
        if self._temp_image_path and self._temp_image_path.exists():
            try:
                self._temp_image_path.unlink()
            except OSError:
                pass
        
        if self._playwright_context:
            try:
                asyncio.create_task(self._playwright_context.close())
            except Exception:
                pass
        
        if self._playwright_browser:
            try:
                asyncio.create_task(self._playwright_browser.close())
            except Exception:
                pass

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
