"""Query command to interact with AI."""
import discord
import logging
import os
import json
import traceback
from openai import OpenAI
from ..mcp_client import mcp_client

logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def execute(interaction: discord.Interaction, question: str, use_web_search: bool = True):
    """Execute the query command.

    Args:
        interaction: The Discord interaction object
        question: The question to ask the AI
        use_web_search: Whether to use web search capability (default: True)
    """
    logger.info(f"AI query from {interaction.user}: {question} (web search: {use_web_search})")
    await interaction.response.defer()

    try:
        # Prepare tools list using modern MCP format
        tools = []
        
        # Add web search tool if enabled
        if use_web_search:
            tools.append({"type": "web_search"})
        
        # Add MCP filesystem tools if connected
        if mcp_client.session:
            try:
                # Convert MCP tools to OpenAI tools format for legacy compatibility
                mcp_tools = mcp_client.get_openai_tools()
                tools.extend(mcp_tools)
                logger.info(f"Added {len(mcp_tools)} MCP tools to query")
            except Exception as e:
                logger.warning(f"Could not add MCP tools: {e}")
        else:
            logger.warning("MCP client not connected")
        
        # Create response with simplified parameters
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role": "user", "content": question}],
            tools=tools
        )

        # Handle tool calls if present
        if response.output and len(response.output) > 0:
            first_item = response.output[0]
            
            # Check if we have a function tool call
            if type(first_item).__name__ == 'ResponseFunctionToolCall':
                logger.info(f"Processing function tool call: {first_item.name}")
                
                # Execute the tool call
                tool_name = first_item.name
                args = json.loads(first_item.arguments) if isinstance(first_item.arguments, str) else first_item.arguments
                
                logger.debug(f"Tool: {tool_name}, Args: {args}")
                
                # Execute MCP tool if available
                if tool_name in [tool.name for tool in mcp_client.tools]:
                    result = await mcp_client.call_tool(tool_name, args)
                    tool_result = json.dumps(result)
                    logger.debug(f"Tool result: {result}")
                else:
                    tool_result = json.dumps({"error": f"Unknown tool '{tool_name}'"})
                    logger.warning(f"Unknown tool: {tool_name}")
                
                # Build messages for the follow-up request
                messages = [
                    {"role": "user", "content": question},
                    {
                        "type": "function_call",
                        "call_id": first_item.call_id,
                        "name": tool_name,
                        "arguments": json.dumps(args)
                    },
                    {
                        "type": "function_call_output", 
                        "call_id": first_item.call_id,
                        "output": tool_result
                    }
                ]
                
                # Get final response with tool results
                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=messages,
                    tools=tools
                )
        
        # Extract final response content with debug logging
        ai_response = ""
        logger.debug(f"Response output length: {len(response.output) if response.output else 0}")
        
        if response.output and len(response.output) > 0:
            logger.debug(f"Response output items: {[type(item).__name__ for item in response.output]}")
            
            # Get the final assistant message
            for i, item in enumerate(reversed(response.output)):
                logger.debug(f"Item {i}: type={type(item).__name__}, hasattr role={hasattr(item, 'role')}")
                if hasattr(item, 'role'):
                    logger.debug(f"Item {i} role: {item.role}")
                    
                if hasattr(item, 'role') and item.role == 'assistant':
                    logger.debug(f"Found assistant message: content={hasattr(item, 'content')}")
                    if hasattr(item, 'content') and item.content:
                        logger.debug(f"Content type: {type(item.content)}, content: {item.content}")
                        if isinstance(item.content, list) and len(item.content) > 0:
                            logger.debug(f"Content[0] type: {type(item.content[0])}")
                            if hasattr(item.content[0], 'text'):
                                ai_response = item.content[0].text
                            else:
                                ai_response = str(item.content[0])
                        elif isinstance(item.content, str):
                            ai_response = item.content
                    break
        
        if not ai_response:
            ai_response = "I apologize, but I couldn't generate a response."
        
        # Format and send response
        formatted_response = f"{interaction.user.mention} Asked: {question}\n\n{ai_response}"
        await interaction.followup.send(formatted_response)
        logger.info(f"AI response to {interaction.user}: {ai_response[:50]}...")

    except Exception as e:
        logger.error(f"Error querying OpenAI API: {e}")
        logger.error(f"Full error details: {traceback.format_exc()}")
        await interaction.followup.send("Sorry, I encountered an error while processing your request.")