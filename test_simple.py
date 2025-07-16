import os
import asyncio
from agents import Agent, Runner

async def main():
    """Simple test."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY")
        return
    
    agent = Agent(name="Test", instructions="You are helpful.")
    
    result = await Runner.run(agent, [{"content": "Say hello!", "role": "user"}])
    
    print("Result items:", len(result.new_items))
    for item in result.new_items:
        print(f"Item type: {type(item)}")
        if hasattr(item, 'content'):
            print(f"Content: {item.content}")
        else:
            print(f"Item: {item}")

if __name__ == "__main__":
    asyncio.run(main()) 