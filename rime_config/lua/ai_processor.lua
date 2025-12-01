-- ================================
-- AI Processor: 处理按键事件
-- 功能：
-- 1. 空格键：在 AI 命令输入中追加空格，不上屏
-- 2. 回车键：调用 AI，上屏结果
-- ================================

local placeholder = "AI:"
local LOG_PATH = "/tmp/rime_ai.log"
local MAX_LOG_SIZE = 5 * 1024 * 1024  -- 5MB，超过此大小则轮转
local last_size_check = 0  -- 上次检查的文件大小

local function log(kind, fmt, ...)
    local ok, msg = pcall(string.format, fmt, ...)
    if not ok then msg = fmt end
    local log_msg = string.format("[%s][%s] %s", os.date("%H:%M:%S"), kind, msg)
    
    -- 检查日志文件大小（每 1000 次写入或文件可能超过限制时检查）
    -- 使用简单的计数器避免每次都检查文件大小
    local check_size = false
    if last_size_check == 0 or last_size_check > 1000 then
        check_size = true
        last_size_check = 0
    else
        last_size_check = last_size_check + 1
    end
    
    if check_size then
        local f = io.open(LOG_PATH, "r")
        if f then
            local size = f:seek("end")
            f:close()
            if size and size > MAX_LOG_SIZE then
                -- 轮转日志：直接删除旧日志，新文件从头开始
                os.execute(string.format('rm "%s" 2>/dev/null', LOG_PATH))
            end
        end
    end
    
    -- 写入文件日志
    local f = io.open(LOG_PATH, "a")
    if f then
        f:write(log_msg .. "\n")
        f:close()
    end
end

local ai_commands = {
    ["ai:"] = "ai",
    ["chat:"] = "chat",
    ["tr:"] = "translate",
}

local M = {}

-- 初始化
function M.init(env) 
    -- local success, data = pcall(require, "module")
    -- if not success then
    --     env.log.warning("Failed to load module: " .. data)
    --     data = {}
    -- end
    log("PROCESSOR", "initialized") 
end

