--[[
    debug_ui.lua - In-Game Telemetry HUD & Graphics Debug Monitor
    Displays real-time time-of-day, sun angles, atmospheric metrics,
    surface wetness %, puddle %, FPS, and active object statistics.
    Toggle via F7 or /citydebug.
]]

DebugUI = {}
DebugUI.Visible = true

local fpsCount = 0
local currentFPS = 60
local lastFpsUpdate = getTickCount()

addEventHandler("onClientRender", root, function()
    -- Calculate real FPS
    fpsCount = fpsCount + 1
    local now = getTickCount()
    if now - lastFpsUpdate >= 1000 then
        currentFPS = fpsCount
        fpsCount = 0
        lastFpsUpdate = now
    end

    if not DebugUI.Visible then return end

    local x = 20
    local y = 20
    local w = 340
    local h = 210

    -- Background panel
    dxDrawRectangle(x, y, w, h, tocolor(15, 20, 28, 210))
    dxDrawRectangle(x, y, w, 28, tocolor(25, 40, 60, 240))
    dxDrawRectangle(x, y + 27, w, 2, tocolor(80, 180, 255, 255))

    -- Header Title
    dxDrawText("NEW AMERICAN CITY — ENGINE HUD", x + 12, y + 6, x + w, y + 26,
        tocolor(255, 255, 255, 255), 1.0, "default-bold")

    -- Content Metrics
    local h_int, m_int = getTime()
    local timeStr = string.format("%02d:%02d", h_int, m_int)
    local sunElevDeg = math.floor(math.deg(Environment.SunElevation))
    local sunAzDeg = math.floor(math.deg(Environment.SunAzimuth))
    local wetnessPct = math.floor(PuddleSystem.SurfaceWetness * 100)
    local puddlePct = math.floor(PuddleSystem.PuddleDepth * 100)
    local cloudPct = math.floor(Weather.CloudCoverage * 100)

    local lines = {
        string.format("Time of Day:       %s  (Sun Elev: %d°, Az: %d°)", timeStr, sunElevDeg, sunAzDeg),
        string.format("Weather State:     %s", Weather.Current.id),
        string.format("Cloud Coverage:    %d%%", cloudPct),
        string.format("Surface Wetness:   %d%%  (Puddles: %d%%)", wetnessPct, puddlePct),
        string.format("Quality Preset:    %s", Config.CurrentPreset.name),
        string.format("Spawned Objects:   %d  (FPS: %d)", #Streaming.SpawnedObjects, currentFPS),
        "Press F7 or /citydebug to toggle HUD",
    }

    local curY = y + 36
    for i, line in ipairs(lines) do
        local col = (i == #lines) and tocolor(150, 160, 180, 200) or tocolor(220, 230, 245, 255)
        dxDrawText(line, x + 12, curY, x + w - 12, curY + 20, col, 1.0, "default")
        curY = curY + 22
    end
end)

bindKey("F7", "down", function()
    DebugUI.Visible = not DebugUI.Visible
end)

addCommandHandler("citydebug", function()
    DebugUI.Visible = not DebugUI.Visible
    outputChatBox("[NewCity] Debug HUD: " .. (DebugUI.Visible and "ON" or "OFF"), 180, 220, 255)
end)
