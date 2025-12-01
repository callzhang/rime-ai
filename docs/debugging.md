# Rime Lua 脚本调试指南

> 本文档基于 [Rime 输入方案设计书 - 关于调试](https://github.com/rime/home/wiki/RimeWithSchemata#关于调试) 整理

## 📋 目录
1. [日志文件位置](#日志文件位置)
2. [Squirrel 日志](#squirrel-日志)
3. [Lua 脚本调试](#lua-脚本调试)
4. [配置验证](#配置验证)
5. [常见问题诊断](#常见问题诊断)
6. [调试工具](#调试工具)
7. [调试流程](#调试流程)
8. [快速参考](#快速参考)

---

## 日志文件位置

### Squirrel 主日志（macOS）

根据 [Rime 输入方案设计书](https://github.com/rime/home/wiki/RimeWithSchemata#关于调试)，Rime 的日志文件位置：

- **【鼠鬚管（macOS）】**：`$TMPDIR/rime.squirrel.*`
  - 实际路径：`/var/folders/*/T/rime.squirrel/`
  - 日志级别：INFO、WARNING、ERROR
- **【小狼毫（Windows）】**：`%TEMP%\rime.weasel.*`
- **【中州韻（Linux）】**：`/tmp/rime.ibus.*`
- **早期版本**：`用户资料夹/rime.log`

日志按照级别分为 INFO（信息）、WARNING（警告）、ERROR（错误）。后两类应重点关注，如果新方案部署后不可用或输出与设计不一致，原因可能在此。

```bash
# Squirrel 的日志文件（macOS）
# 注意：实际路径是一个目录，包含多个日志文件
/var/folders/*/T/rime.squirrel/

# 日志文件结构：
# - rime.squirrel.INFO -> 指向最新的 INFO 日志
# - rime.squirrel.ERROR -> 指向最新的 ERROR 日志
# - rime.squirrel.WARNING -> 指向最新的 WARNING 日志

# 查看最新的 INFO 日志
LATEST_LOG=$(readlink /var/folders/*/T/rime.squirrel/rime.squirrel.INFO 2>/dev/null | head -1)
cat "/var/folders/*/T/rime.squirrel/$LATEST_LOG"

# 或者查找所有日志文件
find /var/folders -name "rime.squirrel*" -type d 2>/dev/null | head -1 | xargs ls -lt | head -5
```

### Rime 用户数据库日志

```bash
# Rime 用户数据库日志
~/Library/Rime/rime_ice.userdb/*.log

# 查看最新的日志
ls -lt ~/Library/Rime/rime_ice.userdb/*.log | head -1
```

### 自定义调试日志

```bash
# AI 模块初始化日志
/tmp/rime_ai_init.txt

# AI Translator 调用日志
/tmp/rime_ai_debug.txt

# AI Processor 调用日志
/tmp/rime_ai_processor.txt

# 统一日志文件（推荐）
/tmp/rime_ai.log
```

---

## Squirrel 日志

### 查看实时日志

```bash
# 实时查看 Squirrel INFO 日志
LATEST_LOG=$(readlink /var/folders/*/T/rime.squirrel/rime.squirrel.INFO 2>/dev/null | head -1)
tail -f "/var/folders/*/T/rime.squirrel/$LATEST_LOG"

# 或者使用符号链接
tail -f /var/folders/*/T/rime.squirrel/rime.squirrel.INFO

# 搜索错误信息
grep -i "error\|fail\|exception" /var/folders/*/T/rime.squirrel/rime.squirrel.INFO

# 搜索 Lua 相关
grep -i "lua\|ai\|module\|require" /var/folders/*/T/rime.squirrel/rime.squirrel.INFO

# 检查 Lua 插件是否加载
grep -i "loaded plugin.*lua" /var/folders/*/T/rime.squirrel/rime.squirrel.INFO

# 检查 Lua 组件是否注册
grep -i "registering component.*lua" /var/folders/*/T/rime.squirrel/rime.squirrel.INFO

# 查看 WARNING 日志（env.log.warning 的输出）
tail -f /var/folders/*/T/rime.squirrel/rime.squirrel.WARNING

# 查看 ERROR 日志
tail -f /var/folders/*/T/rime.squirrel/rime.squirrel.ERROR

# 搜索最近的错误（最后 100 行）
tail -100 /var/folders/*/T/rime.squirrel/rime.squirrel.INFO | grep -i error
```

### 清空日志

```bash
# 清空 Squirrel INFO 日志（重新部署前）
LATEST_LOG=$(readlink /var/folders/*/T/rime.squirrel/rime.squirrel.INFO 2>/dev/null | head -1)
> "/var/folders/*/T/rime.squirrel/$LATEST_LOG"

# 或者删除所有日志文件（Squirrel 会重新创建）
rm /var/folders/*/T/rime.squirrel/*.log
```

---

## Lua 脚本调试

### 1. 在 Lua 脚本中写入日志

#### 方式一：使用文件日志（开发阶段推荐）

```lua
-- 初始化时写入日志
function M.init(env)
  local init_file = io.open("/tmp/rime_ai_init.txt", "w")
  if init_file then
    init_file:write("AI module initialized at: " .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
    init_file:close()
  end
end

-- Translator 中写入日志
function M.func(input, seg, env)
  local debug_file = io.open("/tmp/rime_ai_debug.txt", "a")
  if debug_file then
    debug_file:write(string.format("[%s] input='%s', start=%d, _end=%d\n", 
      os.date("%H:%M:%S"), input, seg.start, seg._end))
    debug_file:close()
  end
  -- ... 其他代码
end

-- Processor 中写入日志
function M.func(key, env)
  local proc_file = io.open("/tmp/rime_ai_processor.txt", "a")
  if proc_file then
    proc_file:write(string.format("processor: key_code=%d, input='%s'\n", 
      key:code(), env.engine.context.input))
    proc_file:close()
  end
  return 2
end
```

#### 方式二：使用 env.log（推荐，会写入 Squirrel 日志）

```lua
-- 初始化时写入日志
function M.init(env)
  -- 使用 env.log（推荐，会写入 Squirrel 日志）
  env.log.info("AI module initialized")
end

-- Translator 中写入日志
function M.func(input, seg, env)
  -- 使用 env.log
  env.log.info(string.format("Translator called: input='%s'", input))
end

-- Processor 中写入日志
function M.func(key, env)
  -- 使用 env.log
  env.log.warning("Processor called: key=" .. key:repr())
  env.log.error("Error occurred: " .. error_message)
end
```

**注意**：`env.log` 只在函数内部（如 `M.init(env)` 或 `M.func(key, env)`）可用，不能在模块级别使用。

#### 方式三：统一日志文件（推荐用于项目）

```lua
local LOG_PATH = "/tmp/rime_ai.log"

local function log(kind, fmt, ...)
  local ok, msg = pcall(string.format, fmt, ...)
  if not ok then msg = fmt end
  local log_msg = string.format("[%s][%s] %s", os.date("%H:%M:%S"), kind, msg)
  
  local f = io.open(LOG_PATH, "a")
  if f then
    f:write(log_msg .. "\n")
    f:close()
  end
end

function M.init(env)
  log("INIT", "AI module initialized")
end

function M.func(key, env)
  log("PROCESSOR", "key=%s, input=%s", key:repr(), env.engine.context.input)
end
```

### 2. 检查日志文件

```bash
# 检查模块是否初始化
cat /tmp/rime_ai_init.txt

# 查看 Translator 调用记录
cat /tmp/rime_ai_debug.txt

# 查看 Processor 调用记录
cat /tmp/rime_ai_processor.txt

# 查看统一日志文件
tail -f /tmp/rime_ai.log

# 实时监控
tail -f /tmp/rime_ai_debug.txt
```

### 3. 调试技巧

```lua
-- 使用 pcall 捕获错误
local success, result = pcall(function()
  -- 可能出错的代码
  return some_function()
end)

if not success then
  local err_file = io.open("/tmp/rime_ai_error.txt", "a")
  if err_file then
    err_file:write("Error: " .. tostring(result) .. "\n")
    err_file:close()
  end
  
  -- 或者使用 env.log
  env.log.error("Error: " .. tostring(result))
end
```

---

## 配置验证

### 1. 检查 YAML 语法

```bash
# 使用 Python 验证 YAML
python3 -c "import yaml; yaml.safe_load(open('~/Library/Rime/rime_ice.custom.yaml'))" && echo "✅ YAML 语法正确"

# 或者使用 yamllint（如果已安装）
yamllint ~/Library/Rime/rime_ice.custom.yaml
```

### 2. 检查构建文件

```bash
# 检查构建文件中是否包含配置
grep -E "lua_translator@\*ai|lua_processor@\*ai" ~/Library/Rime/build/rime_ice.schema.yaml

# 检查 lua 映射
grep -A 5 "lua:" ~/Library/Rime/build/rime_ice.schema.yaml | grep "\*ai"
```

### 3. 检查文件存在性

```bash
# 检查 Lua 文件
ls -la ~/Library/Rime/lua/ai_processor.lua
ls -la ~/Library/Rime/lua/ai_translator.lua

# 检查 rime.lua（如果使用）
ls -la ~/Library/Rime/rime.lua

# 检查配置文件
ls -la ~/Library/Rime/rime_ice.custom.yaml
```

---

## 常见问题诊断

### 问题 1: 模块未初始化

**症状**：`/tmp/rime_ai_init.txt` 不存在，或 `env.log.info()` 没有输出

**可能原因**：
1. Rime 未重新部署
2. `rime.lua` 未正确加载模块（如果使用 lua 映射）
3. 模块路径错误
4. Lua 语法错误导致加载失败

**诊断步骤**：
```bash
# 1. 检查 Squirrel 日志中的错误
grep -i "error\|lua\|ai" /var/folders/*/T/rime.squirrel/rime.squirrel.ERROR

# 2. 检查构建文件
grep -E "lua_translator@\*ai" ~/Library/Rime/build/rime_ice.schema.yaml

# 3. 验证 Lua 文件语法（如果安装了 Lua）
lua -l ai_processor  # 基本语法检查

# 4. 检查文件权限
ls -la ~/Library/Rime/lua/ai_processor.lua
```

### 问题 2: Translator 未被调用

**症状**：`/tmp/rime_ai_debug.txt` 不存在，输入 `ai:` 没有反应

**可能原因**：
1. Translator 配置未生效
2. 输入模式不匹配
3. 被其他 translator 优先处理
4. recognizer 未正确配置

**诊断步骤**：
```bash
# 1. 检查配置
grep -A 2 "lua_translator@\*ai" ~/Library/Rime/rime_ice.custom.yaml

# 2. 检查构建文件
grep "lua_translator@\*ai" ~/Library/Rime/build/rime_ice.schema.yaml

# 3. 检查 recognizer 配置（如果使用）
grep -A 3 "recognizer:" ~/Library/Rime/rime_ice.custom.yaml

# 4. 检查日志
tail -20 /tmp/rime_ai.log

# 5. 尝试输入测试
# 输入 "test" 应该显示"测试成功"
# 输入 "ai:" 应该显示 AI 提示
```

### 问题 3: Processor 未被调用

**症状**：`/tmp/rime_ai_processor.txt` 不存在，按键没有反应

**可能原因**：
1. Processor 配置未生效
2. 函数签名错误
3. 返回值不正确

**诊断步骤**：
```bash
# 1. 检查配置
grep -A 2 "lua_processor@\*ai" ~/Library/Rime/rime_ice.custom.yaml

# 2. 检查构建文件
grep "lua_processor@\*ai" ~/Library/Rime/build/rime_ice.schema.yaml

# 3. 检查函数签名
grep -A 10 "function M.func" ~/Library/Rime/lua/ai_processor.lua
```

### 问题 4: 输入被当作拼音处理

**症状**：输入 `ai:` 显示"爱："而不是 AI 提示

**可能原因**：
1. `recognizer/patterns` 未配置
2. Translator 未检查 `seg:has_tag()`
3. punctuator 先处理了特殊字符

**解决方案**：
```yaml
# 在 rime_ice.custom.yaml 中添加
recognizer:
  patterns:
    ai_cmd: "^ai:.*$"
```

```lua
-- 在 translator 中检查
function M.func(input, seg, env)
  if not seg:has_tag("ai_cmd") then
    return
  end
  -- ... 处理逻辑
end
```

### 问题 5: env.log.warning 没有输出

**症状**：在代码中调用了 `env.log.warning()`，但日志文件中没有看到

**可能原因**：
1. `env.log` 在模块级别使用（不可用）
2. 日志级别设置问题
3. Squirrel 日志路径不正确

**解决方案**：
```lua
-- ❌ 错误：在模块级别使用
local success, data = pcall(require, "module")
if not success then
  env.log.warning("Failed to load module: " .. data)  -- 错误！env 不可用
end

-- ✅ 正确：在函数内部使用
function M.init(env)
  local success, data = pcall(require, "module")
  if not success then
    env.log.warning("Failed to load module: " .. data)  -- 正确
  end
end
```

**查看日志**：
```bash
# 查看 WARNING 日志
tail -f /var/folders/*/T/rime.squirrel/rime.squirrel.WARNING

# 搜索特定内容
grep -i "module\|failed" /var/folders/*/T/rime.squirrel/rime.squirrel.WARNING
```

---

## 调试工具

### 1. 检查脚本调用状态

创建 `check_lua_call.sh`：

```bash
#!/bin/bash
# 检查 Lua 脚本是否被调用

echo "🔍 检查 Lua 脚本调用状态..."
echo ""

# 统一日志文件
LOG=/tmp/rime_ai.log

if [ -f "$LOG" ]; then
    echo "✅ 发现统一日志文件: $LOG"
    echo ""

    echo "✅ 模块初始化记录（INIT）："
    grep "\[INIT\]" "$LOG" | tail -5 || echo "   (暂无 INIT 记录)"

    echo ""
    echo "✅ Translator 调用记录（TRANS）："
    grep "\[TRANS\]" "$LOG" | tail -5 || echo "   (暂无 TRANS 记录，尝试输入 'ai:' 查看提示)"

    echo ""
    echo "✅ Processor 调用记录（PROC）："
    grep "\[PROC\]" "$LOG" | tail -10 || echo "   (暂无 PROC 记录，尝试输入 'ai:你好' 后按回车)"

    echo ""
    echo "⚠️ 错误记录（ERROR，如有）："
    grep "\[ERROR\]" "$LOG" | tail -5 || echo "   (暂无 ERROR 记录)"
else
    echo "❌ 统一日志文件不存在：$LOG"
    echo "   可能原因："
    echo "   1. Rime 未重新部署"
    echo "   2. 模块从未被调用"
    echo "   3. 模块路径错误"
fi

echo ""
echo "---"

# 检查配置文件
echo "📝 配置文件检查："
if grep -q "lua_translator@\*ai" ~/Library/Rime/rime_ice.custom.yaml 2>/dev/null; then
    echo "✅ rime_ice.custom.yaml 中已配置 translator"
else
    echo "❌ rime_ice.custom.yaml 中未配置 translator（但可能在 schema 中已有）"
fi

# 在 build 文件中检查 processor / translator 是否最终生效
if grep -q "lua_processor@\*ai" ~/Library/Rime/build/rime_ice.schema.yaml 2>/dev/null; then
    echo "✅ build/rime_ice.schema.yaml 中已配置 processor"
else
    echo "❌ build/rime_ice.schema.yaml 中未找到 processor（lua_processor@*ai）"
fi

if grep -q "lua_translator@\*ai" ~/Library/Rime/build/rime_ice.schema.yaml 2>/dev/null; then
    echo "✅ build/rime_ice.schema.yaml 中已配置 translator"
else
    echo "❌ build/rime_ice.schema.yaml 中未找到 translator（lua_translator@*ai）"
fi
```

### 2. 实时监控脚本

创建 `monitor_rime.sh`：

```bash
#!/bin/bash
# 实时监控 Rime 日志

LOG_DIR=$(find /var/folders -name "rime.squirrel*" -type d 2>/dev/null | head -1)

if [ -z "$LOG_DIR" ]; then
    echo "❌ 未找到 Squirrel 日志文件"
    exit 1
fi

echo "📊 监控 Squirrel 日志: $LOG_DIR"
echo "按 Ctrl+C 退出"
echo ""

tail -f "$LOG_DIR"/*.log 2>/dev/null | grep --color=always -E "error|Error|ERROR|lua|Lua|LUA|ai|AI|module|Module"
```

### 3. 清理日志脚本

创建 `clean_logs.sh`：

```bash
#!/bin/bash
# 清理所有调试日志

echo "🧹 清理调试日志..."

rm -f /tmp/rime_ai_*.txt
rm -f /tmp/rime_test_*.txt
rm -f /tmp/rime_ai.log

LOG_DIR=$(find /var/folders -name "rime.squirrel*" -type d 2>/dev/null | head -1)
if [ -n "$LOG_DIR" ]; then
    > "$LOG_DIR"/*.log 2>/dev/null
    echo "✅ 已清空 Squirrel 日志"
fi

echo "✅ 清理完成"
```

---

## 调试流程

### 标准调试流程

1. **清理旧日志**
   ```bash
   ./clean_logs.sh
   ```

2. **重新部署 Rime**
   - 菜单栏 Squirrel 图标 → 重新部署
   - 或：`killall Squirrel && sleep 2 && open -a Squirrel`

3. **等待几秒**
   ```bash
   sleep 5
   ```

4. **检查初始化**
   ```bash
   cat /tmp/rime_ai_init.txt
   # 或
   tail -20 /tmp/rime_ai.log | grep INIT
   ```

5. **测试输入**
   - 输入 `test` 看是否显示"测试成功"
   - 输入 `ai:` 看是否显示 AI 提示

6. **检查日志**
   ```bash
   ./check_lua_call.sh
   ```

7. **查看 Squirrel 日志**
   ```bash
   tail -50 /var/folders/*/T/rime.squirrel/rime.squirrel.INFO | grep -i error
   tail -50 /var/folders/*/T/rime.squirrel/rime.squirrel.WARNING
   tail -50 /var/folders/*/T/rime.squirrel/rime.squirrel.ERROR
   ```

---

## 快速参考

### 常用命令

```bash
# 查看 Squirrel 日志
tail -f /var/folders/*/T/rime.squirrel/rime.squirrel.INFO

# 检查模块初始化
cat /tmp/rime_ai_init.txt

# 查看 Translator 调用
tail -20 /tmp/rime_ai_debug.txt

# 查看 Processor 调用
tail -20 /tmp/rime_ai_processor.txt

# 查看统一日志文件
tail -f /tmp/rime_ai.log

# 检查配置
grep -E "lua_translator@\*ai|lua_processor@\*ai" ~/Library/Rime/build/rime_ice.schema.yaml

# 验证 YAML
python3 -c "import yaml; yaml.safe_load(open('~/Library/Rime/rime_ice.custom.yaml'))"

# 查看 WARNING 日志（env.log.warning 的输出）
tail -f /var/folders/*/T/rime.squirrel/rime.squirrel.WARNING

# 查看 ERROR 日志
tail -f /var/folders/*/T/rime.squirrel/rime.squirrel.ERROR
```

### 日志文件位置速查

| 日志类型 | 路径 |
|---------|------|
| Squirrel 主日志目录 | `/var/folders/*/T/rime.squirrel/` |
| Squirrel INFO 日志 | `/var/folders/*/T/rime.squirrel/rime.squirrel.INFO` (符号链接) |
| Squirrel ERROR 日志 | `/var/folders/*/T/rime.squirrel/rime.squirrel.ERROR` (符号链接) |
| Squirrel WARNING 日志 | `/var/folders/*/T/rime.squirrel/rime.squirrel.WARNING` (符号链接) |
| Rime 用户数据库日志 | `~/Library/Rime/rime_ice.userdb/*.log` |
| AI 模块初始化 | `/tmp/rime_ai_init.txt` |
| AI Translator 调用 | `/tmp/rime_ai_debug.txt` |
| AI Processor 调用 | `/tmp/rime_ai_processor.txt` |
| 统一日志文件 | `/tmp/rime_ai.log` |
| 测试模块日志 | `/tmp/rime_test_init.txt` |

---

## 注意事项

1. **日志文件权限**：确保 `/tmp` 目录可写
2. **日志轮转**：定期清理旧日志，避免占用磁盘空间
3. **Squirrel 日志路径**：路径中的文件夹 ID 可能因系统而异，使用 `find` 或 `ls -t` 查找最新文件
4. **重新部署**：修改配置后必须重新部署 Rime 才能生效
5. **调试模式**：生产环境建议移除或注释掉调试日志代码
6. **env.log 使用**：`env.log` 只在函数内部可用，不能在模块级别使用

---

## 参考资料

- [Rime 输入方案设计书 - 关于调试](https://github.com/rime/home/wiki/RimeWithSchemata#关于调试)
- [Rime Lua 插件文档](https://rimeinn.github.io/plugin/lua/)
- [rime-ice 文档](https://github.com/iDvel/rime-ice)
- [Rime 配置文档](https://github.com/rime/home/wiki)
- [Rime Lua 运行逻辑详解](./rime_lua_execution_logic.md)


