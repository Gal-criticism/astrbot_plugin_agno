#!/usr/bin/env python3
"""运行此脚本获取AgentOS上的agents/teams/workflows的id"""

import asyncio
from agno.client import AgentOSClient

AGNO_BASE_URL = "http://192.168.254.193:8001"


async def main():
    client = AgentOSClient(base_url=AGNO_BASE_URL)
    try:
        config = await client.aget_config()
        print("=" * 50)
        print(f"Connected to: {config.name or config.os_id}")
        print("=" * 50)

        if config.agents:
            print("\nAgents:")
            for a in config.agents:
                print(f"  id={a.id!r}, name={a.name!r}")
        else:
            print("\nNo agents")

        if config.teams:
            print("\nTeams:")
            for t in config.teams:
                print(f"  id={t.id!r}, name={t.name!r}")
        else:
            print("\nNo teams")

        if config.workflows:
            print("\nWorkflows:")
            for w in config.workflows:
                print(f"  id={w.id!r}, name={w.name!r}")
        else:
            print("\nNo workflows")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
