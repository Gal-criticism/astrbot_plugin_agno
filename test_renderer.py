"""
渲染器测试用例
"""
import asyncio
from renderer import MarkdownRenderer

# 测试 markdown 数据
TEST_MARKDOWN = """## 📊 GitHub仓库最新更新情况总结

根据您的GitHub应用权限，我可以访问**Gal-criticism**组织下的20个仓库。以下是最近更新的仓库情况：

### 🏆 **最近更新的仓库（Top 5）**

1. **astrbot_plugin_agno** (2026-02-24 11:32:48 UTC)
   - **描述**: astrbot plugin for agno framework
   - **状态**: ⭐ 0 | 🍴 0 | 🐛 0
   - **链接**: https://github.com/Gal-criticism/astrbot_plugin_agno

2. **agent-server** (2026-02-20 04:43:32 UTC)
   - **描述**: agent server

### 📈 **活跃度分析**

- **最近一周更新**: 3个仓库
- **最近一个月更新**: 6个仓库

### 💡 **建议**

1. 关注最新项目
2. 活跃度提升

```python
# 代码测试
def hello():
    print("Hello World!")
```

需要我帮您查看某个特定仓库的详细信息吗？
"""


async def test_render():
    """测试渲染功能"""
    print("=" * 50)
    print("测试 1: plain 模式")
    print("=" * 50)
    
    renderer = MarkdownRenderer(render_mode="plain")
    await renderer.initialize()
    
    result = await renderer.render(TEST_MARKDOWN, title="测试纯文本")
    print(f"结果类型: {type(result)}")
    print(f"结果: {result[:100]}...")
    
    print("\n" + "=" * 50)
    print("测试 2: local 模式")
    print("=" * 50)
    
    renderer2 = MarkdownRenderer(render_mode="local")
    await renderer2.initialize()
    
    try:
        result2 = await renderer2.render(TEST_MARKDOWN, title="测试本地渲染")
        print(f"结果类型: {type(result)}")
        if result2.startswith("base64://"):
            print(f"Base64 长度: {len(result2)}")
        else:
            print(f"结果: {result2[:100]}...")
    except Exception as e:
        print(f"本地渲染失败: {e}")
        print("提示: 需要安装依赖: pip install markdown2 weasyprint")
    
    print("\n" + "=" * 50)
    print("测试 3: astrbot 模式")
    print("=" * 50)
    
    renderer3 = MarkdownRenderer(render_mode="astrbot", render_threshold=0)
    await renderer3.initialize()
    
    try:
        result3 = await renderer3.render(TEST_MARKDOWN, title="测试渲染")
        print(f"结果类型: {type(result3)}")
        if result3.startswith("http"):
            print(f"图片URL: {result3[:100]}...")
        else:
            print(f"结果: {result3[:100]}...")
    except Exception as e:
        print(f"渲染失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试 4: should_render 判断")
    print("=" * 50)
    
    renderer4 = MarkdownRenderer(render_mode="astrbot", render_threshold=100)
    print(f"render_mode=plain should_render: {renderer4.should_render('a' * 50)}")
    renderer4.render_mode = "plain"
    print(f"render_mode=plain should_render: {renderer4.should_render('a' * 50)}")
    renderer4.render_mode = "astrbot"
    print(f"render_mode=astrbot should_render: {renderer4.should_render('a' * 50)}")
    print(f"render_mode=astrbot should_render: {renderer4.should_render('a' * 150)}")


if __name__ == "__main__":
    asyncio.run(test_render())
