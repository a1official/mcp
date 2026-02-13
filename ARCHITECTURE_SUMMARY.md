# OpenClaw Architecture Summary

## Executive Overview

OpenClaw is a **personal AI assistant platform** that runs on your own infrastructure, connecting multiple messaging channels (WhatsApp, Telegram, Discord, Slack, Signal, iMessage, etc.) to AI models through a unified WebSocket control plane. The architecture is built around extensibility, security isolation, and multi-agent coordination.

## Core Architecture Pattern: Gateway Control Plane

### Central Hub: WebSocket Gateway Server
- **Location**: `src/gateway/server.impl.ts`
- **Default Port**: 18789 (configurable)
- **Protocol**: Versioned RPC over WebSocket with method-based routing
- **Authentication**: Token-based, password, or Tailscale identity
- **Clients**: CLI, macOS app, iOS/Android nodes, WebChat UI

The Gateway is the **single source of truth** for:
- Session state and routing
- Channel connection lifecycle
- Agent execution coordination
- Configuration hot-reloading
- Presence and health monitoring

### Key Design Decision: Everything Connects to Gateway
```
WhatsApp/Telegram/Discord/Slack/Signal/iMessage/etc
               │
               ▼
┌───────────────────────────────────┐
│      Gateway (WebSocket)          │
│      ws://127.0.0.1:18789         │
└──────────────┬────────────────────┘
               │
               ├─ Pi Agent (RPC mode)
               ├─ CLI (openclaw ...)
               ├─ WebChat UI
               ├─ macOS app
               └─ iOS/Android nodes
```

## 1. Multi-Channel Messaging Architecture

### Channel Plugin System

**Registry**: `src/channels/registry.ts`
- Core channels: Telegram, WhatsApp, Discord, Google Chat, Slack, Signal, iMessage
- Extension channels: BlueBubbles, Microsoft Teams, Matrix, Zalo, WebChat, Voice Call

**Channel Plugin Interface** (`src/channels/plugins/types.plugin.ts`):
```typescript
type ChannelPlugin = {
  id: ChannelId;
  meta: ChannelMeta;
  capabilities: ChannelCapabilities;
  config: ChannelConfigAdapter;
  auth?: ChannelAuthAdapter;
  outbound?: ChannelOutboundAdapter;
  status?: ChannelStatusAdapter;
  gateway?: ChannelGatewayAdapter;
  security?: ChannelSecurityAdapter;
  groups?: ChannelGroupAdapter;
  // ... 15+ adapter types
}
```

**Channel Docking Pattern**:
1. Add channel to `CHAT_CHANNEL_ORDER` in registry
2. Implement `ChannelPlugin` interface
3. Register plugin in extension entrypoint
4. Plugin auto-loads at gateway startup

### Adapter-Based Integration
Each channel implements adapters for specific capabilities:
- **Auth**: Login/logout flows (QR codes, tokens, OAuth)
- **Outbound**: Message sending with chunking/formatting
- **Status**: Connection health and diagnostics
- **Security**: DM policies, allowlists, pairing
- **Groups**: Group detection, mention handling
- **Streaming**: Real-time message delivery
- **Threading**: Thread/reply support

## 2. Plugin/Extension System

### Plugin SDK (`src/plugin-sdk/index.ts`)
Exports all types and utilities needed for extensions:
- Channel plugin types
- Gateway request handlers
- Config schemas
- Tool definitions

### Plugin Types
1. **Channel Plugins**: Messaging platform integrations
2. **Provider Plugins**: Model provider auth/config
3. **Skill Plugins**: Bundled tool collections

### Plugin Loading (`src/plugins/runtime.js`)

```typescript
// Plugin discovery order:
1. Bundled plugins (extensions/*)
2. Global plugins (~/.openclaw/plugins/*)
3. Workspace plugins (workspace/plugins/*)
4. Config-declared plugins
```

**Plugin API** (`src/plugins/types.ts`):
```typescript
type OpenClawPluginApi = {
  registerTool: (tool, opts?) => void;
  registerHook: (events, handler, opts?) => void;
  registerHttpHandler: (handler) => void;
  registerHttpRoute: (params) => void;
  registerChannel: (registration) => void;
  registerGatewayMethod: (method, handler) => void;
  registerCli: (registrar, opts?) => void;
  registerService: (service) => void;
  registerProvider: (provider) => void;
  registerCommand: (command) => void;
  on: (hookName, handler, opts?) => void;
}
```

