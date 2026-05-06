# AOT Web Interface Deployment Guide

This guide describes how to deploy and run the web-based morphological and syntactic analysis interface for the AOT project.

## Components

The AOT web stack consists of two main parts:
1.  **Backend (`SynanDaemon`)**: A C++ HTTP server that provides morphological and syntactic analysis.
2.  **Frontend (`wwwroot`)**: A collection of HTML/JavaScript files that interact with the backend via AJAX.

---

## 1. Backend Setup (`SynanDaemon`)

### Building
The backend is built as part of the main CMake project.
```bash
mkdir build
cd build
cmake ..
make SynanDaemon
```

### Configuration (`rml.ini`)
Ensure `Bin/rml.ini` (or the file pointed to by the `RML` environment variable) contains the correct paths to your dictionaries.
```ini
[Software\Dialing\Lemmatizer]
Russian\DictPath = /path/to/Dicts/Morph/Russian/
German\DictPath = /path/to/Dicts/Morph/German/
English\DictPath = /path/to/Dicts/Morph/English/
Ukrainian\DictPath = /path/to/Dicts/Morph/Ukrainian/
```

### Running
Run the daemon on a specific port (e.g., 8089).
```bash
./Bin/SynanDaemon --host 127.0.0.1 --port 8089
```

---

## 2. Frontend Setup (`wwwroot`)

The frontend files are located in `Source/www/wwwroot`.

### Configuration (`common.js`)
You must configure the frontend to talk to your `SynanDaemon` instance. Edit `Source/www/wwwroot/demo/common.js`:
```javascript
export var SynanDaemonUrl = 'http://localhost:8089?dummy=1';
```

### Serving Static Files
You can serve the `wwwroot` directory using any web server. For development, a simple Python server works well:
```bash
python3 -m http.server 8080 --directory Source/www/wwwroot
```
The interface will then be available at:
- Morphology Demo: `http://localhost:8080/demo/morph.html`
- Syntax Demo (Visualizer): `http://localhost:8080/demo/synt.html`

---

## 3. Production Deployment (Nginx)

For production, it is recommended to use Nginx as a reverse proxy to handle both static files and API requests.

Example Nginx configuration (`/etc/nginx/sites-available/aot`):

```nginx
server {
    listen 80;
    server_name aot.example.com;

    # Static frontend files
    location / {
        root /path/to/aot/Source/www/wwwroot;
        index index.html;
    }

    # Proxy morphology/syntax requests to SynanDaemon
    location /api/synan {
        proxy_pass http://127.0.0.1:8089;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Add CORS if needed (SynanDaemon already adds them)
        # add_header 'Access-Control-Allow-Origin' '*';
    }
}
```

## 4. Troubleshooting

- **CORS Errors**: If you access the frontend from a different domain/port than the daemon, ensure `SynanDaemon` is sending `Access-Control-Allow-Origin` headers (this is enabled by default in recent versions).
- **Empty Reply**: Check `synan.log` for crashes. Ensure dictionaries are correctly loaded and `rml.ini` paths are absolute.
- **Missing Characters**: Verify the alphabet mapping in `Source/morph_dict/common/single_byte_encoding.cpp`.
