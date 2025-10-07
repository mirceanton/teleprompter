# OBS Integration Testing Guide

This document provides comprehensive testing instructions for the OBS integration feature.

## Prerequisites

1. **OBS Studio** installed and running
2. **OBS WebSocket Server** enabled:
   - Open OBS Studio
   - Go to **Tools → WebSocket Server Settings**
   - Check **"Enable WebSocket server"**
   - Note the **Server Port** (default: 4455)
   - Optionally set a password
   - Click **Apply** and **OK**

3. **Teleprompter Application** running:
   - Backend on port 8001
   - Frontend on port 8000 (Docker) or 3000 (local dev)

## Test Scenarios

### 1. OBS Settings Configuration

#### Test Case 1.1: Access OBS Settings
1. Navigate to Controller mode
2. Click the **"OBS Settings"** button in the top navigation bar
3. **Expected**: OBS Settings page opens with configuration form

#### Test Case 1.2: Configure OBS Connection
1. In OBS Settings:
   - Enter OBS Host (e.g., `localhost` or `192.168.1.100`)
   - Enter OBS Port (default: `4455`)
   - Enter OBS Password (if configured in OBS)
   - Toggle **"Enable OBS Integration"** to ON
   - Set **"Start Delay"** (e.g., 3 seconds)
2. Click **"Test Connection"**
3. **Expected**: Success message appears
4. Click **"Save Settings"**
5. **Expected**: Settings saved confirmation
6. Navigate back to Controller

#### Test Case 1.3: Invalid Connection
1. In OBS Settings:
   - Enter incorrect host or port
   - Enable OBS Integration
2. Click **"Test Connection"**
3. **Expected**: Error message appears
4. **Expected**: Connection status shows "Failed"

### 2. OBS Status Display

#### Test Case 2.1: OBS Status in Controller
1. Configure and enable OBS integration
2. Navigate to Controller view
3. Scroll to **"OBS Recording"** section in the right sidebar
4. **Expected**: 
   - Shows connection status
   - Shows recording state (not recording)
   - Displays green indicator for connected status

#### Test Case 2.2: OBS Status Updates
1. With OBS integration enabled and connected
2. Manually start recording in OBS Studio
3. **Expected**: Controller view updates to show "Recording Active"
4. Stop recording in OBS Studio
5. **Expected**: Controller view updates to show "Ready to Record"

### 3. Automated Recording Control

#### Test Case 3.1: Start Recording with Teleprompter
1. Configure OBS integration with 0 second delay
2. Ensure OBS is NOT recording
3. In Controller, click the **Play** button (start teleprompter)
4. **Expected**: 
   - Teleprompter starts scrolling
   - OBS automatically starts recording
   - Recording indicator appears on teleprompter display
   - OBS status in controller shows "Recording Active"

#### Test Case 3.2: Start Recording with Delay
1. Configure OBS integration with 3 second delay
2. Ensure OBS is NOT recording
3. In Controller, click the **Play** button
4. **Expected**:
   - OBS starts recording immediately
   - After 3 seconds, teleprompter starts scrolling
   - Recording indicator appears on teleprompter display

#### Test Case 3.3: Stop Recording with Teleprompter
1. Start teleprompter (with OBS recording)
2. Click the **Pause** button
3. **Expected**:
   - Teleprompter stops scrolling
   - OBS recording stops
   - Recording indicator disappears from teleprompter display

#### Test Case 3.4: Stop Recording at End
1. Start teleprompter with a short script
2. Let the teleprompter scroll to the end
3. **Expected**:
   - Teleprompter auto-resets
   - OBS recording stops
   - Recording indicator disappears

### 4. Recording Indicator Display

#### Test Case 4.1: Indicator Appearance
1. Configure OBS integration and enable
2. Navigate to Teleprompter mode (on a separate device or browser tab)
3. Start teleprompter from Controller
4. **Expected**:
   - Recording indicator appears in top-right corner
   - Shows red circle icon with "REC" text
   - Icon pulses/animates

#### Test Case 4.2: Indicator Disappearance
1. With recording active and indicator visible
2. Stop teleprompter from Controller
3. **Expected**:
   - Recording indicator disappears
   - Happens immediately across all devices

#### Test Case 4.3: Indicator in Fullscreen
1. Start teleprompter with OBS recording
2. Click on teleprompter display to enter fullscreen
3. **Expected**:
   - Recording indicator remains visible in fullscreen
   - Positioned correctly in top-right corner

### 5. Multi-Device Synchronization

