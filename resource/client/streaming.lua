--[[
    streaming.lua - Dynamic Cell-Based Asset & Object Streaming Engine
    Loads DFF, LOD DFF, and COL files into allocated model IDs, creates world
    objects, links LOD elements via setLowLODElement, and manages distance culling.
]]

Streaming = {}

Streaming.LoadedModels = {}      -- model_name -> { id, lodId }
Streaming.SpawnedObjects = {}    -- list of { obj, lodObj, pos, model }
Streaming.IsLoaded = false

function Streaming.Init()
    outputDebugString("[NewCity Streaming] Loading city spatial database...")

    if not fileExists("data/city_layout.json") then
        outputDebugString("[NewCity Streaming] ERROR: city_layout.json not found!", 1)
        return false
    end

    local f = fileOpen("data/city_layout.json")
    local size = fileGetSize(f)
    local rawJson = fileRead(f, size)
    fileClose(f)

    local data = fromJSON(rawJson)
    if not data or not data.models or not data.instances then
        outputDebugString("[NewCity Streaming] ERROR: Failed to parse city_layout.json!", 1)
        return false
    end

    local lodMult = Config.CurrentPreset.lodDistanceMultiplier or 1.0

    -- 1. Load TXD Texture Dictionary
    if fileExists("textures/city_textures.txd") then
        local txd = engineLoadTXD("textures/city_textures.txd")
        if txd then
            outputDebugString("[NewCity Streaming] Loaded city_textures.txd dictionary.")
        end
    end

    -- 2. Allocate & Load Models and Collisions
    local fallbackBaseId = 1337
    for name, mInfo in pairs(data.models) do
        local modelId, lodModelId

        -- Request dynamic model IDs or use static fallback IDs
        if engineRequestModel then
            modelId = engineRequestModel("object")
            lodModelId = engineRequestModel("object")
        else
            modelId = fallbackBaseId
            fallbackBaseId = fallbackBaseId + 1
            lodModelId = fallbackBaseId
            fallbackBaseId = fallbackBaseId + 1
        end

        if modelId and lodModelId then
            -- Load Primary DFF
            if fileExists(mInfo.dff) then
                local dff = engineLoadDFF(mInfo.dff)
                if dff then
                    engineReplaceModel(dff, modelId)
                end
            end

            -- Load LOD DFF
            if fileExists(mInfo.lod_dff) then
                local lodDff = engineLoadDFF(mInfo.lod_dff)
                if lodDff then
                    engineReplaceModel(lodDff, lodModelId)
                end
            end

            -- Load Collision (COL)
            if fileExists(mInfo.col) then
                local col = engineLoadCOL(mInfo.col)
                if col then
                    engineReplaceCOL(col, modelId)
                end
            end

            -- Configure draw distances
            local nearDist = (mInfo.lod_distance or 200.0) * lodMult
            local farDist = (mInfo.far_lod_distance or 1500.0) * lodMult
            engineSetModelLODDistance(modelId, nearDist)
            engineSetModelLODDistance(lodModelId, farDist)

            Streaming.LoadedModels[name] = { id = modelId, lodId = lodModelId }
        end
    end

    -- 3. Spawn World Instances & Link LOD Elements
    outputDebugString("[NewCity Streaming] Spawning world instances and linking LODs...")
    for _, inst in ipairs(data.instances) do
        local mData = Streaming.LoadedModels[inst.model]
        if mData then
            local px, py, pz = inst.pos[1], inst.pos[2], inst.pos[3]
            local rx, ry, rz = inst.rot[1], inst.rot[2], inst.rot[3]

            -- High-detail primary object
            local obj = createObject(mData.id, px, py, pz, rx, ry, rz)
            -- Low-poly LOD counterpart (isLowLOD = true)
            local lodObj = createObject(mData.lodId, px, py, pz, rx, ry, rz, true)

            if obj and lodObj then
                -- Link LOD element
                setLowLODElement(obj, lodObj)

                if inst.scale and inst.scale ~= 1.0 then
                    setObjectScale(obj, inst.scale)
                    setObjectScale(lodObj, inst.scale)
                end

                table.insert(Streaming.SpawnedObjects, {
                    obj = obj,
                    lodObj = lodObj,
                    pos = {px, py, pz},
                    model = inst.model
                })
            end
        end
    end

    Streaming.IsLoaded = true
    outputDebugString(string.format("[NewCity Streaming] Successfully loaded %d models and spawned %d instances.",
        table.size(Streaming.LoadedModels), #Streaming.SpawnedObjects))
    return true
end

function Streaming.Destroy()
    for _, item in ipairs(Streaming.SpawnedObjects) do
        if isElement(item.obj) then destroyElement(item.obj) end
        if isElement(item.lodObj) then destroyElement(item.lodObj) end
    end
    Streaming.SpawnedObjects = {}
    Streaming.LoadedModels = {}
    Streaming.IsLoaded = false
end

function table.size(t)
    local c = 0
    for _ in pairs(t) do c = c + 1 end
    return c
end
