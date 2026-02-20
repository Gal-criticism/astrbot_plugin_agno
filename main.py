from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig


@register("agno", "AGNO-AGENTOS集成", "AstrBot集成AGNO（https://docs.agno.com/），使其能否复用当前已部署AgentOS能力的插件", "1.0.0")
class AgnoPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.client = None
        self.base_url = None

    async def initialize(self):
        from agno.client import AgentOSClient
        import httpx
        self.base_url = self.config.get("agentos_base_url", "http://192.168.254.193:8001")
        logger.info(f"Connecting to AgentOS: {self.base_url}")

        # 测试网络连接
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/health", follow_redirects=True)
                logger.info(f"AgentOS health check: {resp.status_code}")
        except Exception as e:
            logger.warning(f"AgentOS health check failed: {e}")

        self.client = AgentOSClient(base_url=self.base_url, timeout=300)
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
            logger.exception("gal_resources error")
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
            yield event.plain_result(" ")
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
            yield event.plain_result(" ")
            result = await self.client.run_agent(agent_id="knowledge-news-agent", message=msg)
            yield event.plain_result(result.content if result.content else "无响应")
        except Exception as e:
            logger.exception("gal_news error")
            yield event.plain_result(f"执行失败: {e}")

    @gal.command("gh")
    async def gal_gh(self, event: AstrMessageEvent):
        """GitHub Agent: /gh <问题>"""
        if not self.client:
            yield event.plain_result("未连接到AgentOS服务")
            return

        msg = event.message_str.strip()
        if not msg:
            yield event.plain_result("用法: /gh <问题>")
            return

        try:
            yield event.plain_result(" ")
            result = await self.client.run_agent(agent_id="github_agent", message=msg)
            yield event.plain_result(result.content if result.content else "无响应")
        except Exception as e:
            logger.exception("gal_gh error")
            yield event.plain_result(f"执行失败: {e}")

    @gal.command("test")
    async def gal_test(self, event: AstrMessageEvent):
        """测试AgentOS连接"""
        import httpx
        if not self.base_url:
            yield event.plain_result("未配置AgentOS地址")
            return

        try:
            yield event.plain_result(f"测试连接: {self.base_url}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/health", follow_redirects=True)
                yield event.plain_result(f"Health check: {resp.status_code}\n{resp.text}")
        except Exception as e:
            yield event.plain_result(f"连接失败: {e}")

    async def terminate(self):
        pass
