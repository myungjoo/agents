# AI Agent Configurator and Simulator

This repository contains a React-based web application that allows you to configure AI agents (defining their role, goal, and tools) and simulate their thought processes using the Google Gemini API. The application leverages Firebase Firestore for persistence of agent configurations.

## Project Structure

```
.
├── public/
│   └── index.html
├── src/
│   └── App.js
│   └── index.js
├── server.js
├── package.json
├── .env.example
├── setup.sh
└── run.sh
```

-   `public/`: Contains the public assets for the React application.
-   `src/`: Contains the React source code.
    -   `App.js`: The main React component for the agent configurator.
    -   `index.js`: Entry point for the React application.
-   `server.js`: A simple Node.js Express server to serve the React build and potentially handle API calls (though direct client-side calls to Gemini are used here).
-   `package.json`: Defines the project dependencies and scripts for the React app and server.
-   `.env.example`: Example file for environment variables (though API key is handled by Canvas).
-   `setup.sh`: Script to prepare your Debian 12 ARM device for running the application.
-   `run.sh`: Script to build and run the application on your Debian 12 ARM device.

## Features

-   **Agent Configuration:** Define agent name, role, goal, and available tools.
-   **Gemini API Integration:** Simulate agent responses based on the defined configuration.
-   **Firebase Persistence:** Agent configurations are automatically saved and loaded using Firestore.
-   **Responsive UI:** Built with React and Tailwind CSS for a modern and adaptive user experience.

## Setup and Running on Debian 12 ARM

Follow these steps to set up and run the application on your Debian 12 ARM device.

### Prerequisites

-   A Debian 12 (Bookworm) ARM device (e.g., Raspberry Pi 4).
-   Internet connectivity.

### 1. Clone the Repository

First, clone this repository to your Debian 12 ARM device:

```bash
git clone <your-repository-url>
cd ai-agent-configurator # Or whatever your repository name is
```

### 2. Setup Script

The `setup.sh` script will install Node.js (via nvm for better version management), npm, and other necessary build tools.

```bash
chmod +x setup.sh
./setup.sh
```

This script will:
-   Update package lists.
-   Install `curl` and `build-essential`.
-   Install `nvm` (Node Version Manager).
-   Install the latest LTS version of Node.js.

**Note:** After running `setup.sh`, you might need to close and reopen your terminal session or run `source ~/.bashrc` (or `source ~/.profile`) to ensure `nvm` and `node` commands are available in your PATH.

### 3. Running Script

The `run.sh` script will install Node.js dependencies, build the React application, and start the Node.js server.

```bash
chmod +x run.sh
./run.sh
```

This script will:
-   Install project dependencies (`npm install`).
-   Build the React front-end (`npm run build`).
-   Start the Express server (`node server.js`).

### 4. Access the Application

Once the `run.sh` script is executing, the server will typically be running on `http://localhost:3000` (or `http://<your-device-ip>:3000`).
Open a web browser on your Debian device or another device on the same network and navigate to the appropriate address.

## Development

If you wish to develop locally (on a machine with Node.js and npm installed):

1.  **Install Dependencies:**
    ```bash
    npm install
    ```
2.  **Run Development Server (React App):**
    ```bash
    npm start
    ```
    This will run the React app in development mode, usually on `http://localhost:3000`.
3.  **Run Backend Server (if needed separately):**
    ```bash
    node server.js
    ```