### Plugin Isolation
- Plugin-only dependencies stay in extension `package.json`
- Avoid `workspace:*` in dependencies (breaks npm install)
- Runtime resolves `openclaw/plugin-sdk` via jiti alias
- Plugins loaded at gateway startup via `loadGatewayPlugins()`

## 3. Agent Runtime: Embedded Pi Agent

### Pi Framework Integration
**Entry Point**: `src/agents/pi-embedded.ts`
- Built on Mario Zechner's Pi framework
- Runs in RPC mode with streaming support
- Session-based execution model

**Agent Execution** (`src/agents/pi-embedded-runner.ts`):
```typescript
runEmbeddedPiAgent({
  agentId,
  sessionKey,
  prompt,
  config,
  tools,
  sandbox,
  streaming: true
}) => EmbeddedPiRunResult
```

### Session Model
**Session Key Format**: `agent:{agentId}:{sessionType}:{peerId}`

**Session Types**:
- `main` - Direct chats with the user
- `channel:group` - Group conversations
- `channel:dm` - Channel-specific DMs
- `thread` - Threaded conversations

**Storage**: `~/.openclaw/sessions/{agentId}/`
- Per-agent isolation
- JSONL transcript format
- Automatic pruning and compaction

### Tool System
**Tool Composition** (`src/agents/pi-tools.ts`):

```typescript
// Tool categories:
1. Bash tools: exec, process (command execution)
2. File tools: read, write, edit (filesystem ops)
3. Channel tools: Discord actions, Slack actions
4. OpenClaw tools: sessions, cron, browser, canvas, nodes
5. Plugin tools: Dynamically registered by plugins
```

**Tool Policy Cascade** (applied in order):
1. Profile-based (`tools.profile`)
2. Provider-specific (`tools.byProvider.{provider}.profile`)
3. Global allow/deny (`tools.allow`, `tools.deny`)
4. Agent-specific (`agents.{id}.tools.allow`)
5. Group-level policy
6. Sandbox restrictions
7. Subagent restrictions

**Policy Resolution** (`src/agents/pi-tools.policy.ts`):
```typescript
filterToolsByPolicy(tools, profilePolicy)
  .then(filterToolsByPolicy(_, globalPolicy))
  .then(filterToolsByPolicy(_, agentPolicy))
  .then(filterToolsByPolicy(_, sandboxPolicy))
```

### Streaming Architecture
- **Block-based streaming**: Chunks sent as they complete
- **Tool streaming**: Real-time tool execution updates
- **Chunking**: Configurable per-channel (length/newline modes)
- **Coalescing**: Debounced delivery for rapid updates

## 4. Configuration & Dependency Injection

### Configuration System
**Config File**: `~/.openclaw/openclaw.json` (JSON5 format)
**Schema**: `src/config/zod-schema.js` (Zod validation)

**Config Loading** (`src/config/config.ts`):
```typescript
readConfigFileSnapshot() => {
  exists: boolean,
  valid: boolean,
  parsed: OpenClawConfig,
  issues: ValidationIssue[],
  legacyIssues: LegacyIssue[]
}
```

**Hot Reload**:
- Config changes trigger selective restart
- No full gateway restart needed
- Channel-specific config reloads

### Dependency Injection Pattern
**CLI Dependencies** (`src/cli/deps.ts`):
```typescript
createDefaultDeps() => {
  sendMessageWhatsApp,
  sendMessageTelegram,
  sendMessageDiscord,
  sendMessageSlack,
  sendMessageSignal,
  sendMessageIMessage
}
```

**Outbound Send Deps** (`src/infra/outbound/deliver.ts`):

```typescript
createOutboundSendDeps(deps) => {
  sendWhatsApp: deps.sendMessageWhatsApp,
  sendTelegram: deps.sendMessageTelegram,
  // ... maps CLI deps to outbound interface
}
```

**Pattern**: Functions accept config/deps as parameters, no global state

## 5. Session & Routing Architecture

### Session Key Structure
**Format**: `agent:{agentId}:{sessionType}:{peerId}`

