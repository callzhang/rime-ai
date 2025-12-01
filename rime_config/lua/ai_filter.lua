-- =========================================
-- AI Type Filter
-- 只保留 type == "ai_test" 的候选
-- =========================================

local TARGET_TYPE = "ai"
local M = {}
local LOG_PATH = "/tmp/rime_ai.log"
local function log(kind, fmt, ...)
    local f = io.open(LOG_PATH, "a")
    if not f then return end
    local ok, msg = pcall(string.format, fmt, ...)
    if not ok then msg = fmt end
    f:write(string.format("[%s][%s] %s\n", os.date("%H:%M:%S"), kind, msg))
    f:close()
end

function M.init(env)
    log("AI_FILTER", "initialized")
end

function M.func(input, env)
    local max_ai_len = 0
    local max_len_cand = nil
    local other_cands = {}
    for cand in input:iter() do
        -- cand.type 可能不存在，用 get_genuine 更稳
        -- local g = cand:get_genuine()
        local ctype = cand.type
        if ctype == TARGET_TYPE then
            -- AI 候选，找出最长的那个
            ai_text = cand.text
            log("AI_FILTER", "type: %s, max_ai_len: %s", ctype, max_ai_len)
            if #ai_text > max_ai_len then
                max_ai_len = #ai_text
                max_len_cand = cand
            end
        else
            table.insert(other_cands, cand)
        end
    end
    -- 如果找到了最长的 AI 候选，则 yield
    if max_len_cand then
        log("AI_FILTER", "yield max_len_cand: %s", max_len_cand.text)
        yield(max_len_cand)
    end
    -- yield regular candidates
    for _, cand in ipairs(other_cands) do
        yield(cand)
    end
end

return M