#### Test Case 5.1: Status Sync Across Devices
1. Open Controller on Device A (e.g., computer)
2. Open Teleprompter on Device B (e.g., phone)
3. Configure OBS in Controller on Device A
4. Start recording in Controller
5. **Expected**:
   - Recording indicator appears on Device B immediately
   - Both devices show synchronized recording status

#### Test Case 5.2: Multiple Teleprompters
1. Open Controller on Device A
2. Open Teleprompter on Device B and Device C
3. Start recording from Controller
4. **Expected**:
   - Recording indicator appears on both Device B and C
   - All teleprompters show synchronized status

### 6. Environment Variables Configuration

#### Test Case 6.1: Docker Compose Configuration
1. Edit `compose.yaml`:
   ```yaml
   environment:
     - OBS_HOST=192.168.1.100
     - OBS_PORT=4455
     - OBS_PASSWORD=mysecret
     - OBS_START_DELAY=3
   ```
2. Restart Docker Compose
3. Check backend logs for OBS connection status
4. **Expected**: Backend connects to OBS on startup

#### Test Case 6.2: Settings Override
1. Configure OBS via environment variables
2. Open OBS Settings in UI
3. Change host/port/password
4. Save settings
5. **Expected**: UI settings override environment variables

### 7. Error Handling

#### Test Case 7.1: OBS Not Running
1. Ensure OBS Studio is not running
2. Enable OBS integration in settings
3. Start teleprompter
4. **Expected**:
   - Connection fails gracefully
   - Teleprompter still works normally
   - Error logged in backend

#### Test Case 7.2: OBS Connection Lost
1. Start with OBS connected
2. Close OBS Studio while teleprompter is active
3. **Expected**:
   - Recording stops gracefully
   - Status updates to "Not connected"
   - Teleprompter continues to work

#### Test Case 7.3: Invalid Credentials
1. Configure OBS with wrong password
2. Try to connect
3. **Expected**:
   - Connection fails with authentication error
   - Clear error message shown to user

### 8. Performance Testing

#### Test Case 8.1: Recording Indicator Performance
1. Start teleprompter with OBS recording
2. Observe CPU/memory usage
3. Check for smooth animation
4. **Expected**: Minimal performance impact

#### Test Case 8.2: WebSocket Performance
1. Connect multiple devices
2. Start/stop recording multiple times
3. **Expected**: Quick response time (<500ms)

## Expected Behaviors

### When OBS Integration is Disabled
- No OBS-related UI elements visible
- Teleprompter works normally without OBS
- No OBS connection attempts

### When OBS Integration is Enabled but Not Connected
- OBS status shows "Not connected"
- Teleprompter works normally
- No recording control
- No recording indicator

### When OBS Integration is Enabled and Connected
- OBS status shows "Connected"
- Recording starts automatically with teleprompter
- Recording indicator visible during recording
- Recording stops with teleprompter

## Common Issues and Solutions

### Issue: "Failed to connect to OBS"
**Solutions**:
1. Verify OBS Studio is running
2. Check WebSocket Server is enabled in OBS
3. Verify correct host/port configuration
4. Check firewall settings
5. Ensure password matches (if set)

### Issue: Recording indicator not appearing
**Solutions**:
1. Refresh teleprompter page
2. Check WebSocket connection in browser console
3. Verify OBS integration is enabled
4. Check that recording actually started in OBS

### Issue: Recording doesn't stop automatically
**Solutions**:
1. Check OBS connection status
2. Verify WebSocket communication
3. Manually stop recording in OBS
4. Check backend logs for errors

### Issue: Delay not working correctly
**Solutions**:
1. Verify delay value is set correctly (0-60 seconds)
2. Check backend logs for delay execution
3. Test with different delay values
4. Ensure OBS starts recording before delay expires

## Testing Checklist

- [ ] OBS Settings page accessible
- [ ] Connection test works
- [ ] Settings save successfully
- [ ] OBS status displays in controller
- [ ] Recording starts automatically
- [ ] Recording starts with correct delay
- [ ] Recording stops with teleprompter
- [ ] Recording indicator appears on teleprompter
- [ ] Indicator disappears when recording stops
- [ ] Indicator visible in fullscreen mode
- [ ] Status syncs across all devices
- [ ] Environment variables configuration works
- [ ] Error handling works gracefully
- [ ] Performance is acceptable
- [ ] Works with disabled integration
- [ ] Works without OBS connection

## Notes

- OBS WebSocket protocol: v5.x (obs-websocket 5.0+)
- Python library: `obsws-python`
- Minimum OBS version: 28.0+ (includes WebSocket server)
- Network requirements: Backend must be able to reach OBS host on specified port
