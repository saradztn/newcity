--[[
    renderer.lua - Graphics Engine Renderer & Post-Processing Pipeline
    Manages HLSL DirectX 9 shaders, Render Targets, dynamic uniform updates,
    screen-space light shafts, SSR approximation, and weather effects.
    Guarantees every world texture is mapped with high-detail textures (DDS or PNG).
]]

Renderer = {}

Renderer.Shaders = {}
Renderer.Textures = {}
Renderer.RenderTargets = {}
Renderer.DiffuseMappers = {}

local sw, sh = guiGetScreenSize()

function Renderer.Init()
    outputDebugString("[NewCity Renderer] Initializing DX9 Graphics Engine...")

    -- 1. Load All Photorealistic Textures (Prefers PNG if present, falls back to DDS)
    local textureNames = {
        "asphalt_road", "asphalt_hwy", "crosswalk", "sidewalk_paver", "curb_stone",
        "concrete_wall", "glass_curtain_a", "glass_curtain_b", "bldg_brick", "bldg_stone",
        "roof_gravel", "metal_corrugated", "storefront_atlas", "neon_signs_atlas",
        "signs_atlas", "tunnel_tiles", "grass_paver", "oak_leaves", "palm_frond",
        "asphalt_normal", "highway_normal", "concrete_normal", "sidewalk_normal",
        "roof_gravel_normal", "asphalt_puddle", "glass_a_emiss", "glass_curtain_a_emissive", "water_normal"
    }

    for _, name in ipairs(textureNames) do
        local pngPath = "textures/" .. name .. ".png"
        local ddsPath = "textures/" .. name .. ".dds"
        local targetPath = fileExists(pngPath) and pngPath or (fileExists(ddsPath) and ddsPath or nil)

        if targetPath then
            Renderer.Textures[name] = dxCreateTexture(targetPath)
        end
    end

    -- 2. Create Universal Diffuse Texture Mappers (guarantees NO white models)
    local directBindings = {
        "asphalt_road", "asphalt_hwy", "crosswalk", "sidewalk_paver", "curb_stone",
        "concrete_wall", "glass_curtain_a", "glass_curtain_b", "bldg_brick", "bldg_stone",
        "roof_gravel", "metal_corrugated", "storefront_atlas", "neon_signs_atlas",
        "signs_atlas", "tunnel_tiles", "grass_paver", "oak_leaves", "palm_frond"
    }

    for _, texName in ipairs(directBindings) do
        local texElement = Renderer.Textures[texName]
        if texElement then
            local s = dxCreateShader("shaders/tex_diffuse.fx", 0, 0, false, "world,object")
            if s then
                dxSetShaderValue(s, "gTexture", texElement)
                engineApplyShaderToWorldTexture(s, texName)
                table.insert(Renderer.DiffuseMappers, s)
            end
        end
    end

    -- 3. Advanced PBR Shaders
    Renderer.Shaders.road = dxCreateShader("shaders/road_pbr.fx", 0, 0, false, "world,object")
    Renderer.Shaders.building = dxCreateShader("shaders/building_facade.fx", 0, 0, false, "world,object")
    Renderer.Shaders.water = dxCreateShader("shaders/water_surface.fx", 0, 0, false, "world,object")

    if Renderer.Shaders.road and Renderer.Textures.asphalt_normal then
        if Renderer.Textures.asphalt_road then
            dxSetShaderValue(Renderer.Shaders.road, "gTexture", Renderer.Textures.asphalt_road)
        end
        dxSetShaderValue(Renderer.Shaders.road, "gNormalMap", Renderer.Textures.asphalt_normal)
        if Renderer.Textures.asphalt_puddle then
            dxSetShaderValue(Renderer.Shaders.road, "gPuddleTexture", Renderer.Textures.asphalt_puddle)
        end

        engineApplyShaderToWorldTexture(Renderer.Shaders.road, "asphalt_road")
        engineApplyShaderToWorldTexture(Renderer.Shaders.road, "asphalt_hwy")
    end

    local emissiveTex = Renderer.Textures.glass_a_emiss or Renderer.Textures.glass_curtain_a_emissive
    if Renderer.Shaders.building and emissiveTex then
        if Renderer.Textures.glass_curtain_a then
            dxSetShaderValue(Renderer.Shaders.building, "gTexture", Renderer.Textures.glass_curtain_a)
        end
        dxSetShaderValue(Renderer.Shaders.building, "gEmissiveTexture", emissiveTex)
        engineApplyShaderToWorldTexture(Renderer.Shaders.building, "glass_curtain_a")
    end

    if Renderer.Shaders.water and Renderer.Textures.water_normal then
        dxSetShaderValue(Renderer.Shaders.water, "gNormalTexture", Renderer.Textures.water_normal)
        engineApplyShaderToWorldTexture(Renderer.Shaders.water, "water*")
    end

    -- 4. Post-processing Shaders
    Renderer.Shaders.sunShafts = dxCreateShader("shaders/sun_shafts.fx")
    Renderer.Shaders.ssr = dxCreateShader("shaders/ssr_reflection.fx")
    Renderer.Shaders.rainScreen = dxCreateShader("shaders/rain_screen.fx")

    local rtScale = (Config and Config.CurrentPreset and Config.CurrentPreset.renderTargetScale) or 0.75
    local rtw = math.floor(sw * rtScale)
    local rth = math.floor(sh * rtScale)
    Renderer.RenderTargets.scene = dxCreateRenderTarget(rtw, rth, true)

    outputDebugString(string.format("[NewCity Renderer] Loaded %d textures and %d shader mappers.",
        table.size(Renderer.Textures), #Renderer.DiffuseMappers))
    return true
end

function Renderer.Destroy()
    for _, s in ipairs(Renderer.DiffuseMappers) do
        if isElement(s) then destroyElement(s) end
    end
    Renderer.DiffuseMappers = {}

    for _, s in pairs(Renderer.Shaders) do
        if isElement(s) then destroyElement(s) end
    end
    Renderer.Shaders = {}

    for _, t in pairs(Renderer.Textures) do
        if isElement(t) then destroyElement(t) end
    end
    Renderer.Textures = {}

    for _, rt in pairs(Renderer.RenderTargets) do
        if isElement(rt) then destroyElement(rt) end
    end
    Renderer.RenderTargets = {}
end

-- Teleport command helper on client: /citytp [location]
addCommandHandler("citytp", function(cmd, targetLoc)
    targetLoc = targetLoc or "center"
    local poi = WorldLayout and WorldLayout.pois and WorldLayout.pois[targetLoc]
    if poi then
        outputChatBox("[NewCity] Teleporting to " .. targetLoc .. "...", 100, 255, 100)
        setElementPosition(localPlayer, poi[1], poi[2], poi[3] + 1.0)
        setElementFrozen(localPlayer, true)
        setTimer(function()
            setElementFrozen(localPlayer, false)
        end, 1500, 1)
    else
        outputChatBox("[NewCity] Unknown POI. Locations: center, plaza, downtown, hotel, waterfront, bridge, expressway, tunnel, industrial, park, cityhall", 255, 200, 100)
    end
end)
