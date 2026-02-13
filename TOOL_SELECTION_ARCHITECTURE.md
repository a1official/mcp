# Tool Selection Architecture - Industry Best Practices

## The Problem We're Solving

When you have many tools (15+ in our case), sending ALL tool definitions with every LLM request causes:
- **Massive token consumption** (13,000+ tokens per request)
- **High API costs** (hitting rate limits quickly)
- **Slower responses** (more tokens = more processing time)
- **Poor tool selection** (LLM confused by too many options)

## Industry Solutions (Token Reduction: 91-98%)

### 1. **Semantic Tool Selection** (91% reduction)
Source: [MLOps Community Blog](https://home.mlops.community/en/public/blogs/how-i-reduced-ai-token-costs-by-91percent-with-semantic-tool-selection-and-redis)

**How it works:**
- Use vector embeddings to understand tool semantics
- Match user query to relevant tools using cosine similarity
- Only send 2-3 most relevant tools to LLM

**Architecture:**
```
User Query → Embed Query → Vector Search (Redis/Pinecone) → Top 3 Tools → LLM
```

**Key Components:**
1. **Multi-component embeddings** for each tool:
   - Description (50% weight)
   - Parameters (25% weight)
   - Usage examples (15% weight)
   - Return types (10% weight)

2. **Vector Database** (Redis Stack recommended):
   - HNSW indexing for fast similarity search
   - Sub-millisecond latency
   - Built-in caching

3. **Adaptive Selection**:
   - Return tools with similarity score > 0.7
   - Minimum 1 tool, maximum 5 tools
   - Score gap threshold to avoid marginal matches

**Implementation:**
```python
# 1. Embed all tools once (offline)
for tool in tools:
    embedding = openai.embed(tool.description + tool.params + tool.examples)
    redis.hset(f"tool:{tool.name}", "embedding", embedding)

# 2. At query time
query_embedding = openai.embed(user_query)
similar_tools = redis.ft().search(
    query_embedding,
    k=3,  # Top 3 tools
    score_threshold=0.7
)

# 3. Send only relevant tools to LLM
llm.chat(messages, tools=similar_tools)
```

### 2. **MCP-Zero: Active Tool Discovery** (98% reduction)
Source: [ArXiv Paper](https://arxiv.org/html/2506.01056v4)

**How it works:**
- Don't send ANY tool definitions initially
- LLM identifies capability gaps and requests specific tools
- System provides only requested tools on-demand

**Architecture:**
```
User Query → LLM (no tools) → "I need X capability" → Tool Registry → Specific Tool → LLM
```

**Two-Phase Approach:**
1. **Phase 1**: LLM analyzes query, identifies needed capabilities
2. **Phase 2**: System fetches and provides only those tools

**Benefits:**
- 98% token reduction
- Works with 1000+ tools
- LLM becomes autonomous agent

### 3. **JSPLIT: Hierarchical Tool Organization** (100x reduction)
Source: [Jane Systems Blog](https://www.janeasystems.com/blog/up-to-100x-token-cost-reduction-in-agentic-ai-with-jsplit)

**How it works:**
- Organize tools into hierarchical categories
- First, LLM selects category
- Then, only send tools from that category

**Architecture:**
```
User Query → Category Selection → Tool Subset → LLM
```

**Example Hierarchy:**
```
Tools/
├── Music/
│   ├── play_music
│   ├── search_music
│   └── get_artist_info
├── Web/
│   ├── browse_website
│   ├── search_google
│   └── search_products_smart
└── Redmine/
    ├── list_projects
    ├── list_issues
    └── get_issue
```

### 4. **Spring AI Dynamic Tool Discovery** (34-64% reduction)
Source: [Spring.io Blog](https://spring.io/blog/2025/12/11/spring-ai-tool-search-tools-tzolov)

**How it works:**
- Provide ONE meta-tool: `search_tools(capability_description)`
- LLM calls this tool to discover what's available
- System expands relevant tools into context

**Architecture:**
```
User Query → LLM + search_tools() → "search_tools('music playback')" → 
Expand music tools → LLM with music tools
```

## Our Current Implementation

We're using **keyword-based tool filtering** (basic version of JSPLIT):

```python
# Analyze query for keywords
if 'play' in query and 'music' in query:
    tools = [play_music]
elif 'issue' in query:
    tools = [redmine_list_issues]
```

**Pros:**
- Simple to implement
- No external dependencies
- Works reasonably well

**Cons:**
- Brittle (misses synonyms)
- Can't handle complex queries
- Manual keyword maintenance

## Recommended Architecture for Production

### Phase 1: Keyword + Semantic Hybrid (Quick Win)
**Token Reduction: 70-80%**

```python
# 1. Quick keyword filter (fast)
category = detect_category(query)  # music, web, redmine

# 2. Semantic search within category (accurate)
query_embedding = embed(query)
tools = vector_search(query_embedding, category=category, k=2)

# 3. Send to LLM
llm.chat(messages, tools=tools)
```

**Benefits:**
- Best of both worlds
- Fast category detection
- Accurate tool selection
- 2-3 tools per request instead of 15

### Phase 2: Full Semantic Selection (Production)
**Token Reduction: 90%+**

**Stack:**
- **Vector DB**: Redis Stack (HNSW indexing)
- **Embeddings**: OpenAI text-embedding-3-small ($0.02/1M tokens)
- **Caching**: Redis (cache embeddings for 24h)

**Implementation:**
```python
class SemanticToolSelector:
    def __init__(self, redis_client, openai_client):
        self.redis = redis_client
        self.openai = openai_client
    
    async def select_tools(self, query: str, max_tools: int = 3):
        # 1. Check cache
        cache_key = f"query_tools:{hash(query)}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 2. Embed query
        query_embedding = await self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        
        # 3. Vector search
        results = await self.redis.ft("tool_index").search(
            Query(f"*=>[KNN {max_tools} @embedding $vec AS score]")
            .sort_by("score")
            .return_fields("tool_name", "score")
            .dialect(2),
            query_params={"vec": query_embedding.data[0].embedding}
        )
        
        # 4. Filter by threshold
        tools = [r for r in results if r.score > 0.7]
        
        # 5. Cache result
        await self.redis.setex(cache_key, 3600, json.dumps(tools))
        
        return tools
```

### Phase 3: MCP-Zero (Advanced)
**Token Reduction: 95%+**

**Two-step process:**
```python
# Step 1: Capability detection (no tools)
response = llm.chat([
    {"role": "system", "content": "Identify what capabilities you need. Reply with: NEED_CAPABILITY: <description>"},
    {"role": "user", "content": query}
])

# Step 2: Fetch and provide specific tools
if "NEED_CAPABILITY:" in response:
    capability = extract_capability(response)
    tools = tool_registry.search(capability)
    
    # Now call with specific tools
    final_response = llm.chat(messages, tools=tools)
```

## Cost Comparison

**Current (Keyword Filtering):**
- Tokens per request: ~3,000-5,000
- Cost per 1000 requests: ~$0.30-$0.50
- Rate limit issues: Frequent

**With Semantic Selection:**
- Tokens per request: ~500-1,000
- Cost per 1000 requests: ~$0.05-$0.10
- Rate limit issues: Rare

**Savings: 80-90% reduction in token costs**

## Implementation Roadmap

### Week 1: Setup Vector DB
- [ ] Install Redis Stack
- [ ] Create HNSW index
- [ ] Embed all 15 tools

### Week 2: Semantic Search
- [ ] Implement query embedding
- [ ] Vector similarity search
- [ ] Caching layer

### Week 3: Integration
- [ ] Replace keyword filtering
- [ ] A/B test accuracy
- [ ] Monitor token usage

### Week 4: Optimization
- [ ] Fine-tune similarity thresholds
- [ ] Add fallback logic
- [ ] Performance tuning

## References

1. [91% Token Reduction with Semantic Tool Selection](https://home.mlops.community/en/public/blogs/how-i-reduced-ai-token-costs-by-91percent-with-semantic-tool-selection-and-redis)
2. [MCP-Zero: 98% Token Reduction](https://arxiv.org/html/2506.01056v4)
3. [JSPLIT: 100x Cost Reduction](https://www.janeasystems.com/blog/up-to-100x-token-cost-reduction-in-agentic-ai-with-jsplit)
4. [Spring AI Dynamic Tool Discovery](https://spring.io/blog/2025/12/11/spring-ai-tool-search-tools-tzolov)
5. [Semantic Tool Selection Architecture](https://vllm-semantic-router.com/blog/semantic-tool-selection)

## Conclusion

The industry standard for production LLM applications with many tools is **semantic tool selection using vector databases**. This approach:

- Reduces tokens by 90%+
- Improves tool selection accuracy
- Scales to 100+ tools
- Provides better UX

Our current keyword-based approach is a good starting point, but for production scale, we should implement semantic selection with Redis Stack.
