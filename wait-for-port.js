import net from 'net';

const port = parseInt(process.argv[2] || '3000', 10);
const timeout = parseInt(process.argv[3] || '60000', 10);
const start = Date.now();

function wait() {
  return new Promise((resolve, reject) => {
    const socket = new net.Socket();
    socket.connect(port, '127.0.0.1', () => {
      socket.destroy();
      resolve();
    });
    socket.on('error', () => {
      socket.destroy();
      if (Date.now() - start > timeout) {
        reject(new Error(`Timeout waiting for port ${port}`));
      } else {
        setTimeout(wait, 200);
      }
    });
  });
}

wait()
  .then(() => {
    console.log(`Port ${port} is ready`);
    process.exit(0);
  })
  .catch((err) => {
    console.error(err.message);
    process.exit(1);
  });
