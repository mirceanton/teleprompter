# Manual Testing Guide

## Testing the Admin UI Play State Fix

This document describes how to manually test the fix for the admin UI play state synchronization issue.

### Issue Description
When API endpoints are called to control playback (start/stop/rewind/fast-forward), the Controller (admin UI) should update its internal play state and change the play/pause button accordingly.

### Prerequisites
- Docker and Docker Compose installed
- Two browser tabs/windows or two different devices on the same network

### Test Setup

1. **Start the application with Docker Compose:**
   ```bash
   docker compose -f compose.yaml -f compose.dev.yaml up --build
   ```

2. **Access the application:**
   - Frontend: http://localhost:8000
   - Backend API: http://localhost:8001

3. **Open two browser sessions:**
   - **Session 1 (Controller)**: Navigate to http://localhost:8000 and click "Controller" mode
   - **Session 2 (Teleprompter)**: Navigate to http://localhost:8000 and click "Teleprompter" mode
   - Ensure both sessions are viewing the same content

### Test Cases

#### Test Case 1: API Start Command Updates Admin UI
1. Verify the Controller UI shows a **Play** button (not Pause)
2. Use curl or browser to call the start API:
   ```bash
   curl -X POST http://localhost:8001/api/playback/start
   ```
3. **Expected Result**: 
   - Controller UI button changes to **Pause** (red color)
   - Teleprompter starts scrolling
   - Admin UI `isPlaying` state is now `true`

#### Test Case 2: API Stop Command Updates Admin UI
1. Start playback using the Controller UI play button
2. Verify the Controller UI shows a **Pause** button (red)
3. Use curl to call the stop API:
   ```bash
   curl -X POST http://localhost:8001/api/playback/stop
   ```
4. **Expected Result**: 
   - Controller UI button changes to **Play** (green color)
   - Teleprompter stops scrolling
   - Admin UI `isPlaying` state is now `false`

#### Test Case 3: API Scroll to Beginning Updates Admin UI
1. Start playback using the API or UI
2. Wait a few seconds for scrolling
3. Call the scroll to beginning API:
   ```bash
   curl -X POST http://localhost:8001/api/playback/scroll/top
   ```
4. **Expected Result**:
   - Controller UI button changes to **Play** (green color)
   - Teleprompter scrolls to the top and stops
   - Admin UI `isPlaying` state is now `false`
   - Admin UI `currentScrollPosition` is reset to 0

#### Test Case 4: API Scroll to End Updates Admin UI
1. Start playback using the API or UI
2. Call the scroll to end API:
   ```bash
   curl -X POST http://localhost:8001/api/playback/scroll/bottom
   ```
3. **Expected Result**:
   - Controller UI button changes to **Play** (green color)
   - Teleprompter scrolls to the end and stops
   - Admin UI `isPlaying` state is now `false`

#### Test Case 5: Multiple API Calls in Sequence
1. Call start API → verify Controller shows Pause button
2. Call stop API → verify Controller shows Play button
3. Call start API again → verify Controller shows Pause button
4. Call scroll to top API → verify Controller shows Play button
5. **Expected Result**: Each API call correctly updates the Controller UI state

#### Test Case 6: API Calls While Using Controller UI
1. Click Play button in Controller UI (should show Pause button)
2. Call stop API via curl
3. **Expected Result**: Controller UI updates to show Play button
4. Click Play in Controller UI again
5. Call scroll to beginning API
6. **Expected Result**: Controller UI updates to show Play button

### Verification Points

For each test case, verify:
- ✅ The play/pause button icon changes correctly (Play ↔ Pause)
- ✅ The button color changes correctly (Green for Play, Red for Pause)
- ✅ The Teleprompter display responds to the commands
- ✅ The WebSocket communication is working (check browser console for messages)
- ✅ No JavaScript errors in the browser console

### Additional API Endpoints to Test

The fix also works with these alternate API endpoints:

**Scroll to Beginning:**
- `/api/playback/scroll/top`
- `/api/playback/scroll/start`
- `/api/playback/scroll/beginning`

**Scroll to End:**
- `/api/playback/scroll/bottom`
- `/api/playback/scroll/end`
- `/api/playback/scroll/finish`

### Expected Behavior Summary

| API Endpoint | Controller `isPlaying` | Button Display | Teleprompter Action |
|--------------|----------------------|----------------|-------------------|
| `/api/playback/start` | `true` | Pause (Red) | Starts scrolling |
| `/api/playback/stop` | `false` | Play (Green) | Stops scrolling |
| `/api/playback/scroll/top` | `false` | Play (Green) | Scrolls to top & stops |
| `/api/playback/scroll/bottom` | `false` | Play (Green) | Scrolls to end & stops |

### Debugging Tips

1. **Check WebSocket Connection:**
   - Open browser DevTools → Network tab
   - Filter by "WS" to see WebSocket connections
   - Check for successful connection and messages

2. **Monitor Console Logs:**
   - Backend logs: Check the Docker container logs for message broadcasts
   - Frontend logs: Check browser console for "Received message:" logs

3. **Redis Connection:**
   - Ensure Redis is running: `docker ps | grep redis`
   - Check backend health: `curl http://localhost:8001/api/health`

### Known Limitations

- Testing in sandbox environments may fail due to Docker restrictions
- Local development testing (without Docker) requires running backend and frontend separately
- Manual testing is the primary validation method as there are no automated tests
