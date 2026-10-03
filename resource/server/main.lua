--[[
    main.lua - Server-Side Lifecycle & Player Synchronization
    Provides teleportation commands to the new American city, global time/weather sync,
    and server administration commands.
]]

-- Downtown Grand Boulevard Spawn Coordinates
local CITY_SPAWN = {0.0, 10.0, 5.5}

addEventHandler("onResourceStart", resourceRoot, function()
    outputServerLog("[NewAmericanCity] Resource started successfully. Procedural metropolis ready.")
    -- Set default morning time and clear weather
    setTime(8, 0)
    setWeather(0)
    setMinuteDuration(1000) -- Smooth time passage
end)

-- Teleport command to spawn in the new city
addCommandHandler("citytp", function(player, cmd, targetPlayerName)
    local target = player
    if targetPlayerName and hasObjectPermissionTo(player, "command.kick", false) then
        target = getPlayerFromName(targetPlayerName) or player
    end

    if isElement(target) then
        setElementPosition(target, CITY_SPAWN[1], CITY_SPAWN[2], CITY_SPAWN[3])
        outputChatBox("[NewCity] Welcome to New American City! (Downtown Core)", target, 100, 220, 255)
    end
end)

-- Time change command
addCommandHandler("citytime", function(player, cmd, hourStr, minStr)
    local h = tonumber(hourStr)
    local m = tonumber(minStr) or 0
    if h and h >= 0 and h <= 23 then
        setTime(h, m)
        outputChatBox(string.format("[NewCity] Server time updated to %02d:%02d", h, m), root, 255, 220, 100)
    else
        outputChatBox("Usage: /citytime <0-23> [minute]", player, 255, 120, 120)
    end
end)
