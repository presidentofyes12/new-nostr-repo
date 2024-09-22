const express = require('express');
const { exec } = require('child_process');
const cors = require('cors');
const util = require('util');
const execAsync = util.promisify(exec);

const app = express();

app.use(cors());
app.use(express.json());

// Enable CORS for all routes
app.use(cors());

app.use(express.json());

app.post('/api/create-meshcentral-account', async (req, res) => {
  const { npubKey, nsecKey, email } = req.body;

  if (!npubKey || !nsecKey || !email) {
    return res.status(400).json({ success: false, error: 'Public key, private key, and email are required' });
  }

  try {
    await executeMeshCentralCommands(npubKey, nsecKey, email);
    res.json({ success: true, message: 'MeshCentral account created successfully' });
  } catch (error) {
    console.error('MeshCentral account creation failed:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

function executeMeshCentralCommands(npubKey, nsecKey, email) {
  return new Promise((resolve, reject) => {
    const commands = [
      `node ~/Downloads/Telegram\\ Desktop/nostr-w-relay-main\\ (2)/nostr-w-relay-main/src/meshcentral/node_modules/meshcentral --createaccount ${npubKey} --pass ${nsecKey} --email ${email}`,
      `node ~/Downloads/Telegram\\ Desktop/nostr-w-relay-main\\ (2)/nostr-w-relay-main/src/meshcentral/node_modules/meshcentral --adminaccount ${npubKey}`,
    ];

    const executeCommands = (index) => {
      if (index >= commands.length) {
        resolve();
        return;
      }

      exec(commands[index], (error, stdout, stderr) => {
        if (error) {
          console.error(`Error executing command: ${commands[index]}`);
          console.error(stderr);
          reject(error);
          return;
        }
        console.log(stdout);
        executeCommands(index + 1);
      });
    };

    executeCommands(0);
  });
}

app.post('/api/start-odoo', async (req, res) => {
  const { publicKey, privateKey } = req.body;

  if (!publicKey || !privateKey) {
    return res.status(400).json({ success: false, error: 'Public key and private key are required' });
  }

  try {
    await startOdoo(publicKey, privateKey);
    res.json({ success: true, message: 'Odoo started successfully' });
  } catch (error) {
    console.error('Failed to start Odoo:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

async function startOdoo(publicKey, privateKey) {
  try {
    // Stop and remove existing containers
    await execAsync('sudo podman stop postgres odoo-openeducat || true');
    await execAsync('sudo podman rm postgres odoo-openeducat || true');

    // Start containers
    //const { stdout, stderr } = await execAsync(`sudo ~/Downloads/Telegram\\ Desktop/new/nostr-w-relay-main/src/views/components/login/start-odoo.sh "${publicKey}" "${privateKey}"`);
    const { stdout, stderr } = await execAsync(`sudo ./start-odoo.sh "${publicKey}" "${privateKey}"`);
    console.log('Odoo startup stdout:', stdout);
    if (stderr) {
      console.error('Odoo startup stderr:', stderr);
    }

    // Wait for a moment to allow containers to start
    await new Promise(resolve => setTimeout(resolve, 10000));

    // Check container logs
    const odooLogs = await execAsync('sudo podman logs odoo-openeducat');
    console.log('Odoo container logs:', odooLogs.stdout);
    if (odooLogs.stderr) {
      console.error('Odoo container error logs:', odooLogs.stderr);
    }
  } catch (error) {
    console.error('Error starting Odoo:', error);
    throw error;
  }
}

const checkContainer = async (containerName) => {
  try {
    const { stdout } = await execAsync(`sudo podman ps -a --format '{{.Names}}' --filter name=${containerName}`);
    return stdout.trim() === containerName;
  } catch (error) {
    console.error(`Error checking container ${containerName}:`, error);
    return false;
  }
};

const PORT = process.env.PORT || 5001;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
