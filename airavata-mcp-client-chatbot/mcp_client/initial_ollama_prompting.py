import asyncio
import os
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from mcp_use import MCPAgent, MCPClient


async def main():
    # Load environment variables (if needed)
    load_dotenv()

    # MCP server config (replace or extend as needed)
    config = {
        "mcpServers": {
            "playwright": {
                "command": "npx",
                "args": ["@playwright/mcp@latest"],
                "env": {
                    "DISPLAY": ":1"
                }
            }
        }
    }

    # Initialize MCPClient
    client = MCPClient.from_dict(config)

    # Use Ollama with a local model (make sure it's already running via `ollama run llama3`)
    llm = Ollama(model="qwen-4b", temperature=0.1, max_tokens=1000)

    # Create MCP Agent
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    # Run a query
    result = await agent.run("What are the best fruiting plants to grow indoors?")
    print(f"\nResult: {result}")

if __name__ == "__main__":
    asyncio.run(main())
