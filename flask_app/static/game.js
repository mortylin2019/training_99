const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreDisplay = document.getElementById('score');

const SCREEN_WIDTH = 320;
const SCREEN_HEIGHT = 240;

// Game State
let gameState = 'MENU'; // MENU, PLAYING, GAMEOVER
let score = 0;
let lastTime = 0;

// Player
const player = {
    x: SCREEN_WIDTH / 2,
    y: SCREEN_HEIGHT - 30,
    width: 16,
    height: 16,
    speed: 150, // pixels per second
    color: '#00ff00'
};

// Input
const keys = {
    ArrowUp: false,
    ArrowDown: false,
    ArrowLeft: false,
    ArrowRight: false,
    Space: false
};

// Entities
const entities = [];
const MAX_ENTITIES = 300;

document.addEventListener('keydown', (e) => {
    if (keys.hasOwnProperty(e.code)) {
        keys[e.code] = true;
    }
    if (e.code === 'Space' && gameState !== 'PLAYING') {
        startGame();
    }
});

document.addEventListener('keyup', (e) => {
    if (keys.hasOwnProperty(e.code)) {
        keys[e.code] = false;
    }
});

function startGame() {
    gameState = 'PLAYING';
    score = 0;
    entities.length = 0;
    player.x = SCREEN_WIDTH / 2;
    player.y = SCREEN_HEIGHT - 30;
    lastTime = performance.now();
    requestAnimationFrame(gameLoop);
}

function spawnEntity() {
    if (entities.length >= MAX_ENTITIES) return;

    // Random spawn position at top
    const x = Math.random() * (SCREEN_WIDTH - 10);
    const y = -10;
    
    // Type: 0 = Linear Down, 1 = Homing, 2 = Bouncing
    const type = Math.floor(Math.random() * 3);
    
    entities.push({
        x: x,
        y: y,
        width: 8,
        height: 8,
        vx: (Math.random() - 0.5) * 50,
        vy: 30 + Math.random() * 50,
        type: type,
        color: type === 1 ? '#ff0000' : (type === 2 ? '#ffff00' : '#ffa500')
    });
}

function update(dt) {
    if (gameState !== 'PLAYING') return;

    // Player Movement
    if (keys.ArrowLeft) player.x -= player.speed * dt;
    if (keys.ArrowRight) player.x += player.speed * dt;
    if (keys.ArrowUp) player.y -= player.speed * dt;
    if (keys.ArrowDown) player.y += player.speed * dt;

    // Clamp Player Position
    player.x = Math.max(0, Math.min(SCREEN_WIDTH - player.width, player.x));
    player.y = Math.max(0, Math.min(SCREEN_HEIGHT - player.height, player.y));

    // Spawn Entities
    if (Math.random() < 0.05) { // Spawn rate
        spawnEntity();
    }

    // Update Entities
    for (let i = entities.length - 1; i >= 0; i--) {
        const ent = entities[i];
        
        if (ent.type === 1) { // Homing
            const dx = player.x - ent.x;
            const dy = player.y - ent.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist > 0) {
                ent.vx += (dx / dist) * 100 * dt;
                ent.vy += (dy / dist) * 100 * dt;
                // Cap speed
                const speed = Math.sqrt(ent.vx*ent.vx + ent.vy*ent.vy);
                if (speed > 80) {
                    ent.vx = (ent.vx / speed) * 80;
                    ent.vy = (ent.vy / speed) * 80;
                }
            }
        } else if (ent.type === 2) { // Bouncing
            if (ent.x <= 0 || ent.x >= SCREEN_WIDTH - ent.width) {
                ent.vx *= -1;
            }
        }

        ent.x += ent.vx * dt;
        ent.y += ent.vy * dt;

        // Collision Check
        if (
            player.x < ent.x + ent.width &&
            player.x + player.width > ent.x &&
            player.y < ent.y + ent.height &&
            player.y + player.height > ent.y
        ) {
            gameState = 'GAMEOVER';
        }

        // Remove off-screen entities
        if (ent.y > SCREEN_HEIGHT + 20 || ent.y < -50 || ent.x < -50 || ent.x > SCREEN_WIDTH + 50) {
            entities.splice(i, 1);
            score += 10;
        }
    }
}

function draw() {
    // Clear Screen
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

    if (gameState === 'MENU') {
        ctx.fillStyle = '#ffffff';
        ctx.font = '20px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('TOKKUN REMAKE', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20);
        ctx.font = '14px Arial';
        ctx.fillText('Press SPACE to Start', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20);
        return;
    }

    if (gameState === 'GAMEOVER') {
        ctx.fillStyle = '#ff0000';
        ctx.font = '20px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20);
        ctx.fillStyle = '#ffffff';
        ctx.font = '14px Arial';
        ctx.fillText(`Final Score: ${score}`, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 10);
        ctx.fillText('Press SPACE to Restart', SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40);
        return;
    }

    // Draw Player
    ctx.fillStyle = player.color;
    ctx.fillRect(player.x, player.y, player.width, player.height);

    // Draw Entities
    for (const ent of entities) {
        ctx.fillStyle = ent.color;
        ctx.fillRect(ent.x, ent.y, ent.width, ent.height);
    }
    
    // Update Score Display HTML
    scoreDisplay.innerText = `Score: ${score}`;
}

function gameLoop(timestamp) {
    const dt = (timestamp - lastTime) / 1000;
    lastTime = timestamp;

    update(dt);
    draw();

    if (gameState === 'PLAYING' || gameState === 'GAMEOVER') {
        requestAnimationFrame(gameLoop);
    }
}

// Initial Draw
draw();
