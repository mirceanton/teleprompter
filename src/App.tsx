import React, { useState, useCallback, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket'
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Rewind, 
  FastForward, 
  RefreshCw, 
  X, 
  Smartphone, 
  Monitor,
  Minus,
  Plus
} from 'lucide-react'

type Mode = 'controller' | 'teleprompter' | null

const App: React.FC = () => {
  // UI state
  const [mode, setMode] = useState<Mode>(null)
  const [channel, setChannel] = useState('')
  const [script, setScript] = useState(`Welcome to Remote Teleprompter!

This is your teleprompter script. Edit this text on your computer, and it will appear on your phone's screen.

Instructions:
1. Use the same channel name on both devices
2. Select "Controller Mode" on your computer
3. Select "Teleprompter Mode" on your phone
4. Click Connect on both devices
5. Start controlling your teleprompter remotely!

The text will sync automatically as you type. Use the controls below to manage scrolling speed and playback.

Happy recording! 🎬`)

  // Teleprompter state
  const [isScrolling, setIsScrolling] = useState(false)
  const [scrollPosition, setScrollPosition] = useState(0)
  const [scrollSpeed, setScrollSpeed] = useState([5])
  const [fontSize, setFontSize] = useState(2.5)
  const [textWidth, setTextWidth] = useState([100])
  const [horizontalMirror, setHorizontalMirror] = useState(false)
  const [verticalMirror, setVerticalMirror] = useState(false)

  // Refs
  const animationRef = useRef<number | undefined>(undefined)
  const syncTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  // WebSocket message handler
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'text':
        setScript(message.text)
        break
      case 'start':
        setIsScrolling(true)
        break
      case 'pause':
        setIsScrolling(false)
        break
      case 'reset':
        setScrollPosition(0)
        setIsScrolling(false)
        break
      case 'rewind':
        setScrollPosition(prev => Math.min(prev + scrollSpeed[0] * 50, 0))
        break
      case 'fastforward':
        setScrollPosition(prev => prev - scrollSpeed[0] * 50)
        break
      case 'speed':
        setScrollSpeed([message.value])
        break
      case 'width':
        setTextWidth([message.value])
        break
      case 'fontsize':
        setFontSize(message.value)
        break
      case 'mirror':
        setHorizontalMirror(message.horizontal)
        setVerticalMirror(message.vertical)
        break
    }
  }, [scrollSpeed])

  const { connectionStatus, connect, sendMessage } = useWebSocket(handleMessage)

  // Generate random channel name on load
  useEffect(() => {
    const randomChannel = 'room-' + Math.random().toString(36).substring(2, 8)
    setChannel(randomChannel)
  }, [])

  // Auto-sync text with debounce
  useEffect(() => {
    if (mode === 'controller' && connectionStatus === 'connected') {
      clearTimeout(syncTimeoutRef.current)
      syncTimeoutRef.current = setTimeout(() => {
        sendMessage({ type: 'text', text: script })
      }, 300)
    }
  }, [script, mode, connectionStatus, sendMessage])

  // Teleprompter animation
  useEffect(() => {
    if (isScrolling && mode === 'teleprompter') {
      const animate = () => {
        setScrollPosition(prev => {
          const newPosition = prev - (scrollSpeed[0] / 10)
          // Check boundaries (simplified for now)
          return newPosition
        })
        animationRef.current = requestAnimationFrame(animate)
      }
      animationRef.current = requestAnimationFrame(animate)
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [isScrolling, mode, scrollSpeed])

  // Control functions
  const handleConnect = () => {
    if (!channel.trim()) {
      alert('Please enter a channel name')
      return
    }
    if (!mode) {
      alert('Please select a mode first')
      return
    }
    connect(channel.trim())
  }

  const handleStart = () => {
    setIsScrolling(true)
    sendMessage({ type: 'start' })
  }

  const handlePause = () => {
    setIsScrolling(false)
    sendMessage({ type: 'pause' })
  }

  const handleReset = () => {
    setScrollPosition(0)
    setIsScrolling(false)
    sendMessage({ type: 'reset' })
  }

  const handleRewind = () => {
    const newPosition = Math.min(scrollPosition + scrollSpeed[0] * 50, 0)
    setScrollPosition(newPosition)
    sendMessage({ type: 'rewind' })
  }

  const handleFastForward = () => {
    const newPosition = scrollPosition - scrollSpeed[0] * 50
    setScrollPosition(newPosition)
    sendMessage({ type: 'fastforward' })
  }

  const handleSpeedChange = (value: number[]) => {
    setScrollSpeed(value)
    sendMessage({ type: 'speed', value: value[0] })
  }

  const handleWidthChange = (value: number[]) => {
    setTextWidth(value)
    sendMessage({ type: 'width', value: value[0] })
  }

  const handleFontSizeChange = (delta: number) => {
    const newSize = Math.max(1, Math.min(8, fontSize + delta))
    setFontSize(newSize)
    sendMessage({ type: 'fontsize', value: newSize })
  }

  const handleMirrorChange = (horizontal: boolean, vertical: boolean) => {
    setHorizontalMirror(horizontal)
    setVerticalMirror(vertical)
    sendMessage({ type: 'mirror', horizontal, vertical })
  }

  const syncText = () => {
    sendMessage({ type: 'text', text: script })
  }

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-400'
      case 'connecting': return 'text-yellow-400'
      default: return 'text-red-400'
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return `Connected - ${mode?.toUpperCase()} Mode`
      case 'connecting': return 'Connecting...'
      default: return 'Not Connected'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-blue-900 text-white">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <Card className="mb-8 bg-gradient-to-r from-blue-600 to-purple-600 border-0">
          <CardHeader className="text-center">
            <CardTitle className="text-4xl mb-2 text-white">📱 Remote Teleprompter</CardTitle>
            <CardDescription className="text-blue-100 text-lg">
              Control your phone's teleprompter from your computer
            </CardDescription>
          </CardHeader>
        </Card>

        {/* Mode Selector */}
        <div className="flex gap-4 justify-center mb-8">
          <Button
            variant={mode === 'controller' ? 'default' : 'outline'}
            size="lg"
            onClick={() => setMode('controller')}
            className="flex items-center gap-2"
          >
            <Monitor className="w-5 h-5" />
            Controller Mode
          </Button>
          <Button
            variant={mode === 'teleprompter' ? 'default' : 'outline'}
            size="lg"
            onClick={() => setMode('teleprompter')}
            className="flex items-center gap-2"
          >
            <Smartphone className="w-5 h-5" />
            Teleprompter Mode
          </Button>
        </div>

        {/* Connection Panel */}
        <Card className="mb-8">
          <CardContent className="pt-6">
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <Label htmlFor="channel">Channel Name</Label>
                <Input
                  id="channel"
                  value={channel}
                  onChange={(e) => setChannel(e.target.value)}
                  placeholder="Enter a unique channel name"
                  onKeyDown={(e) => e.key === 'Enter' && handleConnect()}
                />
              </div>
              <Button onClick={handleConnect} size="lg">
                Connect to Channel
              </Button>
            </div>
            <div className={`mt-4 text-center font-medium ${getStatusColor()}`}>
              {getStatusText()}
            </div>
          </CardContent>
        </Card>

        {/* Controller Panel */}
        {mode === 'controller' && connectionStatus === 'connected' && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>📝 Script Editor</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <Textarea
                value={script}
                onChange={(e) => setScript(e.target.value)}
                placeholder="Paste or type your script here..."
                className="min-h-[400px] font-mono text-lg leading-relaxed"
              />

              {/* Control Buttons */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <Button onClick={handleStart} variant="default" className="flex items-center gap-2">
                  <Play className="w-4 h-4" />
                  Start
                </Button>
                <Button onClick={handlePause} variant="secondary" className="flex items-center gap-2">
                  <Pause className="w-4 h-4" />
                  Pause
                </Button>
                <Button onClick={handleReset} variant="secondary" className="flex items-center gap-2">
                  <RotateCcw className="w-4 h-4" />
                  Reset
                </Button>
                <Button onClick={handleRewind} variant="secondary" className="flex items-center gap-2">
                  <Rewind className="w-4 h-4" />
                  Rewind
                </Button>
                <Button onClick={handleFastForward} variant="secondary" className="flex items-center gap-2">
                  <FastForward className="w-4 h-4" />
                  Fast Forward
                </Button>
                <Button onClick={syncText} variant="outline" className="flex items-center gap-2">
                  <RefreshCw className="w-4 h-4" />
                  Sync Text
                </Button>
              </div>

              {/* Controls */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Speed Control */}
                <div className="space-y-2">
                  <Label>Speed: {scrollSpeed[0]}</Label>
                  <Slider
                    value={scrollSpeed}
                    onValueChange={handleSpeedChange}
                    max={10}
                    min={1}
                    step={1}
                    className="w-full"
                  />
                </div>

                {/* Text Width Control */}
                <div className="space-y-2">
                  <Label>Text Width: {textWidth[0]}%</Label>
                  <Slider
                    value={textWidth}
                    onValueChange={handleWidthChange}
                    max={100}
                    min={30}
                    step={10}
                    className="w-full"
                  />
                </div>

                {/* Font Size Control */}
                <div className="space-y-2">
                  <Label>Font Size: {fontSize.toFixed(1)}em</Label>
                  <div className="flex items-center gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleFontSizeChange(-0.2)}
                    >
                      <Minus className="w-4 h-4" />
                    </Button>
                    <span className="flex-1 text-center">{fontSize.toFixed(1)}em</span>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleFontSizeChange(0.2)}
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Mirror Controls */}
              <div className="space-y-4">
                <Label className="text-lg">Mirror Controls</Label>
                <div className="flex gap-6">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="horizontal-mirror"
                      checked={horizontalMirror}
                      onCheckedChange={(checked) => handleMirrorChange(checked, verticalMirror)}
                    />
                    <Label htmlFor="horizontal-mirror">Horizontal</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="vertical-mirror"
                      checked={verticalMirror}
                      onCheckedChange={(checked) => handleMirrorChange(horizontalMirror, checked)}
                    />
                    <Label htmlFor="vertical-mirror">Vertical</Label>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Teleprompter Panel */}
        {mode === 'teleprompter' && connectionStatus === 'connected' && (
          <div className="fixed inset-0 bg-black z-50 flex flex-col">
            {/* Teleprompter Controls */}
            <div className="flex justify-between items-center p-4 bg-black/50">
              <div className="flex gap-2">
                <Button 
                  variant="secondary" 
                  size="sm" 
                  onClick={() => setMode(null)}
                  className="flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  Exit
                </Button>
                <Button 
                  variant="secondary" 
                  size="sm" 
                  onClick={() => handleMirrorChange(!horizontalMirror, verticalMirror)}
                  className="flex items-center gap-2"
                >
                  🔄 Mirror
                </Button>
              </div>

              {/* Quick Controls */}
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleFontSizeChange(-0.2)}
                >
                  <Minus className="w-4 h-4" />
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleFontSizeChange(0.2)}
                >
                  <Plus className="w-4 h-4" />
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleWidthChange([Math.max(30, textWidth[0] - 10)])}
                >
                  ◀
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleWidthChange([Math.min(100, textWidth[0] + 10)])}
                >
                  ▶
                </Button>
              </div>
            </div>

            {/* Mirror Indicator */}
            {(horizontalMirror || verticalMirror) && (
              <div className="text-center py-2 bg-yellow-600 text-black font-bold">
                MIRROR MODE
              </div>
            )}

            {/* Teleprompter Text */}
            <div className="flex-1 overflow-hidden relative flex items-center justify-center p-8">
              <div 
                className="teleprompter-content whitespace-pre-wrap text-center leading-relaxed transition-transform duration-100 ease-linear"
                style={{
                  fontSize: `${fontSize}em`,
                  width: `${textWidth[0]}%`,
                  transform: `
                    translateY(${scrollPosition}px) 
                    ${horizontalMirror && verticalMirror ? 'scale(-1, -1)' : 
                      horizontalMirror ? 'scaleX(-1)' : 
                      verticalMirror ? 'scaleY(-1)' : ''}
                  `,
                }}
              >
                {script || 'Waiting for text from controller...'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App