# RedisInsight - Redis GUI

RedisInsight is the official graphical user interface for Redis, providing a visual way to interact with your Redis databases.

## 🚀 Quick Start

### Access RedisInsight
```bash
open http://localhost:5540
```

Or visit: **http://localhost:5540** in your browser

### First-Time Setup

1. **Open RedisInsight** at http://localhost:5540
2. Click **"Add Redis Database"** or **"Connect to Redis"**
3. Enter connection details:
   - **Host**: `redis` (container name) or `host.docker.internal` 
   - **Port**: `6379`
   - **Database Alias**: `Local Redis` (any name you prefer)
   - **Username**: Leave empty
   - **Password**: Leave empty
4. Click **"Add Redis Database"**

**Alternative (if above doesn't work):**
- **Host**: `localhost` or `127.0.0.1`
- **Port**: `6379`

---

## 📊 Features

### 1. **Browser (Key Management)**
- View all keys with patterns
- Search and filter keys
- Add, edit, delete keys
- Supports all Redis data types:
  - Strings
  - Hashes
  - Lists
  - Sets
  - Sorted Sets
  - Streams
  - JSON

### 2. **Workbench (Command Execution)**
- Execute Redis commands
- Command history
- Auto-completion
- Multi-line support
- Results visualization

**Try these commands:**
```redis
# View all keys
KEYS *

# Get demo API keys
SCAN 0 MATCH demo_api:*

# View user profile
HGETALL demo_api:user:user123

# Check rate limit
GET demo_api:rate_limit:user123

# Monitor commands in real-time
MONITOR
```

### 3. **Analysis Tools**

#### Memory Analysis
- View memory usage by key pattern
- Find large keys
- Identify memory leaks
- Optimize storage

#### Slow Log
- Track slow queries
- Identify performance bottlenecks
- Optimize commands

### 4. **Pub/Sub**
- Subscribe to channels
- Publish messages
- Monitor message flow
- Test messaging patterns

### 5. **Profiler**
- Real-time command monitoring
- Performance analysis
- Throughput metrics
- Command breakdown

---

## 🎯 Common Tasks

### View Your Demo API Data

After running `demo_redis_api.py`, check your cached data:

```redis
# 1. Switch to Browser tab
# 2. Search for: demo_api:*
# 3. Click on any key to view details
```

**Keys you'll find:**
- `demo_api:cache:*` - Basic cache items
- `demo_api:user:*` - User profiles (hashes)
- `demo_api:rate_limit:*` - Rate limiting counters
- `demo_api:lock:*` - Distributed locks
- `demo_api:queue:tasks` - Task queue (list)

### Execute Commands

1. Go to **Workbench** tab
2. Type commands in the editor
3. Press **Ctrl+Enter** (or click Run)

**Example commands:**
```redis
-- Get all demo keys
KEYS demo_api:*

-- View user profile
HGETALL demo_api:user:user123

-- Check cache value
GET demo_api:cache:hello

-- View task queue
LRANGE demo_api:queue:tasks 0 -1

-- Get key TTL
TTL demo_api:cache:mykey

-- Monitor live commands
MONITOR
```

### Monitor Performance

1. Click **"Analysis Tools"** → **"Profiler"**
2. Click **"Start"**
3. Run your API tests (`python test_redis_api.py`)
4. See real-time command execution

---

## 🔍 Viewing Demo Data

### After Running test_redis_api.py

You can visually inspect all the data created by the test:

#### 1. Basic Cache Items
**Browser → Search**: `demo_api:cache:*`
- `demo_api:cache:hello` → `"world"`
- `demo_api:cache:config` → JSON object
- `demo_api:cache:count` → number

#### 2. User Profiles (Hashes)
**Browser → Search**: `demo_api:user:*`

Click on `demo_api:user:user123` to see:
```
user_id:    user123
name:       John Doe
email:      john@example.com
age:        30
city:       San Francisco
```

#### 3. Rate Limiting
**Workbench → Execute**:
```redis
GET demo_api:rate_limit:user123
TTL demo_api:rate_limit:user123
```

#### 4. Task Queue
**Workbench → Execute**:
```redis
LRANGE demo_api:queue:tasks 0 -1
```

---

## 💡 Advanced Features

### Bulk Operations

```redis
-- Delete all demo keys
DEL demo_api:cache:key1 demo_api:cache:key2

-- Or use pattern (requires SCAN + DEL)
EVAL "return redis.call('DEL', unpack(redis.call('KEYS', ARGV[1])))" 0 demo_api:*
```

### Lua Scripts

Test your Lua scripts directly in Workbench:

```redis
-- Rate limiting script (same as in demo)
EVAL "
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('GET', key)
if not current then
    redis.call('SETEX', key, window, 1)
    return 1
end
current = tonumber(current)
if current < limit then
    redis.call('INCR', key)
    return current + 1
end
return 0
" 1 demo_api:rate_limit:test 10 60
```

### Pipeline Commands

RedisInsight supports multi-line commands:

```redis
SET key1 "value1"
SET key2 "value2"
SET key3 "value3"
MGET key1 key2 key3
```

Press **Ctrl+Enter** to execute all at once.

---

## 🎨 Tips & Tricks

### 1. **Auto-Refresh**
Enable auto-refresh in Browser to see live updates:
- Click the refresh icon
- Select refresh interval (e.g., 5 seconds)

### 2. **Key Filtering**
Use Redis patterns:
- `*` - All keys
- `demo_api:*` - Keys starting with "demo_api:"
- `*:user:*` - Keys containing ":user:"
- `cache:??:*` - Two-character wildcard

### 3. **Command Templates**
Save frequently used commands:
- Write command in Workbench
- Click **"Save"**
- Name your template
- Reuse later

### 4. **Export Data**
- Select keys in Browser
- Click **"Export"**
- Choose format (JSON, CSV)
- Download to file

### 5. **Keyboard Shortcuts**
- `Ctrl/Cmd + Enter` - Run command
- `Ctrl/Cmd + K` - Clear console
- `Ctrl/Cmd + F` - Search in results
- `Ctrl/Cmd + L` - Clear editor

---

## 🔧 Configuration

### Connect to Remote Redis

If your Redis is on a remote server:

1. Click **"Add Redis Database"**
2. Enter remote details:
   ```
   Host: your-redis-server.com
   Port: 6379
   Password: your-password (if any)
   TLS: Enable if using SSL
   ```

### Multiple Databases

Redis has 16 databases (0-15) by default:

1. In connection settings
2. Set **"Database Index"**: 0-15
3. Or switch using:
   ```redis
   SELECT 1
   ```

---

## 🐛 Troubleshooting

### Cannot Connect to Redis

**Problem**: "Could not connect to Redis"

**Solutions**:
1. Check Redis is running:
   ```bash
   docker ps | grep redis
   ```

2. Try different host values:
   - `redis` (container name)
   - `host.docker.internal`
   - `localhost`
   - `127.0.0.1`

3. Verify port is correct: `6379`

4. Check Docker network:
   ```bash
   docker network inspect fastapibuildingblocks_app_network
   ```

### RedisInsight Not Loading

```bash
# Check container logs
docker logs redisinsight

# Restart container
docker restart redisinsight

# Full restart
docker-compose -f docker-compose.redis.yml restart
```

### Permission Issues

```bash
# Fix volume permissions
docker-compose -f docker-compose.redis.yml down
docker volume rm fastapibuildingblocks_redisinsight_data
docker-compose -f docker-compose.redis.yml up -d
```

---

## 📚 Resources

### Official Documentation
- **RedisInsight**: https://redis.io/docs/ui/insight/
- **Redis Commands**: https://redis.io/commands/

### Learn by Doing

1. **Try Interactive Tutorial** in RedisInsight
   - Open RedisInsight
   - Look for "Tutorials" or "Getting Started"

2. **Run Demo Scripts**
   ```bash
   # Populate data
   python demo_redis_cache.py
   
   # Or use API
   python test_redis_api.py
   ```

3. **Explore in UI**
   - Browse keys
   - Execute commands
   - Analyze performance

---

## 🎯 Integration with Your Application

### Monitor Your Application

While your app is running:

1. **Enable Profiler**
   - Go to Profiler tab
   - Click Start
   - Run your application
   - See all Redis commands in real-time

2. **Check Memory Usage**
   - Go to Analysis Tools
   - View memory by key pattern
   - Identify large keys

3. **Monitor Slow Commands**
   - Check Slow Log
   - Optimize queries

### Debug Cache Issues

```redis
-- Check if key exists
EXISTS demo_api:cache:mykey

-- Get TTL
TTL demo_api:cache:mykey

-- View key type
TYPE demo_api:cache:mykey

-- View memory usage
MEMORY USAGE demo_api:cache:mykey

-- Get all info
DEBUG OBJECT demo_api:cache:mykey
```

---

## 🚀 Quick Start Checklist

- [x] RedisInsight running at http://localhost:5540
- [ ] Connect to Redis database (host: `redis` or `localhost`, port: `6379`)
- [ ] Browse existing keys
- [ ] Execute test commands in Workbench
- [ ] Run demo script: `python test_redis_api.py`
- [ ] View created data in Browser
- [ ] Enable Profiler to monitor commands
- [ ] Check memory usage in Analysis Tools

---

## 💡 Next Steps

1. **Explore Your Data**: Run `python test_redis_api.py` and view results
2. **Learn Redis Commands**: Use Workbench with auto-completion
3. **Monitor Performance**: Enable Profiler while testing
4. **Analyze Memory**: Check which keys use most memory
5. **Build Dashboards**: Create custom views for your data

---

**Status**: ✅ RedisInsight running at http://localhost:5540
**Redis Server**: localhost:6379
**Container**: `redisinsight`