**Key Functions** (`src/routing/session-key.ts`):
```typescript
buildAgentMainSessionKey({ agentId, mainKey })
buildAgentPeerSessionKey({ agentId, channel, peerId, dmScope })
resolveAgentIdFromSessionKey(sessionKey)
toAgentStoreSessionKey({ agentId, requestKey, mainKey })
```

### DM Scoping Modes
1. **per-peer**: One session per peer (default)
2. **per-channel-peer**: Separate sessions per channel
3. **per-account-channel-peer**: Separate per account+channel

### Multi-Agent Coordination
**Agent Isolation**:
- Separate workspace: `~/.openclaw/workspace/{agentId}`
- Separate sessions: `~/.openclaw/sessions/{agentId}`
- Separate tool policies

**Cross-Agent Communication**:
- `sessions_list` - Discover active agents
- `sessions_history` - Read other agent transcripts
- `sessions_send` - Message another agent
- `sessions_spawn` - Create subagent

## 6. Security Model

### Default Security Posture
- **Main session**: Tools run on host (full access)
- **Non-main sessions**: Optional Docker sandbox
- **DM policy**: Pairing required by default

### Sandbox Architecture
**Sandbox Mode** (`agents.defaults.sandbox.mode`):
- `off` - No sandboxing
- `non-main` - Sandbox groups/channels only
- `always` - Sandbox everything

**Sandbox Tool Policy**:
```typescript
// Default allowlist:
['bash', 'process', 'read', 'write', 'edit', 
 'sessions_list', 'sessions_history', 'sessions_send']

// Default denylist:
['browser', 'canvas', 'nodes', 'cron', 'discord', 'gateway']
```

### DM Security Policies
**Pairing Mode** (default):

- Unknown senders receive pairing code
- Must approve via `openclaw pairing approve <channel> <code>`
- Sender added to local allowlist

**Open Mode** (opt-in):
- Set `dmPolicy="open"`
- Include `"*"` in channel allowlist
- Requires explicit configuration

## 7. Media Pipeline

### Media Storage
**Location**: `~/.openclaw/media/`
**Processing** (`src/media/`):
- Image resizing and format conversion
- HEIC → JPEG conversion
- EXIF normalization
- Size caps per media type

**Key Functions**:
```typescript
saveMediaSource(url, opts) => MediaSaveResult
saveMediaBuffer(buffer, opts) => MediaSaveResult
fetchRemoteMedia(url, opts) => Buffer
resizeToJpeg(buffer, maxWidth, maxHeight) => Buffer
```

**TTL-Based Cleanup**:
- Automatic cleanup of old media
- Configurable retention period
- Optional media server for URL hosting

## 8. CLI Architecture

### Command Structure
**Entry Points**:
- `src/entry.ts` - Respawn handler for daemon mode
- `src/index.ts` - Main CLI program
- `openclaw.mjs` - Binary entry point

**Command Categories**:
- `agent` - Run agent directly or via gateway
- `channels` - Channel management (login, status, etc.)
- `gateway` - Start/stop control plane
- `models` - Model configuration
- `onboard` - Interactive setup wizard
- `doctor` - Diagnostics and migrations

**Shared Patterns**:
```typescript
// Every command uses:
1. createDefaultDeps() for dependency injection
2. Config loading and validation
3. Prompt-based wizards for interactive flows
4. Consistent error handling
```

## 9. Testing Infrastructure

### Test Framework
**Framework**: Vitest with V8 coverage
**Coverage Thresholds**: 70% lines/branches/functions/statements

**Test Types**:
1. **Unit tests**: `*.test.ts` (colocated with source)
2. **E2E tests**: `*.e2e.test.ts`
3. **Live tests**: Real API keys via `CLAWDBOT_LIVE_TEST=1`
4. **Docker tests**: Integration tests in containers

**Test Helpers** (`test/helpers/`):

```typescript
installGatewayTestHooks() - Test setup
startGatewayServer() - In-process gateway
connectReq() / rpcReq() - WebSocket client helpers
```

**Test Configuration** (`vitest.config.ts`):
- Pool: forks (process isolation)
- Workers: 4-16 local, 2-3 CI
- Timeout: 120s (180s on Windows)

## 10. Build & Development

### Runtime Requirements
- **Node**: 22+ (baseline)
- **Bun**: Optional for TypeScript execution
- **pnpm**: Preferred for builds

