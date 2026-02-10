"""
单独测试AGNO插件命令的脚本
用法: python test_commands.py <命令> [参数]

命令:
    resources        列出所有agents/teams/workflows
    game <问题>       测试游戏Agent
    news <问题>       测试新闻Agent

示例:
    python test_commands.py resources
    python test_commands.py game 原神最新消息
    python test_commands.py news 今天的科技新闻
"""
import asyncio
import sys
import json
import os

# 尝试从配置文件读取地址
def get_base_url():
    config_path = "_conf_schema.json"
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
            return config.get("agentos_base_url", {}).get("default", "http://192.168.254.193:8001")
    return "http://192.168.254.193:8001"

AGNO_BASE_URL = get_base_url()


async def get_client():
    """获取AgentOS客户端"""
    from agno.client import AgentOSClient
    return AgentOSClient(base_url=AGNO_BASE_URL)


async def cmd_resources():
    """列出所有资源"""
    print("\n" + "=" * 50)
    print("命令: gal.resources")
    print("=" * 50)

    client = await get_client()
    try:
        config = await client.aget_config()
        print(f"已连接到: {config.name or config.os_id}\n")

        if config.agents:
            print("Agents:")
            for a in config.agents:
                print(f"  - {a.id} ({a.name})")

        if config.teams:
            print("\nTeams:")
            for t in config.teams:
                print(f"  - {t.id} ({t.name})")

        if config.workflows:
            print("\nWorkflows:")
            for w in config.workflows:
                print(f"  - {w.id} ({w.name})")

        return True
    except Exception as e:
        print(f"错误: {e}")
        return False


async def cmd_game(question: str, stream: bool = False):
    """测试游戏Agent"""
    print("\n" + "=" * 50)
    print(f"命令: gal.game '{question}'")
    print(f"流式: {stream}")
    print("=" * 50)

    if not question:
        print("用法: python test_commands.py game <问题>")
        return False

    client = await get_client()
    try:
        if stream:
            print("\n流式响应:")
            async for chunk in client.run_agent_stream(agent_id="knowledge-game-agent", message=question):
                if chunk.content:
                    print(chunk.content, end="", flush=True)
            print()
        else:
            result = await client.run_agent(agent_id="knowledge-game-agent", message=question)
            print(f"\n响应: {result.content}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False


async def cmd_news(question: str, stream: bool = False):
    """测试新闻Agent"""
    print("\n" + "=" * 50)
    print(f"命令: gal.news '{question}'")
    print(f"流式: {stream}")
    print("=" * 50)

    if not question:
        print("用法: python test_commands.py news <问题>")
        return False

    client = await get_client()
    try:
        if stream:
            print("\n流式响应:")
            async for chunk in client.run_agent_stream(agent_id="knowledge-news-agent", message=question):
                if chunk.content:
                    print(chunk.content, end="", flush=True)
            print()
        else:
            result = await client.run_agent(agent_id="knowledge-news-agent", message=question)
            print(f"\n响应: {result.content}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n可用命令: resources, game <问题>, news <问题>")
        print("选项: --stream 启用流式响应")
        return

    command = sys.argv[1]
    use_stream = "--stream" in sys.argv

    # 过滤掉 --stream 参数
    args = [a for a in sys.argv[2:] if a != "--stream"]

    if command == "resources":
        success = asyncio.run(cmd_resources())
    elif command == "game":
        question = " ".join(args)
        success = asyncio.run(cmd_game(question, stream=use_stream))
    elif command == "news":
        question = " ".join(args)
        success = asyncio.run(cmd_news(question, stream=use_stream))
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        return

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