-- Processor 函数：处理按键事件
function M.func(key, env)
    local context = env.engine.context
    local key_repr = key:repr()
    local char_code = key.keycode
    local input = context.input or ""
    local char = nil
    if char_code >= 32 and char_code <= 126 then
        char = string.char(char_code)
    else char = key_repr end
    -- 记录每次调用（详细日志）
    log("PROCESSOR", "key:'%s', key_repr='%s', key_code=%d, input='%s', is_composing=%s, has_menu=%s",
        char, key_repr, char_code, input, tostring(context:is_composing()), tostring(context:has_menu()))

    -- 不在输入状态时不处理
    if not context:is_composing() then return 2 end

    -- 只关心以 cmd: 开头的输入
    local cmd_str, query = input:match("^(.+:)(.+)$")
    cmd = ai_commands[cmd_str]
    if not cmd then return 2 end

    -- Escape 键：清空输入
    if key_repr == "Escape" then
        -- context:clear()
        return 2
    end

    
    -- 回车：直接调用 AI，提交结果（优先处理，不受候选词面板影响）
    if key_repr == "Return" or key_repr == "Enter" then

        log("PROCESSOR", "Enter on AI cmd:'%s', query='%s'", cmd, tostring(query))

        if not cmd or not query or query == "" then
            -- 没有内容，交给默认处理
            log("PROCESSOR", "no query, returning 2")
            return 2
        end

        -- 仅作为 AI 触发器：不再由 Rime 输出任何流式文本
        context:clear()
        env.engine:commit_text(placeholder)

        local home = os.getenv("HOME") or ""
        local streamer_path = home .. "/Library/Rime/ai_streamer.py"
        
        -- 检查文件是否存在
        local file = io.open(streamer_path, "r")
        if not file then
            log("PROCESSOR", "ERROR: streamer file not found: %s", streamer_path)
            return 1
        end
        file:close()

        -- 使用系统默认的 python3，脚本会自动安装依赖
        -- 脚本会使用 sys.executable 来安装依赖，确保使用正确的 Python 环境
        local python3_cmd = "python3"
        
        -- 将错误输出到日志文件，方便调试
        local error_log = "/tmp/ai_streamer_error.log"
        local cmd_str = string.format(
            '%s "%s" "%s" "%s" >>"%s" 2>&1 &',
            python3_cmd, streamer_path, cmd, query, error_log
        )

        log("PROCESSOR", "spawn streamer: %s", cmd_str)
        local result = os.execute(cmd_str)
        log("PROCESSOR", "os.execute returned: %s", tostring(result))

        return 1
    end

    -- 检查是否有候选词面板
    local has_menu = context:has_menu()

    -- 如果有候选词面板，对 space 和 digit 进行特殊处理
    if has_menu then
        -- 处理空格键和数字键：选择候选词但不立即上屏
        local current_candidate = nil
        local candidate_index = nil
        local digit = key_repr:match("^([1-9])$")
        -- 获取候选词
        local composition = context.composition
        local segmentation = composition:toSegmentation()
        
        if key_repr == "space" then
            -- 空格键：获取当前选中的候选词
            current_candidate = context:get_selected_candidate()
        elseif digit then
            -- 数字键：选择对应位置的候选词
            candidate_index = tonumber(digit) - 1 -- 转换为 0-based index
            if not composition:empty() then
                local segment = composition:back()
                local menu = segment.menu
                local candidate_count = menu:candidate_count()
                
                if candidate_index >= 0 and candidate_index < candidate_count then
                    current_candidate = menu:get_candidate_at(candidate_index)
                    log("PROCESSOR", "digit %s: selected candidate %d='%s'", digit, candidate_index, current_candidate.text)
                end
            end
        end
        
        if current_candidate then
            -- 获取前缀和 segment_length
            local prefix = ""
            local segment_length = 0
            
            if not composition:empty() then
                local segment = composition:back()
                -- 计算 Segment 的长度（原始拼音输入的长度）
                segment_length = segment._end - segment.start
                log("PROCESSOR", "segment_length=%d (from segment [%d,%d])", segment_length, segment.start, segment._end)
                -- 移除包含原始拼音输入的 Segment
                -- composition:pop_back()
                -- log("PROCESSOR", "popped back segment")
            else
                -- 如果无法获取 Segment，尝试从输入中提取前缀
                prefix = input:match("^(ai:)") or input:match("^(@ai%s+)") or ""
                -- 估算 Segment 长度（输入长度减去前缀长度）
                segment_length = #input - #prefix
                log("PROCESSOR", "prefix='%s' (extracted from input), segment_length=%d", prefix, segment_length)
            end
            
            -- 尝试使用 pop_input 移除原始拼音输入（从光标位置向左删除 segment_length 个字符）
            if segment_length > 0 then
                context:pop_input(segment_length)
                log("PROCESSOR", "popped %d characters from input", segment_length)
            end
            
            -- 推入候选词文本
            context:push_input(current_candidate.text)
            log("PROCESSOR", "pushed candidate='%s' (index %d)", current_candidate.text, candidate_index)
            segmentation:forward() -- 新增一个 Segment，防止候选词再出来
            return 1 -- ✅ 已处理，阻止默认行为（默认行为会上屏并终止 compose）
        end
        
        -- 检查是否是普通字符（ASCII 可打印字符）
        local char_code = key.keycode
        if char_code >= 32 and char_code <= 126 then
            context:push_input(char)
            log("PROCESSOR", "pushed '%s' -> '%s'", char, context.input)
            return 1 -- 已处理，阻止默认行为
        end

        -- 其他特殊按键，交给默认处理
        return 2
    end

    -- 其他输入都 push_input
    -- 检查是否是普通字符（ASCII 可打印字符）
    -- 0-31：控制字符（不可打印）
    -- 32：空格（Space）
    -- 33-125：可打印字符
    -- 33-47：标点符号 ! " # $ % & ' ( ) * + , - . /
    -- 48-57：数字 0-9
    -- 58-64：标点符号 : ; < = > ? @
    -- 65-90：大写字母 A-Z
    -- 91-96：标点符号 [ \ ] ^ _ 
    -- 97-122：小写字母 a-z 
    -- 123-125：标点符号 { | } 
    -- 123-125：标点符号 { | } 
    -- 126：波浪号 ~ 
    -- 127+：扩展字符 
    if char_code >= 32 and char_code <= 126 then
        context:push_input(char)
        log("PROCESSOR", "pushed '%s'->'%s'", char, context.input)
        return 1 -- 已处理，阻止默认行为
    end

    -- 退格键
    if key_repr == "BackSpace" then
        chat_len = #context.input - utf8.offset(context.input, -1) + 1
        context:pop_input(chat_len)
        log("PROCESSOR", "popped %d characters from input", chat_len)
        return 1 -- 已处理，阻止默认行为
    end

    return 2
end

return M