### Build Pipeline
```bash
pnpm install          # Install dependencies
pnpm build            # TypeScript → dist/
pnpm check            # Lint + format
pnpm test             # Run tests
pnpm test:coverage    # Coverage report
```

**Build Steps** (`package.json`):
1. Bundle A2UI canvas assets
2. Run tsdown (TypeScript bundler)
3. Copy canvas assets to dist
4. Copy hook metadata
5. Write build info

### Development Commands
```bash
pnpm openclaw ...     # Run CLI via tsx (TypeScript)
pnpm dev              # Dev mode with auto-reload
pnpm gateway:watch    # Watch mode for gateway
```

## 11. Key Design Patterns

### 1. Adapter Pattern (Channels)
Each channel implements adapters for specific capabilities:
```typescript
ChannelPlugin {
  auth: ChannelAuthAdapter,
  outbound: ChannelOutboundAdapter,
  status: ChannelStatusAdapter,
  // ... 15+ adapters
}
```

### 2. Registry Pattern (Plugins)
Plugins register capabilities at startup:
```typescript
loadGatewayPlugins({ cfg, workspaceDir })
  .forEach(plugin => plugin.register(api))
```

### 3. Policy Cascade (Tools)
Multi-level policies applied in order with fallback:
```typescript
resolveEffectiveToolPolicy(
  profilePolicy,
  globalPolicy,
  agentPolicy,
  sandboxPolicy
)
```

### 4. Session Scoping (Routing)
Hierarchical session keys for isolation:
```typescript
agent:{agentId}:main
agent:{agentId}:channel:group:{groupId}
agent:{agentId}:channel:dm:{peerId}
```

### 5. Hot Reload (Config)
Config changes trigger selective restart:

```typescript
startGatewayConfigReloader({
  onHotReload: (changes) => applyChanges(changes),
  onRestart: () => restartGateway()
})
```

### 6. Dependency Injection
Functions accept config/deps as parameters:
```typescript
createOpenClawCodingTools({
  config,
  sandbox,
  sessionKey,
  workspaceDir,
  agentDir
})
```

## 12. Gateway Protocol (RPC over WebSocket)

### Protocol Structure
**Request Frame**:
```typescript
{
  id: string,           // Request ID
  method: string,       // RPC method name
  params: unknown,      // Method parameters
  meta?: unknown        // Optional metadata
}
```

**Response Frame**:
```typescript
{
  id: string,           // Matches request ID
  ok: boolean,          // Success flag
  payload?: unknown,    // Response data
  error?: ErrorShape,   // Error details
  meta?: unknown        // Optional metadata
}
```

### Gateway Methods (`src/gateway/server-methods/`)
- `agent_run` - Execute agent with prompt
- `agent_abort` - Cancel running agent
- `sessions_list` - List active sessions
- `sessions_patch` - Update session config
- `channels_status` - Get channel health
- `channels_start` - Start channel
- `channels_stop` - Stop channel
- `config_get` - Get configuration
- `config_set` - Update configuration
- `health_get` - Get health snapshot
- `node_list` - List connected nodes
- `node_invoke` - Execute node action

### Gateway Context (`src/gateway/server-methods/types.ts`)
```typescript
type GatewayRequestContext = {
  deps: ReturnType<typeof createDefaultDeps>,
  cron: CronService,
  loadGatewayModelCatalog: () => Promise<ModelCatalogEntry[]>,
  getHealthCache: () => HealthSummary | null,
  broadcast: (event, payload, opts?) => void,
  nodeSendToSession: (sessionKey, event, payload) => void,
  nodeRegistry: NodeRegistry,
  chatAbortControllers: Map<string, ChatAbortControllerEntry>,
  // ... 20+ context properties
}
```

## 13. Node Architecture (Device Integration)

### Node Types
1. **macOS Node**: System commands, notifications, canvas
2. **iOS Node**: Camera, screen recording, canvas, location
3. **Android Node**: Camera, screen recording, canvas

### Node Capabilities
**Advertised via Gateway**:

