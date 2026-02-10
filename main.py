from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig


@register("agno", "AGNO-AGENTOS集成", "AstrBot集成AGNO（https://docs.agno.com/），使其能否复用当前已部署AgentOS能力的插件", "1.0.0")
class AgnoPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.client = None

    async def initialize(self):
        from agno.client import AgentOSClient
        base_url = self.config.get("agentos_base_url", "http://192.168.254.193:8001")
        self.client = AgentOSClient(base_url=base_url)
        try:
            config = await self.client.aget_config()
            logger.info(f"Connected to AgentOS: {config.name or config.os_id}")
            for agent in config.agents:
                logger.info(f"Loaded agent: {agent.id} ({agent.name})")
        except Exception as e:
            logger.error(f"Failed to connect to AgentOS: {e}")

    @filter.command_group("gal")
    def gal(self):
        """AGNO AgentOS 指令组"""
        pass

    @gal.command("resources")
    async def gal_resources(self, event: AstrMessageEvent):
        """列出所有可用的agents、teams、workflows"""
        if not self.client:
            yield event.plain_result("未连接到AgentOS服务")
            return

        try:
            config = await self.client.aget_config()
            msg = []

            if config.agents:
                msg.append("Agents:")
                for a in config.agents:
                    msg.append(f"  - {a.id} ({a.name})")
            else:
                msg.append("无可用Agents")

            if config.teams:
                msg.append("\nTeams:")
                for t in config.teams:
                    msg.append(f"  - {t.id} ({t.name})")
            else:
                msg.append("\n无可用Teams")

            if config.workflows:
                msg.append("\nWorkflows:")
                for w in config.workflows:
                    msg.append(f"  - {w.id} ({w.name})")
            else:
                msg.append("\n无可用Workflows")

            yield event.plain_result("\n".join(msg))
        except Exception as e:
            yield event.plain_result(f"获取失败: {e}")

    @gal.command("game")
    async def gal_game(self, event: AstrMessageEvent):
        """游戏Agent: /gal game <问题>"""
        if not self.client:
            yield event.plain_result("未连接到AgentOS服务")
            return

        msg = event.message_str.strip()
        if not msg:
            yield event.plain_result("用法: /gal game <问题>")
            return

        try:
            result = await self.client.run_agent(agent_id="knowledge-game-agent", message=msg)
            yield event.plain_result(result.content if result.content else "无响应")
        except Exception as e:
            yield event.plain_result(f"执行失败: {e}")

    @gal.command("news")
    async def gal_news(self, event: AstrMessageEvent):
        """新闻Agent: /gal news <问题>"""
        if not self.client:
            yield event.plain_result("未连接到AgentOS服务")
            return

        msg = event.message_str.strip()
        if not msg:
            yield event.plain_result("用法: /gal news <问题>")
            return

        try:
            result = await self.client.run_agent(agent_id="knowledge-news-agent", message=msg)
            yield event.plain_result(result.content if result.content else "无响应")
        except Exception as e:
            yield event.plain_result(f"执行失败: {e}")

    async def terminate(self):
        pass
