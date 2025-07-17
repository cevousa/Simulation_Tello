-- Proximity Sensor Script for CoppeliaSim
-- Used with Quadcopter object and proximity sensor object

function sysCall_init()
    -- Try to get proximity sensor with different possible paths
    local success = false
    local possiblePaths = {
        '/Quadcopter/proximitySensor',
        'proximitySensor',
        '/proximitySensor'
    }
    
    for _, path in ipairs(possiblePaths) do
        local handle = nil
        pcall(function() 
            handle = sim.getObject(path)
        end)
        
        if handle then
            proximitySensor = handle
            success = true
            sim.addLog(sim.verbosity_infos, 'Found proximity sensor at: ' .. path)
            break
        end
    end
    
    if not success then
        sim.addLog(sim.verbosity_warnings, 'ERROR: Could not find proximity sensor!')
    end
    
    -- Initialize variables
    lastDistance = nil
    lastDetection = false
    detectionHistory = {}
    
    if success then
        sim.addLog(sim.verbosity_infos, "Proximity sensor script initialized successfully")
    else
        sim.addLog(sim.verbosity_errors, "Proximity sensor initialization FAILED!")
    end
end

function sysCall_sensing()
    -- Only proceed if we have a valid proximity sensor
    if not proximitySensor then
        return
    end
    
    -- Read data from proximity sensor (with error handling)
    local result, distance, detectedPoint, detectedObjectHandle, detectedSurfaceNormal
    
    local success, err = pcall(function()
        result, distance, detectedPoint, detectedObjectHandle, detectedSurfaceNormal = 
            sim.readProximitySensor(proximitySensor)
    end)
    
    if not success then
        sim.addLog(sim.verbosity_warnings, 'Error reading proximity sensor: ' .. tostring(err))
        return
    end
    
    if result > 0 then
        -- Detection successful
        lastDistance = distance
        lastDetection = true
        
        -- Store detection in history
        table.insert(detectionHistory, {
            time = sim.getSimulationTime(),
            distance = distance,
            point = detectedPoint,
            objectHandle = detectedObjectHandle
        })
        
        -- Limit history size
        if #detectionHistory > 100 then
            table.remove(detectionHistory, 1)
        end
        
        -- Set string signals with specific names to avoid conflicts
        sim.setStringSignal('proximity_distance', string.format("%.3f", distance))
        sim.setStringSignal('proximity_detected', 'true')
        
    else
        -- No detection
        lastDetection = false
        sim.setStringSignal('proximity_detected', 'false')
        -- Don't clear proximity_distance - this could cause issues
    end
end

function getProximityDistance()
    -- Function accessible from Python
    if lastDetection and lastDistance then
        return lastDistance
    else
        return -1  -- No detection
    end
end

function getProximityStatus()
    -- Return detailed status
    return {
        detected = lastDetection,
        distance = lastDistance or -1,
        historyCount = #detectionHistory
    }
end

function isGroundDetected(maxDistance)
    -- Detect if ground is within maxDistance
    maxDistance = maxDistance or 2.0
    
    if lastDetection and lastDistance then
        return lastDistance <= maxDistance
    end
    return false
end

function getAverageDistance(samples)
    -- Calculate average distance from recent samples
    samples = samples or 10
    
    if #detectionHistory < samples then
        samples = #detectionHistory
    end
    
    if samples == 0 then
        return -1
    end
    
    local sum = 0
    for i = #detectionHistory - samples + 1, #detectionHistory do
        sum = sum + detectionHistory[i].distance
    end
    
    return sum / samples
end

function sysCall_cleanup()
    -- Clean up proximity-specific signals only
    sim.clearStringSignal('proximity_distance')
    sim.clearStringSignal('proximity_detected')
end