```typescript
node.describe() => {
  nodeId: string,
  platform: 'macos' | 'ios' | 'android',
  capabilities: {
    'system.run': { needsScreenRecording?: boolean },
    'system.notify': {},
    'canvas.*': {},
    'camera.*': {},
    'screen.record': {},
    'location.get': {}
  },
  permissions: {
    screenRecording: 'granted' | 'denied' | 'unknown',
    notifications: 'granted' | 'denied' | 'unknown',
    // ... TCC permission status
  }
}
```

**Node Invocation**:
```typescript
node.invoke({
  nodeId,
  action: 'system.run',
  params: { command: 'ls -la' }
}) => { stdout, stderr, exitCode }
```

## 14. Outbound Message Delivery

### Delivery Pipeline (`src/infra/outbound/deliver.ts`)
```typescript
deliverOutboundPayloads({
  cfg,
  channel,
  to,
  payloads,
  deps,
  abortSignal,
  mirror?: { sessionKey, text, mediaUrls }
}) => OutboundDeliveryResult[]
```

**Delivery Steps**:
1. Load channel outbound adapter
2. Normalize payloads (text + media)
3. Apply chunking (length/newline modes)
4. Send text chunks
5. Send media with captions
6. Mirror to session transcript (optional)

**Channel-Specific Handling**:
- **Signal**: Markdown → styled text chunks
- **Telegram**: HTML formatting
- **Discord**: Markdown with embeds
- **WhatsApp**: Plain text with media
- **Slack**: Blocks + attachments

### Chunking Strategies
**Length Mode**: Split at character limit
**Newline Mode**: Split at paragraph boundaries
**Markdown Mode**: Preserve code blocks and formatting

## 15. Cron & Automation

### Cron Service (`src/cron/service.ts`)
**Storage**: `~/.openclaw/cron/jobs.json`

**Job Types**:
1. **Scheduled**: Run at specific times
2. **Interval**: Run every N seconds
3. **Wakeup**: Wake agent at specific time

**Job Management**:
```typescript
cron.schedule({ schedule, prompt, sessionKey })
cron.list() => CronJob[]
cron.delete(jobId)
cron.pause(jobId)
cron.resume(jobId)
```

### Webhook Surface (`src/gateway/server-methods/webhook.ts`)
**Endpoint**: `POST /webhook/{hookId}`
**Auth**: Token-based or password

**Webhook Flow**:
1. Receive HTTP POST
2. Extract payload
3. Queue agent message
4. Return 200 OK immediately

## 16. Browser Control

### Browser Architecture (`src/browser/`)
**Browser**: Dedicated Chrome/Chromium instance
**Control**: CDP (Chrome DevTools Protocol)

**Browser Tools**:

```typescript
browser_navigate(url)
browser_snapshot() => base64 screenshot
browser_action(action, selector)
browser_upload(selector, filePath)
browser_profile(profileName)
```

**Browser Lifecycle**:
- Launched on-demand
- Persistent profiles
- Automatic cleanup
- Headless or headed mode

## 17. Canvas System (A2UI)

### Canvas Architecture
**A2UI**: Agent-to-UI protocol for visual interfaces
**Renderers**: Lit-based web components

**Canvas Tools**:
```typescript
canvas_push(a2uiJson) - Render UI
canvas_reset() - Clear canvas
canvas_eval(code) - Execute JS
canvas_snapshot() - Screenshot
```

**Canvas Hosting**:
- Embedded in macOS app
- Available on iOS/Android nodes
- WebSocket-based updates

## 18. Voice & Audio

### Voice Wake (macOS/iOS/Android)
**Trigger**: Wake word detection
**Flow**: Voice → Transcription → Agent → TTS → Audio

**Voice Wake Tools**:
```typescript
voicewake_configure(triggers)
voicewake_status() => { enabled, triggers }
```

### Talk Mode
**Mode**: Continuous conversation
**Features**:
- Push-to-talk overlay
- Automatic transcription
- TTS playback
- Interrupt handling

## 19. Memory & Compaction

### Session Compaction
**Trigger**: Token limit or manual
**Strategy**: Summarize old messages, keep recent

**Compaction Flow**:
```typescript
compactEmbeddedPiSession({
  agentId,
  sessionKey,
  config
}) => {
  messagesBefore: number,
  messagesAfter: number,
  summary: string
}
```

### Memory Extensions
**Memory Plugins** (`extensions/memory-*`):
- `memory-core` - In-memory storage
- `memory-lancedb` - Vector database

