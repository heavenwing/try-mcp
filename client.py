import asyncio
import json
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.types import TextContent
from mcp.client.stdio import stdio_client

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.ai_client = OpenAI(
            base_url="http://localhost:1234/v1",  # LM Studio的本地地址
            api_key="lm-studio",  # 任意非空字符串即可
        )

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available tools"""
        messages = [{"role": "user", "content": query}]

        # Assuming you have a method to get available tools from your session
        response = await self.session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in response.tools
        ]

        # Initial OpenAI API call
        first_response = self.ai_client.chat.completions.create(
            model="qwen2.5-7b-instruct-1m",
            max_tokens=1000,
            messages=messages,
            tools=available_tools,
        )

        # Process response and handle function calls
        final_text = []

        # detect how the LLM call was completed:
        # tool_calls: if the LLM used a tool
        # stop: If the LLM generated a general response, e.g. "Hello, how can I help you today?"
        stop_reason = (
            "tool_calls"
            if first_response.choices[0].message.tool_calls is not None
            else first_response.choices[0].finish_reason
        )

        if stop_reason == "tool_calls":
            # Extract tool use details from response
            for tool_call in first_response.choices[0].message.tool_calls:
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments

                # arguments = (
                #     json.loads(tool_call.function.arguments)
                #     if isinstance(tool_call.function.arguments, str)
                #     else tool_call.function.arguments
                # )
                # Call the tool with the arguments using our callable initialized in the tools dict
                # tool_result = await tools[tool_call.function.name]["callable"](**arguments)
                tool_result = await self.session.call_tool(
                    function_name, eval(function_args)
                )
                final_text.append(
                    f"[Calling function {function_name} with args {function_args}]"
                )

                # Add the tool result to the messages list
                for tool_result_content in tool_result.content:
                    if isinstance(tool_result_content, TextContent):
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": tool_result_content.text,
                            }
                        )

            # Query LLM with the user query and the tool results
            new_response = self.ai_client.chat.completions.create(
                model="qwen2.5-7b-instruct-1m",
                messages=messages,
            )

        elif stop_reason == "stop":
            # If the LLM stopped on its own, use the first response
            new_response = first_response

        else:
            raise ValueError(f"Unknown stop reason: {stop_reason}")

        # Add the LLM response to the messages list
        messages.append(
            {"role": "assistant", "content": new_response.choices[0].message.content}
        )
        final_text.append(new_response.choices[0].message.content)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
