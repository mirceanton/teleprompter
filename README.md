# Remote Teleprompter

A **multi-device** teleprompter application that enables real-time teleprompter control between devices. One device (computer) acts as a controller to edit scripts and manage playback, while one or more other devices (phones/tablets) display the teleprompter text.

This project has been made to facilitate recording videos for my YouTube channel where I am using my phone on a basic teleprompter in front of my camera and I need to control it from my computer which is recording everything via OBS. With this project, I can simply navigate to a URL on my phone and place it on the prompter and then manage everything from my computer, not having to touch the phone anymore until I'm done.

Multiple teleprompter clients are also supported to account for situations like multi-camera setups with multiple teleprompters.

## 📸 Screenshots

<table>
  <tr>
    <td align="center"><b>Landing Page</b></td>
    <td align="center"><b>Controller Mode</b></td>
    <td align="center"><b>Teleprompter Mode</b></td>
  </tr>
  <tr>
    <td><img src=".img/landing.png" alt="Landing Page" width="300"/></td>
    <td><img src=".img/controller.png" alt="Controller Mode" width="300"/></td>
    <td><img src=".img/teleprompter.png" alt="Teleprompter Mode" width="300"/></td>
  </tr>
  <tr>
    <td align="center">Select your role to get started</td>
    <td align="center">Edit scripts and control playback</td>
    <td align="center">Display the scrolling text</td>
  </tr>
</table>

## ✨ Features

- **Multi-Device Synchronization**: Control teleprompter text from one device while displaying on one or more other devices
- **Real-Time Editing**: Edit scripts with instant synchronization across all connected devices
- **Playback Controls**: Start, pause, reset, and navigate through scripts with smooth scrolling
- **Customizable Display**: Adjust text size, width, scrolling speed, and mirror settings
- **Multi-Camera Support**: Connect multiple teleprompter displays for multi-camera setups
- **Optional OBS Studio Integration**: Automatically control OBS recording based on teleprompter playback with configurable delays and confirmation modes

## 🎯 Requirements

- Docker
- Docker Compose

## 🚀 Deployment Options

This project provides an example Docker Compose configuration via [`compose.yaml`](./compose.yaml). It will spin up:

- a container for the frontend application, using the `ghcr.io/mirceanton/teleprompter-frontend:latest` image
- a container for the backend application, using the `ghcr.io/mirceanton/teleprompter-backend:latest` image
- a container for Redis, using the `docker.io/redis` image
- a container for the OBS bridge (optional), using the `ghcr.io/mirceanton/teleprompter-obs-bridge:latest` image

> [!NOTE]
> **About Redis:**
>
> Redis is used to synchronize state across multiple backend instances when running in a scaled/load-balanced environment (e.g., Kubernetes deployments with multiple replicas). If you're running a single backend instance (e.g. most if not all docker compose scenarios), Redis is **optional** and can be removed. To run without Redis, simply delete the `redis` service section and remove the `depends_on` and `environment` sections from the backend service in `compose.yaml`.

> [!NOTE]
> **About OBS Bridge:**
>
> The OBS bridge service is optional and provides automatic recording control when using OBS Studio. The system works perfectly fine without it. If you don't need OBS integration, you can remove the `obs-bridge` service from `compose.yaml`.

If you prefer to build the images locally instead of using the prebuilt ones, you can apply the `-f compose.dev.yaml` overlay to your command.

## ⚙️ Configuration Options

### Configuring the Frontend

The frontend is a basic static site built using VueJS and then served via an NGINX container. Thus, it can't really take in environment variables to customize, for example, the URL at which the API is located. Thus, it loads the configuration at runtime via a `config.json` file.

This file is located at `/usr/share/nginx/html/config.json`. Its main purpose right now is to point the frontend to the right URL for the backend API. Since this is a static site served by NGINX, this means that the code runs in your browser, not on the server. This is important because it essentially means `localhost` ain't cutting it. You need to provide the actual hostname and port at which the backend is running. For example:

```jsonc
{
  // this is where the backend is found
  "backendUrl": "http://192.168.1.2:8001"
}
```

### Configuring the Backend

| Environment Variable | Description                                                           | Required | Default Value |
| -------------------- | --------------------------------------------------------------------- | :------: | ------------- |
| `REDIS_HOST`         | Hostname or IP address of the Redis server                            |    No    | `redis`       |
| `REDIS_PORT`         | Port number on which Redis is listening                               |    No    | `6379`        |
| `REDIS_PASSWORD`     | Password for authenticating with Redis (if authentication is enabled) |    No    | N/A           |
| `REDIS_DB`           | Redis database number to use (0-15)                                   |    No    | `0`           |

### OBS Integration (Optional)

The OBS bridge service enables automatic recording control when using OBS Studio. To use this feature:

1. Install the [obs-websocket plugin](https://github.com/obsproject/obs-websocket/releases) (v5.x) in OBS Studio
2. Configure OBS WebSocket server (Tools → WebSocket Server Settings)
3. Set the following environment variables for the `obs-bridge` service:

| Environment Variable | Description                                              | Required | Default Value         |
| -------------------- | -------------------------------------------------------- | :------: | --------------------- |
| `BACKEND_WS_URL`     | WebSocket URL of the teleprompter backend                |    No    | `ws://backend:8001/api/ws` |
| `OBS_HOST`           | Hostname or IP address where OBS Studio is running       |    No    | `host.docker.internal` |
| `OBS_PORT`           | Port number for OBS WebSocket server                     |    No    | `4455`                |
| `OBS_PASSWORD`       | Password for OBS WebSocket (if authentication enabled)   |    No    | (empty)               |

**Features:**
- Auto-start recording when teleprompter playback begins
- Auto-stop recording when teleprompter is reset
- Auto-pause recording when teleprompter is paused
- Configurable countdown delay before starting (0-10 seconds)
- Optional "wait for OBS confirmation" mode for guaranteed synchronization
- Visual recording indicators on both controller and teleprompter displays

## 📝 License

This code has been mostly AI generated and used as a playground/testbed for GitHub copilot. My manual intervention in here has been more or less minimal, mostly doing cleanup here and there. Thus, I take no "ownership" over this code. I did not write it, it is not "mine". Feel free to do whatever. As the [LICENSE](./LICENSE) states: "This is free and unencumbered software released into the public domain".