**Memory API**:
```typescript
memory.store(key, value, metadata)
memory.search(query, limit)
memory.retrieve(key)
```

## 20. Error Handling & Diagnostics

### Health Monitoring
**Health Snapshot** (`src/commands/health.ts`):
```typescript
{
  gateway: { status, uptime, version },
  channels: { [id]: { status, issues } },
  models: { [id]: { available, latency } },
  nodes: { [id]: { status, capabilities } }
}
```

### Doctor Command
**Diagnostics** (`openclaw doctor`):
- Config validation
- Legacy migration
- Permission checks
- Channel health
- Model availability

### Logging
**Subsystem Loggers** (`src/logging/subsystem.ts`):

```typescript
createSubsystemLogger('gateway')
  .info('message')
  .warn('warning')
  .error('error')
```

**Log Levels**: debug, info, warn, error
**Log Destinations**: Console, file, structured JSON

## 21. Deployment Patterns

### Local Deployment
**Daemon Mode**:
- launchd (macOS)
- systemd (Linux)
- Windows Service (via WSL2)

**Install**:
```bash
openclaw onboard --install-daemon
```

### Remote Gateway
**Access Methods**:
1. **Tailscale Serve**: Tailnet-only HTTPS
2. **Tailscale Funnel**: Public HTTPS
3. **SSH Tunnels**: Port forwarding

**Remote Flow**:
```
Linux Gateway (exec tools, channels)
         ↕
   Tailscale/SSH
         ↕
macOS/iOS/Android Nodes (device actions)
```

### Docker Deployment
**Sandbox Mode**:
- Per-session containers
- Isolated filesystem
- Network restrictions
- Resource limits

**Docker Compose**:
```yaml
services:
  gateway:
    image: openclaw/openclaw
    ports: ["18789:18789"]
    volumes: ["./data:/data"]
```

## 22. Key Files Reference

### Architecture Foundation
- `src/gateway/server.impl.ts` - Gateway initialization
- `src/channels/registry.ts` - Channel plugin registry
- `src/plugin-sdk/index.ts` - Plugin SDK exports
- `src/routing/session-key.ts` - Session routing logic

### Agent Runtime
- `src/agents/pi-embedded.ts` - Agent execution entry
- `src/agents/pi-embedded-runner.ts` - Agent loop
- `src/agents/pi-tools.ts` - Tool composition
- `src/agents/pi-tools.policy.ts` - Policy resolution

### Configuration
- `src/config/config.ts` - Config loading
- `src/config/types.ts` - Config types
- `src/config/zod-schema.js` - Validation schemas

### CLI
- `src/cli/program.ts` - CLI program builder
- `src/cli/deps.ts` - Dependency injection
- `src/commands/` - Command implementations

### Channels
- `src/channels/plugins/types.plugin.ts` - Plugin interface
- `src/channels/plugins/types.adapters.ts` - Adapter types
- `src/infra/outbound/deliver.ts` - Message delivery

### Testing
- `vitest.config.ts` - Test configuration
- `test/setup.ts` - Test setup
- `test/helpers/` - Test utilities

## 23. Technology Stack

### Core Technologies
- **Runtime**: Node.js 22+, Bun (optional)
- **Language**: TypeScript (strict mode)
- **Build**: tsdown (TypeScript bundler)
- **Package Manager**: pnpm (preferred), npm, bun

### Key Dependencies
- **Agent Framework**: @mariozechner/pi-agent-core
- **WebSocket**: ws
- **Validation**: Zod
- **CLI**: commander, @clack/prompts
- **Testing**: Vitest, V8 coverage

### Channel Libraries
- **WhatsApp**: @whiskeysockets/baileys
- **Telegram**: grammy
- **Discord**: discord.js
- **Slack**: @slack/bolt
- **Signal**: signal-cli (external)

### Platform-Specific
- **macOS**: Swift, SwiftUI, Observation framework
- **iOS**: Swift, SwiftUI, UIKit
- **Android**: Kotlin, Jetpack Compose

## 24. Extensibility Points

### 1. Channel Plugins
Add new messaging platforms:
```typescript
export const myChannelPlugin: ChannelPlugin = {
  id: 'mychannel',
  meta: { label: 'My Channel', ... },
  capabilities: { dm: true, groups: true },
  config: { ... },
  outbound: { sendText, sendMedia },
  status: { getStatus }
}
```

