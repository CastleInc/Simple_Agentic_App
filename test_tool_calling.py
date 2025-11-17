"""Test if llama3.1 supports tool calling"""
from openai import OpenAI
import json

client = OpenAI(
    api_key='fake-key',
    base_url='http://localhost:11434/v1'
)

tools = [{
    'type': 'function',
    'function': {
        'name': 'get_weather',
        'description': 'Get weather information',
        'parameters': {
            'type': 'object',
            'properties': {
                'location': {'type': 'string', 'description': 'City name'}
            },
            'required': ['location']
        }
    }
}]

print("Testing llama3.1 with tool calling...")
print("This may take 30-60 seconds on first run...\n")

try:
    response = client.chat.completions.create(
        model='llama3.1',
        messages=[{'role': 'user', 'content': 'What is the weather in Paris?'}],
        tools=tools,
        tool_choice='auto',
        max_tokens=100
    )
    print('✅ Tool calling is working with llama3.1!')
    print(f'Finish reason: {response.choices[0].finish_reason}')

    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        print(f'🔧 Tool called: {tool_call.function.name}')
        print(f'📝 Arguments: {tool_call.function.arguments}')
    else:
        print('📄 Response:', response.choices[0].message.content[:200])

except Exception as e:
    print(f'❌ Error: {e}')

