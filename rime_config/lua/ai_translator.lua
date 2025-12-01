-- ================================
-- AI Translator: 生成提示候选词
-- 功能：在输入为 @ai 或 ai: 时给出提示
-- ================================
local LOG_PATH = "/tmp/rime_ai.log"

local function log(kind, fmt, ...)
    local f = io.open(LOG_PATH, "a")
    if not f then return end
    local ok, msg = pcall(string.format, fmt, ...)
    if not ok then msg = fmt end
    f:write(string.format("[%s][%s] %s\n", os.date("%H:%M:%S"), kind, msg))
    f:close()
end

local ai_commands = {
    ["ai:"] = "🤖",
    ["chat:"] = "💬",
    ["tr:"] = "🌐",
}

local M = {}

-- 初始化
function M.init(env)
    -- 检查环境
    local config = env.engine.schema.config
    local schema = config:get_string("schema/name") or "unknown"
    log("TRANSLATOR", "initialized, schema: %s", schema)

    -- 检查 recognizer 配置
    local recognizer = config:get_map("recognizer")
    if recognizer then
        local patterns = recognizer:get_map("patterns")
        log("TRANSLATOR", "patterns: %s", tostring(patterns))
        if patterns then
            local ai_cmd_pattern = patterns:get_string("ai_cmd")
            log("TRANSLATOR", "recognizer.patterns.ai_cmd: %s",
                tostring(ai_cmd_pattern))
        else
            log("TRANSLATOR", "WARNING: recognizer.patterns not found")
        end
    else
        log("TRANSLATOR", "WARNING: recognizer not found in config")
    end
end

-- Translator 函数：生成候选词
-- 注意：translator 使用 M.func(input, seg, env)
function M.func(input, seg, env)
    -- 获取完整的输入上下文
    local context = env.engine.context
    local full_input = context.input or ""
    local cmd = ai_commands[full_input]

    -- 优先检查完整输入（因为 segmentor 可能把输入分成片段）
    if cmd then
        log("TRANSLATOR",
            "matched tag:%s, full_input='%s', segment_input='%s', seg=[%d,%d]",
            cmd, full_input, input, seg.start, seg._end)
        local cand = Candidate("ai", seg.start, seg._end, cmd, "输入问题后回车")
        cand.quality = 99999
        yield(cand)
        return
    end

    if input == "aitext" then
        local chunk = ""
        local TEXT = "台湾位于东亚、东海与南海之间，主岛（台湾岛）面积约3.6万平方公里，人口约2300万。"
        for i = 2, utf8.len(TEXT), 5 do
            local pos = utf8.offset(TEXT, i)
            chunk = TEXT:sub(1, pos-1)
            log("TRANSLATOR", "candidate:%s", chunk)
            local comment = (i < utf8.len(TEXT)+1) and '...' or '✅️'
            local cand = Candidate("ai", seg.start, seg._end, chunk, comment)
            cand.quality = i
            yield(cand)
            -- 延迟 0.1 秒
            os.execute("sleep 0.1")
        end
    end
end

return M