### 2. Tool Plugins
Add new agent capabilities:
```typescript
api.registerTool({
  name: 'my_tool',
  description: 'Does something',
  parameters: Type.Object({ ... }),
  execute: async (params) => { ... }
})
```

### 3. Provider Plugins
Add model providers:
```typescript
api.registerProvider({
  id: 'myprovider',
  label: 'My Provider',
  auth: [{ id: 'oauth', kind: 'oauth', run: ... }],
  models: { ... }
})
```

### 4. Gateway Methods
Add RPC endpoints:
```typescript
api.registerGatewayMethod('my_method', async (opts) => {
  const { params, respond } = opts
  // ... handle request
  respond(true, result)
})
```

### 5. Lifecycle Hooks
Hook into system events:
```typescript
api.on('before_agent_start', async (event, ctx) => {
  return { systemPrompt: '...' }
})

api.on('message_sending', async (event, ctx) => {
  return { content: modifiedContent }
})
```

## 25. Security Considerations

### Threat Model
1. **Untrusted DM input**: Pairing required by default
2. **Group messages**: Optional sandbox isolation
3. **Tool execution**: Policy-based restrictions
4. **Media uploads**: Size limits, SSRF protection
5. **Config exposure**: Sensitive fields masked

### Security Best Practices
1. **Use pairing mode** for DMs
2. **Enable sandbox** for non-main sessions
3. **Restrict tool policies** for groups
4. **Use Tailscale Serve** (not Funnel) when possible
5. **Rotate API keys** regularly
6. **Review allowlists** periodically

### Permission Model
- **Main session**: Full host access (trusted)
- **Non-main sessions**: Restricted or sandboxed
- **Node actions**: TCC permission checks
- **Elevated bash**: Per-session toggle with allowlist

## 26. Performance Optimizations

### Caching Strategies
1. **Config snapshot**: Cached until change
2. **Health snapshot**: Cached with version
3. **Model catalog**: Lazy loaded
4. **Channel status**: Cached with TTL

### Streaming Optimizations
1. **Block coalescing**: Debounced delivery
2. **Chunking**: Configurable per-channel
3. **Backpressure**: Drop slow clients
4. **Delta tracking**: Only send changes

### Resource Management
1. **Session pruning**: Automatic cleanup
2. **Media TTL**: Time-based deletion
3. **Process cleanup**: Orphan detection
4. **Connection pooling**: Reuse HTTP clients

## 27. Reverse Engineering Guide

### To Build Similar System

#### 1. Start with Gateway
- Implement WebSocket RPC server
- Define protocol (request/response frames)
- Add authentication layer
- Build client libraries

#### 2. Add Channel Abstraction
- Define adapter interfaces
- Implement plugin loading
- Create registry pattern
- Add hot-reload support

#### 3. Integrate Agent Runtime
- Choose agent framework (Pi, LangChain, etc.)
- Implement session management
- Add tool composition
- Build streaming support

#### 4. Implement Security
- Add DM pairing flow
- Implement sandbox isolation
- Create policy cascade
- Add permission checks

#### 5. Build CLI
- Use commander or similar
- Implement dependency injection
- Add interactive wizards
- Create diagnostic tools

### Key Architectural Decisions to Copy

1. **Single WebSocket control plane**: All clients connect to one gateway
2. **Adapter-based channels**: Uniform interface for diverse platforms
3. **Plugin system**: Extensibility without core changes
4. **Session-based routing**: Hierarchical keys for isolation
5. **Policy cascade**: Multi-level tool restrictions
6. **Hot reload**: Config changes without restart
7. **Dependency injection**: Testable, modular code
8. **Colocated tests**: Tests next to source files

### Patterns to Avoid

1. **Global state**: Use dependency injection instead
2. **Tight coupling**: Use adapters and interfaces
3. **Monolithic plugins**: Keep plugins focused
4. **Manual config parsing**: Use schema validation
5. **Blocking operations**: Use async/await throughout
6. **Hardcoded limits**: Make everything configurable

## 28. Future-Proofing

### Extensibility Principles
1. **Adapter pattern**: New channels without core changes
2. **Plugin hooks**: Intercept at key points
3. **Config-driven**: Feature flags and toggles
4. **Versioned protocol**: Backward compatibility
5. **Schema validation**: Catch errors early

