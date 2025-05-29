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
    # Log the query for debugging
    logger.info(f"AI query from {interaction.user}: {question} (web search enabled)")

    await interaction.response.defer()

    try:
        # Prepare tools list
        tools = []
        
        # Add web search tool if enabled
        if use_web_search:
            tools.append({"type": "web_search"})
        
        # Add MCP filesystem tools if connected
        if mcp_client.session:
            try:
                mcp_tools = mcp_client.get_openai_tools()
                tools.extend(mcp_tools)
                logger.info(f"Added {len(mcp_tools)} MCP tools to query")
            except Exception as e:
                logger.warning(f"Could not add MCP tools: {e}")
        else:
            logger.warning("MCP client not connected")
        
        # Prepare request parameters
        request_params = {
            "input": [{"role": "user", "content": question}],
            "model": "gpt-4.1-mini",
            "tools": tools
        }
        
        # Create a response request with GPT-4.1 Mini using the Responses API
        response = client.responses.create(**request_params)

        # Debug log the response structure
        logger.debug(f"Response type: {type(response)}")
        logger.debug(f"Response attributes: {dir(response)}")
        if hasattr(response, 'output'):
            logger.debug(f"Response output: {response.output}")
            if response.output and len(response.output) > 0:
                message = response.output[0]
                logger.debug(f"First message type: {type(message)}")
                logger.debug(f"First message attributes: {dir(message)}")
                if hasattr(message, 'tool_calls'):
                    logger.debug(f"Message tool_calls: {message.tool_calls}")

        # Check whether the first item in `response.output` is a function‑call object
        # (new Responses API shape) or a normal assistant message that *contains*
        # tool calls (classic chat shape).
        tool_calls: list = []
        if response.output:
            first_item = response.output[0]

            # Newer shape – the item itself *is* the call.
            if getattr(first_item, "type", None) == "function_call":
                tool_calls.append(first_item)

            # Classic shape – the assistant message owns a `.tool_calls` list.
            elif hasattr(first_item, "tool_calls") and first_item.tool_calls:
                tool_calls.extend(first_item.tool_calls)
        
        if tool_calls:
            # Process MCP tool calls
            messages = request_params["input"].copy()
            
            # Extract the actual output text from the response structure
            output_text = ""
            if response.output:
                message = response.output[0]
                # Pure function‑call items never carry free text
                if getattr(message, "type", None) != "function_call" and \
                   hasattr(message, "content") and message.content:
                    output_text = message.content[0].text
            
            for tool_call in tool_calls:
                # Normalise fields for the two possible object shapes
                if hasattr(tool_call, "function"):          # classic message‑embedded call
                    tool_name = tool_call.function.name
                    call_id = tool_call.id
                    arguments_raw = tool_call.function.arguments
                else:                                       # Responses API direct call object
                    tool_name = tool_call.name
                    call_id = tool_call.id
                    arguments_raw = tool_call.arguments

                args = json.loads(arguments_raw) if isinstance(arguments_raw, str) else arguments_raw

                messages.append({
                    "role": "assistant",
                    "tool_calls": [{
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(args)
                        }
                    }]
                })

                if tool_name in [tool.name for tool in mcp_client.tools]:
                    # Call MCP tool
                    result = await mcp_client.call_tool(tool_name, args)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(result)
                    })
            
            # Get final response with tool results
            request_params["input"] = messages
            response = client.responses.create(**request_params)

        # Extract and send the response - Updated to handle the correct response structure
        ai_response = ""
        if response.output and len(response.output) > 0:
            message = response.output[0]
            if hasattr(message, 'content') and len(message.content) > 0:
                ai_response = message.content[0].text
        else:
            ai_response = "I apologize, but I couldn't generate a response."
        
        # Format response 
        formatted_response = f"{interaction.user.mention} Asked: {question}\n\n{ai_response}"
        await interaction.followup.send(formatted_response)

        # Log the response
        logger.info(f"AI response to {interaction.user}: {ai_response[:50]}...")

    except Exception as e:
        logger.error(f"Error querying OpenAI API: {e}")
        logger.error(f"Full error details: {traceback.format_exc()}")
        await interaction.followup.send("Sorry, I encountered an error while processing your request.")