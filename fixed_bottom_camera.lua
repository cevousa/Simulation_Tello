-- VisionSensor child script: save images & signal to Python
-- FIXED VERSION - Works with proximity sensor
local sensor, folder, counter = nil, nil, 0

function sysCall_init()
    -- 1) Get handle for Vision Sensor
    sensor = sim.getObjectHandle('/Quadcopter/bottomcamera')
    if sim.getObjectType(sensor) ~= sim.sceneobject_visionsensor then
        sim.addLog(sim.verbosity_warnings, '[VS] ERROR: Not a vision sensor')
        return
    end

    -- 2) Enable Vision Sensor
    sim.setBoolParam(sim.boolparam_vision_sensor_handling_enabled, true)
    sim.setBoolParam(sim.boolparam_display_enabled, true)

    -- 3) Get scene path using getStringProperty
    local scenePath = sim.getStringProperty(sim.handle_scene, 'scenePath')
    sim.addLog(sim.verbosity_infos, '[VS] Scene path: ' .. scenePath)
    
    folder = 'D:/pythonforcoppelia/captured_images/'
    sim.addLog(sim.verbosity_infos, '[VS] Target folder: ' .. folder)

    -- 4) Create folder if it doesn't exist
    if package.config:sub(1,1)=='\\' then
        os.execute('mkdir "' .. folder:gsub('/','\\') .. '" 2>nul')
    else
        os.execute('mkdir -p "' .. folder .. '"')
    end
    
    -- Test if folder is writable
    local testFile = folder .. 'test.txt'
    local f = io.open(testFile, 'w')
    if f then
        f:write('test')
        f:close()
        os.remove(testFile)
        sim.addLog(sim.verbosity_infos, '[VS] Folder writable: ' .. folder)
    else
        sim.addLog(sim.verbosity_errors, '[VS] Cannot write to: ' .. folder)
    end
end

local function captureImage()
    sim.addLog(sim.verbosity_infos, '[VS] Starting capture...')
    
    -- Handle Vision Sensor (explicit handling)
    sim.handleVisionSensor(sensor)
    
    -- Get image data
    local img, res = sim.getVisionSensorImg(sensor)
    if not img then 
        sim.addLog(sim.verbosity_warnings, '[VS] getVisionSensorImg returned nil')
        return 
    end
    
    sim.addLog(sim.verbosity_infos, '[VS] Image size: ' .. res[1] .. 'x' .. res[2])
    
    -- Generate unique filename
    local name = string.format('image_%s_%04d.png', os.date('%Y%m%d_%H%M%S'), counter)
    local fullPath = folder .. name
    
    sim.addLog(sim.verbosity_infos, '[VS] Saving to: ' .. fullPath)
    
    -- Save image (with quality set to 100)
    local ok = sim.saveImage(img, res, 0, fullPath, 100)
    if ok then
        counter = counter + 1
        -- Use a more specific signal name to avoid conflict with proximity sensor
        sim.setStringSignal('bottom_camera_image_saved', name)
        sim.addLog(sim.verbosity_infos, '[VS] Successfully saved: ' .. name)
    else
        sim.addLog(sim.verbosity_errors, '[VS] saveImage failed for: ' .. name)
    end
end

function sysCall_actuation()
    -- Use direct command comparison instead of clearing signals
    local cmd = sim.getStringSignal('capture_bottom_image')
    if cmd and cmd == '1' then
        -- Don't clear the signal until after capture is complete
        captureImage()
        sim.clearStringSignal('capture_bottom_image')
    end
end

function sysCall_cleanup()
    -- Make sure we clean up our specific signals
    sim.clearStringSignal('bottom_camera_image_saved')
end