### Scalability Considerations
1. **Horizontal scaling**: Multiple gateway instances
2. **Session sharding**: Distribute by session key
3. **Message queuing**: Decouple inbound/outbound
4. **Caching layer**: Redis for shared state
5. **Load balancing**: Round-robin or least-loaded

### Maintenance Strategy
1. **Automated testing**: 70%+ coverage
2. **Type safety**: Strict TypeScript
3. **Linting**: Oxlint + Oxfmt
4. **Documentation**: Inline comments + docs/
5. **Changelog**: Track all changes
6. **Versioning**: Semantic versioning

## 29. Common Pitfalls & Solutions

### Pitfall 1: Plugin Dependency Hell
**Problem**: Plugins with conflicting dependencies
**Solution**: Isolate plugin deps in extension package.json

### Pitfall 2: Config Drift
**Problem**: Config changes not reflected
**Solution**: Hot reload with config watcher

### Pitfall 3: Session Leaks
**Problem**: Sessions never cleaned up
**Solution**: Automatic pruning + compaction

### Pitfall 4: Tool Policy Confusion
**Problem**: Unclear which policy applies
**Solution**: Policy cascade with clear precedence

### Pitfall 5: Channel-Specific Logic in Core
**Problem**: Core code knows about specific channels
**Solution**: Adapter pattern + plugin system

## 30. Summary: What Makes OpenClaw Unique

### Architectural Strengths
1. **Unified control plane**: Single WebSocket for everything
2. **True multi-channel**: 13+ platforms, uniform interface
3. **Plugin extensibility**: Add channels/tools without forking
4. **Security by default**: Pairing, sandboxing, policies
5. **Multi-agent coordination**: Isolated agents, cross-agent messaging
6. **Device integration**: macOS/iOS/Android nodes
7. **Hot reload**: Config changes without restart
8. **Comprehensive testing**: 70%+ coverage, E2E tests

### Key Innovations
1. **Session-based routing**: Hierarchical keys for isolation
2. **Policy cascade**: Multi-level tool restrictions
3. **Adapter-based channels**: Uniform interface for diverse platforms
4. **Node architecture**: Device actions via gateway protocol
5. **Canvas system**: Agent-driven visual interfaces
6. **Voice wake**: Always-on speech integration

### Lessons for Other Projects
1. **Start with abstractions**: Adapters, plugins, policies
2. **Invest in testing**: Colocated tests, high coverage
3. **Config-driven everything**: Feature flags, toggles
4. **Security from day one**: Pairing, sandboxing, policies
5. **Documentation matters**: Inline comments, external docs
6. **Hot reload is worth it**: Better DX, faster iteration

---

## Appendix: Quick Reference

### Essential Commands
```bash
# Install
npm install -g openclaw@latest

# Onboard
openclaw onboard --install-daemon

# Start gateway
openclaw gateway --port 18789

# Send message
openclaw message send --to +1234567890 --message "Hello"

# Run agent
openclaw agent --message "Task" --thinking high

# Check health
openclaw health --probe

# Diagnostics
openclaw doctor
```

### Essential Config Keys
```json5
{
  agent: {
    model: "anthropic/claude-opus-4-5"
  },
  gateway: {
    port: 18789,
    bind: "loopback",
    auth: { mode: "token" }
  },
  channels: {
    whatsapp: { allowFrom: ["*"] },
    telegram: { botToken: "..." }
  },
  tools: {
    profile: "default",
    allow: ["*"],
    deny: []
  },
  agents: {
    defaults: {
      sandbox: { mode: "non-main" }
    }
  }
}
```

### Essential File Locations
- Config: `~/.openclaw/openclaw.json`
- Sessions: `~/.openclaw/sessions/{agentId}/`
- Workspace: `~/.openclaw/workspace/{agentId}/`
- Media: `~/.openclaw/media/`
- Credentials: `~/.openclaw/credentials/`
- Cron: `~/.openclaw/cron/jobs.json`

---

**End of Architecture Summary**

This document provides a comprehensive overview of OpenClaw's architecture, suitable for understanding the system, extending it, or building similar systems. For implementation details, refer to the source code and inline documentation.
