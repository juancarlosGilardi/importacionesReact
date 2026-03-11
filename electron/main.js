const { app, BrowserWindow, Menu, shell, dialog } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");

let mainWindow;
let backendProcess = null;

const isDev = !app.isPackaged;
const BACKEND_PORT = 8000;
const FRONTEND_DEV_URL = "http://localhost:5173";

function getBackendPath() {
  if (isDev) {
    return path.join(__dirname, "..", "backend");
  }
  return path.join(process.resourcesPath, "backend");
}

function startBackend() {
  const backendPath = getBackendPath();
  const mainModule = path.join(backendPath, "app", "main.py");

  if (!fs.existsSync(mainModule)) {
    console.warn("Backend not found at:", mainModule);
    return null;
  }

  const pythonCmd = process.platform === "win32" ? "python" : "python3";

  const proc = spawn(
    pythonCmd,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)],
    {
      cwd: backendPath,
      env: { ...process.env },
      stdio: ["pipe", "pipe", "pipe"],
    }
  );

  proc.stdout.on("data", (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  proc.stderr.on("data", (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  proc.on("error", (err) => {
    console.error("Failed to start backend:", err.message);
  });

  proc.on("exit", (code) => {
    console.log(`Backend exited with code ${code}`);
    backendProcess = null;
  });

  return proc;
}

function stopBackend() {
  if (backendProcess) {
    if (process.platform === "win32") {
      spawn("taskkill", ["/pid", String(backendProcess.pid), "/f", "/t"]);
    } else {
      backendProcess.kill("SIGTERM");
    }
    backendProcess = null;
  }
}

function createSplashWindow() {
  const splash = new BrowserWindow({
    width: 400,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    webPreferences: { nodeIntegration: false },
  });

  const splashPath = path.join(__dirname, "splash.html");
  if (fs.existsSync(splashPath)) {
    splash.loadFile(splashPath);
  }
  return splash;
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    show: false,
    title: "ImportCost Pro",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Menu personalizado
  const menuTemplate = [
    {
      label: "Archivo",
      submenu: [
        { label: "Recargar", accelerator: "F5", click: () => mainWindow.reload() },
        { type: "separator" },
        { label: "Salir", accelerator: "Alt+F4", click: () => app.quit() },
      ],
    },
    {
      label: "Ver",
      submenu: [
        { label: "Zoom +", accelerator: "CmdOrCtrl+Plus", click: () => mainWindow.webContents.setZoomLevel(mainWindow.webContents.getZoomLevel() + 0.5) },
        { label: "Zoom -", accelerator: "CmdOrCtrl+-", click: () => mainWindow.webContents.setZoomLevel(mainWindow.webContents.getZoomLevel() - 0.5) },
        { label: "Zoom Reset", accelerator: "CmdOrCtrl+0", click: () => mainWindow.webContents.setZoomLevel(0) },
        { type: "separator" },
        { label: "Pantalla Completa", accelerator: "F11", click: () => mainWindow.setFullScreen(!mainWindow.isFullScreen()) },
      ],
    },
    {
      label: "Herramientas",
      submenu: [
        { label: "DevTools", accelerator: "F12", click: () => mainWindow.webContents.toggleDevTools() },
      ],
    },
    {
      label: "Ayuda",
      submenu: [
        { label: "Acerca de ImportCost Pro", click: () => dialog.showMessageBox(mainWindow, { type: "info", title: "ImportCost Pro", message: "ImportCost Pro v1.0.0\nSistema de Importaciones y Costeo" }) },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(menuTemplate);
  Menu.setApplicationMenu(menu);

  // Abrir links externos en el navegador
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  return mainWindow;
}

async function waitForBackend(maxRetries = 30, interval = 1000) {
  const http = require("http");

  for (let i = 0; i < maxRetries; i++) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/api/health`, (res) => {
          if (res.statusCode === 200) resolve();
          else reject(new Error(`Status ${res.statusCode}`));
        });
        req.on("error", reject);
        req.setTimeout(2000, () => { req.destroy(); reject(new Error("Timeout")); });
      });
      return true;
    } catch {
      await new Promise((r) => setTimeout(r, interval));
    }
  }
  return false;
}

app.whenReady().then(async () => {
  const splash = createSplashWindow();
  const win = createMainWindow();

  // Iniciar backend
  backendProcess = startBackend();

  if (isDev) {
    // En desarrollo, cargar desde Vite dev server
    win.loadURL(FRONTEND_DEV_URL);
    win.show();
    splash.close();
  } else {
    // En produccion, esperar al backend y cargar build
    const backendReady = await waitForBackend();
    if (!backendReady) {
      console.warn("Backend did not start in time, loading frontend anyway");
    }

    const indexPath = path.join(__dirname, "web-dist", "index.html");
    if (fs.existsSync(indexPath)) {
      win.loadFile(indexPath);
    } else {
      win.loadURL(`http://127.0.0.1:${BACKEND_PORT}`);
    }

    win.once("ready-to-show", () => {
      splash.close();
      win.show();
    });
  }
});

app.on("window-all-closed", () => {
  stopBackend();
  app.quit();
});

app.on("before-quit", () => {
  stopBackend();
});
