# Gradio Widget Development Shim

This development shim allows you to test the Gradio Widget locally without needing ChatGPT integration.

## Usage

```bash
npm run dev:widget
```

Then navigate to `http://localhost:5173/gradio-widget-dev.html`

## How It Works

The shim provides a **generic iframe-based testing environment** for any Skybridge widget component:

1. **Left Panel (60%)**: iframe displaying your widget (`gradio-widget.html`)
2. **Right Panel (40%)**: Interactive controls for testing

### Initialization Flow

```
1. Iframe loads gradio-widget.html
2. Shim injects window.openai mock API
3. Shim auto-sends initial toolOutput data
4. Widget React app initializes with data
5. Hooks (useWidgetProps, etc.) read window.openai
6. Widget renders with test data
```

## Features

- **Live Preview**: Widget loads in isolated iframe (production-like)
- **Interactive Controls**:
  - JSON editor for `toolOutput` (data sent to widget)
  - JSON editor for `widgetState` (bidirectional state)
  - Display mode buttons (inline/fullscreen/pip)
  - Max height slider (400-1200px)
  - Theme toggle (light/dark)
  - Quick presets for common scenarios
- **Auto-initialization**: Initial data sent automatically on load
- **State Persistence**: Test data saved in localStorage
- **Console Logging**: All shim operations logged with `[Shim]` prefix

## Testing Scenarios

### Audio File
```json
{
  "url": "https://example.com/audio.wav"
}
```

### Video File
```json
{
  "url": "https://example.com/video.mp4"
}
```

### Empty State
```json
{}
```

### Custom Data
```json
{
  "url": "https://your-file-url.com/file.ext",
  "metadata": {
    "duration": 120,
    "title": "My Audio"
  }
}
```

## Debugging

Open browser DevTools console to see:
- `[Shim] window.openai initialized in iframe` - Setup complete
- `[Shim] Initial data sent to widget` - Auto-send successful
- `[Shim] Update sent to widget` - Manual update dispatched
- `[Shim] setWidgetState called: {...}` - Widget called setWidgetState

## Architecture

### Shim Component
- `GradioWidgetDevShim.tsx` - Main testing harness
- Mocks `window.openai` API in iframe
- Dispatches `openai:set_globals` CustomEvents
- Manages test state and controls

### Widget Component
- `gradio-widget.html` → `gradio-widget.tsx` → `GradioWidgetApp.tsx`
- Uses hooks: `useWidgetProps`, `useDisplayMode`, `useMaxHeight`
- Hooks subscribe to `openai:set_globals` events via `useSyncExternalStore`
- Reactively updates when shim sends new data

### Event Flow
```
Shim (parent window)
  ↓ iframe.contentWindow.openai = {...}
  ↓ new CustomEvent('openai:set_globals')
  ↓ iframeWindow.dispatchEvent(event)
  ↓
Widget (iframe)
  ← useSyncExternalStore listens to events
  ← Hook triggers re-render
  ← Component updates with new data
```

## Extending for Other Widgets

This is a **generic shim** that can test any Skybridge widget:

1. Change iframe `src` to your widget HTML
2. Adjust `DEFAULT_TOOL_OUTPUT` for your widget's data shape
3. Add widget-specific controls if needed
4. All OpenAI SDK hooks work automatically!

## Production vs Development

| Aspect | Development (Shim) | Production (ChatGPT) |
|--------|-------------------|---------------------|
| Data Source | JSON textarea | ChatGPT tool output |
| window.openai | Mocked by shim | Provided by ChatGPT |
| Events | Manually triggered | Triggered by ChatGPT |
| Isolation | Iframe sandbox | Iframe sandbox |
| Behavior | **Identical** | **Identical** |

The widget behaves identically in both environments because:
- Same hooks (useWidgetProps, etc.)
- Same event system (openai:set_globals)
- Same isolation (iframe)
- Same API (window.openai)
