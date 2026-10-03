--[[
    puddle_system.lua - Dynamic Road Wetness Accumulation & Drying State Machine
    Simulates water pooling during rainfall and progressive evaporation drying after rain.
]]

PuddleSystem = {}

PuddleSystem.SurfaceWetness = 0.0  -- 0.0 (bone dry) to 1.0 (soaked)
PuddleSystem.PuddleDepth = 0.0     -- 0.0 (no puddles) to 1.0 (deep pools)

addEventHandler("onClientPreRender", root, function(dt)
    dt = dt / 1000.0 -- seconds

    local rain = Weather.RainIntensity

    if rain > 0.02 then
        -- 1. Rain Accumulation Phase
        -- Surface wetness rises rapidly
        PuddleSystem.SurfaceWetness = math.min(1.0, PuddleSystem.SurfaceWetness + dt * (rain * 0.12))
        -- Puddles pool progressively
        PuddleSystem.PuddleDepth = math.min(1.0, PuddleSystem.PuddleDepth + dt * (rain * 0.05))
    else
        -- 2. Post-Rain Dynamic Drying Phase
        -- Drying rate accelerates with sun intensity and elevation
        local sunDryingPower = math.max(0.1, Environment.SunColor[1] * math.max(0.0, math.sin(Environment.SunElevation)))
        local dryRate = 0.012 * sunDryingPower

        -- Asphalt surfaces dry first
        if PuddleSystem.SurfaceWetness > 0.0 then
            PuddleSystem.SurfaceWetness = math.max(0.0, PuddleSystem.SurfaceWetness - dt * dryRate)
        end

        -- Deep puddles evaporate more slowly
        if PuddleSystem.PuddleDepth > 0.0 then
            PuddleSystem.PuddleDepth = math.max(0.0, PuddleSystem.PuddleDepth - dt * (dryRate * 0.45))
        end
    end
end)
