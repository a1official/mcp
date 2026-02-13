# Adding Custom MCP Tools

This guide shows you how to extend the MCP server with your own custom tools.

## Basic Tool Structure

Every MCP tool needs:
1. **Tool Definition** - Describes the tool to the LLM
2. **Tool Handler** - Executes the tool logic

## Example: Adding a Weather Tool

### Step 1: Add Tool Definition

In `mcp-server/index.js`, add to the `ListToolsRequestSchema` handler:

```javascript
{
  name: 'get_weather',
  description: 'Get current weather for a city',
  inputSchema: {
    type: 'object',
    properties: {
      city: {
        type: 'string',
        description: 'City name',
      },
      units: {
        type: 'string',
        description: 'Temperature units: celsius or fahrenheit',
        enum: ['celsius', 'fahrenheit'],
      },
    },
    required: ['city'],
  },
}
```

### Step 2: Add Tool Handler

In the `handleToolCall` method, add a case:

```javascript
async handleToolCall(request) {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'get_weather':
        return await this.getWeather(args);
      // ... other cases
    }
  } catch (error) {
    // ... error handling
  }
}
```

### Step 3: Implement the Tool Method

```javascript
async getWeather({ city, units = 'celsius' }) {
  // Example using OpenWeatherMap API
  const apiKey = process.env.WEATHER_API_KEY;
  const unitsParam = units === 'fahrenheit' ? 'imperial' : 'metric';
  
  const response = await axios.get(
    `https://api.openweathermap.org/data/2.5/weather`,
    {
      params: {
        q: city,
        units: unitsParam,
        appid: apiKey,
      },
    }
  );

  const weather = response.data;
  
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify({
          city: weather.name,
          temperature: weather.main.temp,
          description: weather.weather[0].description,
          humidity: weather.main.humidity,
          units: units,
        }, null, 2),
      },
    ],
  };
}
```

### Step 4: Add API Key to `.env`

```env
WEATHER_API_KEY=your_openweathermap_api_key
```

### Step 5: Restart the Server

```bash
npm run dev:server
```

Now users can ask: "What's the weather in London?"

## More Complex Tool Examples

### Database Query Tool

```javascript
{
  name: 'query_database',
  description: 'Query a SQL database',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'SQL query to execute (SELECT only)',
      },
      limit: {
        type: 'number',
        description: 'Maximum number of rows to return',
      },
    },
    required: ['query'],
  },
}
```

### File System Tool

```javascript
{
  name: 'read_file',
  description: 'Read contents of a file',
  inputSchema: {
    type: 'object',
    properties: {
      path: {
        type: 'string',
        description: 'File path to read',
      },
    },
    required: ['path'],
  },
}
```

### Slack Integration Tool

```javascript
{
  name: 'send_slack_message',
  description: 'Send a message to a Slack channel',
  inputSchema: {
    type: 'object',
    properties: {
      channel: {
        type: 'string',
        description: 'Slack channel name or ID',
      },
      message: {
        type: 'string',
        description: 'Message text',
      },
    },
    required: ['channel', 'message'],
  },
}
```

## Best Practices

### 1. Clear Descriptions
Make tool descriptions clear and specific so the LLM knows when to use them.

**Bad:**
```javascript
description: 'Gets data'
```

**Good:**
```javascript
description: 'Retrieves current stock price for a given ticker symbol from Yahoo Finance'
```

### 2. Input Validation
Always validate inputs before making external API calls:

```javascript
async getWeather({ city, units = 'celsius' }) {
  if (!city || typeof city !== 'string') {
    throw new Error('City must be a non-empty string');
  }
  
  if (!['celsius', 'fahrenheit'].includes(units)) {
    throw new Error('Units must be celsius or fahrenheit');
  }
  
  // ... proceed with API call
}
```

### 3. Error Handling
Return helpful error messages:

```javascript
try {
  const response = await axios.get(apiUrl);
  return { content: [{ type: 'text', text: JSON.stringify(response.data) }] };
} catch (error) {
  return {
    content: [{
      type: 'text',
      text: `Failed to fetch weather: ${error.response?.data?.message || error.message}`
    }],
    isError: true,
  };
}
```

### 4. Response Formatting
Return structured JSON that's easy for the LLM to understand:

```javascript
return {
  content: [{
    type: 'text',
    text: JSON.stringify({
      success: true,
      data: {
        temperature: 72,
        conditions: 'sunny',
      },
      timestamp: new Date().toISOString(),
    }, null, 2),
  }],
};
```

## Testing Your Tools

### 1. Test Standalone
Create a test script to verify your tool works:

```javascript
// test-weather.js
import { MCPIntegrationServer } from './mcp-server/index.js';

const server = new MCPIntegrationServer();
const result = await server.getWeather({ city: 'London', units: 'celsius' });
console.log(result);
```

### 2. Test via Chat
Once integrated, test through the chat interface:
- "What's the weather in Paris?"
- "Get weather for Tokyo in fahrenheit"

### 3. Check Error Cases
- Invalid city names
- Missing API keys
- Network failures

## Tool Ideas to Implement

- 📅 **Google Calendar** - Schedule events, list meetings
- 📊 **Database Query** - Query your database
- 🌐 **Web Scraper** - Extract data from websites
- 📝 **Note Taking** - Save notes to files or databases
- 🔔 **Notifications** - Send push notifications
- 💰 **Crypto Prices** - Get real-time cryptocurrency prices
- 🗺️ **Maps** - Get directions, calculate distances
- 📸 **Image Generation** - Create images with DALL-E or Stable Diffusion
- 🎬 **YouTube** - Search videos, get transcripts

## Resources

- [MCP Specification](https://modelcontextprotocol.io)
- [MCP SDK Documentation](https://github.com/modelcontextprotocol/sdk)
- [Groq Function Calling](https://console.groq.com/docs/tool-use)

Happy tool building! 🛠️
