--[[
    weather.lua - Dynamic Weather Director & Atmospheric State Machine
    CLEAR, PARTLY_CLOUDY, OVERCAST, LIGHT_RAIN, HEAVY_RAIN, STORM, FOG, MIST, POST_RAIN.
    Handles cloud coverage, rain accumulation, drying cycle, and rare lightning events.
]]

Weather = {}

Weather.States = {
    CLEAR         = { id = "CLEAR",         clouds = 0.05, rain = 0.0, fog = 950.0, sunMult = 1.0,  mtaId = 0 },
    PARTLY_CLOUDY = { id = "PARTLY_CLOUDY", clouds = 0.40, rain = 0.0, fog = 850.0, sunMult = 0.95, mtaId = 1 },
    OVERCAST      = { id = "OVERCAST",      clouds = 0.85, rain = 0.0, fog = 650.0, sunMult = 0.55, mtaId = 4 },
    LIGHT_RAIN    = { id = "LIGHT_RAIN",    clouds = 0.90, rain = 0.35,fog = 500.0, sunMult = 0.40, mtaId = 8 },
    HEAVY_RAIN    = { id = "HEAVY_RAIN",    clouds = 0.95, rain = 0.75,fog = 350.0, sunMult = 0.25, mtaId = 8 },
    STORM         = { id = "STORM",         clouds = 1.00, rain = 1.00,fog = 220.0, sunMult = 0.15, mtaId = 8 },
    FOG           = { id = "FOG",           clouds = 0.70, rain = 0.0, fog = 120.0, sunMult = 0.30, mtaId = 9 },
    MIST          = { id = "MIST",          clouds = 0.50, rain = 0.0, fog = 320.0, sunMult = 0.60, mtaId = 9 },
    POST_RAIN     = { id = "POST_RAIN",     clouds = 0.30, rain = 0.0, fog = 750.0, sunMult = 0.90, mtaId = 1 },
    HOT_CLEAR     = { id = "HOT_CLEAR",     clouds = 0.00, rain = 0.0, fog = 1100.0,sunMult = 1.10, mtaId = 11},
    COLD_CLOUDY   = { id = "COLD_CLOUDY",   clouds = 0.80, rain = 0.0, fog = 600.0, sunMult = 0.65, mtaId = 7 },
}

Weather.Current = Weather.States.CLEAR
Weather.Target = Weather.States.CLEAR
Weather.Blend = 1.0

-- Dynamic environmental metrics
Weather.CloudCoverage = 0.05
Weather.RainIntensity = 0.0
Weather.AtmosphericHaze = 0.0
Weather.LastLightningTime = 0

function Weather.SetState(stateKey)
    local upper = string.upper(stateKey)
    if Weather.States[upper] then
        Weather.Target = Weather.States[upper]
        Weather.Blend = 0.0
        setWeather(Weather.Target.mtaId)
        outputChatBox("[NewCity Weather] Transitioning to: " .. upper, 150, 230, 255)
        return true
    end
    return false
end

-- Update every frame
addEventHandler("onClientPreRender", root, function(dt)
    dt = dt / 1000.0 -- seconds

    -- Smooth state transition over 6 seconds
    if Weather.Blend < 1.0 then
        Weather.Blend = math.min(1.0, Weather.Blend + dt * 0.16)
    end

    -- Blend metrics
    local c0 = Weather.Current.clouds
    local c1 = Weather.Target.clouds
    Weather.CloudCoverage = c0 + (c1 - c0) * Weather.Blend

    local r0 = Weather.Current.rain
    local r1 = Weather.Target.rain
    Weather.RainIntensity = r0 + (r1 - r0) * Weather.Blend

    -- Rare Lightning Event during Storms
    if Weather.Target.id == "STORM" and math.random() < 0.002 then
        local now = getTickCount()
        if now - Weather.LastLightningTime > 8000 then
            Weather.LastLightningTime = now
            -- Momentary bright flash
            setSkyGradient(255, 255, 255, 255, 255, 255)
            setTimer(function()
                -- Restore sky
                Environment.Update()
                -- Distant thunder sound effect
                playSoundFrontEnd(43)
            end, 120, 1)
        end
    end

    if Weather.Blend >= 1.0 then
        Weather.Current = Weather.Target
    end
end)

addCommandHandler("cityweather", function(cmd, stateName)
    if stateName then
        if not Weather.SetState(stateName) then
            outputChatBox("Invalid weather. Available: clear, partly_cloudy, overcast, light_rain, heavy_rain, storm, fog, post_rain", 255, 120, 120)
        end
    else
        outputChatBox("[NewCity Weather] Current: " .. Weather.Current.id, 255, 220, 100)
    end
end)
