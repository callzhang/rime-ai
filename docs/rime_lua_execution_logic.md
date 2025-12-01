# Rime Lua 运行逻辑详解

> 本文档基于 [librime-lua 官方文档](https://github.com/hchunhui/librime-lua/wiki/Scripting) 和 [Rime 输入方案设计书](https://github.com/rime/home/wiki/RimeWithSchemata) 整理

## 📋 目录
1. [整体架构](#整体架构)
2. [Lua 模块加载机制](#lua-模块加载机制)
3. [三种 Lua 组件类型](#三种-lua-组件类型)
4. [核心对象说明](#核心对象说明)
5. [执行流程详解](#执行流程详解)
6. [配置映射机制](#配置映射机制)
7. [触发 Lua 脚本的方法](#触发-lua-脚本的方法)
8. [实际示例分析](#实际示例分析)
9. [调试指南](#调试指南)
10. [常见问题](#常见问题)
11. [最佳实践](#最佳实践)
12. [参考资料](#参考资料)

---

## 整体架构

### Rime 输入引擎的组件层次

根据 [Rime 输入方案设计书](https://github.com/rime/home/wiki/RimeWithSchemata)，Rime 输入引擎的处理流程如下：

```
用户输入
    ↓
┌─────────────────────────────────────┐
│  Processors（处理器）                │  ← 处理按键事件
│  - lua_processor@*ai                │
│  - ascii_composer                   │
│  - recognizer                       │  ← 识别特殊模式（如 ai:）
│  - key_binder                       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Segmentors（分段器）                │  ← 将输入分割成片段
│  - ascii_segmentor                  │
│  - matcher                          │
│  - abc_segmentor                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Translators（翻译器）               │  ← 将输入转换为候选词
│  - lua_translator@*ai               │
│  - script_translator                │
│  - lua_translator@*date_translator  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Filters（过滤器）                   │  ← 过滤和排序候选词
│  - lua_filter@*corrector            │
│  - lua_filter@*pin_cand_filter     │
│  - simplifier@emoji                 │
└─────────────────────────────────────┘
    ↓
候选词列表（显示给用户）
```

### 日志文件位置

根据 [Rime 输入方案设计书 - 关于调试](https://github.com/rime/home/wiki/RimeWithSchemata#关于调试)，Rime 的日志文件位置：

- **【鼠鬚管（macOS）】**：`$TMPDIR/rime.squirrel.*`
  - 实际路径：`/var/folders/*/T/rime.squirrel/`
  - 日志级别：INFO、WARNING、ERROR
- **【小狼毫（Windows）】**：`%TEMP%\rime.weasel.*`
- **【中州韻（Linux）】**：`/tmp/rime.ibus.*`
- **早期版本**：`用户资料夹/rime.log`

日志按照级别分为 INFO（信息）、WARNING（警告）、ERROR（错误）。后两类应重点关注，如果新方案部署后不可用或输出与设计不一致，原因可能在此。

---

## Lua 模块加载机制

### 1. 模块文件位置

```
~/Library/Rime/
├── rime.lua              # Lua 模块加载入口（可选）
└── lua/
    ├── ai_processor.lua  # AI Processor 模块
    ├── ai_translator.lua # AI Translator 模块
    ├── date_translator.lua
    ├── calc_translator.lua
    └── ...
```

### 2. rime.lua 的作用

```lua
-- rime.lua
ai = require("ai")
```

**作用**：
- 在全局作用域中创建 `ai` 变量
- 这个变量指向 `lua/ai.lua` 返回的模块对象
- Rime 通过这个变量找到对应的 Lua 模块

**是否必须**：
- ❌ **不是必须的**
- 如果使用 `lua_processor@*module_name` 或 `lua_translator@*module_name` 语法，Rime 会自动加载对应的 Lua 模块
- 只有在需要显式 `require` 模块或进行模块间依赖时才需要 `rime.lua`
- 当前项目中的 `ai_processor` 和 `ai_translator` 使用 `*module_name` 语法，不需要 `rime.lua`

**加载时机**：
- Rime 启动时加载
- 重新部署时重新加载

### 3. 模块结构

每个 Lua 模块必须返回一个表（table），包含特定的函数：

```lua
-- ai.lua
local M = {}

-- 初始化函数（可选）
function M.init(env)
  -- 在模块被使用时调用一次
  -- 可以读取配置、初始化变量等
  local config = env.engine.schema.config
  env.prefix = config:get_string('my_module/prefix') or 'default'
end

-- Processor 函数（可选）
function M.func(key, env)
  -- 处理按键事件
  return 2  -- 返回值：1=已处理，2=未处理
end

-- Translator 函数（可选）
function M.func(input, seg, env)
  -- 将输入转换为候选词
  yield(cand)  -- 生成候选词
end

-- Filter 函数（可选）
function M.func(input, env)
  -- 过滤和排序候选词
  for cand in input:iter() do
    -- 处理每个候选词
    yield(cand)
  end
end

return M  -- 返回模块对象
```

**注意**：如果使用 `M.func` 作为函数名，translator 和 processor **不能**共用一个模块，因为它们有不同的函数签名。需要使用不同的函数名（如 `M.translator` 和 `M.processor`）或分开为不同的模块。

---

## 三种 Lua 组件类型

### 1. Processor（处理器）

**作用**：处理按键事件，在输入处理的最早阶段执行

**配置方式**：
```yaml
engine/processors/@before 0:
  - lua_processor@*ai
```

**函数签名**：
```lua
function M.func(key, env)
  -- key: 按键对象
  --   - key:repr() 返回按键的字符串表示（如 "space", "Return", "a"）
  --   - key:code() 返回按键的代码值（数字，如 32=空格，13=回车）
  --   - key:release() 返回是否释放按键（布尔值，false=按下，true=释放）
  -- env: 环境对象
  --   - env.engine: Rime 引擎对象
  --   - env.engine.context: 输入上下文对象（Context）
  --     - context.input: 当前输入字符串（原始输入，如 "ai:test"）
  --     - context:is_composing(): 是否正在输入（布尔值）
  --     - context:has_menu(): 是否有候选词面板（布尔值）
  --     - context:clear(): 清空输入
  --     - context:push_input(str): 追加输入字符串到输入区域（不会提交上屏）
  --       可以追加普通字符串，也可以追加候选词文本（如 current_candidate.text）
  --     - context:pop_input(count): 删除 count 个字符（从光标位置向左）
  --     - context:select(index): 选择候选词（index 从 0 开始），不立即上屏
  --     - context:confirm_current_selection(): 确认当前选中的候选词并上屏，结束输入过程
  --     - context:get_selected_candidate(): 获取当前选中的候选词对象（Candidate）
  --     - context:get_preedit(): 获取预编辑文本对象（Preedit）
  --     - context:get_script_text(): 获取按音节分割的文本（如 "ni hao"）
  --     - context.composition: Composition 对象（输入构建状态）
  --     - context.commit_history: CommitHistory 对象（提交历史）
  --     - context.commit_notifier: Notifier 对象（提交事件通知器）
  --     - context.select_notifier: Notifier 对象（选择事件通知器）
  --     - context.update_notifier: Notifier 对象（更新事件通知器）
  --     - context.delete_notifier: Notifier 对象（删除事件通知器）
  --   - env.engine.schema: 方案对象
  --   - env.log: 日志对象（env.log.warning(), env.log.error(), env.log.info()）
  --     日志会写入到 Squirrel 的日志文件中（WARNING/ERROR/INFO）
  -- 返回值：
  --   0 = kRejected：拒绝处理，交还操作系统按默认方式响应
  --      ⚠️ 注意：如果已响应但返回 0，按键会被操作系统再处理一次（可能处理两次）
  --   1 = kAccepted：已处理，结束流程，不传递给其他 processor，不执行默认行为（最常用）
  --      ⚠️ 注意：如果未响应但返回 1，相当于禁用这个按键
  --   2 = kNoop：不处理，交给接下来的处理器决定（最常用）
  --      ⚠️ 注意：如果已响应但返回 2，按键会被其他组件再处理（可能处理多次）
  --   其他值 = 等同于 2（kNoop）
  return 2
end
```

**执行时机**：
- 每次按键时都会调用
- 在所有其他处理之前执行
- 可以拦截按键，修改输入状态

**示例**：
```lua
function M.func(key, env)
  local key_code = key:code()
  local input = env.engine.context.input
  
  -- 如果按下 Escape 键，清空输入
  if key_code == 27 then  -- Escape
    env.engine.context:clear()
    return 1  -- 已处理
  end
  
  return 2  -- 未处理，继续传递
end
```

### 2. Translator（翻译器）

**作用**：将输入字符串转换为候选词列表

**配置方式**：
```yaml
engine/translators/@before 0:
  - lua_translator@*ai
```

**函数签名**：
```lua
function M.func(input, seg, env)
  -- input: 输入字符串（当前片段）
  -- seg: 片段对象
  --   - seg.start: 片段在输入中的开始位置（数字，从 0 开始）
  --   - seg._end: 片段在输入中的结束位置（数字）
  --   - seg:has_tag(tag): 检查片段是否有指定标签（布尔值）
  -- env: 环境对象
  
  -- 生成候选词
  -- Candidate 函数参数（5个参数）：
  --   1. type: 候选词类型（字符串），用于标识候选词的来源或类别
  --   2. start: 候选词对应的输入开始位置（数字），通常使用 seg.start
  --   3. _end: 候选词对应的输入结束位置（数字），通常使用 seg._end
  --   4. text: 候选词的文本内容（字符串），用户选择后上屏的内容
  --   5. comment: 候选词的注释（字符串），显示在候选词面板中的提示信息
  local cand = Candidate("type", seg.start, seg._end, "候选词", "注释")
  cand.quality = 99999  -- 设置权重（越高越靠前，默认值通常较小）
  yield(cand)  -- 输出候选词
  
  -- 返回值：
  --   Translator 函数通常不返回值（隐式返回 nil）
  --   或者显式 return（不返回值）
  --   返回值不影响候选词的生成
end
```

**执行时机**：
- 在 Segmentor 分割输入后执行
- 每个输入片段都会调用一次
- 可以生成多个候选词

**执行顺序**：
```yaml
translators:
  - lua_translator@*ai          # 1. 最先执行（@before 0）
  - punct_translator            # 2. 标点符号翻译器
  - script_translator           # 3. 拼音翻译器
  - lua_translator@*date_translator  # 4. 日期翻译器
  - ...
```

**示例**：
```lua
function M.func(input, seg, env)
  -- 如果输入是 "test"，生成候选词
  if input == "test" then
    local cand = Candidate("test", seg.start, seg._end, "测试成功", "✅")
    cand.quality = 99999
    yield(cand)
    return
  end
  
  -- 如果输入以 "ai:" 开头
  if input:match("^ai:") then
    local cand = Candidate("ai", seg.start, seg._end, "AI 功能", "🤖")
    cand.quality = 99999
    yield(cand)
    return
  end
end
```

### 3. Filter（过滤器）

**作用**：过滤、排序、修改候选词列表

**配置方式**：
```yaml
engine/filters:
  - lua_filter@*corrector
  - lua_filter@*pin_cand_filter
```

**函数签名**：
```lua
function M.func(input, env)
  -- input: 候选词迭代器
  -- env: 环境对象
  
  -- 遍历所有候选词
  for cand in input:iter() do
    -- 修改候选词
    cand.quality = cand.quality + 100
    yield(cand)  -- 输出候选词
  end
end
```

**执行时机**：
- 在所有 Translator 生成候选词后执行
- 可以修改候选词的顺序、内容、权重等

**执行顺序**：
```yaml
filters:
  - lua_filter@*corrector          # 1. 错音错字提示
  - lua_filter@*pin_cand_filter    # 2. 置顶候选项
  - lua_filter@*long_word_filter   # 3. 长词优先
  - simplifier@emoji               # 4. Emoji 转换
  - uniquifier                     # 5. 去重
```

---

## 核心对象说明

### Composition（输入构建状态）

**含义**：代表用户当前的输入构建状态，包含候选词菜单、候选词和分段等相关信息。

**访问方式**：
```lua
local composition = env.engine.context.composition
```

**主要方法**（根据 [librime-lua Objects 文档](https://github.com/hchunhui/librime-lua/wiki/Objects)）：

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `empty()` | 无 | boolean | 判断当前输入是否为空 |
| `back()` | 无 | Segment | 获取输入序列中最后一个 Segment 对象 |
| `pop_back()` | 无 | 无 | 移除输入序列中最后一个 Segment 对象 |
| `push_back(seg)` | seg: Segment | 无 | 在输入序列末尾添加一个新的 Segment 对象 |
| `has_finished_composition()` | 无 | boolean | 判断输入构建是否完成 |
| `get_prompt()` | 无 | string | 获取最后一个 Segment 的提示字符串 |
| `toSegmentation()` | 无 | Segmentation | 将 Composition 转换为 Segmentation 对象 |

**使用示例**：
```lua
local composition = env.engine.context.composition

if not composition:empty() then
  -- 获取最后一个 Segment 对象
  local segment = composition:back()
  
  -- 获取选中的候选词索引
  local selected_index = segment.selected_index
  
  -- 获取候选词菜单
  local menu = segment.menu
  
  -- 获取已加载的候选词数量
  local count = menu:candidate_count()
  
  -- 移除最后一个 Segment（用于替换输入）
  composition:pop_back()
end
```

### Segmentation（分词结果）

**含义**：用于在分词处理流程中存储 Segment，并将其传递给 Translator 进行翻译处理。

**访问方式**：
```lua
local composition = env.engine.context.composition
local segmentation = composition:toSegmentation()
```

**主要方法**：

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `empty()` | 无 | boolean | 判断是否包含 Segment 或 Menu |
| `back()` | 无 | Segment | 获取输入序列中最后一个 Segment 对象 |
| `pop_back()` | 无 | 无 | 移除输入序列中最后一个 Segment 对象 |
| `reset_length(size)` | size: number | 无 | 保留指定数量的 Segment |
| `add_segment(seg)` | seg: Segment | 无 | 添加新的 Segment 对象 |
| `forward()` | 无 | 无 | 新增一个 kVoid 的 Segment |
| `trim()` | 无 | 无 | 移除输入序列中长度为 0 的 Segment |
| `has_finished_segmentation()` | 无 | boolean | 判断分词是否完成 |
| `get_current_start_position()` | 无 | number | 获取当前 Segment 的起始位置 |
| `get_current_end_position()` | 无 | number | 获取当前 Segment 的结束位置 |
| `get_current_segment_length()` | 无 | number | 获取当前 Segment 的长度 |
| `get_confirmed_position()` | 无 | number | 获取已确认的输入长度 |

**使用场景**：
- 在 Segmentor 中创建和分割 Segment
- 在 Translator 中接收 Segment 并生成候选词

### Preedit（预编辑文本）

**含义**：用户输入但尚未确认上屏的文本，通常显示在光标位置，提示用户当前的输入状态。

**访问方式**：
```lua
local preedit = env.engine.context:get_preedit()
```

**主要属性**：

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `text` | string | 当前的预编辑文本（显示在输入框中的文本） |
| `caret_pos` | number | 光标位置（脱字符位置，以字符数量标记） |
| `sel_start` | number | 选中文本的起始位置 |
| `sel_end` | number | 选中文本的结束位置 |

**与 `context.input` 的区别**：

| 属性 | 说明 | 示例 |
|------|------|------|
| `context.input` | 原始输入字符串（用户实际输入的字符） | `"ai:test"` |
| `preedit.text` | 预编辑文本（经过格式化后显示在输入框中的文本） | `"ai:test"` 或 `"AI:test"`（如果经过格式化） |

**使用示例**：
```lua
-- 获取预编辑文本
local preedit = env.engine.context:get_preedit()
local preedit_text = preedit.text  -- 预编辑文本
local caret_pos = preedit.caret_pos  -- 光标位置

-- 在 Filter 中，候选词也有 preedit 属性
function M.func(input, env)
  for cand in input:iter() do
    -- cand.preedit 是候选词对应的输入编码（经过格式化）
    -- 例如：输入 "nihao"，cand.preedit 可能是 "ni hao"（如果经过格式化）
    if cand.preedit:match("^ni") then
      yield(cand)
    end
  end
end
```

**注意事项**：
- `preedit.text` 可能经过 `preedit_format` 转换（如 `v` → `ü`）
- 在 Filter 中，`cand.preedit` 是候选词对应的输入编码，可能与 `context.input` 不同
- `preedit.text` 会随着用户选择和输入而变化
- 在双拼方案中，`cand.preedit` 可能是全拼或双拼格式，取决于 `preedit_format` 配置

### Notifier（事件通知器）

**含义**：用于监听特定事件并触发回调函数的机制。通过连接（connect）回调函数到相应的 notifier，可以在特定事件发生时执行自定义的操作。

**访问方式**：
```lua
local context = env.engine.context
local commit_notifier = context.commit_notifier
local select_notifier = context.select_notifier
local update_notifier = context.update_notifier
local delete_notifier = context.delete_notifier
```

**主要类型**（根据 [librime-lua Objects 文档](https://github.com/hchunhui/librime-lua/wiki/Objects)）：

| Notifier 类型 | 触发时机 | 回调函数参数 | 说明 |
|--------------|---------|------------|------|
| `commit_notifier` | 用户确认输入（commit）时 | `ctx: Context` | 当用户选择候选词并上屏时触发 |
| `select_notifier` | 用户选择候选项时 | `ctx: Context` | 当用户在候选词面板中选择候选项时触发 |
| `update_notifier` | 输入内容更新时 | `ctx: Context` | 当输入内容发生变化时触发 |
| `delete_notifier` | 输入内容被删除时 | `ctx: Context` | 当用户删除输入内容时触发 |

**主要方法**：

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `connect(callback)` | callback: function | Connection | 连接回调函数到 notifier |
| `disconnect()` | 无 | 无 | 断开连接（通过 Connection 对象调用） |

**使用示例**：

1. **监听提交事件**：
   ```lua
   function M.init(env)
     -- 在初始化时连接 notifier
     env.commit_notifier = env.engine.context.commit_notifier:connect(
       function(ctx)
         local commit_text = ctx:get_commit_text()
         -- 处理提交的文本
         log("committed: %s", commit_text)
       end
     )
   end
   
   -- 在模块卸载时断开连接（如果需要）
   function M.fini(env)
     if env.commit_notifier then
       env.commit_notifier:disconnect()
     end
   end
   ```

2. **监听选择事件**：
   ```lua
   function M.init(env)
     env.select_notifier = env.engine.context.select_notifier:connect(
       function(ctx)
         local selected = ctx:get_selected_candidate()
         if selected then
           log("selected: %s", selected.text)
         end
       end
     )
   end
   ```

3. **监听更新事件**：
   ```lua
   function M.init(env)
     env.update_notifier = env.engine.context.update_notifier:connect(
       function(ctx)
         local input = ctx.input
         log("input updated: %s", input)
       end
     )
   end
   ```

**注意事项**：
- Notifier 回调函数在事件发生时异步执行
- 需要在 `init` 函数中连接 notifier，在 `fini` 函数中断开连接（如果模块支持）
- 多个回调函数可以连接到同一个 notifier
- Connection 对象用于管理连接，可以调用 `disconnect()` 断开连接
- 不要在回调函数中执行耗时操作，以免影响输入响应速度

---

## 执行流程详解

### 完整执行流程示例

假设用户输入：`ai:test`

#### 阶段 1: Processors（处理器）

```
1. lua_processor@*ai.processor(key, env)
   - 处理按键事件
   - 返回 2（未处理）

2. ascii_composer
   - 处理 ASCII 输入

3. recognizer
   - 检查输入是否匹配 patterns
   - 发现 "ai:test" 匹配 "^ai:.*$"
   - 给输入片段打上 "ai_cmd" 标签

4. 其他 processors...
```

#### 阶段 2: Segmentors（分段器）

```
1. ascii_segmentor
   - 识别 ASCII 字符

2. matcher
   - 匹配输入模式

3. abc_segmentor
   - 分割拼音输入
   - 创建片段：start=0, _end=7, input="ai:test"

4. 其他 segmentors...
```

#### 阶段 3: Translators（翻译器）

```
1. lua_translator@*ai.func(input, seg, env)
   - input = "ai:test"
   - seg.start = 0, seg._end = 7
   - 检查 seg:has_tag("ai_cmd")
   - 生成候选词："AI 功能已激活"

2. punct_translator
   - 处理标点符号

3. script_translator
   - 处理拼音输入
   - 生成候选词："爱：test"（如果没有被 ai_translator 拦截）

4. 其他 translators...
```

#### 阶段 4: Filters（过滤器）

```
1. lua_filter@*corrector
   - 检查错音错字

2. lua_filter@*pin_cand_filter
   - 置顶特定候选项

3. lua_filter@*long_word_filter
   - 提升长词优先级

4. simplifier@emoji
   - Emoji 转换

5. uniquifier
   - 去重
```

---

## 配置映射机制

### 1. 配置语法

```yaml
engine/translators/@before 0:
  - lua_translator@*ai
```

**语法解析**：
- `lua_translator`：组件类型（Lua 翻译器）
- `@*ai`：模块名称
  - `*` 表示这是一个 Lua 模块
  - `ai` 是模块名称

### 2. 模块查找流程

**方式一：使用 `*module_name` 语法（推荐，不需要 rime.lua）**

```
1. Rime 看到 lua_translator@*ai
   ↓
2. 提取模块名称：ai
   ↓
3. 直接加载 lua/ai.lua 文件
   ↓
4. 调用 ai.func() 函数
```

**方式二：使用 lua 映射（需要 rime.lua）**

```
1. Rime 看到 lua_translator@*ai
   ↓
2. 提取模块名称：ai
   ↓
3. 查找 lua 映射：
   lua:
     '*ai': ai
   ↓
4. 在全局作用域查找 ai 变量
   ↓
5. 找到 rime.lua 中定义的 ai = require("ai")
   ↓
6. 加载 lua/ai.lua 文件
   ↓
7. 调用 ai.func() 函数
```

### 3. recognizer/patterns 的作用

```yaml
recognizer:
  patterns:
    ai_cmd: "^ai:.*$"
```

**作用**：
- 在 Processor 阶段，`recognizer` 检查输入是否匹配模式
- 如果匹配，给输入片段打上对应的标签（tag）
- Translator 可以通过 `seg:has_tag("ai_cmd")` 检查标签

**执行流程**：
```
输入: "ai:test"
  ↓
recognizer 检查 patterns
  ↓
匹配 "^ai:.*$"
  ↓
给片段打上 "ai_cmd" 标签
  ↓
Translator 检查标签
  ↓
if seg:has_tag("ai_cmd") then
  -- 处理 AI 命令
end
```

---

## 触发 Lua 脚本的方法

### 方法一：recognizer/patterns + lua_translator（推荐）

**原理**：
- 使用 `recognizer/patterns` 定义输入模式
- recognizer 在 processor 阶段识别模式并打标签
- lua_translator 检查标签并处理

**配置**：
```yaml
patch:
  # 1. 定义识别模式
  recognizer:
    patterns:
      my_pattern: "^prefix.*$"  # 匹配以 prefix 开头的输入
  
  # 2. 注册 translator
  engine/translators/@before 0:
    - lua_translator@*my_module
```

**Lua 脚本**：
```lua
local M = {}

function M.func(input, seg, env)
  -- 检查是否有标签
  if not seg:has_tag("my_pattern") then
    return  -- 不处理
  end
  
  -- 处理逻辑
  local cand = Candidate("my_module", seg.start, seg._end, "结果", "注释")
  cand.quality = 99999
  yield(cand)
end

return M
```

**优点**：
- ✅ 不会与拼音输入冲突
- ✅ 可以精确控制匹配模式
- ✅ 支持复杂的正则表达式

**缺点**：
- ⚠️ 需要配置 recognizer
- ⚠️ 如果 punctuator 先处理了字符，可能无法识别

### 方法二：直接匹配输入

**原理**：
- 在 translator 中直接检查输入字符串
- 不需要 recognizer 配置

**配置**：
```yaml
patch:
  engine/translators/@before 0:
    - lua_translator@*my_module
```

**Lua 脚本**：
```lua
local M = {}

function M.func(input, seg, env)
  -- 直接匹配输入
  if input == "test" then
    local cand = Candidate("my_module", seg.start, seg._end, "测试", "test")
    cand.quality = 99999
    yield(cand)
    return
  end
  
  -- 或者使用模式匹配
  if input:match("^prefix") then
    -- 处理逻辑...
  end
end

return M
```

**优点**：
- ✅ 简单直接
- ✅ 不需要 recognizer 配置
- ✅ 适合简单的固定输入

**缺点**：
- ⚠️ 可能与拼音输入冲突（如 "ai" 会被当作拼音）
- ⚠️ 需要设置高权重才能优先显示

### 方法三：使用 prefix 配置

**原理**：
- 配置一个 prefix（前缀）
- 在 Lua 脚本中读取 prefix 配置
- 匹配以 prefix 开头的输入

**配置**：
```yaml
patch:
  recognizer:
    patterns:
      my_pattern: "^prefix.*$"
  
  my_module:
    prefix: "prefix"  # 可配置的前缀
  
  engine/translators/@before 0:
    - lua_translator@*my_module
```

**Lua 脚本**：
```lua
local M = {}

function M.init(env)
  local config = env.engine.schema.config
  env.prefix = config:get_string('my_module/prefix') or 'default'
end

function M.func(input, seg, env)
  if not seg:has_tag("my_pattern") then
    return
  end
  
  -- 使用配置的 prefix
  local query = input:sub(#env.prefix + 1)
  -- 处理逻辑...
end

return M
```

**优点**：
- ✅ 前缀可配置
- ✅ 灵活，可以修改而不改代码
- ✅ 结合 recognizer 使用，不会冲突

### 方法四：使用 lua_processor 拦截按键

**原理**：
- 使用 processor 在按键阶段拦截
- 可以修改输入或阻止默认行为

**配置**：
```yaml
patch:
  engine/processors/@before 0:
    - lua_processor@*my_module
```

**Lua 脚本**：
```lua
local M = {}

function M.func(key, env)
  local context = env.engine.context
  local input = context.input
  
  -- 检查输入是否匹配
  if input:match("^@") then
    local key_code = key:code()
    
    -- 拦截特定按键
    if key_code == 32 then  -- Space
      context:push_input(" ")
      return 1  -- 已处理
    end
    
    if key_code == 13 then  -- Enter
      return 1  -- 已处理，不上屏
    end
  end
  
  return 2  -- 不处理，继续传递
end

return M
```

**优点**：
- ✅ 可以在按键阶段拦截
- ✅ 可以修改输入行为
- ✅ 可以阻止默认处理

**缺点**：
- ⚠️ 只能处理按键，不能生成候选词
- ⚠️ 需要配合 translator 使用

### 方法对比

| 方法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **recognizer + translator** | 不冲突、精确控制 | 需要配置 | 复杂模式匹配 |
| **直接匹配** | 简单直接 | 可能冲突 | 简单固定输入 |
| **prefix 配置** | 可配置、灵活 | 需要配置 | 需要可配置前缀 |
| **processor 拦截** | 可拦截按键 | 不能生成候选词 | 需要修改按键行为 |

---

## 实际示例分析

### 示例 1: AI 模块配置

#### 配置文件（rime_ice.custom.yaml）

```yaml
patch:
  # 1. 定义识别模式
  recognizer:
    patterns:
      ai_cmd: "^(@ai|ai:).*$"  # 匹配以 @ai 或 ai: 开头的输入
  
  # 2. 注册 Processor（最早执行）
  engine/processors/@before 0:
    - lua_processor@*ai_processor
  
  # 3. 注册 Translator（最早执行）
  engine/translators/@before 0:
    - lua_translator@*ai_translator
```

#### Lua 模块（lua/ai_translator.lua）

```lua
local M = {}

function M.func(input, seg, env)
  -- 检查是否有 ai_cmd 标签
  if not seg:has_tag("ai_cmd") then
    return  -- 不是 AI 命令，不处理
  end
  
  -- 生成提示候选词
  if input == "ai:" or input == "@ai" then
    local cand = Candidate("ai", seg.start, seg._end, "🤖", "输入问题后回车")
    cand.quality = 99999
    yield(cand)
    return
  end
  
  -- 处理 ai:query 格式
  local query = input:match("^(?:ai:|@ai%s+)(.+)$")
  if query then
    local cand = Candidate("ai", seg.start, seg._end, query .. " 🤖", "按回车调用 AI")
    cand.quality = 99999
    yield(cand)
  end
end

return M
```

#### Lua 模块（lua/ai_processor.lua）

```lua
local M = {}

function M.func(key, env)
  local context = env.engine.context
  local key_repr = key:repr()
  local input = context.input
  
  -- 只处理 AI 命令
  if not context:is_composing() then
    return 2
  end
  
  local query = input:match("^(?:ai:|@ai%s+)(.+)$")
  if not query then
    return 2
  end
  
  -- 处理回车键：调用 AI
  if key_repr == "Return" or key_repr == "Enter" then
    -- 调用 AI 并上屏结果
    local ai_response = call_ai_api(query)
    env.engine:commit_text(ai_response)
    context:clear()
    return 1  -- 已处理
  end
  
  return 2  -- 未处理，继续传递
end

return M
```

### 示例 2: 日期翻译器

```lua
local M = {}

function M.init(env)
  local config = env.engine.schema.config
  env.name_space = env.name_space:gsub('^*', '')
  M.date = config:get_string(env.name_space .. '/date') or 'rq'
end

function M.func(input, seg, env)
  if input == M.date then
    local cand = Candidate('date', seg.start, seg._end, os.date('%Y-%m-%d'), '')
    cand.quality = 100
    yield(cand)
  end
end

return M
```

**配置**：
```yaml
patch:
  engine/translators/@before 0:
    - lua_translator@*date_translator
  date_translator:
    date: rq
```

### 示例 3: 计算器

```yaml
patch:
  recognizer:
    patterns:
      calculator: "^cC.+"
  calculator:
    prefix: cC
  engine/translators/@before 0:
    - lua_translator@*calc_translator
```

```lua
local calc = {}

function calc.init(env)
  local config = env.engine.schema.config
  env.prefix = config:get_string('calculator/prefix') or 'cC'
end

function calc.func(input, seg, env)
  if not seg:has_tag('calculator') then
    return
  end
  
  local express = input:sub(#env.prefix + 1)
  -- 计算逻辑...
  local result = calculate(express)
  yield(Candidate('calc', seg.start, seg._end, result, ''))
end

return calc
```

---

## 调试指南

### 日志文件位置

#### Squirrel 主日志（macOS）

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

#### Rime 用户数据库日志

```bash
# Rime 用户数据库日志
~/Library/Rime/rime_ice.userdb/*.log

# 查看最新的日志
ls -lt ~/Library/Rime/rime_ice.userdb/*.log | head -1
```

#### 自定义调试日志

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

# 查看 WARNING 日志（env.log.warning 的输出）
tail -f /var/folders/*/T/rime.squirrel/rime.squirrel.WARNING
```

### 在 Lua 脚本中写入日志

```lua
-- 初始化时写入日志
function M.init(env)
  local init_file = io.open("/tmp/rime_ai_init.txt", "w")
  if init_file then
    init_file:write("AI module initialized at: " .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
    init_file:close()
  end
  
  -- 使用 env.log（推荐，会写入 Squirrel 日志）
  env.log.info("AI module initialized")
end

-- Translator 中写入日志
function M.func(input, seg, env)
  local debug_file = io.open("/tmp/rime_ai_debug.txt", "a")
  if debug_file then
    debug_file:write(string.format("[%s] input='%s', start=%d, _end=%d\n", 
      os.date("%H:%M:%S"), input, seg.start, seg._end))
    debug_file:close()
  end
  
  -- 使用 env.log
  env.log.info(string.format("Translator called: input='%s'", input))
end

-- Processor 中写入日志
function M.func(key, env)
  local proc_file = io.open("/tmp/rime_ai_processor.txt", "a")
  if proc_file then
    proc_file:write(string.format("processor: key_code=%d, input='%s'\n", 
      key:code(), env.engine.context.input))
    proc_file:close()
  end
  
  -- 使用 env.log
  env.log.warning("Processor called: key=" .. key:repr())
end
```

### 配置验证

```bash
# 检查 YAML 语法
python3 -c "import yaml; yaml.safe_load(open('~/Library/Rime/rime_ice.custom.yaml'))" && echo "✅ YAML 语法正确"

# 检查构建文件
grep -E "lua_translator@\*ai|lua_processor@\*ai" ~/Library/Rime/build/rime_ice.schema.yaml

# 检查文件存在性
ls -la ~/Library/Rime/lua/ai_processor.lua
ls -la ~/Library/Rime/lua/ai_translator.lua
ls -la ~/Library/Rime/rime_ice.custom.yaml
```

### 常见问题诊断

#### 问题 1: 模块未初始化

**症状**：`/tmp/rime_ai_init.txt` 不存在

**可能原因**：
1. Rime 未重新部署
2. Lua 语法错误导致加载失败
3. 模块路径错误

**诊断步骤**：
```bash
# 1. 检查 Squirrel 日志中的错误
grep -i "error\|lua\|ai" /var/folders/*/T/rime.squirrel/rime.squirrel.ERROR

# 2. 检查构建文件
grep -E "lua_translator@\*ai" ~/Library/Rime/build/rime_ice.schema.yaml

# 3. 验证 Lua 文件语法
lua -l ai_processor  # 如果安装了 Lua
```

#### 问题 2: Translator 未被调用

**症状**：输入 `ai:` 没有反应

**可能原因**：
1. Translator 配置未生效
2. 输入模式不匹配
3. 被其他 translator 优先处理

**诊断步骤**：
```bash
# 1. 检查配置
grep -A 2 "lua_translator@\*ai" ~/Library/Rime/rime_ice.custom.yaml

# 2. 检查 recognizer 配置
grep -A 3 "recognizer:" ~/Library/Rime/rime_ice.custom.yaml

# 3. 检查日志
tail -20 /tmp/rime_ai.log
```

#### 问题 3: Processor 未被调用

**症状**：按键没有反应

**可能原因**：
1. Processor 配置未生效
2. 函数签名错误
3. 返回值不正确

**诊断步骤**：
```bash
# 1. 检查配置
grep -A 2 "lua_processor@\*ai" ~/Library/Rime/rime_ice.custom.yaml

# 2. 检查函数签名
grep -A 10 "function M.func" ~/Library/Rime/lua/ai_processor.lua
```

---

## 常见问题

### Q1: 为什么我的 Lua 模块没有被调用？

**可能原因**：
1. `rime.lua` 中没有 `require` 模块（如果使用 lua 映射）
2. 配置中没有正确映射（`lua: { '*ai': ai }`）
3. 函数名不正确（应该是 `M.func` 而不是 `M.translator`）
4. 没有重新部署 Rime
5. Lua 语法错误导致加载失败

**解决方案**：
- 使用 `*module_name` 语法，不需要 `rime.lua` 和 `lua:` 映射
- 检查 Squirrel 日志中的错误信息
- 确保函数名正确
- 重新部署 Rime

### Q2: 如何确保我的 Translator 最先执行？

**方法**：
```yaml
engine/translators/@before 0:
  - lua_translator@*ai
```

**注意**：`@before 0` **只在 `custom.yaml` 的 `patch` 中有效**

### Q3: 如何让输入不被其他 Translator 处理？

**方法**：
1. 使用 `recognizer/patterns` 打标签
2. 在 Translator 中检查标签
3. 设置高权重（`quality = 99999`）

### Q4: Processor 和 Translator 的区别？

**Processor**：
- 处理按键事件
- 可以修改输入状态
- 在所有处理之前执行

**Translator**：
- 将输入转换为候选词
- 不能修改输入状态
- 在 Segmentor 之后执行

### Q5: rime.lua 是否必须？

**答案**：❌ **不是必须的**

**说明**：
- 如果使用 `lua_processor@*module_name` 或 `lua_translator@*module_name` 语法，Rime 会自动加载对应的 Lua 模块
- 只有在需要显式 `require` 模块或进行模块间依赖时才需要 `rime.lua`
- 当前项目中的 `ai_processor` 和 `ai_translator` 使用 `*module_name` 语法，不需要 `rime.lua`

### Q6: `engine/translators/@before 0` 不起作用？

**答案**：检查配置位置

**说明**：
- `@before 0` **只在 `custom.yaml` 的 `patch` 中有效**
- 在 `schema.yaml` 中直接配置 `engine/translators` 时，不能使用 `@before 0` 语法
- 如果 `@before 0` 不起作用，确保在 `custom.yaml` 的 `patch` 中配置

**正确配置**：
```yaml
# custom.yaml
patch:
  engine/translators/@before 0:
    - lua_translator@*ai_translator  # ✅ 有效
```

**错误配置**：
```yaml
# schema.yaml
engine:
  translators:
    - lua_translator@*ai_translator/@before 0  # ❌ 无效语法
```

### Q7: 如何处理空格键选择候选词但不立即上屏？

**A**: 使用 `context:select(index)` 方法选择候选词，然后返回 `1`（kAccepted）

**示例**：
```lua
function M.func(key, env)
  local context = env.engine.context
  local key_repr = key:repr()
  
  -- 处理空格键：如果有候选词面板，选择第一个候选词但不立即上屏
  if key_repr == "space" then
    if context:has_menu() then
      -- 选择第一个候选词（index 0），但不立即上屏
      context:select(0)
      return 1  -- ✅ 已处理，阻止默认行为（默认行为会上屏并终止 compose）
    else
      -- 没有候选词面板，追加空格到输入
      context:push_input(" ")
      return 1  -- ✅ 已处理，阻止默认行为
    end
  end
  
  return 2
end
```

### Q8: 如何在 processor 中上屏选中文字但不结束输入？

**A**: 有两种方式：

#### 方式一：使用 `env.engine:commit_text(text)`（上屏但不结束输入）

```lua
function M.func(key, env)
  local context = env.engine.context
  if key:repr() == "Return" then
    local selected = context:get_selected_candidate()
    if selected then
      env.engine:commit_text(selected.text)
      -- 不调用 context:clear()，保持输入状态
      return 1
    end
  end
  return 2
end
```

#### 方式二：使用 `context:push_input(candidate.text)`（添加到输入区域）

```lua
function M.func(key, env)
  local context = env.engine.context
  if key:repr() == "Return" then
    local selected = context:get_selected_candidate()
    if selected then
      -- 将候选词文本添加到输入区域（不会上屏）
      context:push_input(selected.text)
      return 1
    end
  end
  return 2
end
```

### Q9: env.log.warning 的日志在哪里查看？

**A**: `env.log.warning()` 会写入 Squirrel 的 WARNING 日志文件：

```bash
# 查看 WARNING 日志
tail -f /var/folders/*/T/rime.squirrel/rime.squirrel.WARNING

# 搜索特定内容
grep -i "module\|failed" /var/folders/*/T/rime.squirrel/rime.squirrel.WARNING
```

**注意**：`env.log` 只在函数内部（如 `M.init(env)` 或 `M.func(key, env)`）可用，不能在模块级别使用。

---

## 最佳实践

1. **使用模块表结构**：更清晰，支持 init 函数
2. **合理使用 recognizer/patterns**：对于需要匹配特定模式的场景
3. **设置 quality**：控制候选词的排序，值越大越靠前
4. **错误处理**：使用 `pcall` 包装可能出错的代码
5. **性能优化**：避免在每次调用时进行重复计算，使用 `init` 函数初始化
6. **使用 `*module_name` 语法**：推荐使用 `lua_translator@*module_name`，不需要 `rime.lua` 和 `lua:` 映射
7. **合理使用返回值**：
   - Processor 中，已处理时返回 `1`（kAccepted），不处理时返回 `2`（kNoop）
   - 避免已处理但返回 `2`，或未处理但返回 `1` 的错误
8. **使用 `context:push_input()` 添加文本**：需要将文本添加到输入区域时，使用 `push_input()` 而不是 `commit_text()`
9. **使用 `env.log` 记录日志**：推荐使用 `env.log.info()`, `env.log.warning()`, `env.log.error()` 记录日志，会写入 Squirrel 日志文件
10. **调试时写入文件日志**：在开发阶段，可以同时写入文件日志（`/tmp/rime_ai.log`）方便调试

---

## 参考资料

### 官方文档
- [librime-lua Wiki - Scripting](https://github.com/hchunhui/librime-lua/wiki/Scripting) - 脚本开发指南
- [librime-lua Wiki - API](https://github.com/hchunhui/librime-lua/wiki/api) - 编程接口
- [librime-lua Wiki - Objects](https://github.com/hchunhui/librime-lua/wiki/Objects) - 对象接口
- [Rime 输入方案设计书](https://github.com/rime/home/wiki/RimeWithSchemata) - Rime 官方输入方案设计文档

### 社区资源
- [Rime Lua 插件文档](https://rimeinn.github.io/plugin/lua/)
- [rime-ice 文档](https://github.com/iDvel/rime-ice)
- [Rime 配置文档](https://github.com/rime/home/wiki)

### 项目相关
- 本地示例：`~/Library/Rime/lua/` 目录下的脚本
- 调试日志：`/tmp/rime_ai.log` 和 Squirrel 日志文件
