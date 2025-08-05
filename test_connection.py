#!/usr/bin/env python3
"""
Test script to verify the connection between React frontend and Python agent
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_api_connection():
    """Test the FastAPI backend connection"""
    print("🧪 Testing HR Assistant API connection...")
    
    # Test health endpoint
    try:
        async with aiohttp.ClientSession() as session:
            # Test health check
            async with session.get('http://localhost:8000/api/health') as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Health check passed: {health_data}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
            
            # Test agent status
            async with session.get('http://localhost:8000/api/agent/status') as response:
                if response.status == 200:
                    status_data = await response.json()
                    print(f"✅ Agent status: {status_data}")
                else:
                    print(f"❌ Agent status check failed: {response.status}")
                    return False
            
            # Test chat endpoint
            test_message = {
                "text": "Hello, can you help me check my leave balance?",
                "sender": "user",
                "timestamp": datetime.now().isoformat()
            }
            
            async with session.post(
                'http://localhost:8000/api/chat',
                json=test_message,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    chat_data = await response.json()
                    print(f"✅ Chat test passed:")
                    print(f"   Response: {chat_data['text'][:100]}...")
                    return True
                else:
                    print(f"❌ Chat test failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
                    
    except aiohttp.ClientConnectorError:
        print("❌ Cannot connect to API server. Make sure it's running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def main():
    """Main test function"""
    print("🔧 HR Assistant Connection Test")
    print("=" * 40)
    
    success = await test_api_connection()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed! The connection is working properly.")
        print("\nYou can now:")
        print("1. Start the full application with: ./start_app.sh")
        print("2. Open http://localhost:5173 in your browser")
        print("3. Chat with your HR assistant!")
    else:
        print("❌ Tests failed. Please check the API server and try again.")
        print("\nTo start the API server manually:")
        print("python api_server.py")

if __name__ == "__main__":
    asyncio.run(main())
