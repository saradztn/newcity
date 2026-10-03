--[[
    main.lua - Client Lifecycle & Resource Entry Point
    Initializes the procedural world streaming, DX9 shaders, lighting,
    and handles graceful cleanup upon resource stop.
]]

addEventHandler("onClientResourceStart", resourceRoot, function()
    outputChatBox("==================================================", 100, 200, 255)
    outputChatBox("🌆 New American City Graphics Engine Loaded!", 255, 220, 100)
    outputChatBox("   Commands: /citytp, /cityweather [type], /cityquality [preset], /citydebug", 200, 220, 255)
    outputChatBox("==================================================", 100, 200, 255)

    -- Initialize systems in order
    Streaming.Init()
    Renderer.Init()
    Lighting.Init()
end)

addEventHandler("onClientResourceStop", resourceRoot, function()
    Streaming.Destroy()
end)
